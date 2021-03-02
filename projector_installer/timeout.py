#  Copyright 2000-2021 JetBrains s.r.o.
#  Use of this source code is governed by the Apache 2.0 license that can be found
#  in the LICENSE file.

"""timeout decorator implementation"""

from signal import signal, SIGALRM, setitimer, ITIMER_REAL


class TimeoutException(Exception):
    """Timeout exception"""


def timeout(interval: float):  # type: ignore
    """Timeout decorator, interval in seconds.
    Decorated function raises TimeoutException if execution takes more
    time than given interval
    """

    def decorate(function):  # type: ignore
        """decorate"""

        def signal_handler(*args):  # type: ignore
            # pylint: disable=unused-argument
            """SIGALRM handler"""
            raise TimeoutException()

        def wrapped(*args, **kwargs):  # type: ignore
            """Wrapped function"""
            old_handler = signal(SIGALRM, signal_handler)
            setitimer(ITIMER_REAL, interval, 0)

            try:
                res = function(*args, **kwargs)
            finally:
                setitimer(ITIMER_REAL, 0, 0)
                signal(SIGALRM, old_handler)

            return res

        return wrapped

    return decorate
