#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Izaak Neutelings (Februari, 2019)
from TauFW.Plotter.plot.utils import LOG
from TauFW.Plotter.plot.MultiThread import MultiProcessor, Thread
from ROOT import gROOT, gSystem, gDirectory, TFile, TH1D
import time


def foo(i,bar,**kwargs):
  """Simple test function to be multithreaded."""
  if kwargs:
    print 'foo %d says "%s", with extra options: %s'%(i,bar,kwargs)
  else:
    print 'foo %d says "%s"'%(i,bar)
  time.sleep(2)
  #for i in range(100000):
  #  pass
  result = i**2
  return result
  

def draw(histname):
  """Simple test function to be multithreaded."""
  #print ">>> Drawing %s..."%histname
  filename = "/scratch/ineuteli/analysis/LQ_2018/SingleMuon/SingleMuon_Run2018_mutau.root"
  file = TFile.Open(filename)
  tree = file.Get('tree')
  hist = TH1D(histname,histname,100,0,200)
  tree.Draw("m_vis >> %s"%histname,"",'gOff') #getFakeRate(pt_2,m_2,eta_2,decayMode_2)
  print ">>> Drawing %s... %s"%(histname,hist)
  #gDirectory.Delete(histname)
  hist.SetDirectory(0)
  file.Close()
  return hist
  

def drawWithSharedFile(file,histname):
  """Simple test function to be multithreaded with shared TFile."""
  #print ">>> Drawing %s..."%histname
  tree = file.Get('tree')
  hist = TH1D(histname,histname,100,0,200)
  tree.Draw("m_vis >> %s"%histname,"",'gOff')
  print ">>> Drawing %s... %s"%(histname,hist)
  #gDirectory.Delete(histname)
  hist.SetDirectory(0)
  file.Close()
  return hist
  

def testProcess(N=5):
  """Test multiprocessing behavior."""
  LOG.header("testProcess")
  
  print ">>> Sequential:"
  start = time.time()
  for i in range(1,N+1):
    name = "thread %d"%i
    result = foo(i,"Hello world!")
    print ">>>   foo returns:", result
  print ">>> Took %.1f seconds"%(time.time()-start)
  
  print "\n>>> Parallel:"
  start = time.time()
  threads = [ ]
  for i in range(1,N+1):
    name   = "thread %d"%i
    thread = Process(target=foo,args=(i,"Hello world!"))
    thread.start()
    threads.append(thread)
  for thread in threads:
    result = thread.join()
  print ">>> Took %.1f seconds"%(time.time()-start)
  print
  

def testMultiProcessor(N=5):
  """Test multiprocessing behavior."""
  LOG.header("testMultiProcessor")
  
  print ">>> Sequential:"
  start = time.time()
  for i in range(1,N+1):
    result = foo(i,"Hello world!")
    print ">>>   foo returns:",result
  print ">>> Took %.1f seconds"%(time.time()-start)
  
  print "\n>>> Parallel:"
  start = time.time()
  processor = MultiProcessor()
  for i in range(1,N+1):
    name = "thread %d"%i
    processor.start(target=foo,args=(i,"Hello world!"))
  for process in processor:
    result = process.join() # wait for processes to end
    print ">>>   foo returns:", result
  print ">>> Took %.1f seconds"%(time.time()-start)
  print
  

def testMultiProcessorWithDraw(N=5):
  """Test multiprocessing behavior with TTree:Draw."""
  LOG.header("testMultiProcessorWithDraw")
  
  print ">>> Sequential:"
  start = time.time()
  for i in range(1,N+1):
   name = "hist_%d"%i
   result = draw(name)
   print ">>>   draw returns:", result
  print ">>> Took %.1f seconds"%(time.time()-start)
  
  print "\n>>> Parallel:"
  start = time.time()
  processor = MultiProcessor()
  for i in range(1,N+1):
    name = "hist_%d"%i
    processor.start(target=draw,args=(name,))
  for process in processor:
    result = process.join() # wait for processes to end
    print ">>>   draw returns:", result
  print ">>> Took %.1f seconds"%(time.time()-start)
  print
  

def testThread(N=5):
  """Test threading behavior."""
  LOG.header("testThread")
  
  print ">>> Sequential:"
  start = time.time()
  for i in range(1,N+1):
    result = foo(i,"Hello world!")
    print ">>>   foo returns:", result
  print ">>> Took %.1f seconds"%(time.time()-start)
  
  print "\n>>> Parallel:"
  start = time.time()
  threads = [ ]
  for i in range(1,N+1):
    name   = "thread %d"%i
    thread = Thread(target=foo,args=(i,"Hello world!"),name=name) #,kwargs={'lol':8}
    thread.start()
    threads.append(thread)
  for thread in threads:
    result = thread.join()
    print ">>>   %s done, foo returns: %s"%(thread.name,result)
  print ">>> Took %.1f seconds"%(time.time()-start)
  print
  

def testThreadWithDraw(N=5):
  """Test threading behavior with TTree:Draw."""
  LOG.header("testThreadWithDraw")
  
  print ">>> Sequential:"
  start = time.time()
  for i in range(1,N+1):
    name = "hist_%d"%i
    result = draw(name)
    gDirectory.Delete(name)
    print ">>>   %s done, draw returns: %s"%(name,result)
  print "Took %.1f seconds"%(time.time()-start)
  
  print "\n>>> Parallel:"
  start = time.time()
  threads = [ ]
  for i in range(1,N+1):
    name   = "hist_%d"%i
    thread = Thread(target=draw,args=(name,),name=name)
    thread.start()
    threads.append(thread)
  for thread in threads:
    thread.join()
    print ">>>  %s done"%(thread.name)
  print "Took %.1f seconds"%(time.time()-start)
  print
  


def testThreadWithSharedTFile(N=5):
  """Test threading behavior with drawing from the same TFile."""
  LOG.header("testThreadWithSharedTFile")
  filename = "/scratch/ineuteli/analysis/LQ_2018/SingleMuon/SingleMuon_Run2018_mutau.root"
  file = TFile.Open(filename)
  
  print ">>> Sequential:"
  start = time.time()
  for i in range(1,N+1):
    name = "hist_%d"%i
    drawWithSharedFile(file,name)
    gDirectory.Delete(name)
    print ">>>  %s done"%(name)
  print "Took %.1f seconds"%(time.time()-start)
  
  print "\n>>> Parallel:"
  start = time.time()
  threads = [ ]
  for i in range(1,N+1):
    name   = "hist_%d"%i
    thread = Thread(target=drawWithSharedFile,args=(file,name),name=name)
    thread.start()
    threads.append(thread)
  for thread in threads:
    thread.join()
    print ">>>  %s done"%(thread.name)
  print "Took %.1f seconds"%(time.time()-start)
  print
  

def main():
  """Main function."""
  N = 5
  #testProcess(N)
  #testThread(N)
  #testThreadWithDraw(N)
  #testThreadWithSharedTFile(N) # gives issues in ROOT
  testMultiProcessor(N)
  testMultiProcessorWithDraw(N)
  

if __name__ == '__main__':
  main()
  print ">>> Done!"
  
