import os
import unittest

from TofCube.folder import Folder

class t_folder(unittest.TestCase):
    def setUp(self):
        os.makedirs("tests/test", exist_ok=True)
        os.makedirs("tests/test/sub", exist_ok=True)
        with open("tests/test/a.json", "w"):
            pass
        
        with open("tests/test/b.json", "w"):
            pass
        
        with open("tests/test/c.json", "w"):
            pass
        
        with open("tests/test/a.txt", "w"):
            pass
        
        with open("tests/test/sub/x.json", "w"):
            pass
        
        with open("tests/test/sub/y.json", "w"):
            pass
        
        with open("tests/test/sub/w.toml", "w"):
            pass
        
        with open("tests/test/sub/xxx", "w"):
            pass
        
    def test_walkfolders(self):
        x = Folder(
            name="test",
            masks={
                "*.json" : "INCLUDE_EXT",
                "a.txt" : "INCLUDE_MASK",
                "y.json" : "EXCLUDE_MASK"
            },
            
        )
        
        r = x.walkFiles("tests/test")
        self.assertIn(
            'tests/test\\a.json',r
        )
        self.assertIn(
            'tests/test\\b.json',r
        )
        self.assertIn(
            'tests/test\\c.json',r
        )
        self.assertIn(
            'tests/test\\a.txt',r
        )
        self.assertIn(
            'tests/test\\sub\\x.json',r
        )
        self.assertIn(
            'tests/test\\sub\\w.toml',r
        )
        self.assertIn(
            'tests/test\\sub\\xxx',r
        )
        self.assertNotIn(
            'tests/test\\sub\\y.json',r
        )
        
        pass
    
    def tearDown(self) -> None:
        import shutil
        shutil.rmtree("tests/test")