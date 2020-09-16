# Author: Izaak Neutelings (April 2020)
#import os, re, shutil
import os, re
from TauFW.common.tools.utils import execute
from TauFW.PicoProducer.batch.BatchSystem import BatchSystem, Job, JobList


class HTCondor(BatchSystem):
  # https://research.cs.wisc.edu/htcondor/manual/quickstart.html
  # https://twiki.cern.ch/twiki/bin/view/ABPComputing/LxbatchHTCondor
  
  def __init__(self,verb=False):
    super(HTCondor,self).__init__(verb=verb)
    # http://pages.cs.wisc.edu/~adesmet/status.html
    self.statusdict = { 1: 'q', 2: 'r', 3: 'f', 4: 'c', 5: 'f', 6: 'f' }
  
  def submit(self,script,taskfile=None,**kwargs):
    #jobname   = kwargs.get('name',  'job'           )
    #queue     = kwargs.get('queue', 'microcentury'  )
    appcmds   = kwargs.get('app',   [ ]            )
    options   = kwargs.get('opt',   None           )
    queue     = kwargs.get('queue', None           ) # queue: 'all.q','short.q','long.q'
    short     = kwargs.get('short', False          ) # run short test job
    time      = kwargs.get('time',  None           ) # e.g. 420, 04:20:00, 04:20
    name      = kwargs.get('name',  None           )
    dry       = kwargs.get('dry',   False          )
    verbosity = kwargs.get('verb',  self.verbosity )
    failflags = ["no jobs queued"]
    jobidrexp = re.compile("submitted to cluster (\d+).")
    jobids    = [ ]
    subcmd    = "condor_submit"
    if not isinstance(appcmds,list):
      appcmds = [appcmds]
    if name:
      subcmd += " -batch-name %s"%(name)
    if options:
      subcmd += " "+options
    for appcmd in appcmds:
      subcmd += " -append %s"%(appcmd)
    if short:
      if not queue: queue = "short.q" # shortest partition name might vary per system
      if not time:  time  = "00:06:00" # 6 minutes
    if queue:
      subcmd += " -queue %s"%(queue)
    subcmd += " "+script
    if taskfile:
      subcmd += " "+taskfile # list of tasks to be executed per job by submit_SGE.sh
    out = self.execute(subcmd,dry=dry,verb=verbosity)
    for line in out.split(os.linesep):
      if any(f in line for f in failflags):
        print ">>> Warning! Submission failed!"
        print out
      matches = jobidrexp.findall(line)
      for match in matches:
        jobids.append(int(match))
    jobid = jobids[0] if len(jobids)==1 else jobids if len(jobids)>1 else 0
    return jobid
  
  def queue(self,job,**kwargs):
    qcmd  = "condor_q"
    return self.execute(qcmd)
  
  def status(self,job,**kwargs):
    """Check status of queued or running jobs."""
    jobid   = str(job.jobid)
    if job.taskid>=0:
      jobid+= '.%s'%job.taskid
    subcmd  = "condor_q -wide %s"%(jobid)
    return self.execute(subcmd)
  
  def jobs(self,jobids,**kwargs):
    """Get job status, return JobList object."""
    if not isinstance(jobids,list):
      jobids  = [jobids]
    verbosity = kwargs.get('verb', self.verbosity )
    subcmd    = "condor_q"
    for jobid in jobids:
      subcmd += " "+str(jobid)
    subcmd   += " -format '%s ' Owner -format '%s ' ClusterId -format '%s ' ProcId -format '%s ' JobStatus -format '%s\n' Args"
    rows      = self.execute(subcmd,verb=verbosity)
    jobs      = JobList()
    if rows and self.verbosity>=1:
      print ">>> %10s %10s %8s %8s   %s"%('user','jobid','taskid','status','args')
    for row in rows.split('\n'):
      values = row.split()
      if len(values)<5:
        continue
      if verbosity>=3:
        print ">>> job row: %s"%(row)
      user   = values[0]
      jobid  = values[1]
      taskid = values[2]
      status = self.statusdict.get(int(values[3]),'?')
      args   = ' '.join(values[4:])
      if self.verbosity>=1:
        print ">>> %10s %10s %8s %8s   %s"%(user,jobid,taskid,status,args)
      job    = Job(self,jobid,taskid=taskid,args=args,status=status)
      jobs.append(job)
    return jobs
  
