# boxfs
#
# Backend for managing a conceptual directory structure
# 
import os

class BoxFSBase:
    """Base class for BoxFS implementations

    """

    def __init__(self):
        pass

    def normalise_path(self,path):
        """Add leading slash if none found
        """
        if not path.startswith('/'):
            return '/'+path
        return path

    def add_user(self,name,user):
        """Adds a user
        """
        raise NotImplementedError,"Subclass must implement add_user method"

    def list_users(self):
        """Return list of users
        """
        raise NotImplementedError,"Subclass must implement list_users method"

    def add_file(self,path,target,access=[]):
        """Adds a file
        """
        raise NotImplementedError,"Subclass must implement add_user method"

    def target_for(self,path):
        """Returns the target for a file
        """
        raise NotImplementedError,"Subclass must implement target_for method"

    def exists(self,path):
        """Returns True if path is present
        """
        raise NotImplementedError,"Subclass must implement exists method"

    def is_dir(self,path):
        """Returns True if path is a directory
        """
        raise NotImplementedError,"Subclass must implement is_dir method"

    def is_file(self,path):
        """Returns True if path is a directory
        """
        raise NotImplementedError,"Subclass must implement is_file method"

    def list_dir(self,path,user=None):
        """Returns directory contents, optionally restricted by accessibility for user
        """
        raise NotImplementedError,"Subclass must implement list_dir method"

    def grant_access(self,path,user):
        """Grants access permission on path to user
        """
        raise NotImplementedError,"Subclass must implement grant_access method"

    def has_access(self,path,user):
        """Returns True is user has permission to access
        """
        raise NotImplementedError,"Subclass must implement has_access method"

class BoxFS(BoxFSBase):

    def __init__(self):
        """Create new BoxFS instance
        """
        BoxFSBase.__init__(self)
        self.files = {}
        self.dirs = {'/': set()}
        self.users = {}
        self.access = {}

    def add_user(self,user,name):
        """Adds a user
        """
        if user not in self.users:
            self.users[user] = name
        else:
            raise KeyError,"User %s already exists" % user

    def list_users(self):
        """Return list of users
        """
        return self.users.keys()

    def add_file(self,path,target,access=[]):
        """Adds a file
        """
        path = self.normalise_path(path)
        self.files[path] = target
        if not path in self.access:
            self.access[path] = set()
        for user in access:
            self.grant_access(path,user)
        dirent = os.path.basename(path)
        dirpath = os.path.dirname(path)
        while not (dirpath == '' or dirpath == '/'):
            if dirpath not in self.dirs:
                self.dirs[dirpath] = set()
            self.dirs[dirpath].add(dirent)
            dirent = os.path.basename(dirpath)
            dirpath = os.path.dirname(dirpath)
        if dirent != '':
            self.dirs['/'].add(dirent)

    def target_for(self,path):
        """Returns the target for a file
        """
        path = self.normalise_path(path)
        return self.files[path]

    def exists(self,path):
        """Returns True if path is present
        """
        path = self.normalise_path(path)
        return self.is_file(path) or self.is_dir(path)

    def is_dir(self,path):
        """Returns True if path is a directory
        """
        path = self.normalise_path(path)
        return path in self.dirs

    def is_file(self,path):
        """Returns True if path is a directory
        """
        path = self.normalise_path(path)
        return path in self.files

    def list_dir(self,path,user=None):
        """Returns directory contents
        """
        path = self.normalise_path(path)
        if user is None:
            dirents = list(self.dirs[path])
            dirents.sort()
        else:
            dirents = []
            for dirent in self.list_dir(path):
                if self.has_access(os.path.join(path,dirent),user):
                    dirents.append(dirent)
        return dirents

    def grant_access(self,path,user):
        """Grants access permission on path to user
        """
        path = self.normalise_path(path)
        self.access[path].add(user)

    def has_access(self,path,user):
        """Returns True is user has permission to access
        """
        path = self.normalise_path(path)
        try:
            return user in self.access[path] or not self.access[path]
        except KeyError:
            pass
        for filepath in self.access:
            if self.has_access(filepath,user) and filepath.startswith(path):
                return True
        return False

import unittest
class TestBoxFS(unittest.TestCase):
    def setUp(self):
        self.boxfs = BoxFS
    def test_normalise_path(self):
        box = self.boxfs()
        self.assertEqual(box.normalise_path(''),'/')
        self.assertEqual(box.normalise_path('/'),'/')
        self.assertEqual(box.normalise_path('mybox/box.txt'),'/mybox/box.txt')
        self.assertEqual(box.normalise_path('/mybox/box.txt'),'/mybox/box.txt')
    def test_empty_boxfs(self):
        box = self.boxfs()
        self.assertTrue(box.is_dir('/'))
        self.assertEqual(box.list_dir('/'),[])
    def test_boxfs_add_file(self):
        box = self.boxfs()
        box.add_file('myfile','/data/file')
        self.assertTrue(box.is_dir('/'))
        self.assertTrue(box.is_file('myfile'))
        self.assertTrue(box.target_for('myfile'),'/data/file')
        self.assertEqual(box.list_dir('/'),['myfile'])
    def test_boxfs_add_file_implicitly_adds_dir(self):
        box = self.boxfs()
        box.add_file('mydir/test','/data/file')
        self.assertTrue(box.is_dir('/'))
        self.assertTrue(box.is_dir('mydir'))
        self.assertTrue(box.is_file('mydir/test'))
        self.assertTrue(box.target_for('mydir/test'),'/data/file')
        self.assertEqual(box.list_dir('/'),['mydir'])
        self.assertEqual(box.list_dir('mydir'),['test'])
    def test_boxfs_add_deep_file(self):
        box = self.boxfs()
        box.add_file('mydir/mydata/down/below/test','/data/file')
        self.assertTrue(box.is_dir('/'))
        self.assertTrue(box.is_dir('mydir'))
        self.assertTrue(box.is_file('mydir/mydata/down/below/test'))
        self.assertTrue(box.target_for('mydir/mydata/down/below/test'),'/data/file')
        self.assertEqual(box.list_dir('/'),['mydir'])
        self.assertEqual(box.list_dir('mydir'),['mydata'])
        self.assertEqual(box.list_dir('mydir/mydata'),['down'])
        self.assertEqual(box.list_dir('mydir/mydata/down'),['below'])
        self.assertEqual(box.list_dir('mydir/mydata/down/below'),['test'])
    def test_boxfs_add_multiple_files_and_dirs(self):
        box = self.boxfs()
        box.add_file('mydir/test','/data/file')
        box.add_file('mydir/test2','/data/file2')
        self.assertEqual(box.list_dir('/'),['mydir'])
        self.assertEqual(box.list_dir('/mydir'),['test','test2'])
    def test_boxfs_deal_with_leading_slash(self):
        box = self.boxfs()
        box.add_file('mydir/test','/data/file')
        self.assertTrue(box.is_dir('/'))
        self.assertTrue(box.is_dir('/mydir'))
        self.assertTrue(box.is_file('/mydir/test'))
        self.assertTrue(box.target_for('/mydir/test'),'/data/file')
        self.assertEqual(box.list_dir('/'),['mydir'])
        self.assertEqual(box.list_dir('/mydir'),['test'])
    def test_boxfs_add_users(self):
        box = self.boxfs()
        box.add_user('anonymouse',1000)
        box.add_user('catweazle',1001)
        self.assertEqual(box.list_users(),['anonymouse','catweazle'])
        self.assertRaises(KeyError,box.add_user,'catweazle',1002)
    def test_boxfs_add_file_with_no_access(self):
        box = BoxFS()
        box.add_user('anonymouse',1000)
        box.add_file('myfile','/data/file')
        self.assertTrue(box.is_file('myfile'))
        self.assertTrue(box.target_for('myfile'),'/data/file')
        self.assertTrue(box.has_access('myfile',1000))
        self.assertTrue(box.has_access('/myfile',1000))
    def test_boxfs_add_file_with_access(self):
        box = self.boxfs()
        box.add_user('anonymouse',1000)
        box.add_user('catweazle',1001)
        box.add_file('myfile','/data/file',access=[1000])
        self.assertTrue(box.is_file('myfile'))
        self.assertTrue(box.target_for('myfile'),'/data/file')
        self.assertTrue(box.has_access('myfile',1000))
        self.assertTrue(box.has_access('/myfile',1000))
        self.assertFalse(box.has_access('myfile',1001))
        self.assertFalse(box.has_access('/myfile',1001))
    def test_boxfs_add_file_in_dir_with_access(self):
        box = self.boxfs()
        box.add_user('anonymouse',1000)
        box.add_user('catweazle',1001)
        box.add_file('data/myfile','/data/file',access=[1000])
        self.assertTrue(box.is_file('data/myfile'))
        self.assertTrue(box.target_for('data/myfile'),'/data/file')
        self.assertTrue(box.has_access('data/myfile',1000))
        self.assertTrue(box.has_access('data',1000))
        self.assertTrue(box.has_access('/data/myfile',1000))
        self.assertTrue(box.has_access('/data',1000))
        self.assertFalse(box.has_access('data/myfile',1001))
        self.assertFalse(box.has_access('data',1001))
        self.assertFalse(box.has_access('/data/myfile',1001))
        self.assertFalse(box.has_access('/data',1001))
    def test_boxfs_add_file_in_dir_with_access(self):
        box = self.boxfs()
        box.add_user('anonymouse',1000)
        box.add_user('catweazle',1001)
        box.add_file('data/myfile','/data/file',access=[1000])
        self.assertTrue(box.is_file('data/myfile'))
        self.assertTrue(box.target_for('data/myfile'),'/data/file')
        self.assertTrue(box.has_access('data/myfile',1000))
        self.assertTrue(box.has_access('data',1000))
        self.assertTrue(box.has_access('/data/myfile',1000))
        self.assertTrue(box.has_access('/data',1000))
        self.assertFalse(box.has_access('data/myfile',1001))
        self.assertFalse(box.has_access('data',1001))
        self.assertFalse(box.has_access('/data/myfile',1001))
        self.assertFalse(box.has_access('/data',1001))
    def test_boxfs_list_dir_contents_with_mixed_access(self):
        box = self.boxfs()
        box.add_user('anonymouse',1000)
        box.add_user('catweazle',1001)
        box.add_user('publican',1002)
        box.add_file('data/myfile','/data/file',access=[1000])
        box.add_file('data/hisfile','/data/file2',access=[1001])
        box.add_file('data/common','/data/file3',access=[1000,1001])
        box.add_file('data/public','/data/file3')
        self.assertEqual(box.list_dir('/'),['data'])
        self.assertEqual(box.list_dir('/',user=1000),['data'])
        self.assertEqual(box.list_dir('/',user=1001),['data'])
        self.assertEqual(box.list_dir('/',user=1002),['data'])
        self.assertEqual(box.list_dir('/data'),['common','hisfile','myfile','public'])
        self.assertEqual(box.list_dir('/data',user=1000),['common','myfile','public'])
        self.assertEqual(box.list_dir('/data',user=1001),['common','hisfile','public'])
        self.assertEqual(box.list_dir('/data',user=1002),['public'])
