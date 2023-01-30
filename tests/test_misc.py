import os
import unittest
from TofCube.folder import DEFAULT_CONFIG_STRUCTURE

class t_misc(unittest.TestCase):
    def test_1(self):
        # get roaming folder
        roaming_folder = os.getenv("APPDATA")
        tof_launcher_folder = os.path.join(roaming_folder,"tof_launcher")
        
        r = DEFAULT_CONFIG_STRUCTURE.walkFiles(
            tof_launcher_folder
        )
        pass