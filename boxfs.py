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

    def normalise_path(self,path):
        if path == '' or path == '/':
            return '/'
        elif path.startswith('/'):
            return path[1:]
        return path

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
        self.dircontents['/'].append(path.split(os.sep)[0])

    def add_file(self,path,target):
        self.files.append(path)
        filen = os.path.basename(path)
        dirpath = os.path.dirname(path)
        print "add_file: dirpath = %s" % dirpath
        if dirpath:
            self.add_dir(os.path.dirname(path))
        self.targets[path] = target
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
