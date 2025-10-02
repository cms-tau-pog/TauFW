#!/bin/bash
era=$1
WP=$2
folder=/afs/cern.ch/work/r/rasp/public/HighPT_v2/datacards
cd ${folder}
combineTool.py -M T2W -o "ws.root" -i tauID_${WP}_${era}.txt -m 200
combineTool.py -M Impacts -d ws.root -m 200 --robustFit 1 --doInitialFit
combineTool.py -M Impacts -d ws.root -m 200 --robustFit 1 --doFits
combineTool.py -M Impacts -d ws.root -m 200 -o impacts.json
plotImpacts.py -i impacts.json -o impacts
cd -
