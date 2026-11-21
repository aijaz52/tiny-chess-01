# Search terminal-node correction

The engine improvement moves negamax node finalization after the legal-move
loop. Mate and stalemate now receive their proper terminal scores, completed
nodes store their final bound in the transposition table, and interrupted nodes
return without caching a partial result. The original capture ordering is kept.

Before the change, depth-one searches at ply one returned `(-32000, 0)` for
both these positions:

- Checkmate: `7k/6Q1/5K2/8/8/8/8/8 b - - 0 1`
- Stalemate: `7k/5Q2/5K2/8/8/8/8/8 b - - 0 1`

After the change they return `(-29999, None)` and `(0, None)` respectively.
The engine was revised in separate edits for terminal handling and node/cache
finalization, then the final indentation was corrected during verification.

## Build and smoke test

Used the kit compressor, equivalent to packing the source into the entrypoint:

```sh
node /root/makefun/tiny-chess-01-kit/cli/makefun.mjs compress engine.py --out main.py --json
```

The unmodified baseline rebuilt to 4,084 bytes and selected the legal opening
move `g1f3` within 30,000 nodes. The final entry is **4,086 bytes**, leaving
10 bytes below the 4,096-byte limit. Its decompressed source matches `engine.py`.
The packed game loop also completed a mocked four-ply game exchange, choosing
legal moves `g1f3`, `g8f6`, `d2d4`, and `d7d5`.

## Benchmark

Final `python3 bench.py` output (30,000 nodes per position, best of two runs):

```text
budget=30000 reps=2
    30000 nodes   2.984s      10055 nps  d5e6
    30000 nodes   1.638s      18318 nps  e1c1
    30000 nodes   1.589s      18880 nps  f1e2
    30000 nodes   1.519s      19755 nps  d2e2
  TOTAL    120000 nodes   7.729s      15526 nps  avg 1.932s/move
nps=15526 avg_move=1.932s budget=30000
```

Positions are the four FENs in `bench.py`, in their original order. Diagnostics
and replay checks ran concurrently with this benchmark; timings reflect that
load. This is a search-correctness improvement, with no playing-strength claim
based on benchmark throughput.

## Regression checks

Updated obsolete engine references in the existing test scripts.

- `python3 diagnostics.py`: zero failures, covering evaluation symmetry,
  perft, make/unmake, tactics, mate distances, and stalemate.
- The same diagnostic suite against imported `main.py`: zero failures.
- `python3 replay_hang_test.py --limit 8`: eight saved positions tested at
  150,000 nodes each, zero hangs/failures. The limit is a sample of the local
  archive; omitting it runs every saved position.

The legacy `pack_experiment.py` requires an older source layout; the kit
compressor above was used for both required rebuilds.
