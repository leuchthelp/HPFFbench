import numpy as np


def calc_size_unit(
    shape: list[int], dtype: str = "f8", required_unit: str = "GB"
) -> tuple[float, str]:
    compare = 1.0
    size = "Byte"

    if not shape:
        res = 0.0
        return res, size

    for item in shape:
        compare *= item

    compare *= np.dtype(dtype).itemsize

    res = compare / 1024
    size = "KB"

    if required_unit == size:
        return res, size

    res = compare / 1024**2
    size = "MB"

    if required_unit == size:
        return res, size

    res = compare / 1024**3
    size = "GB"

    if required_unit == size:
        return res, size

    res = compare / 1024**4
    size = "TB"

    if required_unit == size:
        return res, size

    res = compare / 1024**5
    size = "PB"

    return res, size
