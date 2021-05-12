#! /bin/bash
# Author: Izaak Neutelings (Februari 2021)
START=`date +%s`

# SET INPUT
ANALYSIS="ztt_tid" # process
CHANNELS="mt"      # channels
ERA="2017"         # era/year
OBSSET="mvis"      # observables
MASS="90"          # Z boson mass (when needed for combine)
BINS="Tight"       # category bins

# USER INPUT
VERBOSITY=0
POSTFIT=0
HARVESTER=1
while getopts "bc:ho:t:vy:" option; do case "${option}" in
  b) BINS=1;;
  c) CHECKS=${OPTARG//,/ };;
  h) HARVESTER=0;;
  o) OBSSET=${OPTARG};;
  t) TAG=${OPTARG//,/ };;
  v) VERBOSITY=1;;
  y) ERA=${OPTARG};;
esac done

# OPTIONS
set -o pipefail # for exit after tee
OBSSET=`echo $OBSSET | grep -Po '\b(?<!#)\w+\b' | xargs`
FIT_OPTS="--expectSignal=1 --robustFit=1 --setRobustFitAlgo=Minuit2 --setRobustFitStrategy=0 --setRobustFitTolerance=0.2" #--preFitValue=1.
XRTD_OPTS="--X-rtd FITTER_NEW_CROSSING_ALGO --X-rtd FITTER_NEVER_GIVE_UP --X-rtd FITTER_BOUND" #--X-rtd FITTER_DYN_STEP
CMIN_OPTS="--cminFallbackAlgo Minuit2,0:0.5 --cminFallbackAlgo Minuit2,0:1.0 --cminPreScan --cminPreFit 1" # --cminPreFit 1 --cminOldRobustMinimize 0"
PULL="$CMSSW_BASE/src/HiggsAnalysis/CombinedLimit/test/diffNuisances.py" # to compute pulls
source ../utils/tools.sh # import helper functions; ensureDir, header, ...
ensureDir "log/$ERA"
ensureDir "output/$ERA"

# HARVEST
if [ $HARVESTER -gt 0 ]; then
  header "Harvest datacards"
  peval "python writecards.py -o $OBSSET -c $CHANNELS -y $ERA" || exit 1
fi
cd "output/$ERA"

# LOOP over CHANNELS
for obs in $OBSSET; do
  [[ $obs == "#"* ]] && continue
  for channel in $CHANNELS; do
    [[ $channel == "#"* ]] && continue
    
    # LOOP over BINS (categories)
    for bin in $BINS; do
      [[ $bin == "#"* ]] && continue
      
      header "$obs, $channel, $bin, $ERA"
      
      # INPUT
      BINLABEL="${obs}_${channel}-${bin}-${ERA}${TAG}"
      DATACARD="${ANALYSIS}_${BINLABEL}.datacard.txt"
      WORKSPACE="${ANALYSIS}_${BINLABEL}.workspace.root"
      FITDIAGN="fitDiagnostics.${BINLABEL}.root"
      SHAPES="${ANALYSIS}_${BINLABEL}.shapes.root"
      LOG="../../log/$ERA/${ANALYSIS}_${BINLABEL}.log"
      echo `date` > $LOG
      
      # DO FIT
      peval "text2workspace.py $DATACARD -o $WORKSPACE -m 90" 2>&1 | tee -a $LOG || exit 1
      peval "combine -M FitDiagnostics -n .$BINLABEL $WORKSPACE -m $MASS $FIT_OPTS $XRTD_OPTS $CMIN_OPTS" 2>&1 | tee -a $LOG || exit 1
      echo
      peval "PostFitShapesFromWorkspace -o $SHAPES -f ${FITDIAGN}:fit_s --postfit --sampling --print -d $DATACARD -w $WORKSPACE -m $MASS" 2>&1 | tee -a $LOG || exit 1
      
      ## PULLS
      #peval "python $PULL --poi r --vtol=0.1 output/$FITDIAGN | sed 's/[!,]/ /g' | tail -n +4 > $PULLST" 2>&1 | tee -a $LOG || exit 1 
      #peval "pulls.py -b -f $PULLST -o plots/pulls_${BINLABEL}-${mass} -t '$bin, $mass GeV'" 2>&1 | tee -a $LOG || exit 1 
      
    done
  done
done

echo ">>> Done fitting in $(runtime)"
exit 0
