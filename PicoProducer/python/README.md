# PicoProducer/python

1. [**`analysis/`**](analysis) contains analysis modules for doing analysis on nanoAOD (pre-selecting and reconstructing events, etc.)
2. [**`batch/`**](analysis) contains tools for batch submission, used by [`pico.py`](../scripts/pico.py).
3. [**`corrections/`**](analysis) contains tools to apply corrections: energy scale, weight, scale factors, ...
4. [**`processors/`**](analysis) contains scripts to run post-processing modules on nanoAOD, like those in `analysis/`.
5. [**`storage/`**](storage) contains tools for handling input/output to storage elements (like `EOS`, `T2`, `T3`, ...), used by [`pico.py`](../scripts/pico.py).
6. [**`tools/`**](tools) contains common tools used by all `python` code.
