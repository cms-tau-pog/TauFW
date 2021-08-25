#! /bin/bash
# modify the tags to decide the work need to perform
# usage: source doTES.sh 2016

DMS="DM0 DM1 DM10 DM11"
VARS="m_vis m_2"
YEAR=$1
NPOINTS="31"
RANGE="0.970,1.030"
TAG="_mtlt50"
EXTRATAG="_DeepTau"
ALGO="--algo=grid --points ${NPOINTS} --alignEdges=1" # --saveWorkspace --saveFitResult
FIT_OPTS="--robustFit=1 --setRobustFitAlgo=Minuit2 --setRobustFitStrategy=0 --setRobustFitTolerance=0.2" #--preFitValue=1. 
POI_OPTS="-P tes --setParameterRanges tes=${RANGE} -m 90 --setParameters r=1 --freezeParameters r" 
XRTD_OPTS="--X-rtd FITTER_NEW_CROSSING_ALGO --X-rtd FITTER_NEVER_GIVE_UP --X-rtd FITTER_BOUND" #--X-rtd FITTER_DYN_STEP
#CMIN_OPTS="" # --cminPreFit 1 --cminOldRobustMinimize 0"      
CMIN_OPTS="--cminFallbackAlgo Minuit2,Migrad,0:0.5 --cminFallbackAlgo Minuit2,Migrad,0:1.0 --cminPreScan" # --cminPreFit 1 --cminOldRobustMinimize 0"      
WORKDIR="${CMSSW_BASE}/src/TauFW/Fitter/analysis/TauES"
OUTDIR="${WORKDIR}/output_${YEAR}"
PULL="${CMSSW_BASE}/src/HiggsAnalysis/CombinedLimit/test/diffNuisances.py"
PULLS="${CMSSW_BASE}/src/TauFW/Fitter/scripts/pulls.py"
#CHECKS="1.020"
CHECKS="0.990 1.000 1.010 "

##### tags #####
doDataCard=1
doWorkSpace=1
doNLLScan=1
doPull=1
doPostFit=1
doParabola=1

function main {
  
  cd ${WORKDIR}
  echo "working with YEAR ${YEAR}"
  ensureDir "log_$YEAR"
  ensureDir "postfit_$YEAR"
  ensureDir "output_$YEAR"
  echo

  #################### make datacard ######################### NOTE: modify the STEPS within harvestDatacards_TES.py according to the NPOINTS
  if [ $doDataCard -gt 0 ]; then
    peval "cd ${WORKDIR}"
    peval "python ./harvestDatacards_TES.py --shift-range ${RANGE} -y $YEAR -o m_vis -d DM0 DM1 DM10 DM11 --tag $TAG -e $EXTRATAG "
    peval "python ./harvestDatacards_TES.py --shift-range ${RANGE} -y $YEAR -o m_2 -d DM1 DM10 DM11 --tag $TAG -e $EXTRATAG "
  fi
  
  for DM in $DMS; do
    echo $DM
    for var in $VARS; do
      [ $var == 'm_2' -a $DM = 'DM0' ] && continue

      ################ common files ##########################

      BINLABEL="mt_${var}-${DM}${TAG}${EXTRATAG}-${YEAR}-13TeV"
      WORKSPACE="ztt_${BINLABEL}.root" 
      IMPA_NAME="impacts_${BINLABEL}"
      OUTPUT_IMPA="${IMPA_NAME}.json"
      DATACARD="ztt_${BINLABEL}.txt"
      LOG="log_$YEAR/ztt_${BINLABEL}.log" 

      ################ produce workspace #####################
      if [ $doWorkSpace -gt 0 ]; then
        peval "cd ${OUTDIR}"
        peval "text2workspace.py ${DATACARD} -o ${WORKSPACE}" 2>&1 | tee -a ../$LOG || exit 1
      fi
  
      ################ NLL profile scan ######################
      if [ $doNLLScan -gt 0 ]; then
        peval "cd ${OUTDIR}"
        peval "combine -M MultiDimFit ${WORKSPACE} ${ALGO} ${POI_OPTS} -n .${BINLABEL} ${FIT_OPTS} ${XRTD_OPTS} ${CMIN_OPTS} --saveNLL --saveSpecifiedNuis all" 2>&1 | tee -a ../$LOG || exit 1
      fi
  
      ################ make pull plots #######################
      if [ $doPull -gt 0 ]; then
        peval "cd ${OUTDIR}"
        peval "combineTool.py -M Impacts -n $BINLABEL -d $WORKSPACE $FIT_OPTS --points ${NPOINTS} --redefineSignalPOIs tes $POI_OPTS $XRTD_OPTS $CMIN_OPTS --doInitialFit" 2>&1 | tee -a ../$LOG || exit 1
        peval "combineTool.py -M Impacts -n $BINLABEL -d $WORKSPACE $FIT_OPTS --points ${NPOINTS} --redefineSignalPOIs tes $POI_OPTS $XRTD_OPTS $CMIN_OPTS --doFits --parallel 4" 2>&1 | tee -a ../$LOG || exit 1
        peval "combineTool.py -M Impacts -n $BINLABEL -d $WORKSPACE $FIT_OPTS --points ${NPOINTS} --redefineSignalPOIs tes $POI_OPTS $XRTD_OPTS $CMIN_OPTS -o $OUTPUT_IMPA" 2>&1 | tee -a ../$LOG || exit 1
        peval "plotImpacts.py -i $OUTPUT_IMPA -o ../postfit_${YEAR}/$IMPA_NAME" 2>&1 | tee -a ../$LOG || exit 1
        peval "convert -density 160 -trim ../postfit_${YEAR}/${IMPA_NAME}.pdf[0] -quality 100 ../postfit_${YEAR}/${IMPA_NAME}.png" 2>&1 | tee -a ../$LOG || exit 1
      fi
  
      ################ Post-fit ##############################
      if [ $doPostFit -gt 0 ]; then
        for tes in $CHECKS; do  
          [[ $tes == "#"* ]] && continue
          header "Post-fit check for var $var for $DM in TES point $tes"
  
          POI_OPTS2="--setParameters tes=${tes} --freezeParameters tes --rMin 0.9999 --rMax 1.0001 -m 90" #--rMin 1 --rMax 1
          PVAL=`percentage $tes`
          TESLABEL=`echo "_TES${tes}" | sed 's/\./p/'`
          DMLABEL=`latexDM $DM`
          TESTAG="$tag$EXTRATAG$TESLABEL"
          BINLABELT="${BINLABEL}${TESLABEL}"
          FITDIAGN="fitDiagnostics.${BINLABELT}.root"
          SHAPES="ztt_${BINLABELT}.shapes.root"
          OUTDIR_PF="postfit_"${YEAR}
          LOGT="postfit_"${YEAR}"/ztt_${BINLABELT}.log"
          PULLT="${OUTDIR_PF}/pulls_${BINLABELT}.txt"
          peval "cd ${OUTDIR}"
          echo `date` > ../$LOGT
        
        ################ COMBINE FIT ##########################
          peval "combine -M FitDiagnostics -n .$BINLABELT $WORKSPACE $POI_OPTS2 $FIT_OPTS $XRTD_OPTS $CMIN_OPTS --saveShapes" 2>&1 | tee -a ../$LOGT || exit 1
        
        ################ POSTFIT SHAPES #######################
          echo
          peval "PostFitShapesFromWorkspace -o $SHAPES -f ${FITDIAGN}:fit_s --postfit --freeze tes=$tes --sampling --print -d $DATACARD -w $WORKSPACE" 2>&1 | tee -a ../$LOGT || exit 1
        
        ################ DRAW #################################
          peval "cd ${WORKDIR}"
          peval "python checkShapes_TES.py $OUTDIR/$SHAPES --postfit --pdf --out-dir $OUTDIR_PF --dirname $DM -t $TESTAG -y ${YEAR}" 2>&1 | tee -a $LOGT || exit 1
        
        ################ PULLS ################################
          echo
          peval "python $PULL --vtol=0.0001 $OUTDIR/$FITDIAGN | sed 's/[!,]/ /g' | tail -n +3 > $PULLT" 2>&1 | tee -a $LOGT || exit 1
          peval "python $PULLS -b -f $PULLT -o ${OUTDIR_PF}/pulls_${BINLABELT} -t '$var, $DMLABEL, $PVAL TES'" 2>&1 | tee -a $LOGT || exit 1
        
        done
      fi
    done
  done
  
  #################### fit with parabola and plot scan ######
  if [ $doParabola -gt 0 -a $doPostFit -gt 0 ]; then
    peval "cd $WORKDIR"
    for var in $VARS; do
      peval "python plotParabola_TES.py -y $YEAR -t $TAG -d $DMS -e $EXTRATAG -a -o $var -r $RANGE" 2>&1 | tee -a $LOG #|| exit 1
      peval "python plotParabola_TES.py -y $YEAR -t $TAG -d $DMS -e $EXTRATAG -r $RANGE -s" 2>&1 | tee -a $LOG #|| exit 1
      peval "python plotPostFitScan_TES.py -y $YEAR -t $TAG -d $DMS -e $EXTRATAG -o $var -r $RANGE" 2>&1 | tee -a $LOG #|| exit 1
    done
  fi

  #################### plot the final results (un-comment the finalCalculation() line in plotParabola_TES.py and update the values from previous fit by hand) #####
  if [ $doParabola -gt 0 -a $doPostFit == 0 ]; then
    peval "cd $WORKDIR"
    for var in $VARS; do
      peval "python plotParabola_TES.py -y $YEAR -t $TAG -d $DMS -e $EXTRATAG -r $RANGE -s" 2>&1 | tee -a $LOG #|| exit 1
    done
  fi

}

function latexDM {
  case "$@" in
    'DM0')  echo "h^{#pm}";;
    "DM1")  echo "h^{#pm}#pi^{0}";;
    "DM10") echo "h^{#pm}h^{#mp}h^{#pm}";;
    'DM11') echo "h^{#pm}h^{#mp}h^{#pm}#pi^{0}";;
    "MDF")  echo "DMs combined";;
  esac;
}

function percentage { # print tes value as percentage
  printf "%+f%%" `echo "($1-1)*100" | bc` | sed 's/\.*0*%/%/';
}

function header { # print box around given string
  local HDR="$@"
  local BAR=`printf '#%.0s' $(seq 1 ${#HDR})`
  printf "\n\n\n"
  echo ">>>     $A####${BAR}####$E"
  echo ">>>     $A#   ${HDR}   #$E"
  echo ">>>     $A####${BAR}####$E"
  echo ">>> ";
}

function peval { # print and evaluate given command
  echo -e ">>> $(tput setab 0)$(tput setaf 7)$@$(tput sgr0)"
  eval "$@";
}

function ensureDir {                                                                                                                                                              
  [ -e "$1" ] || { echo ">>> making $1 directory..."; mkdir "$1"; }
}

function runtime {                                                                                                                                                                
  END=`date +%s`; RUNTIME=$((END-START))
  printf "%d minutes %d seconds" "$(( $RUNTIME / 60 ))" "$(( $RUNTIME % 60 ))"
}

main
echo ">>> "
echo ">>> ${A}done fitting in $(runtime)$E"
echo

