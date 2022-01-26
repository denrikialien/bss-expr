# %%
from operator import mod
import sys

from black import json

sys.path.append("../src")
from experiment import experiment


# %%
def run(cmd, fw, fh, ns, rm, no):
    outdir = "./fw{}-fh{}-ns{}-rm{}-no{}".format(fw, fh, ns, rm, no)
    protocol = {
        "variables": {
            "field width": fw,
            "field height": fh,
            "obstacle width": 40,
            "obstacle height": 40,
            "num mobiles": round(ns * rm / 100),
            "num statics": ns - round(ns * rm / 100),
            "num obstacles": no,
        },
        "config": {
            "command": cmd,
            "outdir": "./fw{}-fh{}-ns{}-rm{}-no{}".format(fw, fh, ns, rm, no),
            "trials": 100,
            "verbose": False,
        },
    }

    experiment(protocol)

    with open("{}/protocol.json".format(outdir), mode="w") as f:
        json.dump(protocol, f, indent=2)


# %%
field_width = [600]
field_height = [400]
num_sensors = list(range(30, 200 + 1, 10))
ratio_mobiles = [50]
num_obstacles = [30]

params = [
    (fw, fh, ns, rm, no)
    for fw in field_width
    for fh in field_height
    for ns in num_sensors
    for rm in ratio_mobiles
    for no in num_obstacles
]

# %%
if __name__ == "__main__":
    cmd = sys.argv[1]
    for (case, (fw, fh, ns, rm, no)) in enumerate(params):
        print(
            "CASE {}/{} | [fw:{}] [fh:{}] [ns:{}] [rm:{}] [no:{}]".format(
                case + 1, len(params), fw, fh, ns, rm, no
            )
        )
        run(cmd, fw, fh, ns, rm, no)
