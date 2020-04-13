#!/usr/bin/python3
import csv
import re
from datetime import datetime
from pathlib import Path
from region import Region, RegionType

RPATH = Path("..", "COVID-19", "csse_covid_19_data", "csse_covid_19_daily_reports")
DATAPATH = Path(__file__).parent.absolute().joinpath(RPATH)

_IGNORE_COUNTRIES = ["Others"]

_COUNTRY_MATCHERS = {
    "Antigua": r"^Antigua and Barbuda$",
    "Bahamas": r"(^Bahamas, The$|^The Bahamas$)",
    "Bosnia": r"^Bosnia and Herzegovina$",
    "China": r"^Mainland China$",
    "Congo": r"(^Congo \(Brazzaville\)$|^Congo \(Kinshasa\)$|^Republic of the Congo$)",
    "Denmark": r"(^Faroe Islands$|^Greenland$)",
    "France": r"(^French Guiana$|^Guadeloupe$|^Martinique$|^Mayotte$|^Reunion$|^Saint Martin$|^St. Martin$)",
    "Gambia": r"(^Gambia, The$|^The Gambia$)",
    "Hong Kong": r"^Hong Kong SAR$",
    "Iran": r"^Iran \(Islamic Republic of\)",
    "Ireland": r"^Republic of Ireland$",
    "Macau": r"^Macao SAR$",
    "Moldova": r"^Republic of Moldova$",
    "Netherlands": r"(^Aruba$|^Curacao$)",
    "Palestine": r"(^occupied Palestinian territory$|^West Bank and Gaza$)",
    "Russia": r"^Russian Federation$",
    "South Korea": r"(^Korea, South$|^Republic of Korea$)",
    "St. Barthelemy": r"^Saint Barthelemy$",
    "St. Kitts": r"^Saint Kitts and Nevis$",
    "St. Lucia": r"^Saint Lucia$",
    "St. Vincent": r"^Saint Vincent and the Grenadines$",
    "Taipei": r"^Taipei and environs$",
    "Taiwan": r"^Taiwan\*$",
    "Trinidad": r"^Trinidad and Tobago$",
    "United Kingdom": r"(^UK$|^Cayman Islands$|^Channel Islands$|^Gibraltar$)",
    "US": r"(^Guam$|^Puerto Rico$)",
    "Vietnam": r"^Viet Nam$",
}

_IGNORE_STATES = [
    "Denmark",
    "External Territories",
    "France",
    "Hong Kong",
    "Macau",
    "Netherlands",
    "None",
    "Recovered",
    "Taiwan",
    "UK",
    "United Kingdom",
    "US",
    "Wuhan Evacuee",
]

_STATE_MATCHERS = {
    "Alberta": r".*, Alberta$",
    "Arizona": r".*, AZ$",
    "California": r"(.*, CA$|.*, CA \(From Diamond Princess\))",
    "Colorado": r".*, CO$",
    "Connecticut": r".*, CT$",
    "District of Columbia": r"Washington, D.C.$",
    "Florida": r".*, FL$",
    "French Guiana": "r^Fench Guiana$",
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
    "St. Martin": r"(^St Martin$|^Sint Maarten$)",
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


def read(region: str):
    data = _Data()
    _states = data._data[RegionType.STATE]
    regions = data._data[RegionType.COUNTRY]
    regions.update(_states)
    return _select_region(region, regions)


def countries():
    data = _Data()
    _countries = data._data[RegionType.COUNTRY]
    return sorted(_countries.values())


def states():
    data = _Data()
    _states = data._data[RegionType.STATE]
    return sorted(_states.values())


def _select_region(region:str, regions: dict):
    matches = list()
    region = Region.normalize_key(region)
    for key in regions:
        if re.search(region, key):
            matches.append(regions[key])

    if not matches:
        return None

    selection = 0
    if len(matches) > 1:
        print("Please select one of the following matching regions: ")
        for idx, match in enumerate(matches):
            print(f"  {idx + 1}. {matches[idx]}")
        selection = int(input(">>> ")) - 1

    return matches[selection]


def _toint(value):
    return int(value) if value else 0


class _Headers:
    def __init__(self, state: str, country: str, last_update: str):
        self._state = state
        self._country = country
        self._last_update = last_update

    @property
    def state(self):
        return self._state

    @property
    def country(self):
        return self._country

    @property
    def last_update(self):
        return self._last_update


class _Data:
    def __init__(self):
        self._data = dict()
        self._data[RegionType.STATE] = dict()
        self._data[RegionType.COUNTRY] = dict()

        for filename in sorted(DATAPATH.glob("*.csv")):
            with filename.open(mode="r", encoding="utf-8-sig") as csvfile:
                csvreader = csv.DictReader(csvfile)
                if "Province/State" in csvreader.fieldnames:
                    headers = _Headers(
                        "Province/State",
                        "Country/Region",
                        "Last Update"
                        )
                    self._parse(csvreader, headers)

                elif "Province_State" in csvreader.fieldnames:
                    headers = _Headers(
                        "Province_State",
                        "Country_Region",
                        "Last_Update"
                        )
                    self._parse(csvreader, headers)

                else:
                    print("Unknown Format")


    def _parse(self, csvreader: csv.DictReader, headers: _Headers):
        for row in csvreader:
            date = _Data._clean_date(row[headers.last_update])
            stats = _Data._parse_stats(row)

            country_name = self._clean_name(
                row[headers.country],
                _IGNORE_COUNTRIES,
                _COUNTRY_MATCHERS
                )
            if country_name:
                country = Region(RegionType.COUNTRY, country_name, country_name)
                self._update(RegionType.COUNTRY, country, date, stats)

            state_name = self._clean_name(
                row[headers.state],
                _IGNORE_STATES,
                _STATE_MATCHERS
                )
            if state_name:
                state = Region(RegionType.STATE, state_name, country_name)
                self._update(RegionType.STATE, state, date, stats)

    def _update(self, region_type: RegionType, region, date, stats):
        dict_ = self._data[region_type]
        key = region.key
        region = dict_.get(key, region)
        region.update_stats(date, stats)
        dict_[key] = region

    @staticmethod
    def _parse_stats(row):
        data = dict()
        data["confirmed"] = _toint(row.get("Confirmed"))
        data["deaths"] = _toint(row.get("Deaths"))
        data["recovered"] = _toint(row.get("Recovered"))
        return data

    @staticmethod
    def _clean_date(date_field):
        match = re.search("^\d+/\d+/\d+", date_field)
        if match:
            month, day, year = tuple(int(x) for x in match[0].split("/"))
            if year < 100:
                year += 2000
            date = datetime.strptime(f"{month:02d}/{day:02d}/{year:04d}", "%m/%d/%Y")
        else:
            match = re.search("^\d+-\d+-\d+", date_field)
            date = datetime.strptime(match[0], "%Y-%m-%d")
        return date

    def _clean_name(self, name, ignore, matchers):
        name = name.strip()

        if not name or self._is_cruise_ship(name) or ignore and name in ignore:
            return ""

        if name in matchers.items():
            return name

        for state, re_str in matchers.items():
            if re.search(re_str, name):
                return state

        return name

    @staticmethod
    def _is_cruise_ship(string) -> bool:
        return not re.search("(princess|cruise ship)", string, re.IGNORECASE) is None
