from loktar.job import context_to_build_params
from loktar.log import Log

logger = Log()


def parse_statuses(statuses):
    """Parse a list of statuses

    Some packages can be simulteneouly in green builds and red builds, if they were built with
    more than one different build type.

    Args:
        statuses (iterator of github.CommitStatus.CommitStatus): List of commit statuses

    Returns:
        a tuple of sets: green_builds, red_builds
    """
    green_builds = set()
    red_builds = set()
    for status in statuses:
        context = status.raw_data['context']
        try:
            package, type_build = context_to_build_params(context)
        except ValueError as exc:
            logger.warning(str(exc))
            continue
        if status.state == 'success':
            green_builds |= {(package, type_build)}
        else:
            red_builds |= {(package, type_build)}

    # If a tuple (package, type_build) is green and also appears in red, remove it from red
    # (since red are also pending)
    red_builds -= green_builds

    green_builds = {package for package, _ in green_builds}
    red_builds = {package for package, _ in red_builds}

    return green_builds, red_builds
