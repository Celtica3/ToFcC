
import typing
from pydantic import BaseModel, Field

from TofCube.folder import Folder, DEFAULT_CONFIG_STRUCTURE

class ProfileConfig(BaseModel):
    name : str
    alias : typing.List[str] = Field(default_factory=list)
    configStructure : Folder = DEFAULT_CONFIG_STRUCTURE
    custom_password : bool = False