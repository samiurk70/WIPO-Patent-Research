"""Write data/raw/MANIFEST.sha256 — a checksum + size + mtime record of every cached
raw input. Committed; everything else under data/raw/ is not.

Run after `python pipeline/run.py raw`. To verify a cache against the committed manifest:
    python pipeline/make_manifest.py --check
"""
import hashlib
import sys
from datetime import datetime, timezone

from _paths import RAW

MANIFEST = RAW / "MANIFEST.sha256"
SKIP = {"MANIFEST.sha256"}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def entries():
    for p in sorted(RAW.rglob("*")):
        if p.is_file() and p.name not in SKIP:
            rel = p.relative_to(RAW).as_posix()
            st = p.stat()
            mtime = datetime.fromtimestamp(st.st_mtime, timezone.utc).isoformat()
            yield rel, sha256(p), st.st_size, mtime


def write():
    lines = [f"# raw input manifest - generated {datetime.now(timezone.utc).isoformat()}",
             "# sha256  size_bytes  mtime_utc  path"]
    for rel, digest, size, mtime in entries():
        lines.append(f"{digest}  {size}  {mtime}  {rel}")
    MANIFEST.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {MANIFEST}  ({len(lines) - 2} files)")


def check():
    if not MANIFEST.exists():
        print("no MANIFEST.sha256 to check against", file=sys.stderr)
        return 1
    want = {}
    for line in MANIFEST.read_text().splitlines():
        if line.startswith("#") or not line.strip():
            continue
        digest, _size, _mtime, rel = line.split(None, 3)
        want[rel] = digest
    have = {rel: digest for rel, digest, _s, _m in entries()}
    bad = [r for r in want if want[r] != have.get(r)]
    missing = [r for r in want if r not in have]
    extra = [r for r in have if r not in want]
    for r in missing:
        print(f"MISSING  {r}")
    for r in bad:
        print(f"CHANGED  {r}")
    for r in extra:
        print(f"UNTRACKED {r}")
    if bad or missing:
        return 1
    print("raw cache matches manifest")
    return 0


if __name__ == "__main__":
    sys.exit(check() if "--check" in sys.argv[1:] else (write() or 0))
