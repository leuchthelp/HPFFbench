from dataclasses import dataclass
from pathlib import Path
import subprocess

@dataclass
class SpackManager:
    
    def __init__(self,
                 bm_id: str,
                 package_list: list,
                 path: Path
                 ):
        
        self.bm_id          = bm_id
        self.package_list   = package_list
        self.path           = path
        self.env_name       = self.path.name

        
        p = subprocess.run("spack find".split(), capture_output=True, check=True)
        #print(p.stderr)
        #print(p.stdout)
        
        try:
            p = subprocess.run(f"spack env create {self.env_name}".split(), capture_output=True, check=True)
            print(p.stderr)
            print(p.stdout)
        except:
            print("spack env already exists - continuing")
        
        p = subprocess.run("spack env list".split(), capture_output=True, check=True)
        print(p.stderr)
        print(p.stdout)
        
        command_ls              = "ls"
        command_find_env_file   = "cd /home/dev/spack/share/spack"
        command_file_executable = "chmod +x /home/dev/spack/share/spack/setup-env.sh"
        command_spack_create_env= f"spack env create {self.path}"
        command_source_file     = ". /home/dev/spack/share/spack/setup-env.sh"
        command_env_activate    = f"spack env activate {self.env_name}"
        command_env_deactivate  = f"spack env deactivate {self.env_name}"
        command_spack_find      = "spack find"
        command_spack_env_status= "spack env status"
        
        p = subprocess.run([command_source_file, command_env_activate, command_spack_env_status, command_spack_find], capture_output=True, shell=True, text=True, check=True)
        print(p.stderr)
        print(p.stdout)
    
    
    
        