#! /bin/sh
# Author: Paola Mastrapasqua (Feb 2024)
# Usage: bash ./doFitsAndImpacts.sh Medium 2018UL 0

wp=$1
era=$2
dm=$3

##wp is  Medium in this tutorial
echo ${wp}
##dms are 0 1 10 11
echo ${dm}
##eras
echo ${era}

###1st step
combineTool.py -m 90  -M Impacts --doInitialFit --robustFit=1 --expectSignal=1.0 --rMin=0.5 --rMax=1.5 -d ./cards/ztt_${wp}_${era}_dm${dm}.card.root --name ${wp}_${era}_dm${dm} --cminDefaultMinimizerStrategy 1 --redefineSignalPOIs r --saveFitResult

###2nd step
combineTool.py -m 90  -M Impacts  --robustFit=1 --doFits --expectSignal=1.0 --rMin=0.5 --rMax=1.5 -d ./cards/ztt_${wp}_${era}_dm${dm}.card.root --name ${wp}_${era}_dm${dm} --cminDefaultMinimizerStrategy 1 --redefineSignalPOIs r
 
##3rd step
combineTool.py -m 90  -M Impacts  -o impacts_${wp}_${era}_dm${dm}.json --expectSignal=1.0 --rMin=0.5 --rMax=1.5 -d ./cards/ztt_${wp}_${era}_dm${dm}.card.root --name ${wp}_${era}_dm${dm} --cminDefaultMinimizerStrategy 1 --redefineSignalPOIs r

##plot
plotImpacts.py -i impacts_${wp}_${era}_dm${dm}.json -o impacts_${wp}_${era}_dm${dm}_r --POI r 

#
###Postfit
PostFitShapesFromWorkspace --output ztt_${wp}_${era}_dm${dm}_PostFitShape.root -m 90 -f multidimfit_initialFit_${wp}_${era}_dm${dm}.root:fit_mdf --postfit --sampling --print -d ./cards/ztt_${wp}_${era}_dm${dm}.card.txt -w ./cards/ztt_${wp}_${era}_dm${dm}.card.root
