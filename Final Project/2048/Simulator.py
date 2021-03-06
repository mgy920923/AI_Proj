import time
import os
import itertools

import pandas as pd
import openpyxl

import AI
from main import run_game


def simulate_config(**kwargs):
    kwargs["simulate"] = True
    start_time = time.time()
    results = run_game(**kwargs)
    end_time = time.time()
    print("total seconds for the simulation:", int(end_time - start_time))
    return results


def _write_to_excel(results: pd.DataFrame, fname: str, sheet_name: str):
    if os.path.isfile(fname):
        book = openpyxl.load_workbook(fname)
        w = pd.ExcelWriter(fname, engine='openpyxl', mode='a')
        w.book = book
        w.sheets = dict((ws.title, ws) for ws in book.worksheets)
    else:
        w = pd.ExcelWriter(fname, engine='openpyxl')
    with w as writer:
        results.to_excel(writer, sheet_name)


def simulate(AI_type="heuristic", num_iterations=30, outfile="simulation.xlsx", **kwargs):

    HEURISTICS = ["safest", "smooth", "monotonic"]
    SHORT_NAMES = {
        "AI_type": '',
        "num_games": 'n=',
        "max_depth": 'd=',
        "num_rollouts": 'r=',
        "epsilon": 'e=',
        "UCT": 'U=',
        "type": 't=',
        "greedy": "grdy",
        "safe": "sf",
        "safest": "sfst",
        "monotonic": "mn",
        "smooth": "smth",
        "corner_dist": "c_d",
        "random": "rnd",
        "rollout": "roll",
        'True': 'T',
        'False': 'F',
        'None': 'rnd',
        "use_expert": 'UE'
    }

    params = {
        "AI_type": [AI_type],
        "num_games": [num_iterations]
    }

    if AI_type in ["rollout", "MCTS"]:
        params["max_depth"] = [4, 6, 8]
        params["num_rollouts"] = [25, 50, 100]
        params["epsilon"] = [0]
        params["type"] = ['None', *HEURISTICS]
        params["use_expert"] = [True, False]
        if AI_type == "MCTS":
            params["UCT"] = [True, False]

    elif AI_type == "heuristic":
        params["type"] = AI.HEURISTICS

    if kwargs:
        for k, v in kwargs.items():
            params[k] = v

    vars = params.keys()
    vals = params.values()

    for val_combo in itertools.product(*vals):
        opts = dict(zip(vars, val_combo))
        print("Current Configuration:")
        print(opts)
        results = simulate_config(**opts)
        results.update(opts)
        df = pd.DataFrame(results)
        sheet_name = ''
        for opt in opts:
            sheet_name += SHORT_NAMES[opt] + \
                          (SHORT_NAMES[str(opts[opt])] if str(opts[opt]) in SHORT_NAMES else str(opts[opt])) + ','
        sheet_name = sheet_name[:-1]
        _write_to_excel(df, outfile, sheet_name)


if __name__ == "__main__":
    simulate("rollout")
