# Author: Yuta Takahashi & Izaak Neutelings

# SETTINGS
#WPS="VVVLoose VVLoose VLoose Loose Medium Tight VTight VVTight"
ERAS="UL2016 UL2017 UL2018"
#ERAS="2018"
WPS="Loose Medium Tight"
PTBINS="1 2 3 4 5 6 7"

# COMMAND LINE SETTINGS
while getopts "w:y:" option; do case "${option}" in
  w) WPS="${OPTARG//,/ }";;
  y) ERAS="${OPTARG//,/ }";;
esac done

for era in $ERAS; do
  for wp in $WPS; do
    for pt in $PTBINS; do
      echo ">>> Setting era=$era WP=$wp ptbin=$pt"
      LABEL="${era}_${wp}_${pt}"
      CARD="cards/mydatacard_${LABEL}.hdf5"
      text2hdf5.py output/sm_cards/LIMITS/mydatacard_${LABEL}.txt -m 90 -o $CARD
      combinetf.py $CARD  --binByBinStat --output root/fitresults_${LABEL}.root --saveHists
    done
  done
done
