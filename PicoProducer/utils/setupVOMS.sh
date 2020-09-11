#! /bin/bash
# Author: Izaak Neutelings (2018)
# Description: Script to check validity of VOMS proxy,
#              if it's almost expired, create a new one
# Usage:
#   source utils/setupVOMS.sh
#   source utils/setupVOMS.sh -m 10 -t 200
# Tip: On lxplus, add this line to your .bashrc:
#   export X509_USER_PROXY=~/.x509up_u`id -u`
function peval { echo ">>> $@"; eval "$@"; }

MINHOURS=12  # default minimum time before renewing proxy: 10 hours
MAXHOURS=200 # default time of proxy's validity: 200 hours
OPTIND=1 # if sourced
while getopts m:t: option; do case "${option}" in
  m) MINHOURS=${OPTARG};; # minimum time before renewing proxy
  t) MAXHOURS=${OPTARG};; # time of proxy's validity
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
