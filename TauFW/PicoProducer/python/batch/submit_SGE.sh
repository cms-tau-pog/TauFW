#! /bin/bash
## Script to run on a Sun Grid Engine batch system
## make sure the right shell will be used
#$ -S /bin/bash
## Black list nodes
##$ -l h=t3wn4*.psi.ch
##$ -l h=!t3wn34.psi.ch
##$ -l h=!(t3wn34.psi.ch|t3wn5*.psi.ch)
##$ -l h=(t3wn4*.psi.ch|t3wn6*.psi.ch)
## the cpu time for this job
#$ -l h_rt=04:20:00
## the maximum memory usage of this job
#$ -l h_vmem=5900M
## Job Name
#$ -N test
## stderr and stdout are merged together to stdout
#$ -j y
## transfer env var from submission host
#$ -V
## set cwd to submission host pwd
#$ -cwd

# START
START=`date +%s`
echo "Job start at `date`"
echo "Running job on machine `uname -a`, host $HOSTNAME"

# PRINT
export JOBID
export TASKID=$SGE_TASK_ID
JOBLIST=$1
echo "\$JOBID=$JOBID"
echo "\$TASKID=$TASKID"
echo "\$HOSTNAME=$HOSTNAME"
echo "\$JOBLIST=$JOBLIST"
TASKCMD=$(cat $JOBLIST | sed "${TASKID}q;d")

# MAIN FUNCTIONALITY
#eval $(scramv1 runtime -sh);
pwd
echo "Going to execute"
echo "  $TASKCMD"
eval $TASKCMD;

# FINISH
END=`date +%s`; RUNTIME=$((END-START))
echo "Job complete at `date`"
printf "Took %d minutes %d seconds" "$(( $RUNTIME / 60 ))" "$(( $RUNTIME % 60 ))"
