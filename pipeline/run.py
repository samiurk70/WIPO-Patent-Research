"""Single entry point for the Paper A pipeline.

Usage:
    python pipeline/run.py raw       # download + cache the WIPO bulk file
    python pipeline/run.py data      # build family and counting tables from the raw cache
    python pipeline/run.py figures   # regenerate Paper A figures
    python pipeline/run.py tables    # regenerate counting_generality tables
    python pipeline/run.py verify    # recompute every manuscript number, fail on mismatch
    python pipeline/run.py all       # data -> figures -> tables -> verify  (assumes raw cache present)

`raw` is deliberately excluded from `all`: the raw cache is checksummed
(data/raw/MANIFEST.sha256) and should change only on an intentional refresh.
"""
import subprocess
import sys
from pathlib import Path

PIPE = Path(__file__).resolve().parent

STEPS = {
    "raw": ["fetch_wipo.py", "make_manifest.py"],
    "data": ["load_wipo_families.py"],
    "figures": ["make_figures_paper_a.py"],
    "tables": ["counting_generality.py"],
    "verify": ["check_numbers.py", "verify_all.py"],
}
ORDER = ["data", "figures", "tables", "verify"]


def run_script(name: str) -> int:
    print(f"\n=== {name} ===", flush=True)
    return subprocess.run([sys.executable, str(PIPE / name)], cwd=PIPE).returncode


def main(argv):
    if len(argv) != 1 or argv[0] not in {*STEPS, "all"}:
        print(__doc__)
        return 2
    targets = ORDER if argv[0] == "all" else [argv[0]]
    for target in targets:
        for script in STEPS[target]:
            rc = run_script(script)
            if rc != 0:
                print(f"\n!! {script} exited {rc}", file=sys.stderr)
                return rc
    print("\nOK")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
