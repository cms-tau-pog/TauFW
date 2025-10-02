#! /bin/bash
## Script to run on a HTCondor batch system

# START
START="$(date +%s)"
echo "Job starts at $(date)"
echo "Running job on machine $(uname -a), host $HOSTNAME"

# SETTINGS: store in file for reuse
cat << EOF > setenv.sh
function peval { echo ">>> \$@"; eval "\$@"; }
function pbar { printf '=%.0s' \$(seq \${1:-70}); echo; }
VERB=${VERB:-0} # verbosity level for debugging
START=$START
JOBID=$JOBID
TASKID=$TASKID
HOSTNAME=$HOSTNAME
PWD=$PWD
WORKDIR=$PWD
CONTAINER='${CONTAINER:-${APPTAINER_CONTAINER:-${SINGULARITY_CONTAINER:-}}}' # to set OS environment with container (Singularity, e.g. "cmssw-el7")
CMSSW_BASE=$CMSSW_BASE # to set CMSSW environment
TASKCMD='$@'
EOF
source setenv.sh # set environment
pbar
peval 'tail -n +3 setenv.sh | while read line; do echo "\$$line"; done'
pbar
[ $VERB -ge 1 ] && { peval "env"; pbar; } # print out environment for debugging

# OS ENVIRONMENT with container (Singularity)
# https://cms-sw.github.io/singularity.html
# https://apptainer.org/docs/user/main/environment_and_metadata.html
if [ ! -z "$CONTAINER" ]; then # if $CONTAINER is set
  echo ">>> Setting OS environment with container '$CONTAINER'..."
  if [[ "$CONTAINER" = *"/"* ]]; then # container/singularity image, e.g. "/cvmfs/unpacked.cern.ch/registry.hub.docker.com/cmssw/el7:x86_64"
    peval "cmssw-env --cmsos \$(basename $CONTAINER)"
  else # container/singularity command, e.g. just "cmssw-el7"
    peval "$CONTAINER" # setup container
  fi
  peval "source setenv.sh" # set environment again (incl. functions) after Singularity
  [ $VERB -ge 1 ] && { peval "env"; pbar; } # print out environment for debugging
fi

# CMSSW ENVIRONMENT
if [ -z "$CMSSW_BASE" ]; then # $CMSSW_BASE is not set
  echo ">>> WARNING! CMSSW_BASE was not defined!"
  # Guess CMSSW_BASE path from $CMSSW_BASE/src/TauFW/PicoProducer/python/batch/submit_HTCondor.sh
  SCRIPT="$(echo $TASKCMD | awk '{ print $2 }')" # assume `[COMMAND] [SCRIPT] [OPTIONS]`
  CMSSW_BASE=$(realpath $(dirname "${SCRIPT}")/../../../../..)
  echo ">>> Guessing CMSSW_BASE=$CMSSW_BASE based on SCRIPT=$SCRIPT"
fi
if [ ! -z "$CMSSW_BASE" ]; then # $CMSSW_BASE is set
  echo ">>> Setting CMSSW environment from CMSSW_BASE=$CMSSW_BASE..."
  if [ -d "/cvmfs/cms.cern.ch/" ]; then # /cvmfs exists/mounted
    peval "source /cvmfs/cms.cern.ch/cmsset_default.sh"
  else # could not find /cvmfs
    echo ">>> WARNING! /cvmfs/cms.cern.ch/ does not exist or not mounted on machine $(uname -a), host $HOSTNAME !"
  fi
  if [ -d "$CMSSW_BASE/src" ]; then # $CMSSW_BASE exists/mounted
    peval "cd $CMSSW_BASE/src"
    peval 'eval $(scramv1 runtime -sh)' # = cmsenv
    peval "cd $WORKDIR"
  else # could not find CMSSW
    echo ">>> WARNING! $CMSSW_BASE/src does not exist or not mounted on machine $(uname -a), host $HOSTNAME !"
  fi
fi

# MAIN FUNCTIONALITY
pbar
#TASKCMD=$(cat $JOBLIST | sed "${TASKID}q;d") # get TASKCMD from job list file
echo "\$PWD=$PWD"
peval "$TASKCMD"

# FINISH
echo
pbar
peval "rm $WORKDIR/setenv.sh"
END="$(date +%s)"; RUNTIME=$((END-START))
echo "Job complete at $(date)"
printf "Took %d minutes %d seconds" "$(( $RUNTIME / 60 ))" "$(( $RUNTIME % 60 ))"
