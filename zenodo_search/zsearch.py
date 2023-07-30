from typing import List
from urllib.parse import urlencode

import requests

BASE_RECORD_URL = 'https://zenodo.org/api/records?'


class ReadOnlyDict(dict):
    __specials__ = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for key, value in self.items():
            if key in self.__specials__:
                setattr(self, key, self.__specials__[key](value))
            else:
                if isinstance(value, dict):
                    setattr(self, key, ReadOnlyDict(value))
                else:
                    setattr(self, key, value)

    def __readonly__(self, *args, **kwargs):
        raise TypeError("Read-only dictionary, cannot modify items.")

    def __setattr__(self, name, value):
        if hasattr(self, name):
            raise TypeError("Read-only dictionary, cannot modify items.")
        super().__setattr__(name, value)

    __setitem__ = __readonly__
    __delitem__ = __readonly__
    pop = __readonly__
    clear = __readonly__
    update = __readonly__


class ZenodoFile(ReadOnlyDict):

    def download(self):
        from .utils import download_file
        return download_file(self)


class ZenodoFiles(list):

    def __getitem__(self, item):
        return ZenodoFile(super().__getitem__(item))

    def download(self):
        from .utils import download_files
        return download_files(self)


class Record(ReadOnlyDict):
    """Zenodo Record. Effectively a wrapper around the dictionary which is
    returned by the Zenodo API upon the query request
    """
    __specials__ = {'files': ZenodoFiles}

    def __repr__(self):
        return f'<Record {self.links.latest_html}: {self.metadata.title}>'

    def __str__(self):
        return f'<Record {self.links.latest_html}: {self.metadata.title}>'

    def _repr_html_(self):
        link = self.links["latest_html"]
        badge = self.links["badge"]
        return f'<a href="{link}" target="_blank"><img src="{badge}" alt="Zenodo Badge" /></a> {self.metadata.title}'


class Records:
    """Multiple Zenodo Record objects"""

    def __init__(self, records: List[Record], query_string: str, response):
        self._records = records
        self.query_string = query_string
        self.response = response

    def __repr__(self) -> str:
        return f'<Records ({self.query_string["q"]} with {len(self)} records>'

    def __len__(self):
        return len(self._records)

    def __getitem__(self, item):
        return self._records[item]

    def __iter__(self):
        return iter(self._records)


def search(search_string: str):
    """post query to zenodo api

    Examples
    --------
    >>> from zsearch import search
    >>> search('resource_type.type:other AND creators.name:("Probst, Matthias")')
    >>> search('type:dataset AND creators.affiliation:("University A" OR "Cambridge")')
    """
    search_query = {"q": search_string.replace("/", "*")}
    api_url = BASE_RECORD_URL + urlencode(search_query)

    response = requests.get(api_url)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Parse the JSON response
        data = response.json()

        # Extract relevant information from the response
        if 'hits' in data:
            return Records([Record(hit) for hit in data['hits']['hits']],
                           search_query,
                           response)
    else:
        raise RuntimeError(f"Error: Request failed with status code {response.status_code}")


def search_keywords(keywords: List[str]):
    """Searches for all keywords"""
    kwds = ' AND '.join(f'"{k}"' for k in keywords)
    return search(f'keywords:({kwds})')