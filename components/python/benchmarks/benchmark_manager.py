from func.datastruct import bcolors
from dataclasses import dataclass
from pathlib import Path
import shutil
import time
import yaml
import hashlib
import asyncio

@dataclass
class BenchmarkManager:
    
    """Defines handler to read configuration from yaml file and create matching benchmarks. Also configures the benchmark environments and gathers system information.
    
    Attributes
    ----------
    handler_id: str
        Unique handler ID to identify the handler assigned to this specific benchmark.
    
    """
    
    handler_id: str
    
    def __init__(self, handler_id: str, run: dict, parallel: bool, par_backend: None | str, language: str, format: str, range: list, stepsize: int, iterations: int, use_path: str, bm_config: dict):
        
        # Object config
        self.handler_id = handler_id
        
        hash_str = str(run) + str(bm_config)
        self.hash       = hashlib.sha256(hash_str.encode()).hexdigest()
        
        self.use_path    = use_path
        self.dir_path    = Path(f"{self.use_path}/{str(self.hash)}")
        
        # Benchmark config
        self.run        = run
        self.parallel   = parallel
        self.par_backend= par_backend
        self.language   = language
        self.format     = format
        self.range      = range
        self.stepsize   = stepsize
        self.iterations = iterations
        
        # Source code
        self.src = bm_config["source"]
        
        # Environment config
        self._checkpoint = yaml
        self._node       = int
        self._node_info  = yaml
        self._profiler   = bool
        
        self.run_benchmark()
    
    
    def run_benchmark(self):
        self.dir_path.mkdir(parents=True)
        with open(f"{self.dir_path}/{str(self.hash)}.{self.language}", "w") as file:
            file.write(self.src)
            
        time.sleep(1)
        shutil.rmtree(path=self.dir_path)