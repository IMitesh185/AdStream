from adstream.metrics import compute_ctr

def test_check_ctr():
    assert compute_ctr(1, 100) == 0.01
    assert compute_ctr(0, 100) == 0.0
    assert compute_ctr(5, 0) == 0.0
    import pytest
    with pytest.raises(ValueError, match="Clicks cannot be negative"):
        compute_ctr(-1, 10)