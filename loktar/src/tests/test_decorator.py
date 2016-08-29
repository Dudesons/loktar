
import pytest

from loktar.decorators import retry


def test_retry():
    @retry
    def simple_run(b):
        pass

    @retry
    def fail_run(b):
        raise ValueError

    simple_run(2)

    with pytest.raises(ValueError):
        fail_run(2)
