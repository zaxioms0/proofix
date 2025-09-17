import subprocess
import time
import random
from concurrent.futures import ThreadPoolExecutor
from find_vars import find_cube_static
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
        occurences[key].pos_occs_weighted += 1 / (clause_len ** (3 / 2))
    else:
        occurences[key].neg_occs_weighted += 1 / (clause_len ** (3 / 2))


def parse_drat_line(line):
    if "d" in line or "c" in line or "SAT" in line:
        return None

    try:
        lits = list(map(lambda x: int(x), line.strip().split(" ")[:-1]))
    except Exception as _:
        print(line)
        exit(1)
    return lits


def score(cfg: Config, occs: OccEntry) -> float:
    match cfg.score_mode:
        case "sum":
            return occs.pos_occs + occs.neg_occs
        case "weighted-sum":
            return occs.pos_occs_weighted + occs.neg_occs_weighted
        case _:
            print("Unreachable")
            exit(1)


def collect_data(cfg: Config, cnf_loc: str) -> tuple[dict[int, OccEntry] | None, str]:
    occurences: dict[int, OccEntry] = {}
    command = [
        "cadical",
        cnf_loc,
        "-q",
        "--binary=false",
        "-",
    ]
    t = time.time()
    process = subprocess.Popen(command, stdout=subprocess.PIPE)

    if process.stdout is None:
        print("Failed to spawn command properly")
        exit(1)

    line_ctr = 0
    for line in process.stdout:
        line = line.decode("utf-8")
        line = parse_drat_line(line)
        if line is not None:
            line_ctr += 1
            for lit in line:
                add_occ(occurences, lit)
                add_weighted_occ(occurences, lit, len(line))
        if line_ctr == cfg.cutoff:
            process.kill()
    process.wait()
    if time.time() - t < 0.5:
        return None, cnf_loc

    return occurences, cnf_loc


def run(cfg: Config):
    util.executor = ThreadPoolExecutor(max_workers=cfg.cube_procs)
    cube_start = time.time()
    cubes = find_cube_static(cfg, collect_data, score, [])
    if cfg.shuffle:
        util.random_seed.shuffle(cubes)
    with open(cfg.log_file, "a") as f:
        f.write("wall clock cube time: {}\n".format(int(time.time() - cube_start)))
    if cfg.icnf is not None:
        util.make_icnf(cubes, cfg.icnf, cfg.cnf if cfg.include_cnf else None)
    if cfg.conquer:
        util.executor = ThreadPoolExecutor(max_workers=cfg.solve_procs)
        # iterate_time_cutoff is either int or none, so if its not set this will
        # behave as normal
        timeout_cubes = util.run_hypercube(
            cfg.cnf, cubes, cfg.log_file, cfg.tmp_dir, cfg.iterate_time_cutoff
        )
        if cfg.iterate_time_cutoff:
            while len(timeout_cubes) != 0:
                cfg.cube_size += cfg.iterate_cube_depth
                new_cubes = find_cube_static(cfg, collect_data, score, timeout_cubes)
                if cfg.shuffle:
                    util.random_seed.shuffle(new_cubes)
                timeout_cubes = util.run_hypercube(
                    cfg.cnf,
                    new_cubes,
                    cfg.log_file,
                    cfg.tmp_dir,
                    cfg.iterate_time_cutoff,
                )
