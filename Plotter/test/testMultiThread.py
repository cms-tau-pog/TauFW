#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Izaak Neutelings (Februari, 2019)
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
  print "Drawing %s..."%histname
  filename = "/scratch/ineuteli/analysis/LQ_2018/SingleMuon/SingleMuon_Run2018_mutau.root"
  file = TFile.Open(filename)
  tree = file.Get('tree')
  hist = TH1D(histname,histname,100,0,200)
  tree.Draw("m_vis >> %s"%histname,"",'gOff') #getFakeRate(pt_2,m_2,eta_2,decayMode_2)
  #gDirectory.Delete(histname)
  hist.SetDirectory(0)
  file.Close()
  return hist
  

def drawWithSharedFile(file,histname):
  """Simple test function to be multithreaded with shared TFile."""
  print "Drawing %s..."%histname
  tree = file.Get('tree')
  hist = TH1D(histname,histname,100,0,200)
  tree.Draw("m_vis >> %s"%histname,"",'gOff')
  #gDirectory.Delete(histname)
  hist.SetDirectory(0)
  file.Close()
  return hist
  

def testProcess(N=5):
  """Test multiprocessing behavior."""
  start = time.time()
  threads = [ ]
  for i in range(1,N+1):
    name   = "thread %d"%i
    thread = Process(target=foo,args=(i,"Hello world!"))
    thread.start()
    threads.append(thread)
  for thread in threads:
    result = thread.join()
  print "Done after %.1f seconds"%(time.time()-start)
  
  start = time.time()
  for i in range(1,N+1):
    name = "thread %d"%i
    print foo(i,"Hello world!")
  print "done after %.1f seconds"%(time.time()-start)
  

def testMultiProcessor(N=5):
  """Test multiprocessing behavior."""
  start = time.time()
  processor = MultiProcessor()
  for i in range(1,N+1):
    name   = "thread %d"%i
    processor.start(target=foo,args=(i,"Hello world!"))
  for process in processor:
    result = process.join() # wait for processes to end
    print result
  print "Done after %.1f seconds"%(time.time()-start)
  
  start = time.time()
  for i in range(1,N+1):
   name = "thread %d"%i
   foo(i,"Hello world!")
  print "Done after %.1f seconds"%(time.time()-start)
  

def testMultiProcessorWithDraw(N=5):
  """Test multiprocessing behavior with TTree:Draw."""
  start = time.time()
  processor = MultiProcessor()
  for i in range(1,N+1):
    name   = "hist_%d"%i
    processor.start(target=draw,args=(name,))
  for process in processor:
    result = process.join() # wait for processes to end
    print result
  print "Done after %.1f seconds"%(time.time()-start)
  
  start = time.time()
  for i in range(1,N+1):
   name = "hist_%d"%i
   print draw(name)
  print "Done after %.1f seconds"%(time.time()-start)
  

def testThread(N=5):
  """Test threading behavior."""
  start = time.time()
  threads = [ ]
  for i in range(1,N+1):
    name   = "thread %d"%i
    thread = Thread(target=foo,args=(i,"Hello world!"),name=name) #,kwargs={'lol':8}
    thread.start()
    threads.append(thread)
  for thread in threads:
    result = thread.join()
    print "%s done, result = %s"%(thread.name,result)
  print "Done after %.1f seconds"%(time.time()-start)
  
  start = time.time()
  for i in range(1,N+1):
    name = "thread %d"%i
    foo(i,"Hello world!")
    #print "  %s done"%(name)
  print "Done after %.1f seconds"%(time.time()-start)
  

def testThreadWithDraw(N=5):
  """Test threading behavior with TTree:Draw."""
  
  start = time.time()
  threads = [ ]
  for i in range(1,N+1):
    name   = "hist_%d"%i
    thread = Thread(target=draw,args=(name,),name=name)
    thread.start()
    threads.append(thread)
  for thread in threads:
    thread.join()
    print "  %s done"%(thread.name)
  print "Done after %.1f seconds"%(time.time()-start)
  
  start = time.time()
  for i in range(1,N+1):
    name = "hist_%d"%i
    draw(name)
    gDirectory.Delete(name)
    print "  %s done"%(name)
  print "Done after %.1f seconds"%(time.time()-start)
  


def testThreadWithSharedTFile(N=5):
  """Test threading behavior with drawing from the same TFile."""
  
  filename = "/scratch/ineuteli/analysis/LQ_2018/SingleMuon/SingleMuon_Run2018_mutau.root"
  file = TFile.Open(filename)
  
  start = time.time()
  threads = [ ]
  for i in range(1,N+1):
    name   = "hist_%d"%i
    thread = Thread(target=drawWithSharedFile,args=(file,name),name=name)
    thread.start()
    threads.append(thread)
  for thread in threads:
    thread.join()
    print "  %s done"%(thread.name)
  print "Done after %.1f seconds"%(time.time()-start)
  
  start = time.time()
  for i in range(1,N+1):
    name = "hist_%d"%i
    drawWithSharedFile(file,name)
    gDirectory.Delete(name)
    print "  %s done"%(name)
  print "Done after %.1f seconds"%(time.time()-start)
  

def main():
  """Main function."""
  #testProcess(5)
  #testMultiProcessor(5)
  testMultiProcessorWithDraw(5)
  #testThread(5)
  #testThreadWithDraw(5)
  #testThreadWithSharedTFile(5) # gives issues in ROOT
  

if __name__ == '__main__':
  main()
  print ">>> Done!"
  
