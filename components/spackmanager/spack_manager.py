from dataclasses import dataclass
from pathlib import Path
from dev_utils import bcolors
import subprocess
import itertools
import shutil


@dataclass
class SpackManager:
    
    handler_id       : str
    spack_env        : dict
    env_name         : str
    target           : list
    language         : list
    packages         : dict
    additional       : str
    env_location     : Path
    package_locations: dict
    initialized      : bool
    
    
    def __init__(self,
                 handler_id     : str,
                 env_name       : str,
                 spack_env      : dict,
                 use_spack_env  : bool,
                 only_data      = False,
                 install        = False,
                 ):
        
        self.initialized    = False
        self.handler_id     = handler_id
        self.spack_env      = spack_env
        self.env_name       = env_name
        self.__use_spack_env= use_spack_env
        self.__only_data    = only_data
        self.install        = install
        
        self.compiler       = self.spack_env["compiler"]
        self.target         = self.spack_env["target"]
        self.language       = self.spack_env["language"]
        self.packages       = self.spack_env["packages"]
        self.package_locations = {}
        self.python_version = "python"
        
        self.additional = ""
        try:
            self.additional = self.spack_env["additional"]
        except:
            pass
        
        
        self.loadables = {}
        
        self.env_location = Path(f"environments/{self.env_name}")
        self.env_location.mkdir(parents=True, exist_ok=True)
        
        self.file_location = Path(f"{self.env_location.absolute()}/env-{self.env_name}.sh")
        
        
        for name, info in self.packages.items():

            versions = info["versions"] if type(info["versions"]) != str else [info["versions"]]
            variants = [""]

            if "variants" in info:
                variants = info["variants"] if type(info["variants"]) != str else [info["variants"]]

            combinations = list(itertools.product(*[versions, variants, [self.compiler]]))
            
            self.loadables[name] = combinations
                
            for combination in combinations:
                package = f"{name}@{combination[0]} {combination[1]} %{combination[2]}"
                    
                if name == "python":
                    self.python_version = package
                
                if self.__only_data == False:
                    p = subprocess.run(f"spack location -i {package}".split(), text=True, check=True, capture_output=True)
                    self.package_locations[name] = (f"{package}", p.stdout.rstrip())
        
        
        if Path(f"{self.env_location}/.venv").is_dir() == True:
            self.initialized = True
        

    def initialize_env(self):
        with open(self.file_location, "w") as file:
            file.write(f"#!/bin/bash \n")
            
            first = True
            for index, (name, info) in enumerate(self.packages.items()):

                combinations = self.loadables[name]

                if self.install == True:

                    fresh = ""
                    if "fresh" in info:
                        fresh = "--fresh "

                    self.__install(file=file, combinations=list(combinations), package_name=name, fresh=fresh)

                if first == True:
                    file.write(f"spack env create {self.env_name}\n")
                    file.write("spack env list\n")
                    first = False
                    
                self.__add_packages(file=file, combinations=list(combinations), package_name=name)
                
                if index == len(self.packages.items())-1:
                    file.write(f"spack -e {self.env_name} install\n")
                    
            
            file.write("spack env list\n")
            file.write(f"spack env activate {self.env_name}\n")
            file.write(f"spack load {self.python_version}\n")
            #file.write("python --version\n")
            file.write(f"python -m venv {self.env_location.absolute()}/.venv\n")
            file.write(f"source {self.env_location.absolute()}/.venv/bin/activate\n")
            file.write("pip install --upgrade pip \n")
            file.write(f"{self.additional}\n")
            file.write("cd components\n")
            file.write("pip install -e .\n")
            file.write("cd -\n")
            #file.write("pip list\n")
            file.write(f"spack env deactivate\n")
        
        print(bcolors.OKCYAN + f"Initialize environment {self.env_name}" + bcolors.ENDC)
        
        if self.__use_spack_env == True:
            p = subprocess.Popen(["bash", self.file_location], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            #import sys
            #for line in iter(lambda: p.stdout.readline(1), b""): # type: ignore
            #    sys.stdout.buffer.write(line)
            p.wait()
            if p.returncode != 0:
                raise RuntimeError(bcolors.FAIL + "Environment creation has failed" + bcolors.ENDC)
            
        print(bcolors.OKGREEN + "Finish Initialize environment" + bcolors.ENDC)
        self.initialized = True
          
        self.file_location.unlink()
   
   
    def load_env(self):
        loadable = f"spack env activate {self.env_name}\n"

        for name, combinations in self.loadables.items():
            loadable = self.__load_packages(loadable=loadable, combinations=list(combinations), package_name=name)
        
        return loadable
        
        
    def __install(self, file, combinations, package_name: str, fresh: str):
        for combination in combinations:

            #print(f"spack install {fresh}{package_name}@{combination[0]} {combination[1]} %{combination[2]}")
            file.write(f"spack install {fresh}{package_name}@{combination[0]} {combination[1]} %{combination[2]}\n")  
        
        
    def __add_packages(self, file, combinations, package_name: str):     
        for combination in combinations:
            
            #print(f"spack -e {self.env_name} add {package_name}@{combination[0]} {combination[1]} %{combination[2]}")
            file.write(f"spack -e {self.env_name} add {package_name}@{combination[0]} {combination[1]} %{combination[2]}\n")  
            

    def __load_packages(self, loadable: str, combinations, package_name: str):
        for combination in combinations:
        
            #print(f"spack -e {self.env_name} load {package_name}@{combination[0]} {combination[1]} %{combination[2]}")
            loadable = loadable + f"eval $(spack -e {self.env_name} load --sh {package_name}@{combination[0]} {combination[1]} %{combination[2]})\n"
            
        return loadable
            
           
    def delete(self):
        
        if self.initialized == True:
            with open(self.file_location, "w") as file:
                file.write("#!/bin/bash  \n")
                file.write(f"spack env activate {self.env_name} -p \n")   
                file.write(f"spack remove --all \n")   
                file.write(f"spack env deactivate\n")    
                file.write(f"spack env remove {self.env_name} -y \n")


            p = subprocess.run(["bash", self.file_location], capture_output=True, check=True)
            #print(p.stderr)
            print(p.stdout)

            self.file_location.unlink()
            shutil.rmtree(path=self.env_location.absolute())
            
        else: 
            print(bcolors.WARNING + f"{self.env_name} has not been initialized, nothing to delete" + bcolors.ENDC)