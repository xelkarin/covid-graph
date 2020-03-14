#!/usr/bin/python
from collections import OrderedDict
from datetime import datetime
from glob import glob
from subprocess import call
import csv, re, sys, tempfile

DATAPATH = "./COVID-19/csse_covid_19_data/csse_covid_19_daily_reports"

STATE_MATCHERS = {
    "Alberta":              re.compile(".*, Alberta$"),
    "Arizona":              re.compile(".*, AZ$"),
    "California":           re.compile("(.*, CA$|.*, CA \(From Diamond Princess\))"),
    "Colorado":             re.compile(".*, CO$"),
    "Connecticut":          re.compile(".*, CT$"),
    "District of Columbia": re.compile("Washington, D.C.$"),
    "Florida":              re.compile(".*, FL$"),
    "Georgia":              re.compile(".*, GA$"),
    "Hawaii":               re.compile(".*, HI$"),
    "Illinois":             re.compile(".*, IL$"),
    "Indiana":              re.compile(".*, IN$"),
    "Iowa":                 re.compile(".*, IA$"),
    "Kansas":               re.compile(".*, KS$"),
    "Kentucky":             re.compile(".*, KY$"),
    "Louisiana":            re.compile(".*, LA$"),
    "Maryland":             re.compile(".*, MD$"),
    "Massachusetts":        re.compile(".*, MA$"),
    "Minnesota":            re.compile(".*, MN$"),
    "Missouri":             re.compile(".*, MO$"),
    "Nebraska":             re.compile("(.*, NE$|.*, NE \(From Diamond Princess\))"),
    "Nevada":               re.compile(".*, NV$"),
    "New Hampshire":        re.compile(".*, NH$"),
    "New Jersey":           re.compile(".*, NJ$"),
    "New York":             re.compile(".*, NY$"),
    "North Carolina":       re.compile(".*, NC$"),
    "Oklahoma":             re.compile(".*, OK$"),
    "Ontario":              re.compile(".*, ON$"),
    "Oregon":               re.compile(".*, OR$"),
    "Pennsylvania":         re.compile(".*, PA$"),
    "Quebec":               re.compile(".*, QC$"),
    "Rhode Island":         re.compile(".*, RI$"),
    "South Carolina":       re.compile(".*, SC$"),
    "Tennessee":            re.compile(".*, TN$"),
    "Texas":                re.compile("(.*, TX$|.*, TX \(From Diamond Princess\))"),
    "Utah":                 re.compile(".*, UT$"),
    "Vermont":              re.compile(".*, VT$"),
    "Virginia":             re.compile(".*, VA$"),
    "Washington":           re.compile(".*, WA$"),
    "Wisconsin":            re.compile(".*, WI$"),
}

class Stats:
    def __init__(self, data=None):
        if data == None:
            self._date = None
            self._confirmed = 0
            self._deaths = 0
            self._recovered = 0
        elif type(data) == OrderedDict:
            data = self._parse_data(data)
            self._date = data[0]
            self._confirmed = data[1]
            self._deaths = data[2]
            self._recovered = data[3]
        elif type(data) == Stats:
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
            day, time = date_field.split(" ")
            m, d, y = day.split("/")
            y = int(y)
            if y < 100: y += 2000
            date_str = "%02d/%02d/%04d" % (int(m), int(d), int(y))
            date = datetime.strptime(date_str, "%m/%d/%Y")
        else:
            date = datetime.strptime(date_field, "%Y-%m-%dT%H:%M:%S")
        return date.strftime("%m/%d/%Y")

    def _parse_data(self, data):
        date = self._massage_date(data["Last Update"])
        c = 0 if data["Confirmed"] == "" else int(data["Confirmed"])
        d = 0 if data["Deaths"] == "" else int(data["Deaths"])
        r = 0 if data["Recovered"] == "" else int(data["Recovered"])
        return (date, c, d, r)

    def __iadd__(self, other):
        other = Stats(other)
        if self._date == None:
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
    exit(1)

if sys.argv[1] == "-l":
    list_states()
    exit(0)

state = sys.argv[1].upper()
data = read_data(state)
with tempfile.NamedTemporaryFile(mode="w") as datfile:
    for key in sorted(data):
        datfile.write(f"{key}\t{data[key]}\n")
    datfile.flush()
    call(["gnuplot", "-p", "-e", f"datfile='{datfile.name}'", "./covid.gp"])
