#! /bin/bash
####### Script to run on a SLURM batch system
####### partition/queue
#SBATCH --partition cp3
####### the cpu time for this job
#SBATCH --time 01:20:00
####### the maximum memory usage of this job
#SBATCH --mem 10000M
####### Job Name
#SBATCH -J test
####### transfer environment variable from submission host
#SBATCH --export ALL

# START
START=`date +%s`
echo "Job start at `date`"
echo "Running job on machine `uname -a`, host $HOSTNAME"
function peval { echo ">>> $@"; eval "$@"; }
#export -f peval
# PRINT
export JOBID=$SLURM_ARRAY_JOB_ID
export TASKID=$SLURM_ARRAY_TASK_ID
if [[ "$HOME" == *"ucl"* ]]
then 
   export WORKDIR="/nfs/scratch/fynu/$USER/$JOBID.$TASKID"
else 
   export WORKDIR="/scratch/$USER/$JOBID.$TASKID"
fi
JOBLIST=$1
echo "\$JOBID=$JOBID"
echo "\$TASKID=$TASKID"
echo "\$SLURM_JOB_ID=$SLURM_JOB_ID"
echo "\$HOSTNAME=$HOSTNAME"
echo "\$JOBLIST=$JOBLIST"
echo "\$SBATCH_TIMELIMIT=$SBATCH_TIMELIMIT"
echo "\$WORKDIR=$WORKDIR"
echo "\$TMPDIR=$TMPDIR"
echo "\$PWD=$PWD"
peval 'TASKCMD=$(cat $JOBLIST | sed "${TASKID}q;d")'
peval "mkdir $WORKDIR"
peval "cd $WORKDIR"
echo "cmssw = $CMSSW_BASE"

# MAIN FUNCTIONALITY
#eval $(scramv1 runtime -sh);
#peval "$TASKCMD"
export SINGULARITYENV_PATH=$PATH
export SINGULARITYENV_LD_LIBRARY_PATH=$LD_LIBRARY_PATH
singularity exec /cvmfs/unpacked.cern.ch/registry.hub.docker.com/cmssw/el7:x86_64 /bin/sh <<- EOF_PAYLOAD
echo ">>> $TASKCMD"
eval "$TASKCMD"
EOF_PAYLOAD

# FINISH
peval "cd -"
peval "rm -rf $WORKDIR"
echo
END=`date +%s`; RUNTIME=$((END-START))
echo "Job complete at `date`"
printf "Took %d minutes %d seconds" "$(( $RUNTIME / 60 ))" "$(( $RUNTIME % 60 ))"
