#!/usr/bin/python3
# pylint: disable=missing-module-docstring, missing-class-docstring, missing-function-docstring
import argparse
import csv
import logging
import re
import sys
import tempfile
from collections import defaultdict
from contextlib import suppress
from datetime import datetime
from pathlib import Path
from subprocess import run
from typing import Dict, Sequence

from pkg_resources import DistributionNotFound, RequirementParseError, get_distribution


_LOGGER = logging.getLogger(__name__)
__version__ = "0.0.0"

with suppress(DistributionNotFound, RequirementParseError):
    __version__ = get_distribution(__name__).version


DATAPATH = Path("COVID-19", "csse_covid_19_data", "csse_covid_19_daily_reports")

class State:
    _STATE_MATCHERS = {
        "Alberta": r".*, Alberta$",
        "Arizona": r".*, AZ$",
        "California": r"(.*, CA$|.*, CA \(From Diamond Princess\))",
        "Colorado": r".*, CO$",
        "Connecticut": r".*, CT$",
        "District of Columbia": r"Washington, D.C.$",
        "Florida": r".*, FL$",
        "Georgia": r".*, GA$",
        "Hawaii": r".*, HI$",
        "Illinois": r".*, IL$",
        "Indiana": r".*, IN$",
        "Iowa": r".*, IA$",
        "Kansas": r".*, KS$",
        "Kentucky": r".*, KY$",
        "Louisiana": r".*, LA$",
        "Maryland": r".*, MD$",
        "Massachusetts": r".*, MA$",
        "Minnesota": r".*, MN$",
        "Missouri": r".*, MO$",
        "Nebraska": r"(.*, NE$|.*, NE \(From Diamond Princess\))",
        "Nevada": r".*, NV$",
        "New Hampshire": r".*, NH$",
        "New Jersey": r".*, NJ$",
        "New York": r".*, NY$",
        "North Carolina": r".*, NC$",
        "Oklahoma": r".*, OK$",
        "Ontario": r".*, ON$",
        "Oregon": r".*, OR$",
        "Pennsylvania": r".*, PA$",
        "Quebec": r".*, QC$",
        "Rhode Island": r".*, RI$",
        "South Carolina": r".*, SC$",
        "Tennessee": r".*, TN$",
        "Texas": r"(.*, TX$|.*, TX \(From Diamond Princess\))",
        "United Kingdom": r"^UK$",
        "Utah": r".*, UT$",
        "Vermont": r".*, VT$",
        "Virginia": r".*, VA$",
        "Virgin Islands": r"(^United States Virgin Islands$|^Virgin Islands, U.S.$)",
        "Washington": r".*, WA$",
        "Wisconsin": r".*, WI$",
    }

    def __init__(self, string: str):
        self._name = self._clean_state_name(string)

    @property
    def name(self) -> str:
        return self._name

    def _clean_state_name(self, string: str) -> str:
        string = string.strip()

        if not string or string == "US" or self._is_cruise_ship(string):
            return ""
        elif string in self._STATE_MATCHERS:
            return string

        for state, re_str in self._STATE_MATCHERS.items():
            if re.search(re_str, string):
                return state

        return string

    @staticmethod
    def _is_cruise_ship(string) -> bool:
        return not re.search("(princess|cruise ship)", string, re.IGNORECASE) is None

    def __eq__(self, other):
        if isinstance(other, State):
            return self._name.casefold() == other._name.casefold()
        elif isinstance(other, str):
            return self._name.casefold() == other.casefold()
        else:
            return false

    def __hash__(self):
        return hash(self._name.casefold())

    def __lt__(self, other):
        if isinstance(other, State):
            return self._name.casefold() < other._name.casefold()
        elif isinstance(other, str):
            return self._name.casefold() < other.casefold()
        else:
            raise RuntimeError(f"Invalid comparison: {self.__class__} and {other.__class__}")

    def __repr__(self):
        return self._name

    def __str__(self):
        return self._name


class Stats:
    _date: str = ""
    _confirmed: int = 0
    _deaths: int = 0
    _recovered: int = 0

    def __init__(self, data=None):
        def toint(data_):
            return int(data_) if data_ else 0

        if isinstance(data, dict):
            self._date = self._datestr(data["Last Update"])
            self._confirmed = toint(data.get("Confirmed"))
            self._deaths = toint(data.get("Deaths"))
            self._recovered = toint(data.get("Recovered"))
        elif isinstance(data, Stats):
            self._date = data._date
            self._confirmed = data._confirmed
            self._deaths = data._deaths
            self._recovered = data._recovered
        elif data:
            raise TypeError(f"Can't convert {data.__class__} to Stats")

    @property
    def date(self):
        return self._date

    @property
    def infected(self) -> int:
        return self._confirmed - self._deaths - self._recovered

    @staticmethod
    def _datestr(date_field):
        if "/" in date_field:
            rawdate = date_field.split(" ")[0]
            month, day, year = tuple(int(x) for x in rawdate.split("/"))
            if year < 100:
                year += 2000
            date = datetime.strptime(f"{month:02d}/{day:02d}/{year:04d}", "%m/%d/%Y")
        else:
            date = datetime.strptime(date_field, "%Y-%m-%dT%H:%M:%S")
        return date.strftime("%m/%d/%Y")

    def __iadd__(self, other):
        other = Stats(other)
        if not self._date:
            self._date = other._date
        elif self._date != other._date:
            raise RuntimeError(f"Dates do not match.")
        self._confirmed += other._confirmed
        self._deaths += other._deaths
        self._recovered += other._recovered
        return self


def get_infected_state_data(state: State) -> Dict[str, int]:
    data = defaultdict(Stats)
    if not state:
        _LOGGER.warning("State cannot be an empty string.")

    for filename in sorted(DATAPATH.glob("*.csv")):
        with filename.open(mode="r", encoding="utf-8-sig") as csvfile:
            csvreader = csv.DictReader(csvfile)
            for row in csvreader:
                if state == State(row["Province/State"]):
                    stats = Stats(row)
                    data[stats.date] += stats
    return {date_: stats_.infected for date_, stats_ in data.items()}


def get_states() -> Sequence[State]:
    states = list()
    for filename in DATAPATH.glob("*.csv"):
        with filename.open(mode="r", encoding="utf-8-sig") as csvfile:
            csvreader = csv.DictReader(csvfile)
            states += list(filter(lambda state : state.name,
                (State(row["Province/State"]) for row in csvreader)))

    return sorted(set(states))


def main():
    """ Main interface """
    parser = _create_parser()
    args = parser.parse_args()

    if len(sys.argv) == 1:
        parser.print_usage()
        parser.exit(status=1)
    elif args.list:
        print("\n".join(map(str, get_states())))
        sys.exit()

    data = get_infected_state_data(args.state)
    with tempfile.NamedTemporaryFile(mode="w") as datfile:
        for key in sorted(data):
            datfile.write(f"{key}\t{data[key]}\n")
        datfile.flush()
        run(["gnuplot", "-p", "-e", f"datfile='{datfile.name}'", "./covid.gp"], check=True)


def _create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=f"%(prog)s CLI Help", allow_abbrev=False,)

    parser.add_argument(
        "-v", "--version", action="version", version=f"%(prog)s {__version__}",
    )

    parser.add_argument(
        "-l", "--list", action="store_true", help="List states",
    )

    parser.add_argument(
        "state", nargs="?", type=State, choices=get_states(), help="State to graph",
    )

    return parser


if __name__ == "__main__":
    main()
