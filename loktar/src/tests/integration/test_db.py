from loktar.check import wait_elasticsearch
from loktar.db import Run
import os
from uuid import uuid4
import time


def test_run_model():
    # Actuyally disable
    return
    if wait_elasticsearch(host="elasticsearch"):
        os.environ["LOKTAR_RUN_DB_DB"] = "loktar_ci_{}".format(str(uuid4()))
        os.environ["LOKTAR_RUN_DB_TABLE"] = "run"

        run = Run()
        payloads = [{
                        "run_archive_path": "run_archive{}".format(i),
                        "depency_graph": [],
                        "artifacts_modified": [],
                        "commit_id": "commit_id_{}".format(i),
                        "committer": "committer_{}".format(i),
                        "git_branch": "git_branch{}".format(i),
                        "result": "result_{}".format(i),
                        "jobs_state": {
                            "success": None,
                            "in_queue": True,
                            "faillure": None
                        },
                        "start_time": time.time() + i,
                        "end_time": None
                    }
                    for i in xrange(20)]

        responses = [run.set_run(payload) for payload in payloads]

        assert len(filter(None, responses)) == len(payloads)

        for id_doc, payload in zip(responses, payloads):
            assert run.get_run(id_doc) == payload

        payload_lenght = len(payloads)
        first_ten_payloads = payloads[:(payload_lenght/2)]
        last_ten_payloads = payloads[payload_lenght/2:payload_lenght]
        from pprint import pprint
        pprint(first_ten_payloads)
        print "="*10
        pprint(run.get_runs())
        print "="*10
        pprint(run.get_runs(page=1))
        print "="*10
        pprint(run.get_runs(size=20))
        assert run.get_runs() == first_ten_payloads
        assert run.get_runs(page=1) == last_ten_payloads
        assert run.get_runs(size=20) == payloads

        del os.environ["LOKTAR_RUN_DB_DB"]
        del os.environ["LOKTAR_RUN_DB_TABLE"]
