#! /bin/bash
# Author: Izaak Neutelings (2019)
# dasgoclient -query="dataset=/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIIFall17NanoAODv5_PU2017RECOSIMstep_12Apr2018_v1-DeepTauv2p1_TauPOG-v1/USER instance=prod/phys03"

BUGFILE="utils/Fall17_oldPU.txt" # /afs/cern.ch/user/g/gurpreet/public/Fall17_oldPU.txt
SAMPLES='/DY*JetsToLL_M-50_TuneCP5*mad*/RunIIFall17*NanoAODv6*/NANOAOD*'

[[ $@ ]] && SAMPLES="$@"

for sample in $SAMPLES; do
  for daspath in `dasgoclient --limit=0 --query="dataset=$sample"`; do
    REQUEST=`dasgoclient --limit=0 --query="mcm dataset=$daspath"`
    PARENT=`dasgoclient --limit=0 --query="parent dataset=$daspath"`
    LINE="\n$daspath\n  $PARENT"
    if [[ $PARENT = */MINIAOD* ]]; then
      PARENT0=$PARENT
      PARENT=`dasgoclient --limit=0 --query="parent dataset=$PARENT"`
      LINE+="\n  $PARENT\n  $REQUEST"
      REQUEST=`dasgoclient --limit=0 --query="mcm dataset=$PARENT0"`
    fi
    printf "$(echo "$LINE\n  $REQUEST\n" | sed -E 's/(PU2017|new_pmx|old_pmx)/\\\e[1m\1\\\e[0m/g')"
    BUGGY=`grep -n $REQUEST $BUGFILE`
    if [ $BUGGY ]; then
      printf '  \e[31;1m!!! BUGGY !!! %s\n\e[0m' "$BUGGY"
    elif [[ $PARENT != *PU2017* ]]; then
      echo -e '  \e[31;1m!!! BUGGY !!!\e[0m'
    else
      echo -e "  \e[32;1mOKAY\e[0m"
    fi
  done
done
echo
