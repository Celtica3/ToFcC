import typing
from pydantic import BaseModel, Field, validator
import os 
import re

class File(BaseModel):
    name : str
    optional : bool = False
    
class Folder(File):
    files : typing.List[File] = Field(default_factory=list)
    folders : typing.List['Folder'] = Field(default_factory=list)
    masks : typing.Dict[str, typing.Literal["INCLUDE_MASK", "EXCLUDE_MASK", "INCLUDE_EXT", "EXCLUDE_EXT"]] = Field(default_factory=dict)
    fullPathComparator : bool  = False
    folderDive : bool = True
    
    @validator("masks", pre=True)
    def _val_masks(cls, v):
        if not isinstance(v, dict):
            raise TypeError("masks must be a dict")
        
        for k, m in v.items():
            k :str
            if m not in ["INCLUDE_MASK", "EXCLUDE_MASK", "INCLUDE_EXT", "EXCLUDE_EXT"]:
                raise ValueError(f"Invalid mask type {m}")
        
            if m in ["INCLUDE_EXT", "EXCLUDE_EXT"] and not k.startswith("*."):
                raise ValueError(f"Mask {k} must start with *. for INCLUDE_EXT or EXCLUDE_EXT")
        
        return v
    
    def walkFiles(
        self, 
        path : str, 
        parent_masks : dict = None
    ):
        if not os.path.isdir(path) or not os.path.exists(path):
            return []
        
        files = []

        if parent_masks is not None:
            masks = parent_masks.copy()
            masks.update(self.masks)
        else:
            masks = self.masks.copy()
        
        exclude_ext_masks = [k for k, v in masks.items() if v == "EXCLUDE_EXT"]
        include_ext_masks = [k for k, v in masks.items() if v == "INCLUDE_EXT"]
        exclude_masks = [k for k, v in masks.items() if v == "EXCLUDE_MASK"]
        include_masks = [k for k, v in masks.items() if v == "INCLUDE_MASK"]
            
        def matchFile(filePath : str, default : bool = False):
            if any([filePath.endswith(ev[2:]) for ev in exclude_ext_masks]):
                return False
            if len(exclude_masks)>0:
                if any([re.match(em, filePath) for em in exclude_masks]):
                    return False

            if any([filePath.endswith(ev[2:]) for ev in include_ext_masks]):
                return True
            if len(include_masks )> 0:
                if any([re.match(em, filePath) for em in include_masks]):
                    return True
            
            return default
        
        gothroughFiles = self.files.copy()
        pending = []
        gothroughFolders = self.folders.copy()
        
        if (len(gothroughFiles) == 0) and self.folderDive:
            for f in os.listdir(path):
                if os.path.isdir(os.path.join(path, f)):
                    pending.append(f)
                elif os.path.isfile(os.path.join(path, f)):
                    gothroughFiles.append(f)
                    
        if (len(gothroughFolders) == 0) and self.folderDive and len(pending) > 0:
            gothroughFolders.extend(pending)
        elif (len(gothroughFolders) == 0) and self.folderDive:
            for f in os.listdir(path):
                if os.path.isdir(os.path.join(path, f)):
                    gothroughFolders.append(f)
            
        for f in gothroughFiles:
            if isinstance(f, str):
                bf : str = f
                absf = os.path.join(path, f)
            else:
                bf = f.name
                absf = os.path.join(path, f.name)
        
            if self.fullPathComparator and not matchFile(absf, True):
                continue
            elif not self.fullPathComparator and not matchFile(bf, True):
                continue
                
            if os.path.exists(absf):
                files.append(absf)
            elif not f.optional:
                raise FileNotFoundError(f"File {bf} not found in {path}")
        
        for f in gothroughFolders:
            if isinstance(f, str):
                f = Folder(
                    name=f,
                    fullPathComparator=self.fullPathComparator,
                    folderDive=self.folderDive
                )
            
            files.extend(
                f.walkFiles(
                    os.path.join(path, f.name),  
                    masks,
                )
            )
        
        return files

    
DEFAULT_CONFIG_STRUCTURE = Folder(
    name="tof_launcher",
    files=[
        {
            "name" : "last_user.dat",
        },
        {
            "name" : "psd.dat",
            "optional" : True
        }
    ],
    folders=[
        {
            "name": "29093",
            "masks" : {"*.log" : "EXCLUDE_EXT"},
        }
    ]
)

