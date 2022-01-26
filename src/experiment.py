# %%
import os
import sys
import json
import subprocess
import datetime
import numpy as np
import hashlib
import tempfile as tmp
import shutil


# %%
def cross_prod(o, p, q):
    return np.cross(p - o, q - o).item()


# %%
def rect_point_collision(rect, point):
    assert rect.shape == (4, 2)
    test = np.array([cross_prod(rect[i - 1], rect[i], point) for i in range(4)])
    return np.all(test >= 0.0) or np.all(test <= 0.0)


# %%
def estimate_area_of_collision_space(xrange, yrange, precision, collision_free):
    """
    r = 20.0
    c = np.array([50, 50])
    xrange = (0, 100)
    yrange = xrange
    is_free = lambda p: np.linalg.norm(c - p) > r
    area = estimate_area_of_collision_space(xrange, yrange, 16.0, is_free)
    """
    assert precision > 0.0
    assert xrange[1] > xrange[0]
    assert yrange[1] > yrange[0]
    xmin, xmax = xrange
    ymin, ymax = yrange
    xsize = xmax - xmin
    ysize = ymax - ymin
    pmin = np.array([xmin, ymin])
    pmax = np.array([xmax, ymax])
    n = round(xsize * ysize * precision ** 2)
    hits = 0
    for i in range(n):
        prand = (pmax - pmin) * np.random.rand(2) + pmin
        if not collision_free(prand):
            hits += 1
    return hits / n * xsize * ysize


# %%
def new_rect(center, width, height, angle):
    assert -180 <= angle <= 180
    t = np.pi * angle / 180.0
    rot = np.array([[np.cos(t), -np.sin(t)], [np.sin(t), np.cos(t)]])
    V = [
        [-width / 2, -height / 2],
        [-width / 2, height / 2],
        [width / 2, height / 2],
        [width / 2, -height / 2],
    ]
    return np.array([np.dot(rot, v) + center for v in V])


# %%
def random_rects(xrange, yrange, width, height, num, collision_free):
    xmin, xmax = xrange
    ymin, ymax = yrange
    pmin = np.array([xmin, ymin])
    pmax = np.array([xmax, ymax])
    rotmin, rotmax = -180, 180
    rects = []
    while len(rects) < num:
        center = (pmax - pmin) * np.random.rand(2) + pmin
        rot = (rotmax - rotmin) * np.random.rand() + rotmin
        rect = new_rect(center, width, height, rot)
        if collision_free(rect):
            rects.append(rect)
    return rects


# %%
def random_points(num, collision_free, generate_point):
    points = []
    rng = np.random.default_rng()
    while len(points) < num:
        prand = generate_point(rng)
        if collision_free(prand):
            points.append(prand)
    return points


# %%
def new_counter(initial):
    next_value = initial

    def counter():
        nonlocal next_value
        ret = next_value
        next_value += 1
        return ret

    return counter


# %%
def new_problem_instance(
    field_size, size_obstacle, num_static, num_mobile, num_obstacle
):

    (field_width, field_height) = field_size
    xrange = (-field_width / 2, field_width / 2)
    yrange = (-field_height / 2, field_height / 2)
    (xmin, xmax) = xrange
    (ymin, ymax) = yrange
    ymid = (ymin + ymax) / 2

    base_nodes = [
        np.array([xmin, ymid]),
        np.array([xmax, ymid]),
    ]

    collision_free = lambda r: all([not rect_point_collision(r, p) for p in base_nodes])

    obstacles = random_rects(
        xrange, yrange, size_obstacle[0], size_obstacle[1], num_obstacle, collision_free
    )

    collision_free = lambda p: all([not rect_point_collision(o, p) for o in obstacles])

    z = 3.29  # 99.9% of generated points are in a range (ymin ,ymax)
    generate_point = lambda rng: np.array(
        [
            rng.uniform(xmin, xmax),
            rng.normal(ymid, (ymax - ymin) / 2 / z),
        ]
    )

    static_nodes = random_points(num_static, collision_free, generate_point)
    mobile_nodes = random_points(num_mobile, collision_free, generate_point)

    next_id = new_counter(initial=0)

    return {
        "field": [xmin, ymin, xmax, ymax],
        "obstacles": [
            {
                "kind": "Hollow",
                "shape": shape.tolist(),
            }
            for shape in obstacles
        ],
        "base_nodes": {str(next_id()): {"x": p[0], "y": p[1]} for p in base_nodes},
        "static_sensor_nodes": {
            str(next_id()): {"x": p[0], "y": p[1], "battery": 0.0, "mode": "Sleep"}
            for p in static_nodes
        },
        "mobile_sensor_nodes": {
            str(next_id()): {"x": p[0], "y": p[1], "battery": 0.0, "mode": "Sleep"}
            for p in mobile_nodes
        },
    }


# %%
def make_problem_file(
    filepath, field_size, size_obstacle, num_static, num_mobile, num_obstacle
):
    instance = new_problem_instance(
        field_size, size_obstacle, num_static, num_mobile, num_obstacle
    )

    with open(filepath, mode="w+") as f:
        json.dump(instance, fp=f)


# %%
def read_protocol_file(filepath):
    with open(filepath, mode="r") as f:
        protocol = json.load(f)
    assert "variables" in protocol
    assert "config" in protocol
    variables = protocol["variables"]
    assert "field width" in variables
    assert "field height" in variables
    assert "obstacle width" in variables
    assert "obstacle height" in variables
    assert "num statics" in variables
    assert "num mobiles" in variables
    assert "num obstacles" in variables
    config = protocol["config"]
    assert "command" in config
    assert "outdir" in config
    assert "trials" in config
    assert "verbose" in config
    return protocol


# %%
def make_problem_files(
    num, field_size, size_obstacle, num_static, num_mobile, num_obstacle
):
    id = "{},{},{},{},{},{}".format(
        num, field_size, size_obstacle, num_static, num_mobile, num_obstacle
    )

    dirname = hashlib.sha256(id.encode("utf-8")).hexdigest()
    dirpath = "{}/{}".format(tmp.gettempdir(), dirname)

    if os.path.exists(dirpath) and len(os.listdir(dirpath)) < num:
        shutil.rmtree(dirpath)

    if not os.path.exists(dirpath):
        os.mkdir(dirpath)
        for i in range(num):
            filepath = "{}/pbm-{}.json".format(dirpath, i)
            make_problem_file(
                filepath,
                field_size,
                size_obstacle,
                num_static,
                num_mobile,
                num_obstacle,
            )

    return ["{}/{}".format(dirpath, filename) for filename in os.listdir(dirpath)]


# %%
def run_expr(command, infile, outfile, logfile=None):
    CMD = "../../border_security_system/target/release/bss"

    if logfile is not None:
        cmd = "{} {} -i {} -o {} -l {} --quiet".format(
            CMD, command, infile, outfile, logfile
        )
    else:
        cmd = "{} {} -i {} -o {} --quiet".format(CMD, command, infile, outfile)

    res = subprocess.call(cmd, shell=True)
    if res != 0:
        return None

    with open(outfile, mode="r") as f:
        snapshot = json.load(f)
        return snapshot[-1]["laptime"] / 3600


# %%
def live_mean():
    mean = 0
    n = 0

    def update(value):
        nonlocal mean, n
        mean = (mean * n + value) / (n + 1)
        n = n + 1
        return mean

    return update


# %%
def experiment(protocol):
    variables = protocol["variables"]
    config = protocol["config"]
    field_size = (variables["field width"], variables["field height"])
    obstacle_size = (variables["obstacle width"], variables["obstacle height"])
    num_statics = variables["num statics"]
    num_mobiles = variables["num mobiles"]
    num_obstacles = variables["num obstacles"]
    trials = config["trials"]
    outdir = config["outdir"]
    command = config["command"]
    verbose = config["verbose"]

    if os.path.exists(outdir):
        print("[ERROR] {} is already exists".format(outdir))
        exit(1)

    os.mkdir(outdir)

    pbmfiles = make_problem_files(
        trials, field_size, obstacle_size, num_statics, num_mobiles, num_obstacles
    )

    update_uptime_mean = live_mean()
    update_err_mean = live_mean()
    mean_uptime = 0
    err_rate = 0

    started_at = datetime.datetime.now()
    for i, infile in enumerate(pbmfiles):
        outfile = "{}/snapshot-{}.json".format(outdir, i)

        if verbose:
            logfile = "{}/log-{}.log".format(outdir, i)
        else:
            logfile = None

        round_started_at = datetime.datetime.now()
        uptime = run_expr(command, infile, outfile, logfile)
        round_ended_at = datetime.datetime.now()

        if uptime is None:
            print("Something went wrong...")
            exit(1)

        if uptime > 0:
            mean_uptime = update_uptime_mean(uptime)
        err_rate = update_err_mean(int(uptime == 0)) * 100

        laptime = round_ended_at - round_started_at
        acc_laptime = round_ended_at - started_at

        print(
            "[#{}/{}] [{}] [+{}] uptime: {:.1f} [h], uptime(mean): {:.1f} [h], error-rate: {:.1f} %".format(
                i + 1,
                len(pbmfiles),
                acc_laptime,
                laptime,
                uptime,
                mean_uptime,
                err_rate,
            )
        )


# %%
def main(protocol_file):
    """
    An example of protocol file (json):

    {
      "variables": {
        "field width": 300,
        "field height": 200,
        "obstacle width": 80,
        "obstacle height": 80,
        "num statics": 20,
        "num mobiles": 20,
        "num obstacles": 2
      },
      "config": {
        "command": "single-bridge -a 0.0 -r 500",
        "outdir": "./expr1",
        "trials": 10,
        "verbose": false
      }
    }

    """
    experiment(read_protocol_file(protocol_file))


# %%
if __name__ == "__main__":
    main(sys.argv[1])
