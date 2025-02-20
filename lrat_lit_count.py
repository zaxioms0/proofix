import subprocess
import sys
from collections import Counter
import random
import os
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
        return (None, None, None)

    try:
        split = line.split(" ")
        id = int(split[0])
        lits = []
        clauses = []
        swap = False
        for i in split:
            i = int(i)
            if i == 0:
                swap = True
            elif swap == False:
                lits.append(i)
            else:
                clauses.append(i)
        return (id, lits, clauses)
    except:
        return (None, None, None)


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
    if cfg.solver == "cadical":
        command = [
            cfg.solver,
            cnf_loc,
            "-q",
            "--lrat",
            "--binary=false",
            "-",
        ] + cfg.solver_args
        process = subprocess.Popen(command, stdout=subprocess.PIPE)

        if process.stdout is None:
            print("Failed to spawn command properly")
            exit(1)

        line_ctr = 0
        while True:
            line = process.stdout.readline()
            line = line.decode("utf-8")
            id, lits, hint_clauses = parse_lrat_line(line)  # type: ignore
            if id is not None:
                line_ctr += 1
                clauses[id] = lits
                for clause in hint_clauses:  # type: ignore
                    if clause in clauses:
                        clause_occs[clause] += 1
                    else:
                        clause_occs[clause] = 1
            if line_ctr == cfg.cutoff:
                process.kill()
                break
            if process.poll() is not None:
                break
        process.wait()
        for clause_id, _ in clause_occs.most_common(cfg.lrat_top):
            for lit in clauses[clause_id]:
                add_occ(occurences, lit)
                add_weighted_occ(occurences, lit, len(clauses[clause_id]))
        return occurences
    else:
        print(f"Unknown solver: {cfg.solver}")
        exit(1)


def run(cfg: Config):
    util.executor = ProcessPoolExecutor(max_workers=cfg.cube_procs)
    cubes = find_cube_static(cfg, [])
    print(cubes)
    if not cfg.cube_only:
        util.executor = ProcessPoolExecutor(max_workers=cfg.solve_procs)
        util.run_hypercube(cfg.cnf, cubes, cfg.log_file, cfg.tmp_dir)
