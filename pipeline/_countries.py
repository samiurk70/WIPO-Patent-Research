"""The study country set, shared by every script that needs it.

Kept out of build_dataset.py so that importing the mapping does not run a build:
build_dataset is a script, and `from build_dataset import COUNTRIES` executed the
whole thing as a side effect.
"""

# ISO2 codes as they appear in the WIPO 'origin' column
COUNTRIES = {
    "BN": "Brunei Darussalam",
    "KH": "Cambodia",
    "ID": "Indonesia",
    "LA": "Lao PDR",
    "MY": "Malaysia",
    "MM": "Myanmar",
    "PH": "Philippines",
    "SG": "Singapore",
    "TH": "Thailand",
    "VN": "Viet Nam",
    "TL": "Timor-Leste",
    "CN": "China",
    "KR": "Korea, Rep.",
    "JP": "Japan",
}

# The eleven ASEAN members; the other three are the benchmark economies.
ASEAN = ["Brunei Darussalam", "Cambodia", "Indonesia", "Lao PDR", "Malaysia", "Myanmar",
         "Philippines", "Singapore", "Thailand", "Viet Nam", "Timor-Leste"]
