#! /bin/bash
# Author: Izaak Neutelings (2019)
# dasgoclient -query="dataset=/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIIFall17NanoAODv5_PU2017RECOSIMstep_12Apr2018_v1-DeepTauv2p1_TauPOG-v1/USER instance=prod/phys03"

BUGFILE="utils/Fall17_oldPU.txt" # /afs/cern.ch/user/g/gurpreet/public/Fall17_oldPU.txt
SAMPLES='/DY*JetsToLL_M-50_TuneCP5*mad*/RunIIFall17*NanoAODv6*/NANOAOD*'
GOODPATHS=""
BUGGYPATHS=""
[[ $@ ]] && SAMPLES="$@"

# LOOK FOR BUGGY FILES
for sample in $SAMPLES; do
  #echo $sample
  #DASCMD="dasgoclient --query=\"dataset=$sample\""
  PATHS=`dasgoclient --query="dataset=$sample"`
  if [[ $PATHS = "" ]]; then
    echo
    echo ">>> Did not find dataset $sample with"
    echo ">>>   dasgoclient --query=\"dataset=$sample\""
    continue
  fi
  for daspath in $PATHS; do
    #echo $daspath
    REQUEST=`dasgoclient --query="mcm dataset=$daspath"`
    PARENT=`dasgoclient --query="parent dataset=$daspath"`
    LINE="\n$daspath\n  $PARENT"
    if [[ $PARENT = */MINIAOD* ]]; then
      PARENT0=$PARENT
      PARENT=`dasgoclient --query="parent dataset=$PARENT"`
      LINE+="\n  $PARENT\n  $REQUEST"
      REQUEST=`dasgoclient --query="mcm dataset=$PARENT0"`
    fi
    printf "$(echo "$LINE\n  $REQUEST\n" | sed -E 's/(PU2017|new_pmx|old_pmx)/\\\e[1m\1\\\e[0m/g')"
    BUGGY=`grep -n $REQUEST $BUGFILE`
    if [ $BUGGY ]; then
      printf '  \e[31;1m!!! BUGGY !!! %s\n\e[0m' "$BUGGY"
      BUGGYPATHS+="$daspath "
    elif [[ $PARENT != *PU2017* ]]; then
      echo -e '  \e[31;1m!!! BUGGY !!!\e[0m'
      BUGGYPATHS+="$daspath "
    else
      echo -e "  \e[32;1mOKAY\e[0m"
      GOODPATHS+="$daspath "
    fi
  done
done
echo

# SUMMARY
NGOOD=`echo $GOODPATHS | wc -w`
NBUGGY=`echo $BUGGYPATHS | wc -w`
if [[ $((NGOOD+NBUGGY)) -gt 1 ]]; then
  if [[ $NGOOD -gt 0 ]]; then
    echo
    echo -e ">>> \e[32;1mFound $NGOOD GOOD paths:\e[0m"
    for daspath in $GOODPATHS; do
      echo "$daspath"
    done
  fi
  if [[ $NBUGGY -gt 0 ]]; then
    echo
    echo -e ">>> \e[31;1mFound $NBUGGY BUGGY paths:\e[0m"
    for daspath in $BUGGYPATHS; do
      echo "$daspath"
    done
  fi
  echo
fi
