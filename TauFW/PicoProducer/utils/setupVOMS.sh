#! /bin/bash
# Author: Izaak Neutelings (2018)
# Description: Script to check validity of VOMS proxy,
#              if it's almost expired, create a new one
# Usage:
#   source utils/setupVOMS.sh
#   source utils/setupVOMS.sh -m 10 -M 200
# Tip: On lxplus, add this line to your .bashrc:
#   export X509_USER_PROXY=~/.x509up_u`id -u`
export VO_CMS_SW_DIR=/cvmfs/cms.cern.ch
function peval { echo ">>> $@"; eval "$@"; }

FORCE=0      # force proxy init (even if valid one exists)
INIT=0       # init proxit
TRIES=3      # max. number of init tries
MINHOURS=12  # default minimum time before renewing proxy: 12 hours
MAXHOURS=200 # default time of proxy's validity: 200 hours
OPTIND=1     # if sourced
while getopts fm:M:t: option; do case "${option}" in
  f) FORCE=1;;            # force proxy init
  m) MINHOURS=${OPTARG};; # minimum time before renewing proxy
  M) MAXHOURS=${OPTARG};; # time of proxy's validity
  t) TRIES=${OPTARG};;    # max. number of init tries
esac; done

# CHECK STATUS
if [[ $FORCE -gt 0 ]]; then
  INIT=1
else
  echo ">>> voms-proxy-info --timeleft"
  SECSLEFT=$(voms-proxy-info --timeleft) # seconds left
  HOURSLEFT=$((SECSLEFT/3600)) # convert seconds to hours
  if [[ $HOURSLEFT -lt $MINHOURS ]]; then
     if [[ $HOURSLEFT -gt 0 ]]; then
       echo ">>> voms valid for less than 10 hours (`date -u -d @$HOURSLEFT +"%-H hours, %-M minutes and %-S seconds"`)"
     else
       echo ">>> voms not valid anymore..."
     fi
     INIT=1
  else
    INIT=0
    echo ">>> voms still valid for another `date -u -d @$HOURSLEFT +"%-d days, %-H hours and %-M minutes"`"
  fi
fi

# INITIALIZE PROXY
if [[ $INIT -gt 0 ]]; then
  for try in `seq $TRIES`; do
    [[ $try -gt 1 ]] && echo ">>> try $try..."
    peval "voms-proxy-init -voms cms -valid $MAXHOURS:0"
    [[ $? = 0 ]] && break # success
  done
fi
