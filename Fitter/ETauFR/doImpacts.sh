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

##1st step
combineTool.py -m 90  -M Impacts --doInitialFit --robustFit=1 --expectSignal=1.0 --rMin=0.1 --rMax=2.0 -d ../../../input/${era}/ETauFR/WorkSpace${wp}_eta${eta}.root --name ${wp}_eta${eta} --cminDefaultMinimizerStrategy 0 #--setParameterRanges shape_fes=-2,2

##2nd step
combineTool.py -m 90  -M Impacts  --robustFit=1 --doFits --expectSignal=1.0 --rMin=0.1 --rMax=2.0 -d ../../../input/${era}/ETauFR/WorkSpace${wp}_eta${eta}.root --name ${wp}_eta${eta} --cminDefaultMinimizerStrategy 0 #--setParameterRanges shape_fes=-2,2

##3rd step
combineTool.py -m 90  -M Impacts  -o impacts_${wp}_eta${eta}.json --expectSignal=1.0 --rMin=0.1 --rMax=2.0 -d ../../../input/${era}/ETauFR/WorkSpace${wp}_eta${eta}.root --name ${wp}_eta${eta} --cminDefaultMinimizerStrategy 0  #--setParameterRanges shape_fes=-2,2

##plot
plotImpacts.py -i impacts_${wp}_eta${eta}.json -o impacts_${wp}_eta${eta} 
