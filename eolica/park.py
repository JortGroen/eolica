from abc import ABC, abstractmethod
import pandas as pd
import numpy as np

import time

class Park(ABC):
    '''
    this is a class to host the windpark object
    '''

    def __init__(self) -> None: 
        self.config = None
        
