#!/bin/env python
#
# Manage the conf file to add users and file entries
import optparse
import os
from boxfs import BoxConfFile

if __name__ == "__main__":
    p = optparse.OptionParser(usage="%prog OPTIONS CONF_FILE",
                              description="Manage CONF_FILE for fusebox virtual file system")
    p.add_option("--add-user",action='store',dest='user',default=None,
                 help="add user info supplied as 'UID:NAME'")
    p.add_option("--add-file",action='store',dest='file',default=None,
                 help="add file supplied as 'FILE:TARGET[:UID[,UID...]]'")
    p.add_option("--grant-access",action='store',dest='access',default=None,
                 help="grant access to a (virtual) file for a user, supplied as 'FILE:UID'")
    options,args = p.parse_args()
    if len(args) != 1:
        p.error("Need to supply conf file name")
    conf_file = args[0]
    if os.path.exists(conf_file):
        conf = BoxConfFile(conf_file)
    else:
        conf = BoxConfFile()
    if options.user:
        uid,name = options.user.split(':')
        conf.add_user(name,uid)
    if options.file:
        path,target = options.file.split(':')[:2]
        target = os.path.abspath(target)
        try:
            access = options.file.split(':')[2]
            access = [int(x) for x in access.split(',')]
        except IndexError:
            access = []
        conf.add_file(path,target,uids=access)
    if options.access:
        path,uid = options.access.split(':')
        conf.grant_access(path,uid)
    conf.save(conf_file)
