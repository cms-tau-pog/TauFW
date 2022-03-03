DMS="DM0 DM1 DM10 DM11"
VARS="m_vis m_2"
YEAR="UL2018"
NPOINTS="41"
RANGE="0.970,1.030"
TAG="_mtlt50"
EXTRATAG="_DeepTau"
ALGO="--algo=grid --points ${NPOINTS} --alignEdges=1 --saveFitResult" # --saveWorkspace 
FIT_OPTS="--robustFit=1 --setRobustFitAlgo=Minuit2 --setRobustFitStrategy=0 --setRobustFitTolerance=0.2" #--preFitValue=1. 
POI_OPTS="-P tes --setParameterRanges tes=${RANGE} -m 90 --setParameters r=1 --freezeParameters r" 
XRTD_OPTS="--X-rtd FITTER_NEW_CROSSING_ALGO --X-rtd FITTER_NEVER_GIVE_UP --X-rtd FITTER_BOUND" #--X-rtd FITTER_DYN_STEP
CMIN_OPTS="--cminFallbackAlgo Minuit2,Migrad,0:0.5 --cminFallbackAlgo Minuit2,Migrad,0:1.0 --cminPreScan" # --cminPreFit 1 --cminOldRobustMinimize 


./TauES/harvestDatacards_TES.py -y $YEAR -t "_mtlt50" -e "_DeepTau" -c $1

for DM in $DMS; do
    echo $DM
    for var in $VARS; do

	BINLABEL="mt_${var}-${DM}${TAG}${EXTRATAG}-${YEAR}-13TeV"

	text2workspace.py output_UL2018/ztt_${BINLABEL}.txt

	WORKSPACE="output_UL2018/ztt_${BINLABEL}.root" 

	combine -M MultiDimFit  ${WORKSPACE} ${ALGO} ${POI_OPTS} -n .${BINLABEL} ${FIT_OPTS} ${XRTD_OPTS} ${CMIN_OPTS} --saveNLL --saveSpecifiedNuis all

    done
done

mv higgsCombine*root output_UL2018

./TauES/plotParabola_TES.py -y $YEAR -t $TAG -e $EXTRATAG -r $RANGE -a -s -c $1
