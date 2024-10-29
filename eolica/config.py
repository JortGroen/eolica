from pydantic import BaseModel
from typing import Optional, List, Union
from pathlib import Path
from json import dump

class ParkConfig(BaseModel):
    '''
    configuration file for a park
    '''

