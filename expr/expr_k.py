# %%
from operator import mod
import sys

from black import json

sys.path.append("../src")
from experiment import experiment


# %%
def run(p, no):
    outdir = "./p{}no{}".format(p, no)
    protocol = {
        "variables": {
            "field width": 600,
            "field height": 400,
            "obstacle width": 40,
            "obstacle height": 40,
            "num mobiles": 50,
            "num statics": 50,
            "num obstacles": no,
        },
        "config": {
            "command": "multi-bridge -r 4000 -u -p {}".format(p),
            "outdir": outdir,
            "trials": 100,
            "verbose": True,
        },
    }

    experiment(protocol)

    with open("{}/protocol.json".format(outdir), mode="w") as f:
        json.dump(protocol, f, indent=2)


# %%
if __name__ == "__main__":
    no = int(sys.argv[1])
    params = list(range(0, 500 + 1, 50))
    for (case, p) in enumerate(params):
        print("CASE {}/{} | [p:{}]".format(case + 1, len(params), p))
        run(p, no)
