#! /bin/bash
#SBATCH --partition quick
#SBATCH --time 01:00:00
#SBATCH --priority TOP
#SBATCH -J clean
#SBATCH -o slurm_clean.%N.%j.log
#
# Script to clean the remnants of finished SLURM jobs on all WN scratch areas
# Job output need to be of the format
#   /scratch/$USER/*/*/$JOBID*
# Submit like:
#   for wn in `sinfo -N -o "%N" | grep t3wn`; do sbatch -J clean_$wn -w $wn cleanWNs_SLURM.sh; done
#r

# START
START=`date +%s`
echo "Job start at `date`"
echo "Running job on machine `uname -a`"
function peval { echo ">>> $@"; eval "$@"; } # print and evaluate
echo

# SETTINGS

MAXJOBID=`squeue -u $USER -o '%i' | sort | head -n1 | sed 's/_.*//'` # oldest running job
OLDDIRS="/scratch/$USER/*/*/*" # directory pattern to delete; should contain JOBID directory name
echo "\$USER=$USER"
echo "\$HOSTNAME=$HOSTNAME"
echo "\$SLURM_JOB_ID=$SLURM_JOB_ID"
echo "\$OLDDIRS=$OLDDIRS"
echo

# CLEANING
[[ `hostname` = "t3ui"* ]] && echo "Don't run on UI!" && exit 1
if [ "$1" = 'all' ]; then
  peval "ls -hlt /tmp | grep $USER"
  peval "ls -hlt /scratch | grep $USER"
  peval "ls -hlt /scratch/$USER | grep $USER"
  peval "find /tmp -maxdepth 1 -user $USER | xargs rm -rfv"
else
  echo "Start cleaning..."
  for oldir in $OLDDIRS; do
    JOBID=`basename $oldir | sed 's/-.*//'` #sed -e 's/.*\([0-9]\{6\}\).*/\1/' # get JOBID from directory
    if [[ ! -z "${JOBID##*[!0-9]*}" && "$JOBID" && $JOBID -lt $MAXJOBID ]]; then
      echo "Removing ${oldir}..."
      peval "rm -rf $oldir"
    elif [[ -e "$oldir" ]]; then
      echo "Keeping ${oldir}..."
    else
      echo "No directories found!"
    fi
  done
fi

# FINISH
echo
END=`date +%s`; RUNTIME=$((END-START))
echo "Job complete at `date`"
printf "Took %d minutes %d seconds" "$(( $RUNTIME / 60 ))" "$(( $RUNTIME % 60 ))"
