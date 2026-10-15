from src.tools import calculate


def test_calculate_ok():
    assert calculate.invoke({"expression": "2 * (3 + 4)"}) == "14"


def test_calculate_blocks_code():
    assert calculate.invoke({"expression": "__import__('os')"}).startswith("Error")
