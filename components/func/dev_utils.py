def calc_size_unit(input: list):
    
    res = 1
    size = "Byte"
    
    if not input:
        return None
    
    for item in input:
        res *= item
    
    res *= 8
    if res > 1 * 1024 * 1024:
        res /= 1024
        size="KB"
       
    if res > 1024:
        res /= 1024
        size = "MB"
        
    if res > 1:
        res /= 1024
        size = "GB"

    return res, size