# TauPOG-recommonded tau corrections

This repository contains the scale factors (SFs) and energy scales recommended by the TauPOG.
More detailed recommendations can be found on this TWiki page: https://twiki.cern.ch/twiki/bin/viewauth/CMS/TauIDRecommendationForRun2


## Summary of available SFs

This is a rough summary of the available SFs for `DeepTau2017v2p1`:

| Tau component  | `genmatch`  | `DeepTau2017v2p1` `VSjet`  | `DeepTau2017v2p1` `VSe`  | `DeepTau2017v2p1` `VSmu`  | energy scale   |
|:--------------:|:-----------:|:--------------------------:|:------------------------:|:-------------------------:|:--------------:|
| real tau       | `5`         | vs. pT, or vs. DM          | – (*)                    | – (*)                     | vs. DM         |
| e -> tau fake  | `1`, `3`    | –                          | vs. eta                  | –                         | vs. DM and eta |
| mu -> tau fake | `2`, `4`    | –                          | –                        | vs. eta                   | – (±1% unc.)   |

(*) An extra uncertainty is recommended if you use a different working point (WP) combination than was used to measure the SFs,
see the [TWiki](https://twiki.cern.ch/twiki/bin/viewauth/CMS/TauIDRecommendationForRun2).

The gen-matching is defined as:
* `1` for prompt electrons
* `2` for prompt muons
* `3` for electrons from tau decay
* `4` for muons from tau decay
* `5` for real taus
* `6` for no match, or jets faking taus.
For more info on gen-matching of taus, please see [here](https://twiki.cern.ch/twiki/bin/viewauth/CMS/HiggsToTauTauWorking2016#MC_Matching).
Note that in nanoAOD this is available as `Tau_GenPartFlav`, but jet or no match correspond to `Tau_GenPartFlav==0` instead of `6`.

The SFs are meant for the following campaigns:

| Year label   | MC campaign              | Data campaign           |
|:------------:|:------------------------:| :----------------------:|
| `2016Legacy` | `RunIISummer16MiniAODv3` | `17Jul2018`             |
| `2017ReReco` | `RunIIFall17MiniAODv2`   | `31Mar2018`             |
| `2018ReReco` | `RunIIAutumn18MiniAOD`   | `17Sep2018`/`22Jan2019` |


## Usage

Please install the [`correctionlib`](https://github.com/cms-nanoAOD/correctionlib) tool to read these SFs.
There are several ways to install, but the best way is via `python3`, for example,
```
source /cvmfs/sft.cern.ch/lcg/views/LCG_99/x86_64-centos7-gcc8-opt/setup.sh
git clone --recursive https://github.com/cms-tau-pog/correctionlib.git
cd correctionlib
python3 -m pip install .
python3 -c 'import correctionlib._core; import correctionlib.schemav2' # test
```
Find out the content of the `tau.json` using
```
gunzip POG/TAU/2018_ReReco/tau.json.gz
correction summary POG/TAU/2018_ReReco/tau.json
```
An example is given in [`examples/tauExample.py`](../../examples/tauExample.py).
You can load the set of corrections as follows in python as
```
import correctionlib as _core
cset = _core.CorrectionSet.from_file("tau.json")
corr1 = cset["DeepTau2017v2p1VSjet"]
corr2 = cset["DeepTau2017v2p1VSe"]
corr3 = cset["tau_trigger"]
corr4 = cset["tau_energy_scale"]
```
And then on an event-by-event basis with reconstructed tau objects, you can do
```
sf1 = corr1.evaluate(pt,dm,genmatch,wp,syst,"pt")
sf2 = corr2.evaluate(eta,genmatch,wp,syst)
sf3 = corr3.evaluate(pt,dm,"etau",wp,"sf",syst)
tes = corr4.evaluate(pt,eta,dm,genmatch,"DeepTau2017v2p1",syst)
```
Where `syst='nom'`, `'up'` or  `'down'`.
A C++ example can be found [here](https://github.com/cms-nanoAOD/correctionlib/blob/master/src/demo.cc).

Alternative way to load the JSON files (including gunzip'ed):
```
import correctionlib as _core
fname = "tau.json.gz"
if fname.endswith(".json.gz"):
  import gzip
  with gzip.open(fname,'rt') as file:
    data = file.read().strip()
  cset = _core.CorrectionSet.from_string(data)
else:
  cset = _core.CorrectionSet.from_file(fname)
```


## References

The TauPOG JSON files are created from https://github.com/cms-tau-pog/correctionlib
