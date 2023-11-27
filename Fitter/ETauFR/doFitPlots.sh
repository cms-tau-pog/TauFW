#! /bin/sh

wp=$1
eta=$2
era=$3

##wps are VVLoose, Medium, Tight
echo ${wp}
##eta regions are barrel (0to1.46) and endcap (1.56to2.3.)
echo ${eta}
##eras are UL2016, UL2017, UL2018
echo ${era}

LAUNCH_FOLDER="./output/${era}/ETauFR/"

cd ${LAUNCH_FOLDER}
 
combine -m 90  -M FitDiagnostics --robustFit=1 --expectSignal=1.0 --rMin=0.1 --rMax=1. --cminFallbackAlgo "Minuit2,0:1" -n ${wp}_${eta} ../../../input/${era}/ETauFR/WorkSpace${wp}_eta${eta}.root --cminDefaultMinimizerStrategy 1    #--setParameterRanges shape_fes=-2,2 

PostFitShapesFromWorkspace -o ETauFR${wp}_eta${eta}_PostFitShape.root -m 90 -f fitDiagnostics${wp}_${eta}.root:fit_s --postfit --sampling --print -d ../../../input/${era}/ETauFR/${wp}_eta${eta}.txt -w ../../../input/${era}/ETauFR/WorkSpace${wp}_eta${eta}.root
