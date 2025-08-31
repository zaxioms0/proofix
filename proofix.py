import argparse
import multiprocessing
from args import validate_config
import drat_lit_count

# import lrat_lit_count
import random


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--cnf", help="cnf file location", dest="cnf", required=True)
    parser.add_argument(
        "--cube-size",
        help="size of cubes to split into",
        dest="cube_size",
        type=int,
        required=True,
    )
    parser.add_argument(
        "--cutoff",
        help="how many clauses to learn in the DRAT",
        dest="cutoff",
        type=int,
        required=True,
    )
    parser.add_argument("--num-samples", dest="num_samples", type=int, default=32)
    parser.add_argument("--log", help="log file location", dest="log", required=True)
    parser.add_argument("--icnf", help="icnf file location", dest="icnf", default=None)
    parser.add_argument("--tmp-dir", dest="tmp_dir", default="tmp")
    parser.add_argument(
        "--cube-procs",
        dest="cube_procs",
        help="How many processors to use while generating cubes",
        type=int,
        default=multiprocessing.cpu_count() - 2,
    )
    parser.add_argument(
        "--solve-procs",
        dest="solve_procs",
        help="How many processors to use while solving cubes in final split",
        type=int,
        default=int(multiprocessing.cpu_count() / 2),
    )
    parser.add_argument(
        "--conquer",
        dest="conquer",
        help="Whether to solve the cubes generated",
        action=argparse.BooleanOptionalAction,
        default=False,
    )
    # parser.add_argument(
    #     "--score-mode",
    #     help="TODO: unimplemented",
    #     dest="score_mode",
    #     type=str,
    #     default="unweighted sum",
    # )
    parser.add_argument("--seed", dest="seed", default=None, type=int)
    # parser.add_argument("--lrat-top", dest="lrat_top", type=int, default=1000)
    # parser.add_argument("--lrat", action=argparse.BooleanOptionalAction,
    #    default=False)
    parser.add_argument(
        "--shuffle",
        dest="shuffle",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Whether to shuffle the order of the generate cubes",
    )
    parser.add_argument(
        "--dump-vars",
        dest="dump_vars",
        action=argparse.BooleanOptionalAction,
        default=False
    )

    args, _ = parser.parse_known_args()
    cfg = validate_config(args)
    if args.seed is not None:
        random.seed(args.seed)
    # if cfg.lrat:
    #     lrat_lit_count.run(cfg)
    drat_lit_count.run(cfg)


if __name__ == "__main__":
    main()
