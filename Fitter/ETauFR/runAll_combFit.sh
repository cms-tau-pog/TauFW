#! /bin/sh

wp=$1
era=$2

##wps are VVLoose, Medium, Tight
echo ${wp}
##eta regions are barrel (0to1.46) and endcap (1.56to2.5)
etas=("0to1.46" , "1.56to2.5")
##dms
dms=("0","1","10","11")
##eras 
echo ${era}


for eta in ${etas[*]}; do
    for dm in ${dms[*]}; do
        #run Impacts and postfit 
        bash doFitsAndImpacts_combFit.sh ${wp} $eta ${era} $dm
        cd -
    done
done
    
python3 ./Plotter/plotpostfit.py -c et -y ${era} -wp ${wp}
