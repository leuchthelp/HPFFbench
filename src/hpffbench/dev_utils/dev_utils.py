from enum import IntEnum

import numpy as np


class FileSizes(IntEnum):
    Byte = 0
    KB = 1
    MB = 2
    GB = 3
    TB = 4
    PB = 5


def calc_size_unit(
    shape: list[int], dtype: str = "f8", required_unit: FileSizes | None = None
) -> tuple[float, FileSizes]:
    compare = 1.0
    size = FileSizes.Byte

    if not shape:
        res = 0.0
        return res, size

    for item in shape:
        compare *= item

    compare *= np.dtype(dtype).itemsize
    res = compare

    if compare >= 1024 or required_unit == FileSizes.KB:
        res = compare / 1024
        size = FileSizes.KB

        if required_unit == size:
            return res, size

    if compare >= 1024**2 or required_unit == FileSizes.MB:
        res = compare / 1024**2
        size = FileSizes.MB

        if required_unit == size:
            return res, size

    if compare >= 1024**3 or required_unit == FileSizes.GB:
        res = compare / 1024**3
        size = FileSizes.GB

        if required_unit == size:
            return res, size

    if compare >= 1024**4 or required_unit == FileSizes.TB:
        res = compare / 1024**4
        size = FileSizes.TB

        if required_unit == size:
            return res, size

    if compare >= 1024**5 or required_unit == FileSizes.PB:
        res = compare / 1024**5
        size = FileSizes.PB

    return res, size
