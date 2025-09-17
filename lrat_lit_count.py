import subprocess
from collections import Counter
import time
from find_vars import find_cube_static
from concurrent.futures import ProcessPoolExecutor

from args import Config
from dataclasses import dataclass
import util


@dataclass
class OccEntry:
    pos_occs: int = 0
    neg_occs: int = 0
    pos_occs_weighted: float = 0
    neg_occs_weighted: float = 0


def add_occ(occurences, lit):
    key = abs(lit)
    if key not in occurences:
        occurences[key] = OccEntry()

    if lit > 0:
        occurences[key].pos_occs += 1
    else:
        occurences[key].neg_occs += 1


def add_weighted_occ(occurences, lit, clause_len):
    key = abs(lit)
    if key not in occurences:
        occurences[key] = OccEntry()

    if lit > 0:
        occurences[key].pos_occs_weighted += 1 / clause_len
    else:
        occurences[key].neg_occs_weighted += 1 / clause_len


def parse_lrat_line(line):
    if "d" in line or "c" in line or "SAT" in line:
        return None

    try:
        split = line.split(" ")
        id = int(split[0])
        lits = []
        clauses = []
        swap = False
        for i in split[1:]:
            i = int(i)
            if i == 0:
                swap = True
            elif not swap:
                lits.append(i)
            else:
                clauses.append(i)
        assert all(map(lambda x: x > 0, clauses))
        if not all(map(lambda x: x != 0, lits)):
            print(line)
    
        return (id, lits, clauses)
    except Exception as _:
        return None


def score(cfg: Config, x):
    return x


def collect_data_cone(cfg: Config, cnf_loc):
    clause_occs = Counter()
    clauses = {}
    occurences = {}
    f = open(cnf_loc, "r")
    for i, line in enumerate(f.readlines()):
        if "cnf" in line:
            continue
        lits = list(map(int, line.split(" ")[:-1]))
        clauses[i] = lits

    command = [
        "cadical",
        cnf_loc,
        "-q",
        "--lrat",
        "--binary=false",
        "-",
    ]
    process = subprocess.Popen(command, stdout=subprocess.PIPE)

    if process.stdout is None:
        print("Failed to spawn command properly")
        exit(1)

    line_ctr = 0
    while True:
        line = process.stdout.readline()
        line = line.decode("utf-8")
        if (parsed_lrat_line := parse_lrat_line(line)) is not None:
            id, lits, hint_clauses = parsed_lrat_line
        else:
            continue
        line_ctr += 1
        clauses[id] = lits
        for clause_id in hint_clauses:
            for lit in clauses[clause_id]:
                add_occ(occurences, lit)
                add_weighted_occ(occurences, lit, len(clauses[clause_id]))
        if line_ctr == cfg.cutoff:
            process.kill()
            break
    process.wait()
    return occurences, cnf_loc


def collect_data_resolution(cfg: Config, cnf_loc):
    clauses = {}
    f = open(cnf_loc, "r")
    for i, line in enumerate(f.readlines()):
        if "cnf" in line:
            continue
        lits = list(map(int, line.strip().split(" ")[:-1]))
        clauses[i] = lits

    command = [
        "cadical",
        cnf_loc,
        "-q",
        "--lrat",
        "--binary=false",
        "-",
    ]
    process = subprocess.Popen(command, stdout=subprocess.PIPE)

    if process.stdout is None:
        print("Failed to spawn command properly")
        exit(1)

    line_ctr = 0
    res_occs: Counter[int] = Counter()
    for line in process.stdout:
        line = line.decode("utf-8")
        if (parsed_lrat_line := parse_lrat_line(line)) is not None:
            id, lits, hint_clauses = parsed_lrat_line
        else:
            continue
        line_ctr += 1
        clauses[id] = lits

        s = set()
        for clause_id in hint_clauses[::-1]:
            for lit in clauses[clause_id]:
                if -lit in s:
                    res_occs.update([abs(lit)])
                    s.remove(-lit)
                else:
                    s.add(lit)
        if line_ctr == cfg.cutoff:
            process.kill()
            break
        if s != set(lits):
            print(line)
            print(parsed_lrat_line)
            print(s)
            print(set(lits))
    process.wait()
    return res_occs, cnf_loc


def run(cfg: Config):
    util.executor = ProcessPoolExecutor(max_workers=cfg.cube_procs)
    cube_start = time.time()
    cubes = find_cube_static(cfg, collect_data_resolution, score, [])
    if cfg.shuffle:
        util.random_seed.shuffle(cubes)
    with open(cfg.log_file, "a") as f:
        f.write("wall clock cube time: {}\n".format(int(time.time() - cube_start)))
    if cfg.icnf is not None:
        util.make_icnf(cubes, cfg.icnf, cfg.cnf if cfg.include_cnf else None)
    if cfg.conquer:
        util.executor = ProcessPoolExecutor(max_workers=cfg.solve_procs)
        # iterate_time_cutoff is either int or none, so if its not set this will
        # behave as normal
        timeout_cubes = util.run_hypercube(
            cfg.cnf, cubes, cfg.log_file, cfg.tmp_dir, cfg.iterate_time_cutoff
        )
        if cfg.iterate_time_cutoff:
            while len(timeout_cubes) != 0:
                cfg.cube_size += cfg.iterate_cube_depth
                new_cubes = find_cube_static(
                    cfg, collect_data_cone, score, timeout_cubes
                )
                if cfg.shuffle:
                    util.random_seed.shuffle(new_cubes)
                timeout_cubes = util.run_hypercube(
                    cfg.cnf,
                    new_cubes,
                    cfg.log_file,
                    cfg.tmp_dir,
                    cfg.iterate_time_cutoff,
                )
