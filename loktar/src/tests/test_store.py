import pytest

from loktar.exceptions import UnknownStorageMethod
from loktar.store import _get_back_artifact_from_s3
from loktar.store import get_back_test_env
from loktar.store import store_artifact

from loktar.store import _store_artifact_on_s3


def test_store_artifact_on_s3(mocker):
    mocker.patch("loktar.store.s3")
    assert "s3:@:toto" == _store_artifact_on_s3("/tmp/toto", None, None)


@pytest.mark.parametrize("store_type", ["s3"])
def test_store_artifact(mocker, store_type):
    mocker.patch("loktar.store.s3")
    assert "{0}:@:toto".format(store_type) == store_artifact(store_type, "/tmp/toto")


@pytest.mark.parametrize("store_type", ["foobar"])
def test_store_artifact_fail_on_unknown_storage_method(mocker, store_type):
    mocker.patch("loktar.store.s3")
    with pytest.raises(UnknownStorageMethod):
        store_artifact(store_type, "/tmp/toto")


def test_get_back_test_env_on_s3(mocker):
    mocker.patch("loktar.store.s3")
    assert "/tmp/toto" == _get_back_artifact_from_s3("toto", None, None)


@pytest.mark.parametrize("target", ["s3:@:toto"])
def test_get_back_test_env(mocker, target):
    mocker.patch("loktar.store.s3")
    assert "/tmp/{0}".format(target.split(":@:")[-1]) == get_back_test_env(target)


@pytest.mark.parametrize("target", ["foobar:@:toto"])
def test_get_back_test_env_fail_on_unknown_storage_method(mocker, target):
    mocker.patch("loktar.store.s3")
    with pytest.raises(UnknownStorageMethod):
        get_back_test_env(target)
