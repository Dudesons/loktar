from copy import deepcopy

from flexmock import flexmock
import pytest

from loktar.plugins.artifact import protobuff


@pytest.mark.parametrize("artifact_info", [{
      "artifact_type": "protobuff",
      "artifact_name": "events",
      "test_type": "no-test",
      "type": "library",
      "build_info": {
        "sub_artifact_types": [
          {"type": "jvm", "remote": True},
          {"type": "whl"}
        ]
      },
      "dependencies_type": [
        "dockerfile",
        "python_requirements"
      ],
      "notification": {
        "slack_channels": [
          "ci-platform"
        ]
      }
    }])
@pytest.mark.parametrize("remote", [True, False])
def test_plugins_artifact_protobuff(artifact_info, remote):

    jvm_protobuff_config = deepcopy(artifact_info)
    jvm_protobuff_config["artifact_type"] = "jvm"
    whl_protobuff_config = deepcopy(artifact_info)
    whl_protobuff_config["artifact_type"] = "whl"

    flexmock(protobuff) \
        .should_receive("strategy_runner") \
        .with_args(jvm_protobuff_config,
                   "artifact",
                   remote=True) \
        .and_return(None)

    flexmock(protobuff) \
        .should_receive("strategy_runner") \
        .with_args(whl_protobuff_config,
                   "artifact",
                   remote=False) \
        .and_return({"version": 42})

    plugin = protobuff.Protobuff(artifact_info, remote)
    plugin.launch_sub_project()
    assert type(plugin.share_memory) is dict
    assert "latest_versions" in plugin.share_memory
    assert "{}-{}-42".format(artifact_info["artifact_name"],
                             whl_protobuff_config["artifact_type"])\
           in plugin.share_memory["latest_versions"]
