from dates import is_valid_date


def test_regular():
    assert is_valid_date(2023, 1, 31)
