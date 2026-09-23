# Thin wrapper around pipeline/run.py so `make` works on systems that have it
# (the local dev machine drives the pipeline with `python pipeline/run.py <target>`).
PY ?= python

.PHONY: raw data figures tables verify all
raw:      ; $(PY) pipeline/run.py raw
data:     ; $(PY) pipeline/run.py data
figures:  ; $(PY) pipeline/run.py figures
tables:   ; $(PY) pipeline/run.py tables
verify:   ; $(PY) pipeline/run.py verify
all:      ; $(PY) pipeline/run.py all
