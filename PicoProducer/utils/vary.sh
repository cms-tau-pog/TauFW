#! /bin/bash
# Author: Izaak Neutelings (August 2020)
# Description: Run systematic variations, e.g. TES, LTF, JTF, ...
#   pico.py channel mutau_TES1p030 'ModuleMuTau tes=1.03'
#   pico.py channel mutau_TES0p970 'ModuleMuTau tes=0.97'
#   ./vary.sh run -T -y UL2017
#   ./vary.sh submit -T -y UL2017
#   ./vary.sh resubmit -T -y UL2017
#   ./vary.sh status -T -y UL2017
#   ./vary.sh hadd -T -y UL2017
set -e

CMD=$1 # subcommand for pico.py
ERAS="UL2017"
CHANNELS='mutau'
SAMPLES=""
OPTIONS="--das "
CLEAN=0
#TES_FIRST=0.970
#TES_LAST=1.030
#STEP_SIZE=0.002
SHIFTS="" #`seq $TES_FIRST $STEP_SIZE $TES_LAST`

OPTIND=2
while getopts ":c:JLm:rs:Tvx:y:" option; do case "${option}" in
  c) CHANNELS="${OPTARG//,/ }";;
  J) SHIFTS+="JTF0p900 JTF1p100 ";;
  L) SHIFTS+="LTF0p970 LTF1p030 ";;
  m) OPTIONS+="-m $OPTARG ";;
  T) SHIFTS+="TES0p970 TES1p030 ";;
  r) OPTIONS+="-r "; CLEAN=1;;
  s) SAMPLES="${OPTARG//,/ }";;
  v) OPTIONS+="-v ";;
  x) OPTIONS+="-x ${OPTARG//,/ } ";;
  y) ERAS="${OPTARG//,/ }";;
  *) OPTIONS+="-$OPTARG ";;
esac done
function peval { echo ">>> $@"; eval "$@"; }
[ "$SHIFTS" = "" ] && echo "Please define systematic variation..." && exit 1

for era in $ERAS; do
  [[ $era = '#'* ]] && continue
  for channel in $CHANNELS; do
    [[ $channel = '#'* ]] && continue
    for shft in $SHIFTS; do
      SAMPLES_=$SAMPLES
      if [ "$SAMPLES" = "" ]; then
        [[ $shft = 'TES'* ]] && SAMPLES_="DY TT"
        [[ $shft = 'LTF'* ]] && SAMPLES_="DY TT"
        [[ $shft = 'JTF'* ]] && SAMPLES_="DY TT W*J"
      fi
      OPTIONS_="-s $SAMPLES_ $OPTIONS"
      CHANNEL_="${channel}_${shft}"
      peval "pico.py $CMD -c $CHANNEL_ -y $era $OPTIONS_"
      ###elif [ $CLEAN -gt 0 ]; then
      ###  for samplename in $SAMPLES; do
      ###    peval "rm output/$CHANNEL_/$era/${samplename}*/"
      ###  done
    done
  done
done
