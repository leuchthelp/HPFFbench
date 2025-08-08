from dataclasses import dataclass
import yaml
from components.handler import Handler

@dataclass
class FFbench:
    
    """Defines FFbench, a benchmark designed for HPC environments.
    
    Attributes
    ----------
    
    """
    
    def __init__(self):
        
        path_to_config = None
        setup = dict
        
        with open(f"{path_to_config}config.yaml", "w") as file:
            yaml.dump(setup, file)
    
        Handler(path_to_config=path_to_config)
    
    
    def _check_capabilities(self):
        pass