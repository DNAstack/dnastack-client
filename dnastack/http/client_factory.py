from contextlib import contextmanager
from http.client import HTTPConnection
from typing import Optional

from imagination.decorator.service import Service
from requests import Session
from requests.adapters import HTTPAdapter
from urllib3 import Retry


@Service()
class HttpClientFactory:
    __DEFAULT_RETRY_OPTION = Retry(total=5,
                                   backoff_factor=0.5,
                                   status_forcelist=[500, 502, 503, 504])

    @classmethod
    def make(cls, retry_option: Optional[Retry] = None) -> Session:
        s = Session()
        for prefix in {'http', 'https'}:
            s.mount(prefix, HTTPAdapter(max_retries=retry_option or cls.__DEFAULT_RETRY_OPTION))
        return s


@contextmanager
def without_wire_debugging():
    # Engine create and update turn off process-global http.client tracing for that one call.
    # CLI debug mode does not set HTTPConnection.debuglevel, and token calls do not use this helper.
    saved = HTTPConnection.debuglevel
    HTTPConnection.debuglevel = 0
    try:
        yield
    finally:
        HTTPConnection.debuglevel = saved
