import re
from datetime import datetime
from enum import Enum
from typing import Dict

Type = Enum("Type", "STATE COUNTRY")

class Region:
    def __init__(self, type: Type, name: str, country: str):
        self._type = type
        self._name = name
        self._country = country
        self._stats = dict()
        self._key = self._create_key()

    @property
    def name(self) -> str:
        return self._name

    @property
    def key(self) -> str:
        return self._key

    @property
    def stats(self) -> Dict:
        return self._stats

    def update_stats(self, date: datetime, stats: Dict):
        stats_ = self._stats.get(date)
        if stats_:
            stats_["confirmed"] += stats["confirmed"]
            stats_["deaths"] += stats["deaths"]
            stats_["recovered"] += stats["recovered"]
        else:
            self._stats[date] = stats

    def _create_key(self) -> str:
        key = self._name
        if self._type == Type.STATE:
            key += "_" + self._country

        key = key.casefold()
        key = re.sub("[ -]", "_", key)
        key = re.sub("['(),.]", "", key)

        return key

    def __lt__(self, other):
        if isinstance(other, Region):
            return self._key < other._key
        else:
            msg = f"Invalid comparison: {self.__class__} and {other.__class__}"
            raise RuntimeError(msg)

    def __iter__(self):
        for date, stats in sorted(self._stats.items()):
            date = date.strftime("%m/%d/%Y")
            stats = stats["confirmed"] - stats["deaths"] - stats["recovered"]
            yield date, stats

    def __repr__(self):
        return self._key

    def __str__(self):
        if self._type == Type.STATE:
            return f"{self._name}, {self._country}"
        else:
            return self._name
