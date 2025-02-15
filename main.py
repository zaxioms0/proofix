import argparse
import multiprocessing
from args import validate_config
from lit_count import run


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
        help="how many clauses to learn in the DRAT",
        dest="cutoff",
        type=int,
        required=True,
    )
    parser.add_argument("--log", help="log file location", dest="log", required=True)
    parser.add_argument("--icnf", help="icnf file location", dest="icnf", default=None)
    parser.add_argument("--tmp-dir", dest="tmp_dir", default="tmp")
    parser.add_argument(
        "--cube-procs",
        dest="cube_procs",
        type=int,
        default=multiprocessing.cpu_count() - 2,
    )
    parser.add_argument(
        "--solve-procs",
        dest="solve_procs",
        type=int,
        default=multiprocessing.cpu_count() / 2,
    )
    parser.add_argument(
        "--cube-only",
        dest="cube_only",
        action=argparse.BooleanOptionalAction,
        default=False,
    )
    parser.add_argument(
        "--dynamic-depth", dest="dynamic_depth", type=int, required=True
    )
    parser.add_argument("--cutoff-time", dest="cutoff_time", type=float, default=1)
    parser.add_argument("--num-samples", dest="num_samples", type=int, default=32)
    parser.add_argument("--lit-set-size", dest="lit_set_size", type=int, default=32)
    parser.add_argument("--solver", dest="solver", type=str, default="cadical")
    parser.add_argument(
        "--cadical-config-file", dest="cadical_config_file", type=str, default=None
    )
    parser.add_argument(
        "--score-mode", dest="score_mode", type=str, default="unweighted sum"
    )
    args = parser.parse_args()
    cfg = validate_config(args)
    run(cfg)


if __name__ == "__main__":
    main()
