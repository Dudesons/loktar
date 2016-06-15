from loktar.job import build_params_to_context
from loktar.parser import parse_statuses


class FakeStatus(object):
    def __init__(self, context, state):
        self.raw_data = {
            "context": context
        }
        self.state = state


def test_parse_statuses():
    build_params = [('The Package', 'Is a Test'),
                    ('swagger-rest-microservice', 'Is-a-Test'),
                    ('swagger-rest-microservice', 'Is a Test'),
                    ('my_client_claims', 'Is a Test')]

    assert parse_statuses(
        [FakeStatus(build_params_to_context(item[0], item[1]),
                    "success" if index % 2 else "failed")
         for index, item in enumerate(build_params)]
    ) == ({'my_client_claims', 'swagger-rest-microservice'}, {'swagger-rest-microservice', 'The Package'})

