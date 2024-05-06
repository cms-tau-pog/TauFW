#! /bin/bash
## Script to run on a HTCondor batch system

# START
START=`date +%s`
echo "Job start at `date`"
echo "Running job on machine `uname -a`, host $HOSTNAME"
function peval { echo ">>> $@"; eval "$@"; }

# SETTING
TASKCMD="$@"
WORKDIR="$PWD"
printf '=%.0s' `seq 60`; echo
echo "\$PWD=$PWD"
echo "\$JOBID=$JOBID"
echo "\$TASKID=$TASKID"
echo "\$HOSTNAME=$HOSTNAME"
echo "\$TASKCMD=$TASKCMD"
echo "\$WORKDIR=$WORKDIR"
#printf '=%.0s' `seq 60`; echo
#env
#printf '=%.0s' `seq 60`; echo

# ENVIRONMENT
#if [ ! -z "$CMSSW_BASE" -a -d "$CMSSW_BASE/src" ]; then
peval "source /cvmfs/cms.cern.ch/cmsset_default.sh"
peval "cd /afs/cern.ch/user/s/snandan/public/tauid_sf/slc7/fork_wosingularity/CMSSW_12_4_8/src"
peval 'eval `scramv1 runtime -sh`'
peval "cd $WORKDIR"
#fi

# MAIN FUNCTIONALITY
#TASKCMD=$(cat $JOBLIST | sed "${TASKID}q;d")
echo "\$PWD=$PWD"
peval "$TASKCMD"

# FINISH
echo
END=`date +%s`; RUNTIME=$((END-START))
echo "Job complete at `date`"
printf "Took %d minutes %d seconds" "$(( $RUNTIME / 60 ))" "$(( $RUNTIME % 60 ))"
