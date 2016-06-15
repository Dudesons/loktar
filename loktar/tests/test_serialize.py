import pytest

from loktar.serialize import serialize
from loktar.serialize import unserialize


@pytest.mark.parametrize("item", ["http://foobar.com?p=5",
                                  {"toto":5},
                                  4,
                                  ["plop", 'tutu'],
                                  {"t", "p"},
                                  "&@!:/*-+5f"])
def test_serialize(item):
    assert unserialize(serialize(item)) == item