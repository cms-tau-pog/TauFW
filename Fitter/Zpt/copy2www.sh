#! /bin/bash
# Author: Izaak Neutelings (June 2021)
#   ./copy2www.sh UL2016 UL2017 UL2018
#   for d in /t3home/ineuteli/eos/www/Zpt/*201*; do cp /t3home/ineuteli/eos/www/Zpt/README.txt $d/; done
function peval { echo -e ">>> $(tput setab 0)$(tput setaf 7)$@$(tput sgr0)"; eval "$@"; }
function header {
  local HDR="$@"
  local BAR=`printf '#%.0s' $(seq 1 ${#HDR})`
  echo
  echo "     $A####${BAR}####$E"
  echo "     $A#   ${HDR}   #$E"
  echo "     $A####${BAR}####$E"
  echo
}
OUTDIR="/t3home/ineuteli/eos/www/Zpt/"
[ ! -d $OUTDIR ] && echo "ERROR! Output directory $OUTDIR does not exist!" && continue

ERAS="$@"
for era in $ERAS; do
  header "Era $era"
  TARGET="/t3home/ineuteli/eos/www/Zpt/${era}/"
  [ ! -d $TARGET ] && echo "ERROR! $TARGET does not exist! Ignoring..." && continue
  peval "cp -v *py /t3home/ineuteli/eos/www/Zpt/${era}/"
  peval "cp -v weights/zpt*weight_${era}.root /t3home/ineuteli/eos/www/Zpt/${era}/"
  peval "cp -v weights/${era}/zpt*[^0]_${era}.p* /t3home/ineuteli/eos/www/Zpt/${era}/"
  peval "cp -v plots/${era}/*baseline*.p* /t3home/ineuteli/eos/www/Zpt/${era}/"
  echo " "
done
