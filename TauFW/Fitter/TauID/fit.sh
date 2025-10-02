#! /bin/bash
# Author: Yuta Takahashi & Izaak Neutelings
START=`date +%s`
set -e # exit when command fails

# SETTINGS
#WPS="Loose Medium Tight"
WPS="VVVLoose VVLoose VLoose Loose Medium Tight VTight VVTight"
ERAS="#UL2016_preVFP #UL2016_postVFP #UL2017 UL2018"
PTBINS="20to25 25to30 30to35 35to40 40to50 50to70 70to2000"
DMBINS="0 1 10 11"
DCPATH="input" # datacard path
DOHARV=0
DOIMPACT=0
VERB=0 # verbosity

# COMMAND LINE SETTINGS
while getopts "hIp:v:w:y:" option; do case "${option}" in
  h) DOHARV=0;; # skip harvester step
  I) DOIMPACT=1;; # do impacts
  d) DMBINS="${OPTARG//,/ }";;
  p) PTBINS="${OPTARG//,/ }";;
  w) WPS="${OPTARG//,/ }";;
  v) VERB="$OPTARG";;
  y) ERAS="${OPTARG//,/ }";;
esac done

# FILTER ITEMS with '#'
ERAS=`echo $ERAS | sed -E 's/\#\w+\s?//g'`
WPS=`echo $WPS | sed -E 's/\#\w+\s?//g'`
BINS=""
for pt in $PTBINS; do [[ $pt == "#"* ]] || BINS+="pt$pt "; done
for dm in $DMBINS; do [[ $dm == "#"* ]] || BINS+="dm$dm "; done
if [ $VERB -gt 0 ]; then
  echo ">>> ERAS='${ERAS}'"
  echo ">>> WPS='${WPS}'"
  echo ">>> PTBINS='${PTBINS}'"
  echo ">>> DMBINS='${DMBINS}'"
  echo ">>> BINS='${BINS}'"
fi

# MAIN FUNCTIONALITY
function main {
  #header "main"
  ensuredir "output" "log"
  for era in $ERAS; do
    for wp in $WPS; do
      #header "era=$era, WP=$wp"
      for bin in $BINS; do
        
        # SETTINGS
        header "era=$era WP=$wp bin=$bin"
        #echo ">>> era=$era WP=$wp bin=$bin"
        LABEL="${wp}_${era}_${bin}"
        CARDTXT="cards/ztt_${LABEL}.card.txt"
        CARDHDF="cards/ztt_${LABEL}.card.hdf5"
        INPUTS_MT="input/ztt_tid_mvis_${bin}_mt_v10_2p5-${era}.inputs.root"
        INPUTS_MM="input/ztt_tid_mvis_mm-${era}.inputs.root"
        [ ! -f $INPUTS_MT ] && echo ">>> $INPUTS_MT not found!!" && continue
        [ ! -f $INPUTS_MM ] && echo ">>> $INPUTS_MM not found!!" && continue
        LOG="log/ztt_${LABEL}.log"
        echo `date` > $LOG
        
        # HARVEST DATACARDS => txt datacards
        if [[ $DOHARV -gt 0 ]]; then
          peval "python harvestcards.py $INPUTS_MT $INPUTS_MM -y $era -w $wp -t _${bin} -v $VERB" | tee -a $LOG
        fi
        
        # COMBINE FIT WITH TENSOR FLOW
        if [[ $DOIMPACT -gt 0 ]]; then # IMPACTS
          combinetf.py $CARDHDF --binByBinStat --output root/impacts_${LABEL}_impact.root --doImpacts | tee -a ./$LOG
        else # MAIN FIT
          peval "text2hdf5.py $CARDTXT -m 90 -o $CARDHDF" | tee -a ./$LOG
          peval "combinetf.py $CARDHDF  --binByBinStat --output output/fit_${LABEL}.root --saveHists" | tee -a ./$LOG
        fi
        
      done
    done
  done
}


function peval {
  echo -e ">>> $(tput setab 0)$(tput setaf 7)$@$(tput sgr0)"
  eval "$@";
}

function header { # print box around given string
  local HDR="$@"
  local BAR=`printf '#%.0s' $(seq 1 ${#HDR})`
  local A="$(tput setab 0)$(tput setaf 7)"
  local R="$(tput setab 0)$(tput bold)$(tput setaf 1)"
  local E="$(tput sgr0)"
  printf ">>>\n>>>\n"
  echo ">>>     $A####${BAR}####$E"
  echo ">>>     $A#   ${HDR}   #$E"
  echo ">>>     $A####${BAR}####$E"
  echo ">>> ";
}

function runtime {
  END=`date +%s`; RUNTIME=$((END-START))
  printf "%d minutes %d seconds" "$(( $RUNTIME / 60 ))" "$(( $RUNTIME % 60 ))"
}

function ensuredir {
  for d in $@; do
    [ -e "$d" ] || { echo ">>> Creating '$d' directory..."; mkdir -p "$d"; }
  done
}

# RUN MAIN
main
echo ">>> Done fitting in $(runtime)"
exit 0
