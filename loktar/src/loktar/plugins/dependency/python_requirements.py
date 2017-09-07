import os
import re


def python_deps(basepath):
    """Get python dependencies from requirements.txt and test_requirements.txt.

    Args:
        basepath (str): Path to the package

    Returns:
        set: Requirements names.
    """
    requirements = []

    requirements_file = os.path.join(basepath, "requirements.txt")
    test_requirements_file = os.path.join(basepath, "test_requirements.txt")
    app_requirements_file = os.path.join(basepath, "app", "requirements.txt")
    app_test_requirements_file = os.path.join(basepath, "app", "test_requirements.txt")
    src_requirements_file = os.path.join(basepath, "src", "requirements.txt")
    src_test_requirements_file = os.path.join(basepath, "src", "test_requirements.txt")

    for req_file in (requirements_file, test_requirements_file, app_requirements_file,
                     app_test_requirements_file, src_requirements_file, src_test_requirements_file):
        if os.path.exists(req_file):
            with open(req_file, "r") as f:
                requirements.extend(f.readlines())

    requirements_names = set(filter(None, map(lambda x: re.split("==|>=|>|<=|<", x)[0], requirements)))
    return requirements_names

Plugin = python_deps
