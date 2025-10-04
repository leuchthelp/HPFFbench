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