import numpy as np


def calc_size_unit(
    shape: list[int], dtype: str = "f8", required_unit: str | None = None
) -> tuple[float, str]:
    compare = 1.0
    size = "Byte"

    if not shape:
        res = 0.0
        return res, size

    for item in shape:
        compare *= item

    compare *= np.dtype(dtype).itemsize

    if compare >= 1024 or required_unit == "KB":
        res = compare / 1024
        size = "KB"

        if required_unit == size:
            return res, size

    if compare >= 1024**2 or required_unit == "MB":
        res = compare / 1024**2
        size = "MB"

        if required_unit == size:
            return res, size

    if compare >= 1024**3 or required_unit == "GB":
        res = compare / 1024**3
        size = "GB"

        if required_unit == size:
            return res, size

    if compare >= 1024**4 or required_unit == "TB":
        res = compare / 1024**4
        size = "TB"

        if required_unit == size:
            return res, size

    if compare >= 1024**5 or required_unit == "PB":
        res = compare / 1024**5
        size = "PB"

    return res, size
