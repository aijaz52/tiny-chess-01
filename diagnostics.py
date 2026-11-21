"""Deterministic regression diagnostics; run with python3 diagnostics.py."""
import os
from pathlib import Path

os.environ.setdefault("MAKEFUN_ENV_URL", "http://diagnostics.invalid")
import engine as e

START = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
KIWI = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"
failures = 0


def check(label, actual, expected):
    global failures
    ok = actual == expected
    failures += not ok
    print(f"{'PASS' if ok else 'FAIL'} {label}: {actual!r}; expected {expected!r}")


def mirror(fen):
    board, side, castle, ep, *rest = fen.split()
    return " ".join(["/".join(r.swapcase() for r in board.split("/")[::-1]),
                     "b" if side == "w" else "w", castle.swapcase(),
                     ep[0] + str(9 - int(ep[1])) if ep != "-" else "-", *rest])


def fen(s):
    rows = []
    for rank in range(7, -1, -1):
        row = ""
        empty = 0
        for file in range(8):
            p = s.b[rank * 16 + file]
            if not p:
                empty += 1
                continue
            if empty:
                row += str(empty)
                empty = 0
            c = " pnbrqk"[p & 7]
            row += c.upper() if p >> 3 == e.W else c
        rows.append(row + (str(empty) if empty else ""))
    return f"{'/'.join(rows)} {'b' if s.s else 'w'} " + (
        "".join(c for bit, c in [(1, "K"), (2, "Q"), (4, "k"), (8, "q")] if s.c & bit) or "-"
    ) + f" {e.a(s.e) if s.e >= 0 else '-'} 0 1"


def snapshot(s):
    return tuple(tuple(getattr(s, k)) if isinstance(getattr(s, k), list)
                 else getattr(s, k) for k in e.S.__slots__)


def perft(s, depth):
    if not depth:
        return 1
    total = 0
    for move in e.lm(s):
        undo = e.ai(s, move)  # engine's make/unmake (mmv/umv equivalents)
        total += perft(s, depth - 1)
        e.ak(s, move, undo)
    return total


def reset():
    e.E.clear()
    e.G.clear()
    e.y.clear()
    e.ND, e.T, e.o, e.q = 0, False, {}, []


def mates(s, moves):
    """Exhaustive legal mate oracle, independent of evaluation/search scores."""
    winners = []
    for move in e.lm(s):
        undo = e.ai(s, move)
        replies = e.lm(s)
        won = not replies and bool(e.ic(s, s.s))
        if replies and moves > 1:
            won = True
            for reply in replies:
                u = e.ai(s, reply)
                continuation = mates(s, moves - 1)
                e.ak(s, reply, u)
                if not continuation:
                    won = False
                    break
        e.ak(s, move, undo)
        if won:
            winners.append(e.mu(move))
    return winners


def run():
    print("EVALUATION SYMMETRY (mover perspective)")
    positions = [START, KIWI,
        "7k/8/3n4/8/2B1P3/3K4/8/8 w - - 0 1",
        "6k1/1p3pp1/4r3/3P4/2B2Q2/6P1/5PK1/8 b - - 0 1",
        "7k/8/8/8/8/8/4P3/K7 w - - 0 1"]
    for f in positions:
        check(f, e.ev(e.pf(f)), e.ev(e.pf(mirror(f))))

    print("MOVE GENERATION / MAKE-UNMAKE")
    for f, counts in [(START, [20, 400, 8902]), (KIWI, [48, 2039, 97862]),
                      ("8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1", [14, 191, 2812]),
                      ("r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1", [6, 264, 9467])]:
        s = e.pf(f)
        before = snapshot(s)
        for depth, count in enumerate(counts, 1):
            check(f"perft depth {depth} {f}", perft(s, depth), count)
            check("root restored", snapshot(s) == before, True)
        consistent = True
        for move in e.lm(s):
            undo = e.ai(s, move)
            consistent &= snapshot(s) == snapshot(e.pf(fen(s)))
            e.ak(s, move, undo)
        check("incremental state equals FEN rebuild", consistent, True)

    print("PAWN ATTACKS")
    for f in ["7k/8/8/3p4/4K3/8/8/8 w - - 0 1",
              "8/8/8/4k3/3P4/8/8/7K b - - 0 1"]:
        s = e.pf(f)
        check(f, bool(e.ic(s, s.s)), True)

    print("TACTICS NL=30000 (expected mates from exhaustive legal-move oracle)")
    e.NL = 30000
    tactics = [
        ("mate in 1", "7k/5Q2/5K2/8/8/8/8/8 w - - 0 1", 1, None),
        ("mate in 1 black", mirror("7k/5Q2/5K2/8/8/8/8/8 w - - 0 1"), 1, None),
        ("hanging queen", "6k1/8/8/8/3q4/8/3R4/6K1 w - - 0 1", 0, ["d2d4"]),
        ("mate in 2", "7k/8/8/5K2/4Q3/8/8/8 w - - 0 1", 2, None),
    ]
    for label, f, distance, expected in tactics:
        s = e.pf(f)
        expected = expected if expected is not None else mates(s, distance)
        if distance == 2:
            check("mate-in-2 fixture has no mate-in-1", mates(s, 1), [])
        before = snapshot(s)
        move = e.sr(s, set(), {})
        chosen = e.mu(move) if move is not None else None
        check(f"{label} FEN={f} chosen={chosen} expected={expected} nodes={e.ND}",
              chosen in expected, True)
        check("search restores root", snapshot(s) == before, True)
        if distance:
            reset()
            value, move = e.X(s, distance * 2 - 1, -e.I, e.I, 0)
            check(f"ng root score={value} move={e.mu(move) if move else None}",
                  value, e.M - (distance * 2 - 1))
            check("ng root move", e.mu(move) in expected if move else False, True)

    print("QUIESCENCE IN CHECK AND MATE DISTANCE")
    s = e.pf("7k/6Q1/5K2/8/8/8/8/8 b - - 0 1")
    reset()
    check("checkmate must override stand-pat beta cutoff", e.x(s, -e.I, -31000, 1), -e.M + 1)
    reset()
    check("mate score at ply 1", e.X(s, 1, -e.I, e.I, 1)[0], -e.M + 1)
    check("TT mate score reused at ply 3", e.X(s, 1, -e.I, e.I, 3)[0], -e.M + 3)
    s = e.pf(tactics[0][1])
    reset()
    check("TT winning mate stored at ply 0", e.X(s, 1, -e.I, e.I, 0)[0], e.M - 1)
    check("TT winning mate reused at ply 2", e.X(s, 1, -e.I, e.I, 2)[0], e.M - 3)
    # A forced losing mate with legal replies exercises stored negative scores.
    s = e.pf(mirror(tactics[3][1]))
    move = next(m for m in e.lm(s) if e.mu(m) == "f4g3")
    e.ai(s, move)
    reset()
    check("TT losing mate stored at ply 1", e.X(s, 2, -e.I, e.I, 1)[0], -e.M + 3)
    check("TT losing mate reused at ply 3", e.X(s, 2, -e.I, e.I, 3)[0], -e.M + 5)
    reset()
    s = e.pf("7k/5Q2/5K2/8/8/8/8/8 b - - 0 1")
    check("stalemate with no legal moves", e.X(s, 1, -e.I, e.I, 1), (0, None))
    size = Path(e.__file__).stat().st_size
    check(f"engine.py bytes={size} <=10300", size <= 10300, True)
    print(f"TOTAL: {failures} failure(s)")
    return failures


if __name__ == "__main__":
    raise SystemExit(bool(run()))
