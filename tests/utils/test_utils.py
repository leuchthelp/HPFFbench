import pytest

from hpffbench.dev_utils import calc_size_unit


@pytest.mark.parametrize(
    "input1, input2, input3, expectation",
    [
        ([134217728], "f8", "GB", (1, "GB")),
        ([10 * 134217728], "f8", "GB", (10, "GB")),
        ([100 * 134217728], "f8", "GB", (100, "GB")),
        ([1024 * 134217728], "f8", "TB", (1, "TB")),
        ([10240 * 134217728], "f8", "TB", (10, "TB")),
        ([134217728], "f8", "MB", (1024, "MB")),
        ([512, 512, 512], "f8", "GB", (1, "GB")),
        ([512, 512, 512], "f8", "MB", (1024, "MB")),
        ([5120, 512, 512], "f8", "GB", (10, "GB")),
        ([5120, 512, 512], "f8", "MB", (10240, "MB")),
        ([5120, 512, 512], "f8", "KB", (10485760, "KB")),
        ([5120, 512, 512], "f8", "TB", (0.009765625, "TB")),
        ([2 * 134217728], "f4", "GB", (1, "GB")),
        ([20 * 134217728], "f4", "GB", (10, "GB")),
        ([2 * 134217728], "i4", "GB", (1, "GB")),
    ],
)
def test_calc_size_unit(input1, input2, input3, expectation):
    assert calc_size_unit(input1, input2, input3) == expectation
