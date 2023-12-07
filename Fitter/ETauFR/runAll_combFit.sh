#! /bin/sh

wp=$1
era=$2

##wps are VVLoose, Medium, Tight
echo ${wp}
##eta regions are barrel (0to1.46) and endcap (1.56to2.3)
etas=("0to1.46" , "1.56to2.3")
##eras are UL2016, UL2017, UL2018
echo ${era}

#for eta in ${etas[*]}; do
#    #run Impacts
#    bash doFitsAndImpacts_combFit.sh ${wp} $eta ${era}
#    cd -
#done
    
python ./Plotter/plotpostfit.py -c et -y ${era} -wp ${wp}
