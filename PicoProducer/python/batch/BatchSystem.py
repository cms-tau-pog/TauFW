# Author: Izaak Neutelings (May 2020)
#import os, re, shutil
import os, re
import importlib
from TauFW.common.tools.utils import execute
from abc import ABCMeta, abstractmethod


class BatchSystem(object):
  """Abstract superclass for batch systems.
  Please subclass and override the abstract methods with your own routines."""
  __metaclass__ = ABCMeta
  
  def __init__(self,verb=1):
    self.verbosity  = verb
    self.statusdict = { }
    self.system     = self.__class__.__name__
  
  def __str__(self):
    return self.system
  
  def __repr__(self):
    return '<%s("%s") at %s>'%(self.__class__.__name__,self.system,hex(id(self)))
  
  def statuscode(self,code):
    status = '?'
    for skey, codelist in self.statusdict.iteritems():
      if code in codelist:
        status = skey
    return status
  
  def execute(self,cmd,dry=False,fatal=True,**kwargs):
    verbosity = kwargs.get('verb',self.verbosity)
    return execute(cmd,dry=dry,fatal=fatal,verb=verbosity)
  
  def parsejobs(self,rows,**kwargs):
    """Help function to parse rows of job output from queue command.
    Columns should be ordered as user, jobid, taskid, status, args."""
    # TODO: allow for job name ?
    verbosity = kwargs.get('verb',self.verbosity)
    jobs      = JobList([])
    rows      = rows.split('\n')
    if len(rows)>0 and self.verbosity>=1:
      print ">>> %10s %10s %8s %8s   %s"%('user','jobid','taskid','status','args')
    for row in rows:
      values = row.split()
      if len(values)<5 or not values[1].isdigit() or not values[2].isdigit():
        continue
      user   = values[0]
      jobid  = values[1]
      taskid = values[2]
      status = self.statuscode(values[3])
      args   = ' '.join(values[4:])
      if self.verbosity>=1:
        print ">>> %10s %10s %8s %8s   %s"%(user,jobid,taskid,status,args)
      job    = Job(self,jobid,taskid=taskid,args=args,status=status)
      jobs.append(job)
    if verbosity>=3:
      for job in jobs:
        print repr(job)
    return jobs
  
  @abstractmethod
  def submit(self,script,taskfile=None,**kwargs):
    """Submit a script with some optional parameters."""
    raise NotImplementedError("BatchSystem.submit is an abstract method. Please implement in a subclass.")
  
  @abstractmethod
  def status(self,**kwargs):
    """Check status of queued or running jobs."""
    raise NotImplementedError("BatchSystem.status is an abstract method. Please implement in a subclass.")
  
  @abstractmethod
  def jobs(self,jobids=[],**kwargs):
    """Get job status, return JobList object."""
    raise NotImplementedError("BatchSystem.jobs is an abstract method. Please implement in a subclass.")
  

class JobList(object):
  """Job list container class."""
  
  def __init__(self,jobs=[ ],verb=0):
    self.jobs      = jobs
    self.verbosity = verb
  
  def __iter__(self):
    for job in self.jobs:
      yield job
  
  def __len__(self):
    return len(self.jobs)
  
  def append(self,job):
    self.jobs.append(job)
  
  def running(self):
    return [j for j in self.jobs if j.getstatus()=='r']
  
  def failed(self):
    return [j for j in self.jobs if j.getstatus()=='f']
  

class Job(object):
  """Job container class. Status:
  q=queued/pending/idle, r=running, f=failed, ?=unknown/missing"""
  
  def __init__(self,batch,jobid,**kwargs):
    self.batch  = batch
    self.jobid  = int(jobid) # or 'clusterid'
    self.taskid = kwargs.get('taskid', -1     )# or 'procid'
    self.name   = kwargs.get('name',   "none" )
    self.args   = kwargs.get('args',   ""     )
    self.status = kwargs.get('status', None   )
    if isinstance(self.taskid,basestring):
      if self.taskid.isdigit():
        self.taskid = int(self.taskid)
      else:
        self.taskid = -1
    if self.status==None:
      self.getstatus()
  
  def __str__(self):
    return self.name
  
  def __repr__(self):
    return '<%s(%s,%s,"%s") at %s>'%(self.__class__.__name__,self.jobid,self.taskid,self.name,hex(id(self)))
  
  def getstatus(self):
    #status = self.batch.status(job)
    return self.status

