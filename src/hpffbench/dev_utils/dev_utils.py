from dataclasses import dataclass

@dataclass
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def calc_size_unit(input: list):
    
    res = 1
    compare = 1
    size = "Byte"
    
    if not input:
        res = 0
        return res, size
    
    for item in input:
        compare *= item
    
    compare *= 8
    res = compare
    
    if compare >= 1 * 1024:
        res = res 
        size="KB"
       
    if compare >= 1 * 1024 ** 2:
        res = res / 1024
        size = "MB"
        
    if compare >= 1 * 1024 ** 3:
        res = res / 1024 ** 2 
        size = "GB"
        
    if compare >= 1 * 1024 ** 4:
        res = res / 1024 ** 3 
        size = "TB"
        
    if compare >= 1 * 1024 ** 5:
        res = res / 1024 ** 4
        size = "PB"

    return res, size