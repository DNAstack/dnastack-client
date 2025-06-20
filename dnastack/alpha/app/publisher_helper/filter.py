from typing import Any, Dict, Iterator, List

from dnastack.client.data_connect import QueryLoader
from dnastack.client.result_iterator import ResultIterator
from dnastack.common.exceptions import DependencyError


class FilterOperation:
    def __init__(self, signed_url):
        self._signed_url = signed_url

    def __iter__(self):
        return ResultIterator(QueryLoader(initial_url=self._signed_url))

    def load_data(self) -> Iterator[Dict[str, Any]]:
        return ResultIterator(QueryLoader(initial_url=self._signed_url))

    def to_list(self) -> List[Dict[str, Any]]:
        return [row for row in self.load_data()]

    def to_data_frame(self):
        try:
            # We delay the import as late as possible so that the optional dependency (pandas)
            # does not block the other functionalities of the library.
            import pandas as pd

            return pd.DataFrame(self.load_data())
        except ImportError:
            raise DependencyError("pandas")
