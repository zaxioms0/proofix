from dataclasses import dataclass
import os

# import shutil


@dataclass
class Config:
    cnf: str
    cube_size: int
    cutoff: int
    num_samples: int
    icnf: str | None
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


def validate_config(args):
    cfg = Config(
        args.cnf,
        args.cube_size,
        args.cutoff,
        args.num_samples,
        None,
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
    )

    os.makedirs(cfg.tmp_dir, exist_ok=True)
    # if shutil.which(cfg.solver) is None:
    #     print(f"Solver '{cfg.solver}' cannot be found on your path")
    #     exit(1)
    #
    if args.icnf != None:
        cfg.icnf = args.icnf
    return cfg
