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
from boxfs import PassThroughBoxFS, BoxFS, BoxConfFile

class FuseBox(Operations):

    def __init__(self,boxfs):
        self.boxfs = boxfs

    def context_uid(self):
        cxt = fuse_get_context()
        return cxt[0]

    def has_permission(self,path):
        uid = self.context_uid()
        return self.boxfs.has_access(path,uid)

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
        raise FuseOSError(errno.EROFS)

    def chown(self, path, uid, gid):
        raise FuseOSError(errno.EROFS)

    def getattr(self, path, fh=None):
        logging.debug("GETATTR %s %s" % (path,fh))
        try:
            full_path = self.boxfs.target_for(path)
        except KeyError:
            full_path = os.getcwd()
        st = os.lstat(full_path)
        s = dict()
        for key in  ('st_atime', 'st_ctime',
                     'st_gid', 'st_mode', 'st_mtime',
                     'st_nlink', 'st_size', 'st_uid',
                     'st_blocks','st_blksize'):
            try:
                s[key] = getattr(st,key)
            except AttributeError:
                logging.debug("statfs: no attr '%s'" % key)
        return s

    def readdir(self, path, fh):
        logging.debug("READDIR %s %s" % (path,fh))
        dirents = ['.', '..']
        if self.boxfs.is_dir(path):
            dirents.extend(self.boxfs.list_dir(path,user=self.context_uid()))
        logging.debug("READDIR dirents %s" % dirents)
        for r in dirents:
            logging.debug("-> yielding %s" % r)
            yield r

    def readlink(self, path):
        return os.readlink(self.boxfs.target_for(path))

    def mknod(self, path, mode, dev):
        raise FuseOSError(errno.EROFS)

    def rmdir(self, path):
        raise FuseOSError(errno.EROFS)

    def mkdir(self, path, mode):
        raise FuseOSError(errno.EROFS)

    def statfs(self, path):
        logging.debug("STATFS %s" % path)
        try:
            full_path = self.boxfs.target_for(path)
        except KeyError:
            full_path = os.getcwd()
        stv = os.statvfs(full_path)
        stvfs = dict()
        for key in ('f_bavail', 'f_bfree',
            'f_blocks', 'f_bsize', 'f_favail', 'f_ffree', 'f_files', 'f_flag',
            'f_frsize', 'f_namemax','st_blocks','st_blksize'):
            try:
                stvfs[key] = getattr(stv,key)
            except AttributeError:
                logging.debug("statfs: no attr '%s'" % key)
        return stvfs

    def unlink(self, path):
        raise FuseOSError(errno.EROFS)

    def symlink(self, target, name):
        raise FuseOSError(errno.EROFS)

    def rename(self, old, new):
        raise FuseOSError(errno.EROFS)

    def link(self, target, name):
        raise FuseOSError(errno.EROFS)

    def utimens(self, path, times=None):
        return os.utime(self.boxfs.target_for(path), times)

    # File methods
    # ============

    def open(self, path, flags):
        logging.debug("OPEN %s %s" % (path,flags))
        full_path = self.boxfs.target_for(path)
        return os.open(full_path, flags)

    def create(self, path, mode, fi=None):
        raise FuseOSError(errno.EROFS)

    def read(self, path, length, offset, fh):
        logging.debug("READ %s %s %s %s" % (path,length,offset,fh))
        os.lseek(fh, offset, os.SEEK_SET)
        return os.read(fh, length)

    def write(self, path, buf, offset, fh):
        raise FuseOSError(errno.EROFS)

    def truncate(self, path, length, fh=None):
        raise FuseOSError(errno.EROFS)

    def flush(self, path, fh):
        return os.fsync(fh)

    def release(self, path, fh):
        return os.close(fh)

    def fsync(self, path, fdatasync, fh):
        return self.flush(path, fh)

def main(fusebox,mountpoint,conf_file=None):
    # Need to set user_allow_other in /etc/fuse.conf for
    # allow_other option to work (or run this process as root)
    ##fusebox = FuseBox(conf_file)
    FUSE(fusebox,mountpoint,foreground=True,allow_other=True)

if __name__ == '__main__':
    
    p = optparse.OptionParser(usage="%prog OPTIONS MOUNTPOINT",
                              description="Start fusebox virtual file system and "
                              "mount at MOUNTPOINT.")
    p.add_option("--type",action='store',dest="vfs",default="passthrough",
                 help="specify type of virtual file system to create; options are "
                 "'passthrough' (default) or 'mapped'")
    p.add_option("--conf",action='store',dest='conf_file',default=None,
                 help="read user and file mapping info from CONF_FILE for 'mapped' "
                 "VFS")
    p.add_option("--root",action='store',dest='root_dir',default=None,
                 help="directory that root of 'passthrough' VFS maps onto in the "
                 "real filesystem")
    p.add_option("--debug",action='store_true',dest='debug',
                 help="turn on debugging output")
    options,args = p.parse_args()
    if options.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    if options.vfs == 'passthrough':
        # Read-only passthrough VFS
        if options.root_dir:
            boxfs = PassThroughBoxFS(options.root_dir)
        else:
            p.error("'passthrough' VFS requires a root directory")
    elif options.vfs == 'mapped':
        # Read-only mapped VFS
        if options.conf_file:
            boxfs = BoxConfFile(conf_file).populate(BoxFS())
        else:
            p.error("'mapped' VFS requires a conf file")
    else:
        p.error("Unknown VFS type: '%s'" % options.vfs)
    fusebox = FuseBox(boxfs)
    main(fusebox,args[0])
