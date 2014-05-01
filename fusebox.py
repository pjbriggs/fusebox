#!/usr/bin/env python
#
# Proof of concept implementation of a virtual filesystem to give
# access to actual files using a per-file permissions system that
# allows access to be granted on a per-user basis
#
# The aim is to allow a more flexible access system than is catered
# for under Linux
#
# The implementation is based on FUSE and uses the Python interface
# from fusepy: https://github.com/terencehonles/fusepy
# fusepy can also be installed directly from PyPI using pip
#
# My code was derived from Stavros Korokithakis' example 'Passthrough'
# implementation: http://www.stavros.io/posts/python-fuse-filesystem/
# This version is heavily modified

from __future__ import with_statement

import os
import sys
import errno
import logging
import optparse

from fuse import FUSE, FuseOSError, Operations, fuse_get_context
from boxfs import BoxFS

class FuseBox(Operations):

    def __init__(self,conf_file=None):
        self.boxfs = BoxFS()
        if conf_file is not None:
            self.read_conf_file(conf_file)

    def read_conf_file(self,conf_file):
        # Conf file is tab-delimited
        # Lines starting with # are comments, blank lines are ignored
        # Lines starting with USER define user name and UID
        # Lines starting with FILE define files, targets and permissions
        for line in open(conf_file,'r'):
            if line.startswith('#') or line.strip() == '':
                continue
            elif line.startswith('USER'):
                # e.g. USER    pjb     1000
                fields = line.strip().split('\t')
                if len(fields) == 3:
                    self.boxfs.add_user(fields[1],int(fields[2]))
                else:
                    logging.error("Bad line: %s" % line.strip())
                    continue
            elif line.startswith('FILE'):
                # e.g. FILE    virtfile    /actual/file     1000
                fields = line.strip().split('\t')
                if len(fields) == 4:
                    access = [int(x) for x in fields[3].split(',')]
                    self.boxfs.add_file(fields[1],fields[2],access=access)
                else:
                    logging.error("Bad line: %s" % line.strip())
                    continue
            else:
                logging.error("Unrecognised line: %s" % line.strip())
                continue

    def context_uid(self):
        cxt = fuse_get_context()
        return cxt[0]

    def has_permission(self,path):
        uid = self.context_uid()
        return self.boxfs.has_permission(path,uid)

    # Filesystem methods
    # ==================

    def access(self, path, mode):
        logging.debug("ACCESS %s %s" % (path,mode))
        if self.boxfs.is_file(path) and self.has_permission(path):
            if not os.access(self.boxfs.target_for(path),mode):
                raise FuseOSError(errno.EACCES)
        elif not self.boxfs.is_dir(path) and self.has_permission(path):
                raise FuseOSError(errno.EACCES)

    def chmod(self, path, mode):
        raise NotImplementedError

    def chown(self, path, uid, gid):
        raise NotImplementedError

    def getattr(self, path, fh=None):
        logging.debug("GETATTR %s %s" % (path,fh))
        try:
            full_path = self.boxfs.target_for(path)
        except KeyError:
            full_path = os.getcwd()
        st = os.lstat(full_path)
        return dict((key, getattr(st, key)) for key in ('st_atime', 'st_ctime',
                                                        'st_gid', 'st_mode', 'st_mtime',
                                                        'st_nlink', 'st_size', 'st_uid',
                                                        'st_blocks','st_blksize'))

    def readdir(self, path, fh):
        logging.debug("READDIR %s %s" % (path,fh))
        dirents = ['.', '..']
        if self.boxfs.is_dir(path):
            for d in self.boxfs.list_dir(path):
                if self.has_permission(os.path.join(path,d)):
                    dirents.append(d)
            logging.debug("READDIR dirents %s" % dirents)
        for r in dirents:
            logging.debug("-> yielding %s" % r)
            yield r

    def readlink(self, path):
        raise NotImplementedError

    def mknod(self, path, mode, dev):
        raise NotImplementedError

    def rmdir(self, path):
        raise NotImplementedError

    def mkdir(self, path, mode):
        raise NotImplementedError

    def statfs(self, path):
        logging.debug("STATFS %s" % path)
        try:
            full_path = self.boxfs.target_for(path)
        except KeyError:
            full_path = os.getcwd()
        stv = os.statvfs(full_path)
        return dict((key, getattr(stv, key)) for key in ('f_bavail', 'f_bfree',
            'f_blocks', 'f_bsize', 'f_favail', 'f_ffree', 'f_files', 'f_flag',
            'f_frsize', 'f_namemax',
            'st_blocks','st_blksize'))

    def unlink(self, path):
        raise NotImplementedError

    def symlink(self, target, name):
        raise NotImplementedError

    def rename(self, old, new):
        raise NotImplementedError

    def link(self, target, name):
        raise NotImplementedError

    def utimens(self, path, times=None):
        return os.utime(self.boxfs.target_for(path), times)

    # File methods
    # ============

    def open(self, path, flags):
        logging.debug("OPEN %s %s" % (path,flags))
        full_path = self.boxfs.target_for(path)
        return os.open(full_path, flags)

    def create(self, path, mode, fi=None):
        raise NotImplementedError

    def read(self, path, length, offset, fh):
        logging.debug("READ %s %s %s %s" % (path,length,offset,fh))
        os.lseek(fh, offset, os.SEEK_SET)
        return os.read(fh, length)

    def write(self, path, buf, offset, fh):
        raise NotImplementedError

    def truncate(self, path, length, fh=None):
        raise NotImplementedError

    def flush(self, path, fh):
        return os.fsync(fh)

    def release(self, path, fh):
        return os.close(fh)

    def fsync(self, path, fdatasync, fh):
        return self.flush(path, fh)

def main(mountpoint,conf_file=None):
    # Need to set user_allow_other in /etc/fuse.conf for
    # allow_other option to work (or run this process as root)
    fusebox = FuseBox(conf_file)
    FUSE(fusebox,mountpoint,foreground=True,allow_other=True)

if __name__ == '__main__':
    
    p = optparse.OptionParser(usage="%prog OPTIONS MOUNTPOINT",
                              description="Start fusebox virtual file system and "
                              "mount at MOUNTPOINT.")
    p.add_option("--conf",action='store',dest='conf_file',default=None,
                 help="read user and file info from CONF_FILE")
    p.add_option("--debug",action='store_true',dest='debug',
                 help="turn on debugging output")
    options,args = p.parse_args()
    if options.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    main(args[0],conf_file=options.conf_file)
