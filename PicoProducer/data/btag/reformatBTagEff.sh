#! /bin/bash
# Author: Izaak Neutelings (November 2021)
# Description: Reformat CSV file so it can be read with old BTagCalibration tool
# TODO: update CMSSW / BTagCalibration tool in order to use the new formats !

FILES="$@"
function peval { echo -e ">>> $(tput setab 0)$(tput setaf 7)$@$(tput sgr0)"; eval "$@"; }

for oldfile in $FILES; do
  if [[ $oldfile != *".csv" ]]; then
    echo "Warning! File $oldfile does not end with '.csv'! Skipping..."
    continue
  fi
  [[ $oldfile = *"reformatted.csv" ]] && continue
  newfile="${oldfile/.csv/_reformatted.csv}"
  newfile2="${oldfile/.csv/_reformatted2.csv}"
  echo "$oldfile -> $newfile"
  sed -uE 's/ $//g' $oldfile | sed -uE 's/([^,]+x[^,]+)$/"\1"/g' > $newfile
  sed -u 's/,/, /g' -i $newfile
  sed -u 's/L,/0,/g' -i $newfile
  sed -u 's/M,/1,/g' -i $newfile
  sed -u 's/T,/2,/g' -i $newfile
  sed -u 's/, 0.0, 2.5,/, -2.5, 2.5,/g' -i $newfile
  #sed -u 's/, 0.0, 1.0,/, 0, 1,/g' -i $newfile
  #sed -u 's/, 20.0, 1000.0,/, 20, 1000,/g' -i $newfile
  sed -uE 's/, 5, -2.5,/, 0, -2.5,/g' -i $newfile
  sed -uE 's/, 4, -2.5,/, 1, -2.5,/g' -i $newfile
  sed -u '/iterativefit/d' -i $newfile
done
