import pytest

from loktar.decorators import retry


def test_retry():
    @retry
    def a(b):
        pass

    @retry
    def aa(b):
        raise ValueError

    a(2)

    with pytest.raises(ValueError):
        aa(2)
