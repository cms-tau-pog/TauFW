# PicoProducer sample lists

All sample lists are stored here as python modules that contain a python list with
[`Sample`](../python/storage/Sample.py) objects. For more information on sample lists,
please refer to the [README in the parent directory](../#Samples).

## Linking an era to a sample list
To link an era to your favorite sample list in `samples/`, do
```
pico.py era 2016 sample_2016.py
```
or more convenient, using tab completion,
```
pico.py era 2016 samples/sample_2016.py
```
You can also make your own subdirectory in `samples/` and do for example
```
pico.py era 2016 samples/examples/sample_2016.py
```
