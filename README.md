fusebox
=======

Implements a FUSE virtual file system that can be used to create a read-only
arbitrary artifical filesystem with fine-grained access to individual files
for users.

This implementation is a proof-of-principle, not a production system.

Installing
----------

Make a virtualenv and get fusepy:

    % virtualenv fuse
    % . fuse/bin/activate
    (fuse)% pip install fusepy

Set up
------

Use `manage_conf.py` to create and edit a conf file , which defines users
along with mappings of virtual files to actual files, and which users have
access to them.

Note that UIDs must correspond to uids of users on the real file system.

Running
-------

Start the `fusebox` instance:

    (fuse)% fusebox.py --conf=CONF_FILE MOUNTPOINT

The CONF_FILE defines the virtual file system. The MOUNTPOINT must be an
existing empty directory, this is where the virtual file system will
appear.

In order to allow other users to access the fusebox file system, either run
fusebox as root or make sure the the `user_allow_other` is present in the
`/etc/fuse.conf` file (non-root users probably also need to be members of
the `fuse` group).

If modifications are made to the conf file then the `fusebox` instance must
be restarted in order for the changes to become visible.

Use the `--debug` option to get debugging output from the fusebox process.

Background
----------

fusebox was derived from Stavros Korokithakis' example `Passthrough`
fuse implementation posted on his blog:

 * <http://www.stavros.io/posts/python-fuse-filesystem/>

The fusepy website is at <https://github.com/terencehonles/fusepy>
