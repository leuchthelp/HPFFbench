def calc_size_unit(input: list[int]) -> tuple[float, str]:
    compare = 1.0
    size = "Byte"

    if not input:
        res = 0.0
        return res, size

    for item in input:
        compare *= item

    compare *= 8.0
    res = compare

    if compare >= 1 * 1024:
        res = res / 1024
        size = "KB"

    if compare >= 1 * 1024**2:
        res = res / 1024
        size = "MB"

    if compare >= 1 * 1024**3:
        res = res / 1024
        size = "GB"

    if compare >= 1 * 1024**4:
        res = res / 1024
        size = "TB"

    if compare >= 1 * 1024**5:
        res = res / 1024
        size = "PB"

    return res, size
