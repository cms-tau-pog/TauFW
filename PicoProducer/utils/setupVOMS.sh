#! /bin/bash
function peval { echo ">>> $@"; eval "$@"; }

echo ">>> voms-proxy-info --timeleft"
TIMELEFT=$(voms-proxy-info --timeleft)
if [[ $TIMELEFT -lt 36000 ]]; then # 10 hours
   if [[ $TIMELEFT -gt 0 ]]; then
     echo ">>> voms valid for less than 10 hours (`date -u -d @$TIMELEFT +"%-H hours, %-M minutes and %-S seconds"`)"
   else
     echo ">>> voms not valid anymore..."
   fi
   peval "voms-proxy-init -voms cms -valid 200:0"
elif [[ "$1" = "-f" ]]; then
  peval "voms-proxy-init -voms cms -valid 200:0"
else
  echo ">>> voms still valid for another `date -u -d @$TIMELEFT +"%-d days, %-H hours and %-M minutes"`"
fi
