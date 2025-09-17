from dataclasses import dataclass

@dataclass
class SpackManager:
    
    def __init__(self,
                 bm_id,
                 package_list
                 ):
        
        self.bm_id = bm_id
        self.package_list = package_list
        
        print("hello")
        
        