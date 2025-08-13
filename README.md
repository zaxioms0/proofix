# Proofix
A tool for partitioning CNF formulas for use via cube and conquer

## Usage
The basic usage is `python --cnf <cnf> --cube-size <n> --cutoff <c> --log <log>`

`python3.7` or greater is required. 

The following are the list of availible command line options:
### Required
- `--cnf`: The location of the CNF file
- `--cube-size`: How deep the partition tree should go (I would start with 10)
- `--cutoff`: How deep each proof prefix should search (100,000 seems to be a good choice)
- `--log`: Where  to write the logs
### Optional
- `--num-samples`: How many samples at each layer of the tree (default: 32)
- `--icnf`: Where to write the icnf file for the cubes (default: None)
- `--tmp-dir`: Where to write all the junk files (default: `tmp`)
- `--cube-procs`: How many processors to allocate for partitioning (default: n - 2)
- `--conquer`: Whether to solve the cubes (see `--solve-procs`) (default: False)
- `--solve-procs`: How many processors to allocate for solving (default n / 2)
- `--seed`: Whether to seed the randomness in the sampler

This is research quality software. If you have issues using it, please feel free to email me!
Also, if you have any feature requests or ideas, please reach out or, if you feel inclined, submit a PR!


## Paper
The Proofix tool is described in detail in the paper [Problem Partitioning via Proof Prefixes](https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.SAT.2025.3).
If you wish to cite it (thank you! it means a lot!) you may use:

Zachary Battleman, Joseph E. Reeves, and Marijn J. H. Heule. Problem Partitioning via Proof Prefixes. In 28th International Conference on Theory and Applications of Satisfiability Testing (SAT 2025). Leibniz International Proceedings in Informatics (LIPIcs), Volume 341, pp. 3:1-3:18, Schloss Dagstuhl – Leibniz-Zentrum für Informatik (2025) https://doi.org/10.4230/LIPIcs.SAT.2025.3
