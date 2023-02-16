# Measurement of DeepTauVSjet efficiency SFs

## 1. Create mutau & dimuon pico files
E.g.
```
cd PicoProducer/
pico.py submit -c mutau mumu -y UL2018
pico.py hadd -c mutau mumu -y UL2018
```

## 2. Create histogram inputs
Create histograms
- mutau: `mvis` in the "Pass" region of some DeepTau WP
- mumu: one-bin `mvis` histogram to control the overall DY cross section, which is kept floating.
```
./createinputs.py -c mutau
./createinputs.py -c mumu
```

## 3. Install tensorflow
We use a tensor-flow version of combine, because there were some issues with the default combine tool when including the mumu channel.
This was likely caused by the large number of events in the single-bin mumu histogram.
```
cmsrel CMSSW_10_3_0_pre2
cd CMSSW_10_3_0_pre2/src
cmsenv
git clone https://github.com/bendavid/HiggsAnalysis-CombinedLimit/ HiggsAnalysis/CombinedLimit
cd HiggsAnalysis/CombinedLimit
git fetch origin
git checkout tensorflowfit
scram b -j8
```

Usage is for example:
```
text2hdf5.py mydatacard.txt -m 90 -o mydatacard.hdf5
combinetf.py mydatacard.hdf5 --binByBinStat --output fitresults.root
```

## 4. Create cards
Use the Combine Harvester:
```
python harvestcards.py input/ztt_tid_mvis_pt30to35_mt-UL2018.inputs.root input/ztt_tid_mvis_mm-UL2018.inputs.root -y UL2018 -w Tight -t _pt30to35 -v 1
python harvestcards.py input/ztt_tid_mvis_dm1_mt-UL2018.inputs.root input/ztt_tid_mvis_mm-UL2018.inputs.root -y UL2018 -w Tight -t _dm1 -v 1
```

## 5. Run combine
The script `fit.sh` creates the datacards for you and runs combine:
```
./fit.sh -y UL2018 -w Tight
./fit.sh -y UL2016_preVFP,UL2016_postVFP,UL2017,UL2018 -w Loose,Medium,Tight
```

## 6. Plot & create ROOT files
if the fit was succesful, use
```
./read.py
./read_dm.py
```


## References
Yuta's presentation: https://indico.cern.ch/event/847119/#13-tau-id-scale-factor-for-dee