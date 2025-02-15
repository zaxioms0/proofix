from dataclasses import dataclass
import shutil
@dataclass
class Config:
    cnf: str
    cube_size: int
    cutoff: int
    num_samples: int
    icnf: str | None
    dynamic_depth: int
    cube_procs: int
    solve_procs: int
    tmp_dir: str
    cube_only: bool
    score_mode: str
    solver: str
    cadical_args: list[str]


def validate_config(args):
    cfg = Config(
        args.cnf,
        args.cube_size,
        args.cutoff,
        args.num_samples,
        None,
        args.dynamic_depth,
        args.cube_procs,
        args.solve_procs,
        args.tmp_dir.strip(),
        args.cube_only,
        args.score_mode,
        args.solver.strip(),
        [],
    )

    if shutil.which(cfg.solver) is None:
        print(f"Solver '{cfg.solver}' cannot be found on your path")
        exit(1)

    if args.icnf != None:
        cfg.icnf = args.icnf
    return cfg


