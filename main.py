import argparse
import multiprocessing
from args import validate_config
import drat_lit_count
import lrat_lit_count


def main():
    parser = argparse.ArgumentParser()
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
        help="how many clauses to learn in the D/LRAT",
        dest="cutoff",
        type=int,
        required=True,
    )
    parser.add_argument(
        "--num-samples",
        dest="num_samples",
        type=int,
        default=32
    )
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
        "--cube-only",
        dest="cube_only",
        help="Whether to only generate cubes without running them",
        action=argparse.BooleanOptionalAction,
        default=False,
    )
    parser.add_argument(
        "--dynamic-depth",
        help="Depth of dynamic split before switching to static on each branch",
        dest="dynamic_depth",
        type=int,
        required=True,
    )
    parser.add_argument(
        "--cutoff-time",
        help="TODO: unimplemented",
        dest="cutoff_time",
        type=float,
        default=1,
    )
    parser.add_argument(
        "--solver",
        help="TODO: unimplemented",
        dest="solver",
        type=str,
        default="cadical",
    )
    parser.add_argument(
        "--solver-args",
        help='args to pass to the solver as a "string"',
        dest="solver_args",
        type=str,
        default=None,
    )
    parser.add_argument(
        "--score-mode",
        help="TODO: unimplemented",
        dest="score_mode",
        type=str,
        default="unweighted sum",
    )
    parser.add_argument("--lrat-top", dest="lrat_top", type=int, default=1000)
    parser.add_argument("--lrat", action=argparse.BooleanOptionalAction,
        default=False)

    args = parser.parse_args()
    cfg = validate_config(args)
    if cfg.lrat:
        lrat_lit_count.run(cfg)
    else:
        drat_lit_count.run(cfg)


if __name__ == "__main__":
    main()
