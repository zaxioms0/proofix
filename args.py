from dataclasses import dataclass
import multiprocessing
import argparse
import os


@dataclass
class Config:
    cnf: str
    cube_size: int
    cutoff: int
    num_samples: int
    icnf: str | None
    include_cnf: bool
    shuffle: bool
    cube_procs: int
    solve_procs: int
    tmp_dir: str
    conquer: bool
    # score_mode: str
    # solver: str
    # solver_args: list[str]
    log_file: str
    # lrat_top: int
    # lrat: bool
    iterate_time_cutoff: int | None
    iterate_cube_depth: int


def collect_args():
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
    parser.add_argument("--num-samples", dest="num_samples", type=int, default=32)
    parser.add_argument("--log", help="log file location", dest="log", required=True)
    parser.add_argument("--icnf", help="icnf file location", dest="icnf", default=None)
    parser.add_argument(
        "--include-cnf",
        help="whether to write cnf with the cubes. This makes the file immediately suitable for incremental SAT",
        dest="include_cnf",
        action=argparse.BooleanOptionalAction,
        default=False,
    )
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

    parser.add_argument("--iterate-time-cutoff", dest="iterate_time_cutoff", required = False, default=None, type=int)
    parser.add_argument("--iterate-cube-depth", dest="iterate_cube_depth", required = False, default=4, type=int)

    args, _ = parser.parse_known_args()
    return args


def validate_config(args):
    cfg = Config(
        args.cnf,
        args.cube_size,
        args.cutoff,
        args.num_samples,
        args.icnf,
        args.include_cnf,
        args.shuffle,
        args.cube_procs,
        args.solve_procs,
        args.tmp_dir.strip(),
        args.conquer,
        # args.score_mode,
        # args.solver.strip(),
        # solver_args,
        args.log,
        # args.lrat_top,
        # args.lrat
        args.iterate_time_cutoff,
        args.iterate_cube_depth
    )

    os.makedirs(cfg.tmp_dir, exist_ok=True)
    # if shutil.which(cfg.solver) is None:
    #     print(f"Solver '{cfg.solver}' cannot be found on your path")
    #     exit(1)
    #

    if not (args.icnf or args.conquer):
        print(
            "Currently, the tool is configured to neither write the icnf file, cube file, nor solve the cubes."
        )
        print(
            "This will do a bunch of computation for nothing, and you will be a bit sad I think."
        )
        print(
            "Please provide either `--conquer`, `--icnf <icnf>`"
        )
        exit(1)
    return cfg
