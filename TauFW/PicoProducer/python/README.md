# PicoProducer/python

1. [**`analysis/`**](analysis) contains analysis modules for doing analysis on nanoAOD (pre-selecting and reconstructing events, etc.)
2. [**`batch/`**](batch) contains tools for batch submission, used by [`pico.py`](../scripts/pico.py).
3. [**`corrections/`**](corrections) contains tools to apply corrections: energy scale, weight, scale factors, ...
4. [**`pico/`**](pico) subroutines for the [`pico.py`](../scripts/pico.py) script.
5. [**`processors/`**](processors) contains scripts to run post-processing modules on nanoAOD, like those in [`analysis/`](analysis).
6. [**`storage/`**](storage) contains tools for handling input/output to storage elements (like `EOS`, `T2`, `T3`, ...), used by [`pico.py`](../scripts/pico.py).
7. [**`tools/`**](tools) contains common tools used by all `python` code.
