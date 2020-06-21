#! /bin/bash
# Author: Izaak Neutelings (November 2019)
# Description: Check if 2017 sample has a buggy pileup distribution
# Source:
#   https://hypernews.cern.ch/HyperNews/CMS/get/generators/4060.html?inline=-1
#   https://hypernews.cern.ch/HyperNews/CMS/get/physics-validation/3128.html

SAMPLES='/DY*JetsToLL_M-50_TuneCP5*mad*/RunIIFall17*/NANOAOD*'
[ $1 ] && SAMPLES="$@"

echo
for samples in $SAMPLES; do
  for sample in `dasgoclient --limit=0 --query="dataset=$samples"`; do
    REQUEST=`dasgoclient --limit=0 --query="mcm dataset=$sample"`
    PARENT=`dasgoclient --limit=0 --query="parent dataset=$sample"`
    INFO="\n$sample\n  $PARENT"
    if [[ $PARENT = */MINIAOD* ]]; then
      PARENT0=$PARENT
      PARENT=`dasgoclient --limit=0 --query="parent dataset=$PARENT"`
      INFO+="\n  $PARENT\n  $REQUEST"
      REQUEST=`dasgoclient --limit=0 --query="mcm dataset=$PARENT0"`;
    fi
    printf "$(echo "$INFO\n  $REQUEST\n" | sed -E 's/(PU2017|new_pmx|old_pmx)/\\\e[1m\1\\\e[0m/g')"
    FOUND=`grep -n $REQUEST /afs/cern.ch/user/g/gurpreet/public/Fall17_oldPU.txt`
    if [ $FOUND ]; then
      printf '  \e[31;1m!!! BUGGY !!! %s\n\e[0m' "$G"
    elif [[ $PARENT != *PU2017* ]]; then
      echo -e '  \e[31;1m!!! BUGGY !!!\e[0m'
    else
      echo -e "  \e[32;1mOKAY\e[0m"
    fi
  done
done
echo