import os
import sys
import shutil
import json
import pandas as pd
import subprocess
import time
import datetime
import itertools

BSS_CMD = "../../border_security_system/target/release/bss"


def main(protocol_file):
    with open(protocol_file) as f:
        protocol = json.load(f)

    solvers = parse_solver(protocol["solver"])
    problems = parse_problem(protocol["problem"])
    trials = protocol["config"]["trials"]
    command = solvers["cmd"]
    args_list = solvers["args"]
    working_dir = protocol["config"]["working dir"]
    output_path = protocol["config"]["output path"]

    if os.path.exists(working_dir):
        print(
            "Error: Specified working directory already exists: {}".format(working_dir)
        )
        exit(1)

    if os.path.exists(output_path):
        print("Error: output file already exists: {}".format(output_path))
        exit(1)

    datetime_start = datetime.datetime.now()

    for i_pbm, problem in enumerate(problems):
        # Cleanup the working directly
        if os.path.exists(working_dir):
            shutil.rmtree(working_dir)
        os.mkdir(working_dir)
        # Generate problem instance files
        make_problem_instances(problem, working_dir, trials)
        for trial in range(trials):
            instance = "{}/instance-{}.json".format(working_dir, trial + 1)

            for i_args, args in enumerate(args_list):

                time_start = time.time()
                uptime = run_simulation(command, args, instance, working_dir)
                time_end = time.time()

                elapsed_time = time_end - time_start
                frame = {**args_list[args], **problem}
                frame["trial"] = "#{}".format(trial)
                frame["uptime"] = uptime
                frame["elapsed time"] = elapsed_time
                frame = pd.DataFrame([frame.values()], columns=frame.keys())

                if os.path.exists(output_path):
                    frame.to_csv(
                        output_path,
                        index=False,
                        encoding="utf-8",
                        mode="a",
                        header=False,
                    )
                else:
                    frame.to_csv(output_path, index=False, encoding="utf-8", mode="w")
                print(
                    "[{}] [problem #{}/{}] [instance #{}/{}] [solver #{}/{}] [elapsed-time: {:.1f} s] [uptime: {:.2f} h] {} {}".format(
                        datetime.datetime.now() - datetime_start,
                        i_pbm + 1,
                        len(problems),
                        trial + 1,
                        trials,
                        i_args + 1,
                        len(args_list),
                        elapsed_time,
                        uptime / 3600,
                        command,
                        args,
                    )
                )


def make_problem_recipe(problem, path):
    assert "field size" in problem
    assert "num mobiles" in problem
    assert "num statics" in problem

    fw = problem["field size"][0]
    fh = problem["field size"][1]
    nm = problem["num mobiles"]
    ns = problem["num statics"]

    obs_var = []
    if "obstacles" in problem:
        with open(problem["obstacles"]) as f:
            obs_var = json.load(f)

    recipe = json.dumps(
        {
            "field_origin": [0.0, 0.0],
            "field_size": [fw, fh],
            "west_base_pos": [0.0, fh / 2],
            "east_base_pos": [fw, fh / 2],
            "num_mobiles": nm,
            "num_statics": ns,
            "num_obstacles": 0,
            "obstacle_variants": obs_var,
        }
    )

    with open(path, mode="w") as f:
        f.write(recipe)


def parse_arg(cfg):
    return [{"key": cfg["key"], "value": value} for value in cfg["values"]]


def parse_args(cfg):
    arg_names = [arg for arg in cfg]
    expanded = [parse_arg(cfg[arg]) for arg in cfg]
    traces = {}
    for arg_list in itertools.product(*expanded):
        trace = {}
        args = []
        for name, kv in zip(arg_names, arg_list):
            trace[name] = kv["value"]
            args.append("{} {}".format(kv["key"], kv["value"]))
        args = " ".join(args)
        traces[args] = trace
    return traces


def parse_solver(cfg):
    return {
        "cmd": cfg["cmd"],
        "args": parse_args(cfg["args"]),
    }


def parse_problem(cfg):
    expanded = [cfg[prop] for prop in cfg]
    prop_names = [prop for prop in cfg]
    problems = []
    for props in itertools.product(*expanded):
        problems.append(dict(zip(prop_names, props)))
    return problems


def make_problem_instances(problem, working_dir, num):
    recipe_file = "{}/recipe.json".format(working_dir)
    make_problem_recipe(problem, recipe_file)

    make_cmd = "{} make -r {} -d {} -n {}".format(
        BSS_CMD, recipe_file, working_dir, num
    )

    res = subprocess.call(make_cmd, shell=True)
    if res != 0:
        print("Error: %s" % make_cmd)
        exit(1)


def run_simulation(command, args, instance_file, working_dir):
    result_file = "%s/simulation_result.json" % working_dir
    if os.path.exists(result_file):
        os.remove(result_file)

    cmd = "%s %s %s -i %s -o %s --quiet" % (
        BSS_CMD,
        command,
        args,
        instance_file,
        result_file,
    )

    res = subprocess.call(cmd, shell=True)
    if res != 0:
        print("Error: %s" % cmd)
        exit(1)

    with open(result_file) as f:
        result = json.load(f)
        return result[-1]["laptime"]


if __name__ == "__main__":
    main(sys.argv[1])
