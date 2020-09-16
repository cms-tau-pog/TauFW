#! /usr/bin/env python
# Author: Izaak Neutelings (September 2020)
# Description: Test BatchSystem
#   test/testBatch.py HTCondor -v2
import os, platform
from time import sleep
from TauFW.common.tools.file import ensuredir
from TauFW.PicoProducer.batch.utils import LOG, getbatch


def createtasks(fname,ntasks=2,pause=10):
  with open(fname,'w') as file:
    for i in xrange(ntasks):
      file.write("echo 'This is task number %d with environment:'; sleep %d; env\n"%(i,pause))
  return fname
  

def testBatch(path,verb=0):
  
  # SETTINGS
  verbosity = args.verbosity
  dryrun    = args.dryrun    # prepare job and submit command, but do not submit
  ntasks    = args.ntasks    # only run a few test tasks per job
  nchecks   = args.nchecks   # number of times to check job status
  queue     = args.queue     # queue option for the batch system (job flavor for HTCondor)
  time      = args.time      # maximum time for the batch system
  batchopts = args.batchopts # extra options for the batch system
  #prompt    = args.prompt    # ask user confirmation before submitting
  outdir    = ensuredir("testBatch")
  logdir    = ensuredir("testBatch/log")
  jobname   = "testBatch"
  tasklist  = os.path.join(outdir,"testBatch.txt")
  
  # INITIALIZE
  LOG.header("__init__")
  #batch = ensuremodule(system,"PicoProducer.batch."+batch)
  batch     = getbatch(args.batch,verb=verbosity+1)
  print ">>> %r"%(batch)
  print ">>> %-10s = %s"%('jobname',jobname)
  print ">>> %-10s = %s"%('ntasks',ntasks)
  print ">>> %-10s = %s"%('nchecks',nchecks)
  print ">>> %-10s = %s"%('outdir',outdir)
  print ">>> %-10s = %s"%('logdir',logdir)
  print ">>> %-10s = %s"%('dryrun',dryrun)
  print ">>> %-10s = %s"%('queue',queue)
  print ">>> %-10s = %s"%('time',time)
  print ">>> %-10s = %s"%('batchopts',batchopts)
  print ">>> %-10s = %s"%('verbosity',verbosity)
  print ">>> "
  
  # PREPARE JOBS
  createtasks(tasklist,ntasks)
  
  # SUBMIT
  LOG.header("Submit")
  jkwargs = { # key-word arguments for batch.submit
    'name': jobname, 'opt': batchopts, 'dry': dryrun,
    'short': True, 'queue':queue, 'time':time
  }
  if batch.system=='HTCondor':
    # use specific settings for KIT condor
    if 'etp' in platform.node():
      script = "python/batch/submit_HTCondor_KIT.sub"
    else:
      script = "python/batch/submit_HTCondor.sub"
    appcmds = ["initialdir=%s"%(outdir),
               "mylogfile='log/%s.$(ClusterId).$(ProcId).log'"%(jobname)]
    jkwargs.update({ 'app': appcmds })
  elif batch.system=='SLURM':
    script  = "python/batch/submit_SLURM.sh"
    logfile = os.path.join(logdir,"%x.%A.%a.log") # $JOBNAME.o$JOBID.$TASKID.log
    jkwargs.update({ 'log': logfile, 'array': ntasks })
  #elif batch.system=='SGE':
  #elif batch.system=='CRAB':
  else:
    LOG.throw(NotImplementedError,"Submission for batch system '%s' has not been implemented (yet)..."%(batch.system))
  jobid = batch.submit(script,tasklist,**jkwargs)
  print ">>> jobid: %s"%(jobid)
  
  # CHECK JOBS
  LOG.header("Check jobs")
  for i in xrange(nchecks):
    jobs = batch.jobs(jobid,verb=verbosity-1) # get refreshed job list
    #jobs = batch.jobs(verb=verbosity-1) # get refreshed job list
    print ">>>   job objects: %r"%(jobs)
    print ">>>   "
    #for job in jobs:
    #  print ">>> Found job %r, status=%r, args=%r"%(job,job.getstatus(),job.args.rstrip())
    if i<nchecks-1:
      sleep(2)
  

def main(args):
  testBatch(args)
  

if __name__ == "__main__":
  import sys
  from argparse import ArgumentParser
  argv = sys.argv
  description = """Test BatchSystem."""
  parser = ArgumentParser(prog="testBatch",description=description,epilog="Good luck!")
  parser.add_argument('batch',              help="batch sytem to test" )
  parser.add_argument('-v', '--verbose',    dest='verbosity', type=int, nargs='?', const=1, default=0, action='store',
                                            help="set verbosity" )
  parser.add_argument('-f','--force',       dest='force', action='store_true',
                                            help='force overwrite')
  parser.add_argument('-d','--dry',         dest='dryrun', action='store_true',
                                            help='dry run: prepare job without submitting for debugging purposes')
  parser.add_argument('-N','--ntasks',      dest='ntasks', type=int, default=2,
                      metavar='N',          help='number of tasks per job to submit, default=%(default)d' )
  parser.add_argument('-n','--nchecks',     dest='nchecks', type=int, default=5,
                      metavar='N',          help='number of job status checks, default=%(default)d' )
  #parser.add_argument('--getjobs',          dest='checkqueue', type=int, nargs='?', const=1, default=-1,
  #                        metavar='N',      help="check job status: 0 (no check), 1 (check once), -1 (check every job)" ) # speed up if batch is slow
  parser.add_argument('-B','--batch-opts',  dest='batchopts', default=None,
                                            help='extra options for the batch system')
  parser.add_argument('-M','--time',        dest='time', default=None,
                                            help='maximum run time of job')
  parser.add_argument('-q','--queue',       dest='queue', default=None,
                                            help='queue of batch system (job flavor on HTCondor)')
  #parser.add_argument('-P','--prompt',      dest='prompt', action='store_true',
  #                                          help='ask user permission before submitting a sample')
  args = parser.parse_args()
  LOG.verbosity = args.verbosity
  main(args)
  print "\n>>> Done."
  
