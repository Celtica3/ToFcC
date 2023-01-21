
import logging
import os
import typing

from pydantic import BaseModel, Field
import json

ROAMING_DIR = os.path.join(os.path.expanduser('~'), 'AppData', 'Roaming')
tof_launcher : str = os.path.join(ROAMING_DIR, "tof_launcher")

def zipdir(path, ziph):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith("log"):
                continue
            ziph.write(os.path.join(root, file), 
                       os.path.relpath(os.path.join(root, file), 
                                       os.path.join(path, '..')))


class TConfig(BaseModel):
    currentDirectory : str = None
    profiles : typing.Dict[str, int] = Field(default_factory=dict)
    launcherDir : str = None
    dir : str
    
    def dict(self):
        return super().dict(exclude={"dir"})
    
    @property
    def cubfigFolder(self):
        return os.path.join(self.dir, "ToFCubfig")
    
    @property
    def cubfigJson(self):
        return os.path.join(self.dir, "ToFCubfig","config.json")
    
    def backup(self, name : str, new : bool = True):
        if not os.path.exists(tof_launcher):
            raise FileNotFoundError("tof_launcher not found")
        
        if name in self.profiles and new:
            raise ValueError("name already exists")
            
            
        # find the only folder that is completely numerical
        profilefolder = [f for f in os.listdir(tof_launcher) if f.isnumeric()]
        if len(profilefolder) != 1:
            raise FileNotFoundError("tof_launcher has no folder")
        
        profilefolder = profilefolder[0]
        
        if os.path.exists(os.path.join(self.cubfigFolder, f"{name}.zip")):
            logging.info("profile already backed up, renaming to bkup")
            if os.path.exists(os.path.join(self.cubfigFolder, f"{name}_bkup.zip")): os.remove(os.path.join(self.cubfigFolder, f"{name}_bkup.zip"))
            
            os.rename(os.path.join(self.cubfigFolder, f"{name}.zip"), os.path.join(self.cubfigFolder, f"{name}_bkup.zip"))
            
        if not os.path.exists(os.path.join(tof_launcher, "psd.dat")):
            raise FileNotFoundError("psd.dat not found")
        
        if not os.path.exists(os.path.join(tof_launcher, "last_user.dat")):
            raise FileNotFoundError("last_user.dat not found")
        
        # create zip file
        import zipfile
        
        with zipfile.ZipFile(os.path.join(self.cubfigFolder, f"{name}.zip"), "w") as z:
            z.write(os.path.join(tof_launcher, "psd.dat"), "psd.dat")
            z.write(os.path.join(tof_launcher, "last_user.dat"), "last_user.dat")
            zipdir(os.path.join(tof_launcher, profilefolder), z)
            # add password
            z.setpassword(f"{name}".encode("utf-8"))

        # add to config
        self.profiles[name] = int(profilefolder)
        
        # save config
        self.save()
        
    def save(self):
        with open(self.cubfigJson, "w") as f:
            json.dump(self.dict(), f)
            
    def kill_tof(self):
        # kill tof_launcher.exe
        import psutil
        for proc in psutil.process_iter():
            if proc.name() == "tof_launcher.exe":
                proc.kill()
            
    def swap(self, name : str):
        
        if name not in self.profiles:
            raise ValueError("name does not exist")
        
        self.kill_tof()
        
        self.backup("current", new=False)
        
        # unpack zip to target
        import zipfile
        
        # remove the numerical folder
        profilefolder = [f for f in os.listdir(tof_launcher) if f.isnumeric()]
        if len(profilefolder) != 1:
            raise FileNotFoundError("tof_launcher has no folder")
        
        profilefolder = profilefolder[0]
        
        import shutil
        shutil.rmtree(os.path.join(tof_launcher, profilefolder))
        
        # extract and unlock
        with zipfile.ZipFile(os.path.join(self.cubfigFolder, f"{name}.zip"), "r") as z:
            z.extractall(tof_launcher, pwd=f"{name}".encode("utf-8"))
        
    @property
    def applicationLocation(self):
        if self.launcherDir:
            return self.launcherDir 
        import psutil
        for proc in psutil.process_iter():
            if proc.name() == "tof_launcher.exe":
                self.launcherDir =  os.path.dirname(proc.exe())
                return self.launcherDir
            
