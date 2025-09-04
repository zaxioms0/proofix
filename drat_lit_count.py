import subprocess
import time
import random
import os
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


def parse_drat_line(line):
    if "d" in line or "c" in line or "SAT" in line:
        return None

    try:
        lits = list(map(lambda x: int(x), line.strip().split(" ")[:-1]))
    except:
        print(line)
        exit(1)
    return lits


def score(cfg: Config, occs: OccEntry):
    return occs.pos_occs + occs.neg_occs


def find_cube_static(cfg: Config, start):
    if all(isinstance(x, list) for x in start) and start != []:
        to_split = start
    else:
        to_split = [start]
    split_lits = set()
    result = []
    while to_split != []:
        # sample num_samples from the current layer
        if len(to_split) <= cfg.num_samples:
            samples = to_split
        else:
            samples = random.sample(to_split, cfg.num_samples)
        procs = []
        for sample in samples:
            base = os.path.basename(cfg.cnf)
            sample_cnf_loc = util.add_cube_to_cnf(cfg.cnf, sample, cfg.tmp_dir)
            proc = util.executor.submit(collect_data, cfg, sample_cnf_loc)
            procs.append((proc, sample_cnf_loc))

        var_score_dict = {}
        for proc, sample_cnf_loc in procs:
            var_occ_dict = proc.result()
            os.remove(sample_cnf_loc)
            for var, occs in var_occ_dict.items():
                var_score_dict[var] = score(cfg, occs)
        for lit in split_lits:
            var_score_dict.pop(lit, None)
        split_lit = max(var_score_dict, key=var_score_dict.get)  # type: ignore
        split_lits.add(split_lit)
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
    occurences = {}
    command = [
        "cadical",
        cnf_loc,
        "-q",
        "--binary=false",
        "-",
    ]
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
        util.make_icnf(cubes, cfg.icnf, cfg.cnf if cfg.write_cnf else None)
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
                print(timeout_cubes)
                new_cubes = find_cube_static(cfg, timeout_cubes)
                if cfg.shuffle:
                    random.shuffle(new_cubes)
                print(new_cubes)
                timeout_cubes = util.run_hypercube(
                    cfg.cnf, new_cubes, cfg.log_file, cfg.tmp_dir, cfg.iterate_time_cutoff
                )
