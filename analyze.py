#!/usr/bin/env python3
"""Temporary search instrumentation for engine.py.

This file deliberately hooks the imported engine at runtime.  engine.py is
left unchanged.
"""

import os
import sys
import time

os.environ.setdefault("MAKEFUN_ENV_URL", "http://analysis.invalid")
import engine as e


FENS = [
    "r1bq1rk1/pp2ppbp/2np1np1/8/2BNP3/2N1BP2/PPPQ2PP/R3K2R w KQ -",
    "rnbq1rk1/ppp1bppp/4pn2/3p4/2PP4/2N1PN2/PP3PPP/R1BQKB1R w KQ -",
    "2rq1rk1/pp1bppbp/3p1np1/8/2BNP3/2N1BP2/PPPQ2PP/2KR3R w - -",
    "4k3/pp3ppp/8/8/8/8/PP3PPP/4K3 w - -",
]


class CountingTT(dict):
    def __init__(self):
        super().__init__()
        self.probes = 0
        self.hits = 0

    def get(self, key, default=None):
        self.probes += 1
        value = super().get(key, default)
        if value is not None:
            self.hits += 1
        return value


ORIGINAL_NG = e.ng
ORIGINAL_QS = e.qs
ORIGINAL_OM = e.om


def run(fen, reverse_root=False):
    e.NL = 150000
    e.TT = CountingTT()
    e.J = [[None, None] for _ in range(64)]
    e.KILLERS = [[None, None] for _ in range(64)]

    stats = {
        "iterations": [],
        "ng_calls": 0,
        "qs_calls": 0,
        "root_calls": 0,
        "root_order_done": False,
        "ng_wrapper_depth": 0,
    }

    def ng(s, depth, alpha, beta, ply):
        stats["ng_calls"] += 1
        outer = stats["ng_wrapper_depth"] == 0
        stats["ng_wrapper_depth"] += 1
        if outer:
            stats["root_calls"] += 1
            before = e.ND
            try:
                value, move = ORIGINAL_NG(s, depth, alpha, beta, ply)
            finally:
                stats["ng_wrapper_depth"] -= 1
            stats["iterations"].append(
                {
                    "depth": depth + 1,
                    "nodes": e.ND - before,
                    "complete": not e.T,
                    "move": None if move is None else e.mu(move),
                }
            )
            return value, move
        try:
            return ORIGINAL_NG(s, depth, alpha, beta, ply)
        finally:
            stats["ng_wrapper_depth"] -= 1

    def qs(s, alpha, beta, ply):
        stats["qs_calls"] += 1
        return ORIGINAL_QS(s, alpha, beta, ply)

    def om(moves, tt_move, ply):
        ordered = ORIGINAL_OM(moves, tt_move, ply)
        # sr() calls om() once with ply/Z == 0 for the root list.  Reverse
        # only that first call; later ply-0 calls belong to descendants or
        # quiescence and should retain their normal ordering.
        if reverse_root and ply == 0 and not stats["root_order_done"]:
            stats["root_order_done"] = True
            return list(reversed(ordered))
        return ordered

    e.ng = ng
    e.qs = qs
    e.om = om
    try:
        s = e.pf(fen)
        legal = {e.mu(m) for m in e.lm(s)}
        t0 = time.perf_counter()
        move = e.sr(s, legal, {s.h: 1})
        elapsed = time.perf_counter() - t0
    finally:
        e.ng = ORIGINAL_NG
        e.qs = ORIGINAL_QS
        e.om = ORIGINAL_OM

    by_depth = {}
    for item in stats["iterations"]:
        row = by_depth.setdefault(item["depth"], {"depth": item["depth"], "nodes": 0, "complete": True})
        row["nodes"] += item["nodes"]
        row["complete"] &= item["complete"]
    iterations = list(by_depth.values())
    complete = [x for x in iterations if x["complete"]]
    deepest = max((x["depth"] for x in complete), default=0)
    return {
        "fen": fen,
        "reverse_root": reverse_root,
        "elapsed": elapsed,
        "nodes": e.ND,
        "qnodes": stats["qs_calls"],
        "deepest": deepest,
        "iterations": iterations,
        "move": None if move is None else e.mu(move),
        "tt_probes": e.TT.probes,
        "tt_hits": e.TT.hits,
        "tt_hit_rate": e.TT.hits / e.TT.probes if e.TT.probes else 0.0,
    }


def print_result(r):
    tag = "reversed-root" if r["reverse_root"] else "normal-root"
    print(f"  {tag}: move={r['move']} time={r['elapsed']:.3f}s nodes={r['nodes']}")
    print(
        f"    deepest_completed={r['deepest']} plies "
        f"qnodes={r['qnodes']} qfraction={r['qnodes']/r['nodes']:.3%} "
        f"TT={r['tt_hits']}/{r['tt_probes']} ({r['tt_hit_rate']:.3%})"
    )
    print("    nodes_per_depth=" + ", ".join(
        f"{x['depth']}:{x['nodes']}{'*' if x['complete'] else '!'}"
        for x in r["iterations"]
    ))


def main():
    for i, fen in enumerate(FENS, 1):
        print(f"FEN {i}: {fen}")
        normal = run(fen)
        reversed_root = run(fen, reverse_root=True)
        print_result(normal)
        print_result(reversed_root)
        print(
            f"  root_order_effect: nodes_delta={reversed_root['nodes']-normal['nodes']} "
            f"time_delta={reversed_root['elapsed']-normal['elapsed']:.3f}s "
            f"same_move={normal['move'] == reversed_root['move']}"
        )


if __name__ == "__main__":
    main()
