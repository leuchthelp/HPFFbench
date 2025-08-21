from func.datastruct import bcolors
from dataclasses import dataclass
import uuid
import yaml
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
    
    def __init__(self, handler_id: str, run: dict, parallel: bool, par_backend: None | str, language: str, format: str, range: list, stepsize: int, iterations: int):
        
        # Object config
        self.handler_id = handler_id
        self.uuid       = uuid.uuid4
        self.dir_path   = str(self.uuid)
        
        # Benchmark config
        self.run        = run
        self.parallel   = parallel
        self.par_backend= par_backend
        self.language   = language
        self.format     = format
        self.range      = range
        self.stepsize   = stepsize
        self.iterations = iterations
        
        # Environment config
        self._checkpoint = yaml
        self._node       = int
        self._node_info  = yaml
        self._profiler   = bool
        

        if parallel:
            if self._check_par_backend(): raise ValueError(bcolors.FAIL + f"Parallel backend {self.par_backend} selected is not supported" + bcolors.ENDC)

        self._run_benchmark()
    
    
    def _check_par_backend(self) -> bool:
        
        print(f"Something went wrong while trying to check of parallel backende {self.par_backend}")
        return True
    
    def _run_benchmark(self):
        
        
        pass