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
```
...
```

## 5. Run combine
```
./fit.sh
```

## References
Yuta's presentation: https://indico.cern.ch/event/847119/#13-tau-id-scale-factor-for-dee