import subprocess
import signal
import sys
import os

from args import Config
from dataclasses import dataclass


@dataclass
class OccEntry:
    pos_occs: int = 0
    neg_occs: int = 0
    pos_occs_weighted: float = 0
    neg_occs_weighted: float = 0


occurences = {}


def add_occ(lit):
    key = abs(lit)
    if key not in occurences:
        occurences[key] = OccEntry()

    if lit > 0:
        occurences[key].pos_occs += 1
    else:
        occurences[key].neg_occs += 1


def add_weighted_occ(lit, clause_len):
    key = abs(lit)
    if key not in occurences:
        occurences[key] = OccEntry()

    if lit > 0:
        occurences[key].pos_occs_weighted += 1 / clause_len
    else:
        occurences[key].neg_occs_weighted += 1 / clause_len


def parse_drat_line(line):
    if "d" in line or "c" in line:
        return None

    lits = list(map(lambda x: int(x), line.strip().split(" ")[:-1]))
    return lits


def collect_data(cfg: Config):
    if cfg.solver == "cadical":
        command = [
            cfg.solver,
            cfg.cnf,
            "-q",
            "--binary=false",
            "/dev/stdout",
        ] + cfg.cadical_args
        process = subprocess.Popen(command, stdout=subprocess.PIPE)

        if process.stdout is None:
            print("Failed to spawn command properly")
            exit(1)

        line_ctr = 0
        for line in process.stdout:
            print(line_ctr)
            line = parse_drat_line(line)
            if line is not None:
                line_ctr += 1
                for lit in line:
                    add_occ(lit)
                    add_weighted_occ(lit, len(line))
            if line_ctr == cfg.cutoff:
                process.kill()
        process.wait()
    else:
        print(f"Unknown solver: {cfg.solver}")
        exit(1)
