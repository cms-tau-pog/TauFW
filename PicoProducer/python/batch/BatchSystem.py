# Author: Izaak Neutelings (May 2020)
#import os, re, shutil
import os, re
import importlib
from TauFW.PicoProducer.batch import moddir
from TauFW.PicoProducer.tools.utils import execute
from abc import ABCMeta, abstractmethod


def getbatch(arg,verb=0):
  if isinstance(arg,str):
    system = arg
  elif hasattr(arg,'batch'):
    system = arg.batch
  else:
    raise IOError("Did not recognize argument",arg)
  modfile = os.path.join(moddir,system+".py")
  modpath = "TauFW.PicoProducer.batch.%s"%(system)
  assert os.path.isfile(modfile), "Did not find python module %s for batch system '%s'"%(modfile,system)
  module  = importlib.import_module(modpath)
  batch   = getattr(module,system)(verb)
  return batch
  

class BatchSystem(object):
  __metaclass__ = ABCMeta
  
  def __init__(self,verb=1):
    self.verbosity = verb
    self.system    = self.__class__.__name__
  
  def execute(self,cmd,dry=False,**kwargs):
    verbosity = kwargs.get('verb',self.verbosity)
    return execute(cmd,dry=dry,verb=verbosity)
  
  @abstractmethod
  def submit(self,script,**kwargs):
    """Submit a script with some optional parameters."""
    raise NotImplementedError("BatchSystem.submit is an abstract method.")
  
  @abstractmethod
  def status(self,**kwargs):
    """Check status of queued or running jobs."""
    raise NotImplementedError("BatchSystem.status is an abstract method.")
  
  @abstractmethod
  def jobs(self,**kwargs):
    """Get job status, return JobList object."""
    raise NotImplementedError("BatchSystem.jobs is an abstract method.")
  

class JobList(object):
  """Job list container class."""
  
  def __init__(self,jobs=[ ]):
    self.jobs = jobs
  
  def __iter__(self):
    for job in self.jobs: yield job
  
  def __len__(self):
    return len(self.jobs)
  
  def append(self,job):
    self.jobs.append(job)
  
  def running(self):
    return [j for j in jobs if j.getstatus()=='r']
  
  def failed(self):
    return [j for j in jobs if j.getstatus()=='f']
  

class Job(object):
  """Job container class. Status:
  q=queued/pending/idle, r=running, f=failed, ?=unknown/missing"""
  
  def __init__(self,batch,jobid,**kwargs):
    self.batch  = batch
    self.jobid  = int(jobid) # or 'clusterid'
    self.taskid = int(kwargs.get('taskid', -1 )) # or 'procid'
    self.name   = kwargs.get('name',   "none" )
    self.args   = kwargs.get('args',   ""     )
    self.status = kwargs.get('status', None   )
    if self.status==None:
      self.getstatus()
    
  def getstatus(self):
    #status = self.batch.status(job)
    return self.status

