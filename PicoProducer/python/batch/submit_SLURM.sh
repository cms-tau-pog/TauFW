#! /bin/bash
####### Script to run on a SLURM batch system
####### partition/queue
#SBATCH --partition standard
####### the cpu time for this job
#SBATCH --time 05:30:00
####### the maximum memory usage of this job
#SBATCH --mem 5500M
####### Job Name
#SBATCH -J test
####### transfer environment variable from submission host
#SBATCH --export ALL

# START
START=`date +%s`
echo "Job start at `date`"
echo "Running job on machine `uname -a`, host $HOSTNAME"
function peval { echo ">>> $@"; eval "$@"; }

# PRINT
export JOBID=$SLURM_ARRAY_JOB_ID
export TASKID=$SLURM_ARRAY_TASK_ID
export WORKDIR="/scratch/$USER/$JOBID.$TASKID"
export TMPDIR="/scratch/$USER/$JOBID.$TASKID" # using /tmp might destabilize
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
peval "mkdir -p $WORKDIR"
peval "cd $WORKDIR"

# MAIN FUNCTIONALITY
#eval $(scramv1 runtime -sh);
peval "$TASKCMD"

# FINISH
peval "rm -rf $WORKDIR"
echo
END=`date +%s`; RUNTIME=$((END-START))
echo "Job complete at `date`"
printf "Took %d minutes %d seconds" "$(( $RUNTIME / 60 ))" "$(( $RUNTIME % 60 ))"
