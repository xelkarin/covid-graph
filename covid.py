#!/usr/bin/python3
import csv
import re
import sys
import tempfile
from datetime import datetime
from glob import glob
from subprocess import call


DATAPATH = "./COVID-19/csse_covid_19_data/csse_covid_19_daily_reports"

STATE_MATCHERS = {
    "Alberta":              re.compile(r".*, Alberta$"),
    "Arizona":              re.compile(r".*, AZ$"),
    "California":           re.compile(r"(.*, CA$|.*, CA \(From Diamond Princess\))"),
    "Colorado":             re.compile(r".*, CO$"),
    "Connecticut":          re.compile(r".*, CT$"),
    "District of Columbia": re.compile(r"Washington, D.C.$"),
    "Florida":              re.compile(r".*, FL$"),
    "Georgia":              re.compile(r".*, GA$"),
    "Hawaii":               re.compile(r".*, HI$"),
    "Illinois":             re.compile(r".*, IL$"),
    "Indiana":              re.compile(r".*, IN$"),
    "Iowa":                 re.compile(r".*, IA$"),
    "Kansas":               re.compile(r".*, KS$"),
    "Kentucky":             re.compile(r".*, KY$"),
    "Louisiana":            re.compile(r".*, LA$"),
    "Maryland":             re.compile(r".*, MD$"),
    "Massachusetts":        re.compile(r".*, MA$"),
    "Minnesota":            re.compile(r".*, MN$"),
    "Missouri":             re.compile(r".*, MO$"),
    "Nebraska":             re.compile(r"(.*, NE$|.*, NE \(From Diamond Princess\))"),
    "Nevada":               re.compile(r".*, NV$"),
    "New Hampshire":        re.compile(r".*, NH$"),
    "New Jersey":           re.compile(r".*, NJ$"),
    "New York":             re.compile(r".*, NY$"),
    "North Carolina":       re.compile(r".*, NC$"),
    "Oklahoma":             re.compile(r".*, OK$"),
    "Ontario":              re.compile(r".*, ON$"),
    "Oregon":               re.compile(r".*, OR$"),
    "Pennsylvania":         re.compile(r".*, PA$"),
    "Quebec":               re.compile(r".*, QC$"),
    "Rhode Island":         re.compile(r".*, RI$"),
    "South Carolina":       re.compile(r".*, SC$"),
    "Tennessee":            re.compile(r".*, TN$"),
    "Texas":                re.compile(r"(.*, TX$|.*, TX \(From Diamond Princess\))"),
    "Utah":                 re.compile(r".*, UT$"),
    "Vermont":              re.compile(r".*, VT$"),
    "Virginia":             re.compile(r".*, VA$"),
    "Washington":           re.compile(r".*, WA$"),
    "Wisconsin":            re.compile(r".*, WI$"),
}

class Stats:
    def __init__(self, data=None):
        if not data:
            self._date = None
            self._confirmed = 0
            self._deaths = 0
            self._recovered = 0
        elif isinstance(data, dict):
            data = self._parse_data(data)
            self._date = data[0]
            self._confirmed = data[1]
            self._deaths = data[2]
            self._recovered = data[3]
        elif isinstance(data, Stats):
            self._date = data._date
            self._confirmed = data._confirmed
            self._deaths = data._deaths
            self._recovered = data._recovered
        else:
            raise TypeError(f"Can't convert {data.__class__} to Stats")

    def date(self):
        return self._date

    def infected(self):
        return self._confirmed - self._deaths - self._recovered

    def _massage_date(self, date_field):
        if "/" in date_field:
            date, _ = date_field.split(" ")
            month, day, year = date.split("/")
            year = int(year)
            if year < 100: year += 2000
            date_str = "%02d/%02d/%04d" % (int(month), int(day), int(year))
            date = datetime.strptime(date_str, "%m/%d/%Y")
        else:
            date = datetime.strptime(date_field, "%Y-%m-%dT%H:%M:%S")
        return date.strftime("%m/%d/%Y")

    def _parse_data(self, data):
        date = self._massage_date(data["Last Update"])
        confirmed = 0 if data["Confirmed"] == "" else int(data["Confirmed"])
        deaths = 0 if data["Deaths"] == "" else int(data["Deaths"])
        recovered = 0 if data["Recovered"] == "" else int(data["Recovered"])
        return (date, confirmed, deaths, recovered)

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
    state_field = state_field.lstrip().rstrip()
    for state in STATE_MATCHERS:
        if STATE_MATCHERS[state].match(state_field):
            return state

    if match_cruise_ship(state_field):
        return None

    if state_field != "":
        return state_field

def read_data(state):
    data = {}
    for filename in sorted(glob(f"{DATAPATH}/*.csv")):
        with open(filename, "r", encoding="utf-8-sig") as csvfile:
            csvreader = csv.DictReader(csvfile)
            for row in csvreader:
                state_field = massage_state(row["Province/State"])
                if state_field and state == state_field.upper():
                    stats = Stats(row)
                    date = stats.date()
                    if data.get(date):
                        data[date] += stats
                    else:
                        data[date] = stats
    for key in data:
        data[key] = data[key].infected()
    return data

def list_states():
    states = set()
    for filename in sorted(glob(f"{DATAPATH}/*.csv")):
        with open(filename, "r", encoding="utf-8-sig") as csvfile:
            csvreader = csv.DictReader(csvfile)
            for row in csvreader:
                state = massage_state(row["Province/State"])
                if state: states.add(state)

    for state in sorted(states):
        print(state)

if len(sys.argv) != 2:
    print("USAGE: covid.py [-l] <STATE>")
    print("  -l\t\tList states")
    sys.exit(1)

if sys.argv[1] == "-l":
    list_states()
    sys.exit(0)

def main():
    state = sys.argv[1].upper()
    data = read_data(state)
    with tempfile.NamedTemporaryFile(mode="w") as datfile:
        for key in sorted(data):
            datfile.write(f"{key}\t{data[key]}\n")
        datfile.flush()
        call(["gnuplot", "-p", "-e", f"datfile='{datfile.name}'", "./covid.gp"])

if __name__ == "__main__":
    main()