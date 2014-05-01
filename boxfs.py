# boxfs
#
# Backend for managing a conceptual directory structure
# 
import os

class BoxFS:

    def __init__(self):
        self.dirs = ['/']
        self.dircontents = {'/':[]}
        self.files = []
        self.targets = {}
        self.permissions = {}
        self.users = {}

    def normalise_path(self,path):
        if path == '' or path == '/':
            return '/'
        elif path.startswith('/'):
            return path[1:]
        return path

    def add_user(self,name,uid):
        if name in self.users:
            raise KeyError,"User '%s' already present" % name
        self.users[name] = uid

    def add_dir(self,path):
        dirpath = self.normalise_path(path)
        while dirpath:
            if dirpath not in self.dirs:
                self.dirs.append(dirpath)
            basename = os.path.dirname(dirpath)
            dirpath = os.path.dirname(dirpath)
            if basename == '':
                continue
            try:
                if basename not in self.dircontents[dirpath]:
                    self.dircontents[dirpath].append(basename)
            except KeyError:
                self.dircontents[dirpath] = [basename]
        basename = path.split(os.sep)[0]
        if basename not in self.dircontents['/']:
            self.dircontents['/'].append(basename)

    def add_file(self,path,target,access=[]):
        self.files.append(path)
        filen = os.path.basename(path)
        dirpath = os.path.dirname(path)
        print "add_file: dirpath = %s" % dirpath
        if dirpath:
            self.add_dir(os.path.dirname(path))
        self.targets[path] = target
        for uid in access:
            self.set_permission(path,uid)
        print "add_file: '%s' '%s' '%s'" % (path,filen,dirpath)
        if dirpath == '':
            dirpath = '/'
            filen = path
        try:
            if filen not in self.dircontents[dirpath]:
                self.dircontents[dirpath].append(filen)
        except KeyError:
            self.dircontents[dirpath] = [filen]

    def is_dir(self,path):
        return self.normalise_path(path) in self.dirs

    def is_file(self,path):
        return self.normalise_path(path) in self.files

    def target_for(self,path):
        return self.targets[self.normalise_path(path)]

    def exists(self,path):
        return self.is_file(path) or self.is_dir(path)

    def list_dir(self,path):
        if not self.is_dir(path):
            return None
        try:
            return self.dircontents[self.normalise_path(path)]
        except KeyError:
            return []

    def list_users(self):
        users = self.users.keys()
        users.sort()
        return users

    def set_permission(self,path,uid):
        if not self.is_file(path):
            return
        try:
            self.permissions[path].append(uid)
        except KeyError:
            self.permissions[path] = [uid]

    def has_permission(self,path,uid):
        path = self.normalise_path(path)
        if self.is_file(path):
            try:
                return uid in self.permissions[path]
            except KeyError:
                return True
        elif self.is_dir(path):
            for f in self.files:
                f = self.normalise_path(f)
                if f.startswith(path) and self.has_permission(f,uid):
                    return True
        return False

import unittest
class TestBoxFS(unittest.TestCase):
    def test_normalise_path(self):
        box = BoxFS()
        self.assertEqual(box.normalise_path(''),'/')
        self.assertEqual(box.normalise_path('/'),'/')
        self.assertEqual(box.normalise_path('mybox/box.txt'),'mybox/box.txt')
        self.assertEqual(box.normalise_path('/mybox/box.txt'),'mybox/box.txt')
    def test_empty_boxfs(self):
        box = BoxFS()
        self.assertEqual(box.dirs,['/'])
        self.assertTrue(box.is_dir('/'))
        self.assertEqual(box.list_dir('/'),[])
    def test_boxfs_add_file(self):
        box = BoxFS()
        box.add_file('myfile','/data/file')
        self.assertEqual(box.dirs,['/'])
        self.assertTrue(box.is_dir('/'))
        self.assertTrue(box.is_file('myfile'))
        self.assertTrue(box.target_for('myfile'),'/data/file')
        self.assertEqual(box.list_dir('/'),['myfile'])
    def test_boxfs_add_dir(self):
        box = BoxFS()
        box.add_dir('mydir')
        self.assertEqual(box.dirs,['/','mydir'])
        self.assertTrue(box.is_dir('/'))
        self.assertTrue(box.is_dir('mydir'))
        self.assertEqual(box.list_dir('/'),['mydir'])
    def test_boxfs_add_file_implicitly_adds_dir(self):
        box = BoxFS()
        box.add_file('mydir/test','/data/file')
        self.assertEqual(box.dirs,['/','mydir'])
        self.assertTrue(box.is_dir('/'))
        self.assertTrue(box.is_dir('mydir'))
        self.assertTrue(box.is_file('mydir/test'))
        self.assertTrue(box.target_for('mydir/test'),'/data/file')
        self.assertEqual(box.list_dir('/'),['mydir'])
        self.assertEqual(box.list_dir('mydir'),['test'])
    def test_boxfs_add_multiple_files_and_dirs(self):
        box = BoxFS()
        box.add_file('mydir/test','/data/file')
        box.add_file('mydir/test2','/data/file2')
        self.assertEqual(box.dirs,['/','mydir'])
        self.assertEqual(box.list_dir('/'),['mydir'])
        self.assertEqual(box.list_dir('/mydir'),['test','test2'])
    def test_boxfs_deal_with_leading_slash(self):
        box = BoxFS()
        box.add_file('mydir/test','/data/file')
        self.assertEqual(box.dirs,['/','mydir'])
        self.assertTrue(box.is_dir('/'))
        self.assertTrue(box.is_dir('/mydir'))
        self.assertTrue(box.is_file('/mydir/test'))
        self.assertTrue(box.target_for('/mydir/test'),'/data/file')
        self.assertEqual(box.list_dir('/'),['mydir'])
        self.assertEqual(box.list_dir('/mydir'),['test'])
    def test_boxfs_add_users(self):
        box = BoxFS()
        box.add_user('anonymouse',1000)
        box.add_user('catweazle',1001)
        self.assertEqual(box.list_users(),['anonymouse','catweazle'])
        self.assertRaises(KeyError,box.add_user,'catweazle',1002)
    def test_boxfs_add_file_with_no_permissions(self):
        box = BoxFS()
        box.add_user('anonymouse',1000)
        box.add_file('myfile','/data/file')
        self.assertTrue(box.is_file('myfile'))
        self.assertTrue(box.target_for('myfile'),'/data/file')
        self.assertTrue(box.has_permission('myfile',1000))
        self.assertTrue(box.has_permission('/myfile',1000))
    def test_boxfs_add_file_with_permissions(self):
        box = BoxFS()
        box.add_user('anonymouse',1000)
        box.add_user('catweazle',1001)
        box.add_file('myfile','/data/file',access=[1000])
        self.assertTrue(box.is_file('myfile'))
        self.assertTrue(box.target_for('myfile'),'/data/file')
        self.assertTrue(box.has_permission('myfile',1000))
        self.assertTrue(box.has_permission('/myfile',1000))
        self.assertFalse(box.has_permission('myfile',1001))
        self.assertFalse(box.has_permission('/myfile',1001))
    def test_boxfs_add_file_in_dir_with_permissions(self):
        box = BoxFS()
        box.add_user('anonymouse',1000)
        box.add_user('catweazle',1001)
        box.add_file('data/myfile','/data/file',access=[1000])
        self.assertTrue(box.is_file('data/myfile'))
        self.assertTrue(box.target_for('data/myfile'),'/data/file')
        self.assertTrue(box.has_permission('data/myfile',1000))
        self.assertTrue(box.has_permission('data',1000))
        self.assertTrue(box.has_permission('/data/myfile',1000))
        self.assertTrue(box.has_permission('/data',1000))
        self.assertFalse(box.has_permission('data/myfile',1001))
        self.assertFalse(box.has_permission('data',1001))
        self.assertFalse(box.has_permission('/data/myfile',1001))
        self.assertFalse(box.has_permission('/data',1001))
