import os
from concurrent.futures import wait, FIRST_COMPLETED
from collections.abc import Callable
from args import Config
import util


def find_cube_static[T](
    cfg: Config,
    collect_data: Callable[[Config, str], tuple[dict[int, T] | None, str]],
    score: Callable[[Config, T], float],
    start: list,
) -> list[list[int]]:
    # list of cubes vs single cube
    if all(isinstance(x, list) for x in start) and start != []:
        to_split = start
    else:
        to_split = [start]
    split_lits = set()
    result: list[list[int]] = []
    while to_split != []:
        # sample num_samples from the current layer
        if len(to_split) <= cfg.num_samples:
            samples = to_split
        else:
            samples = util.random_seed.sample(to_split, cfg.num_samples)

        # initialize a bunch of futures
        max_samples = 2 * cfg.num_samples
        cur_samples = 0
        sample_futs = []
        for sample in samples:
            sample_cnf_loc = util.add_cube_to_cnf(cfg.cnf, sample, cfg.tmp_dir)
            sample_fut = util.executor.submit(collect_data, cfg, sample_cnf_loc)
            sample_futs.append(sample_fut)
            cur_samples += 1

        # compute futures and score them
        # if a sample is bad, redo it
        var_score_dict = {}
        while sample_futs:
            print(sample_futs)
            done, _ = wait(sample_futs, return_when=FIRST_COMPLETED)
            for sample in done:
                var_occ_dict, cnf_loc = sample.result()
                sample_futs.remove(sample)
                os.remove(cnf_loc)
                # if sample is bad and we still have sampling budget
                if var_occ_dict is None and cur_samples < max_samples:
                    print("resampling")
                    new_sample = util.random_seed.choice(to_split)
                    new_sample_cnf_loc = util.add_cube_to_cnf(
                        cfg.cnf, new_sample, cfg.tmp_dir
                    )
                    sample_futs.append(
                        util.executor.submit(collect_data, cfg, new_sample_cnf_loc)
                    )
                    cur_samples += 1
                # good sample
                elif var_occ_dict is None and cur_samples >= max_samples:
                    print("hit sampling budget, not resampling")
                else:
                    print("good")
                    for var, occs in var_occ_dict.items():
                        if var in var_score_dict.keys():
                            var_score_dict[var] += score(cfg, occs)
                        else:
                            var_score_dict[var] = score(cfg, occs)

        for lit in split_lits:
            var_score_dict.pop(lit, None)
        print(
            sorted(var_score_dict.items(), key=lambda item: item[1], reverse=True)[:10]
        )
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
