from dataclasses import dataclass
import time
import os
import subprocess
import random
import string
from itertools import product
from concurrent.futures import ProcessPoolExecutor

executor: ProcessPoolExecutor


@dataclass
class CadicalResult:
    time: float
    learned: int
    props: int
    sat: bool


@dataclass
class CnfHeader:
    var_num: int
    clause_num: int


# no timeout by default
def run_cadical(cnf_loc: str, timeout=None):
    try:
        if timeout:
            p = subprocess.run(
                ["cadical", cnf_loc], stdout=subprocess.PIPE, timeout=timeout
            )
        else:
            p = subprocess.run(["cadical", cnf_loc], stdout=subprocess.PIPE)
    except subprocess.TimeoutExpired:
        return None

    return p.stdout.decode("utf-8")


def run_cadical_cube(base_cnf_loc, cube, tmp="tmp", timeout=None):
    new_cnf_loc = add_cube_to_cnf(base_cnf_loc, cube, tmp)
    p = run_cadical(new_cnf_loc, timeout)
    os.remove(new_cnf_loc)
    return p


def cadical_parse_results(cadical_output: str):
    stats_str = cadical_output.split("[ statistics ]")[-1].split("[ resources ]")[0]

    learned = int(
        stats_str[stats_str.find("learned") :]
        .split(":")[1]
        .split("per")[0]
        .strip()
        .split(" ")[0]
    )
    props = int(
        stats_str[stats_str.find("propagations") :]
        .split(":")[1]
        .split("per")[0]
        .strip()
        .split(" ")[0]
    )
    time_str = cadical_output.split("[ resources ]")[-1]
    time_loc = time_str.find("total process time since initialization")
    time_str = time_str[time_loc:]
    time = float(time_str.split(":")[1].split("seconds")[0].strip())
    sat = True
    if "UNSATISFIABLE" in cadical_output:
        sat = False

    return CadicalResult(time, learned, props, sat)


def cnf_parse_header(cnf_string: str):
    header = cnf_string.split("\n")[0].split(" ")
    return CnfHeader(int(header[2]), int(header[3]))


def add_cube_to_cnf(cnf_loc: str, cube: list[int], tmp_dir):
    cnf_string = open(cnf_loc, "r").read()
    tag = str(time.time())

    header = cnf_parse_header(cnf_string)
    new_num_clauses = header.clause_num + len(cube)

    out = f"p cnf {header.var_num} {new_num_clauses}\n"
    out += "\n".join(cnf_string.split("\n")[1:])

    for lit in cube:
        out += f"{lit} 0\n"

    f = open(os.path.join(tmp_dir, f"{tag}.cnf"), "w+")
    f.write(out)
    f.close()
    return os.path.join(tmp_dir, f"{tag}.cnf")


def generate_hypercube(cube):
    pos_neg_pairs = [(num, -num) for num in cube]
    combinations = list(product(*pos_neg_pairs))
    return list(map(list, combinations))


def run_hypercube_from_cube(cnf_loc, cube, log_file_loc):
    hc = generate_hypercube(cube)
    run_hypercube(cnf_loc, hc, log_file_loc)


def partition_n_ways(numbers, n):
    # Sort numbers in descending order for better distribution
    numbers = sorted(numbers, reverse=True)

    # Initialize n empty partitions
    partitions = [[] for _ in range(n)]
    partition_sums = [0] * n

    for num in numbers:
        min_sum_index = partition_sums.index(min(partition_sums))

        partitions[min_sum_index].append(num)
        partition_sums[min_sum_index] += num

    avg_sum = sum(partition_sums) / n
    max_deviation = max(abs(p_sum - avg_sum) for p_sum in partition_sums)

    return {
        "partitions": partitions,
        "partition_sums": partition_sums,
        "average_sum": avg_sum,
        "max_deviation": max_deviation,
        "max_time": max(partition_sums),
    }


def run_hypercube(cnf_loc, hc, log_file_loc, tmp="tmp", timeout: int | None =None):
    log_file = open(log_file_loc, "a")
    timeout_cubes = []
    futures = []
    for _, cube in enumerate(hc):
        future = executor.submit(run_cadical_cube, cnf_loc, cube, tmp, timeout)
        futures.append((future, cube))
    times = []
    for future, cube in futures:
        output = future.result()
        if output == None:
            log_file.write("c " + ",".join(list(map(str, cube))) + " timeout\n")
            timeout_cubes.append(cube)
        else:
            cadical_result = cadical_parse_results(output)

            log_file.write(
                "c "
                + ",".join(list(map(str, cube)))
                + " time: {}, learned: {}, props: {}, sat: {}\n".format(
                    cadical_result.time,
                    cadical_result.learned,
                    cadical_result.props,
                    cadical_result.sat,
                )
            )
            log_file.flush()
            times.append(cadical_result.time)
    if len(times) == 0:
        log_file.write("c No cubes finished :( within the time limit\n")
    else:
        log_file.write("c solving stats\n")
        log_file.write("c sum time: {:.2f}\n".format(sum(times)))
        log_file.write("c max time: {:.2f}\n".format(max(times)))
        log_file.write("c avg time: {:.2f}\n".format(sum(times) / len(times)))

        log_file.write(
            "c approx optimal scheduling on 4 cores: {:.2f}\n".format(
                partition_n_ways(times, 4)["max_time"]
            )
        )
        log_file.write(
            "c approx optimal scheduling on 8 cores: {:.2f}\n".format(
                partition_n_ways(times, 8)["max_time"]
            )
        )
        log_file.write(
            "c approx optimal scheduling on 16 cores: {:.2f}\n".format(
                partition_n_ways(times, 16)["max_time"]
            )
        )
        log_file.write(
            "c approx optimal scheduling on 32 cores: {:.2f}\n".format(
                partition_n_ways(times, 32)["max_time"]
            )
        )
        log_file.write(
            "c approx optimal scheduling on 64 cores: {:.2f}\n".format(
                partition_n_ways(times, 64)["max_time"]
            )
        )
        log_file.write(
            "c approx optimal scheduling on 128 cores: {:.2f}\n".format(
                partition_n_ways(times, 128)["max_time"]
            )
        )
    if len(timeout_cubes) > 0:
        log_file.write(f"c timeouts: {len(timeout_cubes)}\n")
    log_file.flush()
    log_file.close()
    return timeout_cubes


def make_icnf(cubes, icnf_loc, orig_cnf=None):
    if orig_cnf != None:
        with open(orig_cnf, "r") as fin, open(icnf_loc, "w") as fout:
            next(fin)
            fout.write("p inccnf\n")
            for line in fin:
                fout.write(line)
    icnf_file = open(icnf_loc, "a" if orig_cnf else "w")
    for cube in cubes:
        icnf_file.write("a " + " ".join(map(str, cube)) + " 0\n")
    icnf_file.close()
