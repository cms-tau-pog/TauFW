#! /bin/sh

wp=$1
eta=$2
era=$3

##wps are VVLoose, Medium, Tight
echo ${wp}
##eta regions are barrel (0to1.46) and endcap (5.6to2.3.)
echo ${eta}
##eras are UL2016, UL2017, UL20.
echo ${era}

LAUNCH_FOLDER="./output/${era}/ETauFR/"

cd ${LAUNCH_FOLDER}

#1st step
combineTool.py -m 90  -M Impacts --doInitialFit --robustFit=1 --expectSignal=1.0 --rMin=0.5 --rMax=2.0 -d ../../../input/${era}/ETauFR/WorkSpace${wp}_eta${eta}.root --name ${wp}_eta${eta} --cminDefaultMinimizerStrategy 1 --redefineSignalPOIs r,fes --saveFitResult

##2nd step
combineTool.py -m 90  -M Impacts  --robustFit=1 --doFits --expectSignal=1.0 --rMin=0.5 --rMax=2.0 -d ../../../input/${era}/ETauFR/WorkSpace${wp}_eta${eta}.root --name ${wp}_eta${eta} --cminDefaultMinimizerStrategy 1 --redefineSignalPOIs r,fes

##3rd step
combineTool.py -m 90  -M Impacts  -o impacts_${wp}_eta${eta}.json --expectSignal=1.0 --rMin=0.5 --rMax=2.0 -d ../../../input/${era}/ETauFR/WorkSpace${wp}_eta${eta}.root --name ${wp}_eta${eta} --cminDefaultMinimizerStrategy 1 --redefineSignalPOIs r,fes

##plot
plotImpacts.py -i impacts_${wp}_eta${eta}.json -o impacts_${wp}_eta${eta}_fes --POI fes
plotImpacts.py -i impacts_${wp}_eta${eta}.json -o impacts_${wp}_eta${eta}_r --POI r 

##Postfit
PostFitShapesFromWorkspace -o ETauFR${wp}_eta${eta}_PostFitShape.root -m 90 -f multidimfit_initialFit_${wp}_eta${eta}.root:fit_mdf --postfit --sampling --print -d ../../../input/${era}/ETauFR/${wp}_eta${eta}.txt -w ../../../input/${era}/ETauFR/WorkSpace${wp}_eta${eta}.root
