fusebox
=======

Implements a FUSE virtual file system that can be used to create a read-only
arbitrary artifical filesystem with fine-grained access to individual files
for users.

Make a virtualenv and get fusepy:

    % virtualenv fuse
    % . fuse/bin/activate
    (fuse)% pip install fusepy

Start fusebox instance:

    (fuse)% fusebox.py <mountpoint>
