import subprocess
from collections import Counter
import random
import os
import time
from concurrent.futures import ThreadPoolExecutor

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
            elif swap == False:
                lits.append(i)
            else:
                clauses.append(i)
        return (id, lits, clauses)
    except:
        return None


def score(cfg: Config, occs: OccEntry):
    return occs.pos_occs + occs.neg_occs


def find_cube_static(cfg: Config, starting_cube):
    to_split = [starting_cube]
    result = []
    while to_split != []:
        # sample num_samples from the current layer
        if len(to_split) <= cfg.num_samples:
            samples = to_split
        else:
            samples = random.sample(to_split, cfg.num_samples)
        procs = []
        for sample in samples:
            sample_cnf_loc = util.add_cube_to_cnf(cfg.cnf, sample, cfg.tmp_dir)
            proc = util.executor.submit(collect_data, cfg, sample_cnf_loc)
            procs.append((proc, sample_cnf_loc))

        combined_dict = {}
        for proc, sample_cnf_loc in procs:
            proc_dict = proc.result()
            os.remove(sample_cnf_loc)
            for var, occs in proc_dict.items():
                if var not in combined_dict:
                    combined_dict[var] = score(cfg, occs)
                else:
                    combined_dict[var] += score(cfg, occs)

        print(sorted(combined_dict.items(), key=lambda item: item[1], reverse=True)[:10])
        split_lit = max(combined_dict, key=combined_dict.get)  # type: ignore
        new_to_split = []
        for cube in to_split:
            if len(cube) + 1 < cfg.cube_size:
                new_to_split.append(cube + [split_lit])
                new_to_split.append(cube + [-split_lit])
            else:
                result.append(cube + [split_lit])
                result.append(cube + [-split_lit])
        to_split = new_to_split
    return result


def collect_data(cfg: Config, cnf_loc):
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
    return occurences


def run(cfg: Config):
    util.executor = ThreadPoolExecutor(max_workers=cfg.cube_procs)
    cube_start = time.time()
    cubes = find_cube_static(cfg, [])
    if cfg.shuffle:
        random.shuffle(cubes)
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
                new_cubes = find_cube_static(cfg, timeout_cubes)
                if cfg.shuffle:
                    random.shuffle(new_cubes)
                timeout_cubes = util.run_hypercube(
                    cfg.cnf,
                    new_cubes,
                    cfg.log_file,
                    cfg.tmp_dir,
                    cfg.iterate_time_cutoff,
                )
