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
from typing import Dict, Sequence

from pkg_resources import DistributionNotFound, RequirementParseError, get_distribution

_LIB_PATH = Path("lib")
if _LIB_PATH.joinpath(Path("data.py")):
    sys.path.append(str(_LIB_PATH))

import data
from gnuplot import Gnuplot


_LOGGER = logging.getLogger(__name__)
__version__ = "0.0.0"

with suppress(DistributionNotFound, RequirementParseError):
    __version__ = get_distribution(__name__).version


def main():
    """ Main interface """
    parser = _create_parser()
    args = parser.parse_args()

    if len(sys.argv) == 1:
        parser.print_usage()
        parser.exit(status=1)
    elif args.countries:
        print("\n".join(map(str, data.countries())))
        sys.exit()
    elif args.states:
        print("\n".join(map(str, data.states())))
        sys.exit()

    region = data.read(args.region)
    title = f"COVID-19 Infections ({region})"
    with tempfile.NamedTemporaryFile(mode="w") as datfile:
        for date, infections in region:
            datfile.write(f"{date}\t{infections}\n")
        datfile.flush()
        gnuplot = Gnuplot("./covid.gp", args.terminal, args.output)
        gnuplot.set_var("datfile", datfile.name)
        gnuplot.set_var("title", title)
        gnuplot.run()


def _create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=f"%(prog)s CLI Help", allow_abbrev=False,)

    parser.add_argument(
            "-c", action="store_true", dest="countries", help="List countries"
        )

    parser.add_argument(
            "-o", dest="output", help="Set the output file name"
        )

    parser.add_argument(
            "-s", action="store_true", dest="states", help="List states"
        )

    parser.add_argument(
            "-t", dest="terminal",
            choices=["canvas", "dumb", "pdfcairo", "pngcairo", "svg"],
            help="Set the gnuplot terminal"
        )

    parser.add_argument(
            "-v", action="version", version=f"%(prog)s {__version__}"
        )

    parser.add_argument("region", nargs="?", metavar="REGION", help="Region to graph")

    return parser


if __name__ == "__main__":
    main()
