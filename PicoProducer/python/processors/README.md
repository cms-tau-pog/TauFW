# PicoProducer/python/processors

Scripts to run post-processing modules on nanoAOD, like those in [`analysis/`](../analysis).
These are called by [`pico.py`](../../script/pico.py).
* [`skimjob.py`](skimjob.py): Skim nanoAOD file (input: nanoAOD, output: nanoAOD).
* [`picojob.py`](picojob.py): Analyze nanoAOD events (input: nanoAOD, output: custom "pico" format, e.g. a flat tree).
* [`dumpGen.py`](dumpGen.py): Dump gen-level information of MC events in nanoAOD file (input: nanoAOD).
For instructions, please see [](../..#skimming)