from args import validate_config, collect_args
import drat_lit_count

# import lrat_lit_count
import random


def main():
    args = collect_args()
    cfg = validate_config(args)
    if args.seed is not None:
        random.seed(args.seed)
    # if cfg.lrat:
    #     lrat_lit_count.run(cfg)
    drat_lit_count.run(cfg)


if __name__ == "__main__":
    main()
