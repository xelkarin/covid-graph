import os
from subprocess import run

class Gnuplot:
    def __init__(self, file: str, terminal: str, output: str):
        self._file = file
        self._output = output
        self._terminal = terminal
        self._vars = dict()

    def set_var(self, var: str, value: str):
        self._vars[var] = value

    def run(self):
        cmd = ["gnuplot", "-p"]
        for var, value in self._vars.items():
            cmd += ["-e", f"{var}='{value}'"]

        if self._output:
            cmd += ["-e", f"set output '{self._output}'"]

        if self._terminal:
            os.environ["GNUTERM"] = self._terminal

        cmd.append(self._file)
        run(cmd, check=True)
