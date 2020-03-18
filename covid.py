#!/usr/bin/python3
# pylint: disable=missing-module-docstring, missing-class-docstring, missing-function-docstring
import argparse
import csv
import re
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from subprocess import run

import pkg_resources


try:
    __version__ = pkg_resources.get_distribution(__name__).version
except (pkg_resources.DistributionNotFound, pkg_resources.RequirementParseError):
    __version__ = None


DATAPATH = Path("COVID-19", "csse_covid_19_data", "csse_covid_19_daily_reports")

STATE_MATCHERS = {
    "Alberta": re.compile(r".*, Alberta$"),
    "Arizona": re.compile(r".*, AZ$"),
    "California": re.compile(r"(.*, CA$|.*, CA \(From Diamond Princess\))"),
    "Colorado": re.compile(r".*, CO$"),
    "Connecticut": re.compile(r".*, CT$"),
    "District of Columbia": re.compile(r"Washington, D.C.$"),
    "Florida": re.compile(r".*, FL$"),
    "Georgia": re.compile(r".*, GA$"),
    "Hawaii": re.compile(r".*, HI$"),
    "Illinois": re.compile(r".*, IL$"),
    "Indiana": re.compile(r".*, IN$"),
    "Iowa": re.compile(r".*, IA$"),
    "Kansas": re.compile(r".*, KS$"),
    "Kentucky": re.compile(r".*, KY$"),
    "Louisiana": re.compile(r".*, LA$"),
    "Maryland": re.compile(r".*, MD$"),
    "Massachusetts": re.compile(r".*, MA$"),
    "Minnesota": re.compile(r".*, MN$"),
    "Missouri": re.compile(r".*, MO$"),
    "Nebraska": re.compile(r"(.*, NE$|.*, NE \(From Diamond Princess\))"),
    "Nevada": re.compile(r".*, NV$"),
    "New Hampshire": re.compile(r".*, NH$"),
    "New Jersey": re.compile(r".*, NJ$"),
    "New York": re.compile(r".*, NY$"),
    "North Carolina": re.compile(r".*, NC$"),
    "Oklahoma": re.compile(r".*, OK$"),
    "Ontario": re.compile(r".*, ON$"),
    "Oregon": re.compile(r".*, OR$"),
    "Pennsylvania": re.compile(r".*, PA$"),
    "Quebec": re.compile(r".*, QC$"),
    "Rhode Island": re.compile(r".*, RI$"),
    "South Carolina": re.compile(r".*, SC$"),
    "Tennessee": re.compile(r".*, TN$"),
    "Texas": re.compile(r"(.*, TX$|.*, TX \(From Diamond Princess\))"),
    "Utah": re.compile(r".*, UT$"),
    "Vermont": re.compile(r".*, VT$"),
    "Virginia": re.compile(r".*, VA$"),
    "Washington": re.compile(r".*, WA$"),
    "Wisconsin": re.compile(r".*, WI$"),
}


class Stats:
    def __init__(self, data=None):
        def toint(data_):
            return int(data_) if data_ else 0

        if not data:
            self._date = None
            self._confirmed = 0
            self._deaths = 0
            self._recovered = 0
        elif isinstance(data, dict):
            self._date = self._datestr(data["Last Update"])
            self._confirmed = toint(data.get("Confirmed"))
            self._deaths = toint(data.get("Deaths"))
            self._recovered = toint(data.get("Recovered"))
        elif isinstance(data, Stats):
            self._date = data._date
            self._confirmed = data._confirmed
            self._deaths = data._deaths
            self._recovered = data._recovered
        else:
            raise TypeError(f"Can't convert {data.__class__} to Stats")

    @property
    def date(self):
        return self._date

    @property
    def infected(self):
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
        if self._date is None:
            self._date = other._date
        elif self._date != other._date:
            raise RuntimeError(f"Dates do not match.")
        self._confirmed += other._confirmed
        self._deaths += other._deaths
        self._recovered += other._recovered
        return self


def match_cruise_ship(state_field):
    matcher = re.compile("(.*princess.*|.*cruise ship.*)", re.IGNORECASE)
    if matcher.match(state_field):
        return True
    return False


def massage_state(state_field):
    state_field = state_field.strip()
    for state, matcher in STATE_MATCHERS.items():
        if matcher.match(state_field):
            return state

    if match_cruise_ship(state_field):
        return ""

    return state_field


def read_data(state):
    data = {}
    for filename in sorted(DATAPATH.glob("*.csv")):
        with filename.open(mode="r", encoding="utf-8-sig") as csvfile:
            csvreader = csv.DictReader(csvfile)
            for row in csvreader:
                state_field = massage_state(row["Province/State"])
                if state_field and state == state_field.upper():
                    stats = Stats(row)
                    date = stats.date
                    if data.get(date):
                        data[date] += stats
                    else:
                        data[date] = stats
    for key in data:
        data[key] = data[key].infected
    return data


def list_states():
    states = list()
    for filename in DATAPATH.glob("*.csv"):
        with filename.open(mode="r", encoding="utf-8-sig") as csvfile:
            csvreader = csv.DictReader(csvfile)
            states = sorted(
                set(filter(None, (massage_state(row["Province/State"]) for row in csvreader)))
            )

    return states


def main():
    """ Main interface """
    parser = _create_parser()
    args = parser.parse_args()

    if len(sys.argv) == 1:
        parser.print_usage()
        parser.exit(status=1)
    elif args.list:
        print("\n".join(list_states()))
        sys.exit()

    state = args.state.upper()
    data = read_data(state)
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
        "state", nargs="?", choices=list_states(), help="State to graph",
    )

    return parser


if __name__ == "__main__":
    main()
