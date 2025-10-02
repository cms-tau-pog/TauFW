#! /bin/sh

wp=$1
eta=$2
era=$3
dm=$4

##wps are VVLoose, Medium, Tight
echo ${wp}
##eta regions are barrel (0to1.46) and endcap (5.6to2.3.)
echo ${eta}
##dms are 0 1 10 11
echo ${dm}
##eras
echo ${era}

LAUNCH_FOLDER="./output/${era}/ETauFR/"

cd ${LAUNCH_FOLDER}

#1st step
combineTool.py -m 90  -M Impacts --doInitialFit --robustFit=1 --expectSignal=1.0 --rMin=0.5 --rMax=1.5 -d ../../../input/${era}/ETauFR/WorkSpace${wp}_eta${eta}_dm${dm}.root --name ${wp}_eta${eta}_dm${dm} --cminDefaultMinimizerStrategy 1 --redefineSignalPOIs r,fes --saveFitResult #--setParameterRanges fes=0.9,1.1

###2nd step
combineTool.py -m 90  -M Impacts  --robustFit=1 --doFits --expectSignal=1.0 --rMin=0.5 --rMax=1.5 -d ../../../input/${era}/ETauFR/WorkSpace${wp}_eta${eta}_dm${dm}.root --name ${wp}_eta${eta}_dm${dm} --cminDefaultMinimizerStrategy 1 --redefineSignalPOIs r,fes #--setParameterRanges fes=0.9,1.1

##3rd step
combineTool.py -m 90  -M Impacts  -o impacts_${wp}_eta${eta}_dm${dm}.json --expectSignal=1.0 --rMin=0.5 --rMax=1.5 -d ../../../input/${era}/ETauFR/WorkSpace${wp}_eta${eta}_dm${dm}.root --name ${wp}_eta${eta}_dm${dm} --cminDefaultMinimizerStrategy 1 --redefineSignalPOIs r,fes #--setParameterRanges fes=0.9,1.1

##plot
plotImpacts.py -i impacts_${wp}_eta${eta}_dm${dm}.json -o impacts_${wp}_eta${eta}_dm${dm}_fes --POI fes
plotImpacts.py -i impacts_${wp}_eta${eta}_dm${dm}.json -o impacts_${wp}_eta${eta}_dm${dm}_r --POI r 
#
###Postfit
PostFitShapesFromWorkspace -o ETauFR${wp}_eta${eta}_dm${dm}_PostFitShape.root -m 90 -f multidimfit_initialFit_${wp}_eta${eta}_dm${dm}.root:fit_mdf --postfit --sampling --print -d ../../../input/${era}/ETauFR/${wp}_eta${eta}_dm${dm}.txt -w ../../../input/${era}/ETauFR/WorkSpace${wp}_eta${eta}_dm${dm}.root
