#! /bin/bash
function peval { echo ">>> $@"; eval "$@"; }

MINHOURS=10
MAXHOURS=200
OPTIND=1 # if sourced
while getopts m:t: option; do case "${option}" in
  m) MINHOURS=${OPTARG};;
  t) MAXHOURS=${OPTARG};;
esac; done

echo ">>> voms-proxy-info --timeleft"
SECSLEFT=$(voms-proxy-info --timeleft) # seconds left
HOURSLEFT=$((SECSLEFT/3600)) # convert seconds to hours
if [[ $HOURSLEFT -lt $MINHOURS ]]; then
   if [[ $HOURSLEFT -gt 0 ]]; then
     echo ">>> voms valid for less than 10 hours (`date -u -d @$HOURSLEFT +"%-H hours, %-M minutes and %-S seconds"`)"
   else
     echo ">>> voms not valid anymore..."
   fi
   peval "voms-proxy-init -voms cms -valid $MAXHOURS:0"
elif [[ "$1" = "-f" ]]; then
  peval "voms-proxy-init -voms cms -valid $MAXHOURS:0"
else
  echo ">>> voms still valid for another `date -u -d @$HOURSLEFT +"%-d days, %-H hours and %-M minutes"`"
fi
