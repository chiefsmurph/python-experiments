"""
Smoke test for the "analyze positions" path.

Reproduces exactly what app-actions/run-python-analyze-positions.js does:
  spawn python3 -m final.analyze_positions
    cwd     = repo root (parent of this folder)
    PYTHONPATH = python-experiments
    stdin   = JSON { positions, closedPositions }
    stdout  = JSON { positionAnalysis, topTrends, bottomTrends, wordCount, allWordTrends }

Then it validates the output shape and re-derives the same fields the Node
caller pulls off each position (overallAvgScore, overallScaledAvgScore, ...).

Run from the python-experiments folder:
    python3 test_analyze_positions.py

Exit code 0 = PASS, 1 = FAIL.  No DB, no network — synthetic fixture only.
"""

import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))          # .../python-experiments
REPO_ROOT = os.path.dirname(HERE)                          # repo root (node's cwd)


def build_fixture():
    """
    Synthetic { positions, closedPositions }.

    word_trends_based_on_closed_positions keeps a word only if it appears across
    >= 4 distinct tickers, so we spread each strategy word over >=4 closed
    tickers with varying returns. Position word-lists reuse those same words so
    the positions actually score (non-zero), exercising top/bottom-word logic.
    """
    # Words that will become trends. Uppercase, split from strategy on "-".
    winners = ["ALPHASIG", "MOMENTUM", "BREADTHUP"]     # positive avg trend
    losers = ["BANKRUPTWF", "FADEWF", "CHOPWF"]          # negative avg trend

    closed = []

    def mk_closed(ticker, avg_sell, fill, strat_words):
        return {
            "ticker": ticker,
            "avgSellPrice": avg_sell,
            "sellReturnPerc": round((avg_sell - fill) / fill * 100, 2),
            "buys": [{"fillPrice": fill, "strategy": "-".join(strat_words)}],
        }

    # 6 tickers carrying the winner words at a profit
    for i in range(6):
        closed.append(mk_closed(f"WIN{i}", 11.0 + i, 10.0, winners + ["NEUTRALWF"]))
    # 6 tickers carrying the loser words at a loss
    for i in range(6):
        closed.append(mk_closed(f"LOS{i}", 8.0 + i * 0.1, 10.0, losers + ["NEUTRALWF"]))

    positions = [
        # Should score positive: holds winner words in activeWords + initialWords
        {
            "ticker": "GOODCO",
            "activeWords": winners + ["NEUTRALWF"],
            "interestingWords": ["MOMENTUM"],
            "initialWords": ["ALPHASIG", "BREADTHUP"],
        },
        # Should score negative: holds loser words
        {
            "ticker": "BADCO",
            "activeWords": losers + ["NEUTRALWF"],
            "initialWords": losers,
        },
        # No overlapping words -> analysis categories stay empty (edge case)
        {
            "ticker": "UNKNOWNCO",
            "activeWords": ["ZZZNOMATCH1", "ZZZNOMATCH2"],
        },
    ]
    return {"positions": positions, "closedPositions": closed}


def run_module(payload):
    """Invoke the module exactly like the Node caller does."""
    env = {**os.environ, "PYTHONPATH": "python-experiments"}
    proc = subprocess.run(
        [sys.executable, "-m", "final.analyze_positions"],
        cwd=REPO_ROOT,
        env=env,
        input=json.dumps(payload),
        capture_output=True,
        text=True,
    )
    return proc


def main():
    failures = []

    def check(name, cond, detail=""):
        status = "PASS" if cond else "FAIL"
        print(f"  [{status}] {name}" + (f" — {detail}" if detail else ""))
        if not cond:
            failures.append(name)

    print("analyze-positions smoke test")
    print(f"  repo root : {REPO_ROOT}")
    print(f"  python    : {sys.executable} ({sys.version.split()[0]})")
    print()

    fixture = build_fixture()
    proc = run_module(fixture)

    if proc.returncode != 0:
        print(f"  [FAIL] module exited {proc.returncode}")
        print("  --- stderr ---")
        print(proc.stderr.strip() or "(empty)")
        sys.exit(1)
    check("module exits 0", True)

    try:
        out = json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        print(f"  [FAIL] stdout is not valid JSON: {e}")
        print(proc.stdout[:500])
        sys.exit(1)
    check("stdout is valid JSON", True)

    # Contract keys the Node caller destructures
    for key in ("positionAnalysis", "topTrends", "bottomTrends", "wordCount", "allWordTrends"):
        check(f"output has '{key}'", key in out)

    check("wordCount > 0", out.get("wordCount", 0) > 0, f"wordCount={out.get('wordCount')}")
    check(
        "trends survived >=4-ticker filter",
        len(out.get("allWordTrends", [])) > 0,
        f"{len(out.get('allWordTrends', []))} trend words",
    )

    pa = {p["ticker"]: p for p in out.get("positionAnalysis", [])}
    check("all positions returned", len(pa) == len(fixture["positions"]),
          f"{len(pa)}/{len(fixture['positions'])}")

    # GOODCO should have a numeric, positive overall avgScore
    good = pa.get("GOODCO", {}).get("overall", {})
    check("GOODCO has numeric overall.avgScore", isinstance(good.get("avgScore"), (int, float)),
          f"avgScore={good.get('avgScore')}")
    bad = pa.get("BADCO", {}).get("overall", {})
    check("BADCO has numeric overall.avgScore", isinstance(bad.get("avgScore"), (int, float)),
          f"avgScore={bad.get('avgScore')}")
    check("GOODCO scores above BADCO",
          good.get("avgScore", 0) > bad.get("avgScore", 0),
          f"good={good.get('avgScore')} vs bad={bad.get('avgScore')}")

    # Re-derive the exact fields the Node wrapper attaches to each position
    print()
    print("  Node-side derived fields per position:")
    for p in out.get("positionAnalysis", []):
        overall = p.get("overall", {})
        derived = {
            "overallAvgScore": overall.get("avgScore"),
            "overallScaledAvgScore": overall.get("scaledAvgScore"),
            "overallTotalScore": overall.get("totalScore"),
            "overallScaledTotalScore": overall.get("scaledTotalScore"),
        }
        print(f"    {p['ticker']:>10}: {derived}")

    print()
    if failures:
        print(f"RESULT: FAIL ({len(failures)} check(s) failed: {', '.join(failures)})")
        sys.exit(1)
    print("RESULT: PASS — analyze-positions path is working as expected")
    sys.exit(0)


if __name__ == "__main__":
    main()
