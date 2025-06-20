from typing import Any, Dict, Iterator, List

from dnastack import DataConnectClient
from dnastack.common.exceptions import DependencyError


class SearchOperation:
    def __init__(self, dc: DataConnectClient, no_auth: bool, query: str):
        self._dc = dc
        self._no_auth = no_auth
        self.__query = query

    def __iter__(self):
        return self._dc.query(self.__query, no_auth=self._no_auth)

    def load_data(self) -> Iterator[Dict[str, Any]]:
        return self._dc.query(self.__query, no_auth=self._no_auth)

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
