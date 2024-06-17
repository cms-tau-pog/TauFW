# JetMET POG-recommended corrections

This repository contains the scale factors (SFs) for heavy object tagging, PUJetID and Quark-Gluon tagging and jet energy corrections and resolutions recommended by the JetMET POG.
More detailed recommendations can be found on this TWiki page: https://twiki.cern.ch/twiki/bin/viewauth/CMS/JetMET#Quick_links_to_current_recommend

The exact mapping for **JEC and JER** versions is available from https://twiki.cern.ch/twiki/bin/viewauth/CMS/JECDataMC and https://twiki.cern.ch/twiki/bin/view/CMS/JetResolution#JER_Scaling_factors_and_Uncertai
For the JERC-part we currently provide
- single jet energy correction levels (L1Fastjet, L2Relative, L3Absolute, L2L3Residual)
- convenience "compound" correction level available as L1L2L3Res (combining all levels listed above)
- All uncertainty sources as detailed in https://twiki.cern.ch/twiki/bin/view/CMS/JECUncertaintySources (as of now the full set, not the reduced set)
- Jet resolution scale factors + systematics ("nom","up","down") (as of now only for AK4)
- Jet pt resolution parametrisations (as of now only for AK4)

The .json files are split into YEAR_jmar.json for tagging SFs and \[jet/fatJet\]_jerc.json.gz for jet energy corrections/resolutions.
- Run2: jet\~"AK4PFchs"; fatJet\~"AK8PFPuppi"
- Run3: jet\~"AK4PFPuppi"; fatJet\~"AK8PFPuppi"

The SFs are meant for the following campaigns:

| Year folder   | MC campaign              | Data campaign           |
|:------------:|:------------------------:| :----------------------:|
| `2016_EOY` | `RunIISummer16MiniAODv3` | `17Jul2018`             |
| `2017_EOY` | `RunIIFall17MiniAODv2`   | `31Mar2018`             |
| `2018_EOY` | `RunIIAutumn18MiniAOD`   | `17Sep2018`/`22Jan2019` |
| `2016preVFP_UL`| `RunIISummer20UL16MiniAODAPVv2` |`21Feb2020`|
| `2016postVFP_UL`| `RunIISummer20UL16MiniAODv2` |`21Feb2020`|
| `2017_UL`| `RunIISummer20UL17MiniAODv2` |`09Aug2019`|
| `2018_UL`| `RunIISummer20UL18MiniAODv2` |`12Nov2019`|
| `2022_Prompt` | Winter22 | Prompt RunCDE |
| `2022_Summer22` | Summer22 | `22Sep2023` (ReReco CD) |
| `2022_Summer22EE` | Summer22EE | `22Sep2023` (ReReco E + Prompt RunFG, with EE leak region vetoed) |
| `2023_Summer23` | Summer23 | Prompt23 RunC (divided into Cv123 and Cv4) |
| `2023_Summer23BPix` | Summer23BPix | Prompt23 RunD |


## Usage

Please install the [`correctionlib`](https://github.com/cms-nanoAOD/correctionlib) tool to read these SFs.
Find out the content of the `jmar.json` using
```
gunzip POG/JME/2017_EOY/2017_jmar.json.gz
correction summary POG/JME/2017_EOY/jmar.json
```
Example:

📈 DeepAK8_W_Nominal (v1)                                                                       
│   Scale factor for DeepAK8 algorithm (nominal and mass decorrelated) for particle W               
│   Node counts: Category: 4, Binning: 24                                                           
│   ╭──────────────────────â───── ▶ input ─────────────────────────────╮                            
│   │ eta (real)                                                       │                            
│   │ eta of the jet                                                   │                            
│   │ Range: [-2.4, 2.4)                                               │                            
│   ╰──────────────────────────────────────────────────────────────────╯                            
│   ╭──────────────────────────── ▶ input ─────────────────────────────╮                            
│   │ pt (real)                                                        │                            
│   │ pT of the jet                                                    │                            
│   │ Range: [200.0, 800.0), overflow ok                               │                            
│   ╰──────────────────────────────────────────────────────────────────╯                            
│   ╭──────────────────────────── ▶ input ─────────────────────────────╮                            
│   │ systematic (string)                                              │                            
│   │ systematics: nom, up, down                                       │                            
│   │ Values: down, nom, up                                            │                            
│   ╰â─────────────────────────────────────────────────────────────────╯                            
│   ╭──────────────────────────── ▶ input ─────────────────────────────╮                            
│   │ workingpoint (string)                                            │                            
│   │ Working point of the tagger you use (QCD misidentification rate) │                            
│   │ Values: 0p5, 1p0, 2p5, 5p0                                       │                            
│   ╰──────────────────────────────────────────────────────────────────╯                            
│   ╭â── ◀ output ───╮                                                                              
│   │ weight (real)  │                                                                              
│   │ No description │                                                                              
│   ╰────────────────╯                                               

Examples how to evaluate are given in [`examples/jmarExample.py`](../../examples/jmarExample.py) and [`examples/jercExample.py`](../../examples/jercExample.py).
You can load the set of corrections as follows in python as
```
from correctionlib import _core

evaluator = _core.CorrectionSet.from_file('2017_jmar.json')

valsf= evaluator["DeepAK8_Top_Nominal"].evaluate(eta, pt, syst, wp)
```

Where `syst='nom'`, `'up'` or  `'down'`.
All maps available and the corresponding input parameters can be seen by using the 'correction summary' option mentioned before.

## MET Phi Corrections
The UL Run II MET Phi Corrections from https://lathomas.web.cern.ch/lathomas/METStuff/XYCorrections/XYMETCorrection_withUL17andUL18andUL16.h can now be used with the correctionlib. This implementation was validated against the CMSSW implementation and an independent implementation of these corrections.

The corrections depend on the pt and phi of the phi-uncorrected MET, the number of reconstructed primary vertices, and for data also on the run number. To have a similar call method, the call for simulation also expects a run number but this is not used in any way. The inputs can either all be provided as single numbers or as arrays of similar length. The data type for all inputs is (due to technical reasons) currently 'float'. The call to the evaluate methods returns always the corrected quantity i.e. the corrected pt(s) or the corrected phi(s).

One can load the correction and get the corrected quantities e.g. via
```
# met_pt: float value or array of phi-uncorrected pt(s) of MET
# met_phi: float value or array of phi-uncorrected phi(s) of MET
# npvs: float value or array of number of reconstructed vertices
# run: float value or array of run numbers (is needed for data and simulation, but will be ignored for simulation)
ceval = correctionlib.CorrectionSet.from_file("2018_UL/met.json.gz")
# simulation
# phi-corrected pts
corrected_pts = ceval["pt_metphicorr_pfmet_mc"].evaluate(met_pt,met_phi,npvs,run)
# phi-corrected phis
corrected_phis = ceval["phi_metphicorr_pfmet_mc"].evaluate(met_pt,met_phi,npvs,run)
# data
# phi-corrected pts
corrected_pts = ceval["pt_metphicorr_pfmet_data"].evaluate(met_pt,met_phi,npvs,run)
# phi-corrected phis
corrected_phis = ceval["phi_metphicorr_pfmet_data"].evaluate(met_pt,met_phi,npvs,run)
```

An example script loading and applying the corrections can be found in `examples/metPhiCorrectionExample.py`. The inputs in this example are randomly drawn numbers so the 'corrected' distributions should not be taken too seriously.
## References

The JMAR POG JSON files are created from https://github.com/cms-jet/JSON_Format
The JERC POG JSON files are created from https://github.com/cms-jet/JECDatabase/tree/master/scripts/JERC2JSON
