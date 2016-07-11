from __future__ import division

import random
import time

from loktar.log import Log


def retry(call):
    """Decorator used to retry a function

    Args:
        call: function to be retried

    Returns:
        function equipped with the decorator
    """

    def _retry(*args, **kwargs):
        """Fake doc"""
        logger = Log()
        last_exception = None
        multiplier = 1.5
        retry_interval = 0.5
        randomization_factor = 0.5
        total_sleep_time = 0
        max_sleep_time = 3 * 60

        request_nb = 0
        # Capped to 20 minutes
        while total_sleep_time < max_sleep_time:
            try:
                return call(*args, **kwargs)
            except Exception as exc:
                # Inspired from https://developers.google.com/api-client-library/java/google-http-java-client/reference/
                # 1.20.0/com/google/api/client/util/ExponentialBackOff
                next_retry_sleep = (multiplier ** request_nb *
                                    (retry_interval *
                                     (random.randint(0, int(2 * randomization_factor * 1000)) / 1000 +
                                      1 - randomization_factor)))

                total_sleep_time += next_retry_sleep
                request_nb += 1

                time.sleep(next_retry_sleep)

                last_exception = exc
                logger.info('Got an exception: {0}. Slept ({1} seconds / {2} seconds)'
                            .format(exc,
                                    total_sleep_time,
                                    max_sleep_time))
        logger.info('Max sleep time exceeded, raising exception.')
        raise last_exception

    # Keep the doc
    _retry.__doc__ = call.__doc__

    return _retry
