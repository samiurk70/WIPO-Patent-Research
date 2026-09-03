"""Download the WIPO bulk patent-indicators dataset (direct public link, no login).

Only the patent-indicators bundle is used by this analysis; the trademark bundle
(~100 MB) is intentionally not fetched.
"""
import zipfile
from datetime import datetime, timezone

import requests

from _paths import RAW

WIPO_DIR = RAW / "wipo"
WIPO_DIR.mkdir(parents=True, exist_ok=True)

FILES = {
    "wipo-data-patent-indicators.zip": "https://www.wipo.int/documents/d/ip-statistics/wipo-data-patent-indicators.zip",
}

# Concordances, for defending the green definition (plan task 1.7). Both are ordinary
# public files on wipo.int -- unlike the family series, which lives only behind the Data
# Center's interactive app (see docs/wipo_family_export.md).
CONCORDANCES = {
    # Schmoch's IPC-to-35-field table; field 24 is this paper's green definition
    "ipc_technology.xlsx":
        "https://www.wipo.int/documents/2948119/3215563/ipc_technology.xlsx",
    # WIPO's own Green Technology Inventory for Statistical Use -- the broad comparator
    "green_ipc_technology.xlsx":
        "https://www.wipo.int/documents/d/ip-statistics/docs-en-green-ipc-technology.xlsx",
}

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

for fname, url in FILES.items():
    dest = WIPO_DIR / fname
    if dest.exists() and dest.stat().st_size > 0:
        print(f"{fname} already downloaded")
    else:
        print(f"Downloading {fname} ...")
        r = requests.get(url, headers=headers, timeout=300, stream=True)
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 20):
                f.write(chunk)
        print(f"  -> {dest.stat().st_size / 1e6:.1f} MB")

    with zipfile.ZipFile(dest) as z:
        print(f"  contents of {fname}:")
        for info in z.infolist():
            print(f"    {info.filename}  ({info.file_size / 1e6:.1f} MB)")
        z.extractall(WIPO_DIR / fname.replace(".zip", ""))

for fname, url in CONCORDANCES.items():
    dest = WIPO_DIR / fname
    if dest.exists() and dest.stat().st_size > 0:
        print(f"{fname} already downloaded")
        continue
    print(f"Downloading {fname} ...")
    r = requests.get(url, headers=headers, timeout=120)
    r.raise_for_status()
    dest.write_bytes(r.content)
    print(f"  -> {dest.stat().st_size / 1e3:.1f} kB")

(WIPO_DIR / "RETRIEVED.txt").write_text(
    f"wipo-data-patent-indicators.zip retrieved {datetime.now(timezone.utc).isoformat()}\n"
    f"from {FILES['wipo-data-patent-indicators.zip']}\n",
    encoding="utf-8",
)
print("Done.")
