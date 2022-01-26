# %%
import os
import sys
import json
import pandas as pd
import numpy as np
from experiment import (
    read_protocol_file,
    live_mean,
    estimate_area_of_collision_space,
    rect_point_collision,
)


# %%
def occupancy_ratio_of_obstacles(snapshot):
    snapshot = snapshot[0]["before"]
    obstacles = [np.array(o["shape"][:-1]) for o in snapshot["obstacles"]]
    print("obs.shape", obstacles[0].shape)
    xrange = (snapshot["field"][0], snapshot["field"][2])
    yrange = (snapshot["field"][1], snapshot["field"][3])
    xsize = xrange[1] - xrange[0]
    ysize = yrange[1] - yrange[0]

    def collision_free(p):
        all([not rect_point_collision(r, p) for r in obstacles])

    area = estimate_area_of_collision_space(xrange, yrange, 1.0, collision_free)
    return area / (xsize * ysize)


# %%
def summary_snapshots(protocol, snapshots, tag, outframe):
    protocol = read_protocol_file(protocol)
    var = protocol["variables"]
    outframe["field width"].append(var["field width"])
    outframe["field height"].append(var["field height"])
    outframe["obstacle width"].append(var["obstacle width"])
    outframe["obstacle height"].append(var["obstacle height"])
    outframe["num mobiles"].append(var["num mobiles"])
    outframe["num statics"].append(var["num statics"])
    outframe["num obstacles"].append(var["num obstacles"])
    outframe["tag"].append(tag)

    update_mean_uptime = live_mean()
    update_err_rate = live_mean()
    # update_mean_occ = live_mean()
    update_mean_elt = live_mean()
    mean_uptime = 0
    err_rate = 0
    # mean_occ = 0
    mean_elt = 0

    for ss in snapshots:
        with open(ss, mode="r") as f:
            ss = json.load(f)
        uptime = ss[-1]["laptime"]
        if uptime > 0:
            mean_uptime = update_mean_uptime(uptime)
        err_rate = update_err_rate(int(uptime == 0))
        # occ = occupancy_ratio_of_obstacles(ss)
        # mean_occ = update_mean_occ(occ)
        assert "elapsed_time_millis_after" in ss[0]
        elt = ss[0]["elapsed_time_millis_after"]
        mean_elt = update_mean_elt(elt)

    outframe["mean uptime"].append(mean_uptime)
    outframe["error rate"].append(err_rate * 100)
    outframe["mean elt"].append(mean_elt)
    # outframe["mean occupancy ratio"].append(mean_occ)


# %%
def summary_dir(dir, tag, outframe):
    files = ["{}/{}".format(dir, f) for f in os.listdir(dir)]
    protocol_file = "{}/protocol.json".format(dir)
    assert protocol_file in files
    files.remove(protocol_file)
    summary_snapshots(protocol_file, files, tag, outframe)


# %%
def summary_dirs(rootdir, tag):
    outframe = {
        "field width": [],
        "field height": [],
        "obstacle width": [],
        "obstacle height": [],
        "num mobiles": [],
        "num statics": [],
        "num obstacles": [],
        # "occupancy ratio": [],
        "tag": [],
        "mean uptime": [],
        "error rate": [],
        "mean elt": [],
    }
    for dir in os.listdir(rootdir):
        dir = "{}/{}".format(rootdir, dir)
        summary_dir(dir, tag, outframe)
    return outframe


# %%
def summary(outfile, rootdir, tag):
    df = summary_dirs(rootdir, tag)
    df = pd.DataFrame(df)
    df.to_csv(outfile, index=False)


# %%
if __name__ == "__main__":
    rootdir = sys.argv[1]
    tag = sys.argv[2]
    outfile = sys.argv[3]
    summary(outfile, rootdir, tag)
