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

from fuse import FUSE, FuseOSError, Operations, fuse_get_context
from boxfs import BoxFS

def context(self):
    cxt = fuse_get_context()
    print "UID: %s PID: %s" % (cxt[0],cxt[2])
    return cxt

class FuseBox(Operations):

    def __init__(self):
        self.boxfs = BoxFS()

    # Filesystem methods
    # ==================

    def access(self, path, mode):
        print "ACCESS %s %s" % (path,mode)
        if path.startswith('/'):
            path = path[1:]
        elif self.boxfs.is_file(path):
            if not os.access(self.boxfs.target_for(path),mode):
                raise FuseOSError(errno.EACCES)
        elif not self.boxfs.is_dir(path):
                raise FuseOSError(errno.EACCES)

    def chmod(self, path, mode):
        raise NotImplementedError

    def chown(self, path, uid, gid):
        raise NotImplementedError

    def getattr(self, path, fh=None):
        print "GETATTR %s %s" % (path,fh)
        try:
            full_path = self.boxfs.target_for(path)
        except KeyError:
            full_path = os.getcwd()
        st = os.lstat(full_path)
        return dict((key, getattr(st, key)) for key in ('st_atime', 'st_ctime',
                                                        'st_gid', 'st_mode', 'st_mtime',
                                                        'st_nlink', 'st_size', 'st_uid'))

    def readdir(self, path, fh):
        print "READDIR %s %s" % (path,fh)
        dirents = ['.', '..']
        if self.boxfs.is_dir(path):
            dirents.extend(self.boxfs.list_dir(path))
            print "READDIR dirents %s" % dirents
        for r in dirents:
            print "-> yielding %s" % r
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
        print "STATFS %s" % path
        full_path = self.boxfs.target_for(path)
        stv = os.statvfs(full_path)
        return dict((key, getattr(stv, key)) for key in ('f_bavail', 'f_bfree',
            'f_blocks', 'f_bsize', 'f_favail', 'f_ffree', 'f_files', 'f_flag',
            'f_frsize', 'f_namemax'))

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
        print "OPEN %s %s" % (path,flags)
        full_path = self.boxfs.target_for(path)
        return os.open(full_path, flags)

    def create(self, path, mode, fi=None):
        raise NotImplementedError

    def read(self, path, length, offset, fh):
        print "READ %s %s %s %s" % (path,length,offset,fh)
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


def main(mountpoint):
    # Need to set user_allow_other in /etc/fuse.conf for
    # allow_other option to work (or run this process as root)
    fusebox = FuseBox()
    fusebox.boxfs.add_file('Programs/sam2soap.py',
                           '/home/pjb/genomics_devel/utils/sam2soap.py')
    FUSE(fusebox,mountpoint,foreground=True,allow_other=True)

if __name__ == '__main__':
    
    main(sys.argv[1])
