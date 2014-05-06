fusebox
=======

Implements a number of different read-only FUSE virtual file systems (VFS):

 * `passthrough` VFS providing read-only access to an existing directory
    structure;
 * `mapped` VFS providing a read-only arbitrary artifical filesystem with
    fine-grained access to individual files for users.

**This implementation is a proof-of-principle, not a production system.**

The fusebox file system is defined as a set of mappings of arbitrary paths
to actual files. Access is granted to users on a per-file basis.

Virtual directories only exist as routes to virtual files. A user can always
see a route to a virtual file if they have the right to access that file.
Within a virtual directory a user only sees those virtual files and
subdirectories that they have access to.

Installing
----------

Make a virtualenv and install `fusepy` e.g.:

    % virtualenv fusebox
    % . fusebox/bin/activate
    (fusebox)% pip install fusepy

Then install `fusebox` e.g.:

    (fusebox)% tar zvfx fusebox-0.0.1.tar.gz 
    (fusebox)% cd fusebox-0.0.1
    (fusebox)% python setup.py install

Set up (mapped VFS)
-------------------

A mapped VFS requires a configuration file which defines, which defines
users along with mappings of virtual files to actual files (and which users
have access to them).

The `manage_conf.py` utility can be used to create and edit a conf file by
adding users and files.

Note that UIDs must correspond to uids of users on the real file system.

Running
-------

First activate the virtualenv to make sure that `fusebox` is available, e.g.

    % . fusebox/bin/activate

To start a passthrough VFS instance:

    (fusebox)% fusebox.py [ --type=passthrough ] --root=ROOT_DIR MOUNTPOINT

where `ROOT_DIR` is the root directory (in the actual file system) that will
be exposed by fusebox.

For a mapped VFS:

    (fusebox)% fusebox.py --type=mapped --conf=CONF_FILE MOUNTPOINT

where `CONF_FILE` defines the mapping of files and users in the virtual file
system to those in the real file system.

In both cases the `MOUNTPOINT` must be an existing empty directory; this is
where the virtual file system will appear.

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
