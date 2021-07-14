# -*- coding: utf-8 -*-
# Author: Izaak Neutelings (2017)
# Source: https://stackoverflow.com/questions/6893968/how-to-get-the-return-value-from-a-thread-in-python
#         https://stackoverflow.com/questions/10415028/how-can-i-recover-the-return-value-of-a-function-passed-to-multiprocessing-proce/28799109
#from threading import Thread as _Thread
from multiprocessing import Process, Pipe, Manager
manager = Manager()


class Thread(Process):
    """Class to get return from multithread"""
    def __init__(self, target, args=(), kwargs={}, group=None, name=None, verbose=None):
      Process.__init__(self,group,target,name,args,kwargs)
      self._return = [ ]
      
    def mytarget(self,result,*args,**kwargs):
      result.append(self._target(*self._args,**self._kwargs))
      print result
    
    def run(self):
      """Override run method to save result."""
      self.mytarget(self._return,*self._args,**self._kwargs)
      print self._return
        
    def join(self):
      """Override join method to return result."""
      Process.join(self)
      return self._return
    


class MultiProcessor:
    """Class to get manage multiple processes and their return."""
    
    def __init__(self,name='nameless',max=-1):
      self.name    = name
      self.procs   = [ ]
      self.waiting = [ ]
      self.max     = max # maximum number of parallel jobs (ncores)
      
    def __iter__(self):
      """To loop over processes, and do process.join()."""
      for process, endin, endout in self.procs:
        yield ReturnProcess(process,endin,endout)
        if self.max>=1 and self.waiting:
          #print "MultiProcessor.__iter__: starting new process (i=%d, max=%d, waiting=%d)"%(i,self.max,len(self.waiting))
          proc_wait = self.waiting[0]
          proc_wait.start()
          self.waiting.remove(proc_wait)
      
    def start(self, target, args=(), kwargs={}, group=None, name=None, verbose=False, parallel=True, kwret=None):
      """Start and save process. Create a pipe to return output."""
      if not isinstance(args,tuple):
        args = (args,)
      if parallel: # execute jobs in parallel (main functionality)
        endout, endin = Pipe(False)
        if kwret:
          newargs     = (endin,target,kwret) + args
          mptarget    = self.target_with_kwret
        else:
          newargs     = (endin,target) + args
          mptarget    = self.target
        process       = Process(group,mptarget,name,newargs,kwargs)
        process.kwret = kwret
        if self.max<1 or len(self.procs)<self.max:
          process.start() # start running process in parallel now (or add to queue)
        else:
          self.waiting.append(process) # start later
      else: # execute jobs sequentially
        process = SimpleProcess(target,name,args,kwargs,kwret=kwret)
        endin   = None
        endout  = process.start() # execute process now and wait until it returns
      self.procs.append((process,endin,endout))
      
    def target(self,*args,**kwargs):
      """Return the output to a pipe."""
      # endin.send(target(*args,**kwargs))
      args[0].send(args[1](*args[2:],**kwargs))
      
    def target_with_kwret(self,*args,**kwargs):
      """Return the output to a pipe with an extra key-word return value ("by reference")."""
      # endin.send((target(*args,**kwargs),kwret))
      args[0].send((args[1](*args[3:],**kwargs), kwargs[args[2]]))
    

class SimpleProcess:
    """Class contain a simple process for serial use."""
    
    def __init__(self,target,name,args,kwargs,kwret=None):
      self.name    = name
      self.target  = target
      self.args    = args
      self.kwargs  = kwargs
      self.kwret   = kwret
      
    def start(self):
      """Start process."""
      return self.target(*self.args,**self.kwargs)
    

class ReturnProcess:
    """Class contain a process and its return value passed through a pipe."""
    
    def __init__(self,process,endin,endout):
      self.name    = process.name
      self.process = process
      self.endin   = endin
      self.endout  = endout
      
    def join(self,*args,**kwargs):
      """Join process, and return output."""
      kwret = self.process.kwret
      if isinstance(self.process,Process):
        self.process.join(*args) # wait for process to finish
        #if self.endin:
        #  self.endin.close()
        if kwret in kwargs:
          out, kwretval = self.endout.recv()
          if isinstance(kwretval,dict):
            kwargs[kwret].update(kwretval) # dict only
          elif isinstance(kwretval,list):
            kwargs[kwret].extend(kwretval) # list only
          else:
            print "Warning! MultiThread.ReturnProcess.join: No implementation for keyword return value '%s' of type %s..."%(kwret,type(kwretval))
          return out
        return self.endout.recv()
      else:
        if kwret in kwargs:
          kwretval = self.process.kwargs[kwret]
          if isinstance(kwretval,dict):
            kwargs[kwret].update(kwretval) # dict only
          elif isinstance(kwretval,list):
            kwargs[kwret].extend(kwretval) # list only
          else:
            print "Warning! MultiThread.ReturnProcess.join: No implementation for keyword return value '%s' of type %s..."%(kwret,type(kwretval))
        return self.endout
    

