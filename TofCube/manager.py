from datetime import datetime
import shutil
import typing
from pydantic import BaseModel, Field
from TofCube.folder import DEFAULT_CONFIG_STRUCTURE, Folder
import psutil
from TofCube.profile import ProfileConfig
import os
import zipfile
import json

class CubeManager(BaseModel):
    _defaultPassword : str = "tof123"
    _programLocation : str
    _profiles : typing.Dict[str, ProfileConfig]
    profiles : typing.List[ProfileConfig] = Field(default_factory=list)
    defaultBkupStructure : Folder = DEFAULT_CONFIG_STRUCTURE
    tofLauncherLocation : str = None
    tofRoamingLocation : str
    currentlyUsing : str = None
    
    @property
    def configDir(self):
        return os.path.join(self._programLocation, "CubeConfig")
    
    def __init__(self, programLocation : str, **data) -> None:
        super().__init__(**data)
        object.__setattr__(self, "_programLocation", programLocation)
        object.__setattr__(self, "_profiles", {})
    
    @staticmethod
    def findLauncher():
        """
        this method finds the tof_launcher.exe parent directory from the processes
        """
        for proc in psutil.process_iter():
            if proc.name() == "tof_launcher.exe":
                return os.path.dirname(proc.exe())
        
    
    @staticmethod
    def killLauncher():
        for proc in psutil.process_iter():
            if proc.name() == "tof_launcher.exe":
                proc.kill()
    
    @staticmethod
    def makeTofConfigZip(
        tofRoamingLocation : str, 
        target : str,
        password : str = None,
        bkupStructure : Folder = DEFAULT_CONFIG_STRUCTURE,
        conflictOnTargetExist : typing.Literal["remove", "rename"] = "rename"
    ):
        if password is None:
            password = CubeManager._defaultPassword
        
        filesToCopy = bkupStructure.walkFiles(tofRoamingLocation)
        structure = bkupStructure.dict(exclude_defaults=True)
        
        if os.path.exists(target) and conflictOnTargetExist == "rename":
            # rename target to its modified date
            # filename no ext
            filename = os.path.splitext(os.path.basename(target))[0]
            datestr = datetime.fromtimestamp(os.path.getmtime(target)).strftime("%Y-%m-%d")
            
            shutil.move(
                target,
                os.path.join(
                    os.path.dirname(target),
                    f"bkup_{filename}_{datestr}.zip"
                )
            )
        elif os.path.exists(target) and conflictOnTargetExist == "remove":
            os.remove(target)
        
        with zipfile.ZipFile(target, "w") as z:
            z.setpassword(password.encode("utf-8"))
            for f in filesToCopy:
                z.write(f, os.path.relpath(f, tofRoamingLocation))
            
            z.writestr("_cc.json", json.dumps(structure))
            
        
    def backup(
        self, 
        name : str, 
        *alias, 
        customPassword : str = None,
        backupstructure : Folder = DEFAULT_CONFIG_STRUCTURE,
        conflictOnTargetExist : typing.Literal["remove", "rename"] = "rename"
    ):
        if name in self._profiles:
            profile = self._profiles.get(name)
        else:
            
            for a in alias:
                if a in self._profiles:
                    raise ValueError("alias already exists")
        
            profile = ProfileConfig(
                name = name,
                alias = alias,
                configStructure = backupstructure
            )

            self._profiles[name] = profile
            for alia in alias:
                self._profiles[alia] = profile
        
            self.profiles.append(profile)
        
            self.saveManagerConfig()

        target = os.path.join(self.configDir, f"{name}.zip")
        
        self.makeTofConfigZip(
            self.tofRoamingLocation,
            target=target,
            password=customPassword,
            bkupStructure =backupstructure,
            conflictOnTargetExist =conflictOnTargetExist
        )

        return profile  
            
    def swap(
        self, 
        name : str, 
        password : str = None,
        kill : bool = True, 
        relaunch : bool = False
    ):
        if kill:
            self.killLauncher()
        
        if password is None:
            password = self._defaultPassword
        
        if name not in self._profiles:
            raise ValueError("profile does not exist")
        
        profile = self._profiles[name]
        
        self.makeTofConfigZip(
            self.tofRoamingLocation,
            target=os.path.join(self.configDir, f"last.zip"),
            password=self._defaultPassword,
            bkupStructure =self.defaultBkupStructure,
            conflictOnTargetExist ="remove"
        )
        
        with zipfile.ZipFile(os.path.join(self.configDir, f"{name}.zip"), "r") as z:
            z.extractall(self.tofRoamingLocation, pwd=password)
        
        self.currentlyUsing = name
        self.saveManagerConfig()

        if relaunch:
            self.openLauncher()
    
    def remove(self, name : str):
        if name not in self._profiles:
            raise ValueError("profile does not exist")
        
        profile = self._profiles[name]
        for alia in profile.alias:
            self._profiles.pop(alia, None)
        
        self._profiles.pop(profile.name, None)
        
        if profile in self.profiles:
            self.profiles.remove(profile)
        self.saveConfig(self.configDir)
        return profile
    
    def openLauncher(self):
        if not self.tofLauncherLocation:
            return
            
        if not os.path.exists(self.tofLauncherLocation):
            raise ValueError("tof launcher location does not exist")
        
        if not os.path.isdir(self.tofLauncherLocation):
            raise ValueError("tof launcher location is not a file")
        
        os.startfile(os.path.join(self.tofLauncherLocation, "tof_launcher.exe"))
    
    def verify(self):
        list_of_current_packages = []
        
        for file in os.listdir(self.configDir):
            if not file.endswith(".zip"):
                continue
            
            if file == "last.zip":
                continue
            
            if file.startswith("bkup"):
                continue
            
            list_of_current_packages.append(file[:-4])
        
        oldProfiles = self.profiles.copy()
        self.profiles.clear()
        self._profiles.clear()
        
        for profile in oldProfiles:
            if profile.name not in list_of_current_packages:
                continue
            
            self.profiles.append(profile)
            
            for alia in profile.alias:
                self._profiles[alia] = profile
            
            self._profiles[profile.name] = profile

    
    @classmethod
    def saveConfig(cls, config_path : str, **data : dict):
        if not data:
            data = {
                "tofLauncherLocation" :  cls.findLauncher(),
                "tofRoamingLocation" :  os.path.join(os.getenv("APPDATA"), "tof_launcher")
            }
        with open(os.path.join(config_path, "config.json"), "w") as f:
            json.dump(
                data,
                f    
            )
    
    def saveManagerConfig(
        self, 
    ):
        data = self.dict(
            exclude_defaults=True
        )
        data = {k:v for k,v in data.items() if not k.startswith("_")}
        
        with open(os.path.join(self.configDir, "config.json"), "w") as f:
            json.dump(
                data,
                f    
            )
            
    
    @classmethod
    def create(cls, working_path : str):
        if not os.path.exists(working_path):
            raise ValueError("path does not exist")
        
        if not os.path.isdir(working_path):
            raise ValueError("path is not a directory")

        config_path = os.path.join(working_path, "CubeConfig")
        os.makedirs(os.path.join(working_path, "CubeConfig"), exist_ok=True)
        if not os.path.exists(os.path.join(config_path, "config.json")):
            cls.saveConfig(config_path)
        
        try:
            with open(os.path.join(config_path, "config.json"), "r") as f:
                config = json.load(f)
        except:
            cls.saveConfig(config_path)
            with open(os.path.join(config_path, "config.json"), "r") as f:
                config = json.load(f)
        
        obj = cls(programLocation = working_path, **config)
        obj.verify()
        return obj
        
        
            