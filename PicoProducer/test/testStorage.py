#! /usr/bin/env python
# Author: Izaak Neutelings (July 2020)
# Description: Test StorageSystem
#   test/testStorage.py pathOnMyStorageSystem -v2
#   test/testStorage.py /eos/cms/store/group/phys_tau/ --readonly -v
#   test/testStorage.py /pnfs/lcg.cscs.ch/cms/trivcat/store/user/$USER --readonly -v
from TauFW.PicoProducer.storage.utils import LOG, getstorage
from ROOT import gRandom, TFile, TTree, TH1F
from array import array
from datetime import datetime
#from TauFW.common.tools.file import ensuremodule


def createdummy(fname):
  print ">>> Creating dummy file %r..."%(fname)
  with open(fname,'w') as file:
    file.write("# This is a dummy file for TauFW/PicoProducer/test/testStorage.py")
    file.write("# If you read this, it has probably not been removed correctly.")
    file.write("# Created on %s"%(datetime.now()))
  return fname
  

def createdummyroot(fname,nevts=10000):
  print ">>> Creating dummy ROOT file %r..."%(fname)
  file = TFile(fname,'RECREATE')
  tree = TTree('tree','tree')
  hist = TH1F('hist','hist',50,-2,2)
  pt  = array('d',[0])
  phi = array('d',[0])
  tree.Branch("pt",  pt,  'normal/D')
  tree.Branch("phi", phi, 'uniform/D')
  for i in xrange(nevts):
    pt[0]  = gRandom.Landau(40,20)
    phi[0] = gRandom.Uniform(-1.57,1.57)
    hist.Fill(gRandom.Landau(0,1))
    tree.Fill()
  file.Write()
  file.Close()
  return fname
  

def testStorage(path,readonly=False,hadd=True,verb=0):
  
  # INITIALIZE
  LOG.header("__init__")
  #storage = ensuremodule(system,"PicoProducer.storage"
  storage = getstorage(path,ensure=True,verb=verb)
  print ">>> %r"%(storage)
  print ">>> %-10s = %s"%('path',storage.path)
  print ">>> %-10s = %s"%('rmcmd',storage.rmcmd)
  print ">>> %-10s = %s"%('lscmd',storage.lscmd)
  print ">>> %-10s = %s"%('mkdrcmd',storage.mkdrcmd)
  print ">>> %-10s = %s"%('cpcmd',storage.cpcmd)
  print ">>> %-10s = %s"%('tmpdir',storage.tmpdir)
  print ">>> "
  
  # EXPAND PATH
  LOG.header("expandpath")
  pathargs = [
    ('test.py',),
    ('$PATH/test.py',),
    ('foo','bar',),
  ]
  pathkwargs = [
    {'here':True},
    {'here':False},
  ]
  for patharg in pathargs:
    for pathkwarg in pathkwargs:
      LOG.color("storage.expandpath(%s,%s)"%(','.join(repr(a) for a in patharg),','.join("%s=%r"%(k,v) for k,v in pathkwarg.iteritems())))
      result = storage.expandpath(*patharg,**pathkwarg)
      print ">>>   %r"%(result)
  
  # LS
  LOG.header("ls")
  LOG.color("storage.ls(verb=%d)"%(verb))
  contents = storage.ls(verb=verb)
  print ">>> Found %d items"%(len(contents))
  print ">>> Contents: %s"%(contents)
  
  # FILES
  LOG.header("getfiles")
  LOG.color("storage.getfiles(verb=%d)"%(verb))
  contents = storage.getfiles(verb=verb)
  print ">>> Found %d items"%(len(contents))
  print ">>> Contents: %s"%(contents)
  print ">>> "
  LOG.color("storage.getfiles(filter='*.*',verb=%d)"%(verb))
  contents = storage.getfiles(filter='*.*',verb=verb)
  print ">>> Found %d files"%(len(contents))
  print ">>> Contents: %s"%(contents)
  print ">>> "
  LOG.color("storage.getfiles(filter='*.*',url=None,verb=%d)"%(verb))
  contents = storage.getfiles(filter='*.*',url=None,verb=verb)
  print ">>> Found %d files"%(len(contents))
  print ">>> Contents: %s"%(contents)
  
  if readonly:
    print ">>> Read only. Skip test for cp, rm, mkdir, hadd..."
    return
  
  # CP
  LOG.header("cp")
  fname = createdummy("testStorage.txt")
  LOG.color("storage.cp(%r,verb=%d)"%(fname,verb))
  storage.cp(fname,verb=verb)
  storage.ls(verb=verb)
  
  # EXISTS
  LOG.header("exists")
  LOG.color("storage.exists(%r,verb=%d)"%(fname,verb))
  result = storage.exists(fname,verb=verb)
  print ">>> Exists: %r"%(result)
  storage.ls(verb=verb)
  
  # RM
  LOG.header("rm")
  LOG.color("storage.rm(%r,verb=%d)"%(fname,verb))
  try:
    storage.rm(fname,verb=verb)
  except Exception as error:
    print error
  storage.ls(verb=verb)
  
  # MKDIR
  LOG.header("mkdir")
  dirname = 'test'
  LOG.color("storage.mkdir(%r.verb=%d)"%(dirname,verb))
  try:
    storage.mkdir(dirname,verb=verb)
    storage.ls(verb=verb)
    storage.ls(dirname,here=True,verb=verb)
    result = storage.exists(dirname,verb=verb)
    print ">>> Exists: %r"%(result)
  except Exception as error:
    print error
  
  # RM DIRECTORY
  LOG.header("rm directory")
  submit = raw_input(">>> Careful! Do you really want to remove %r? [y/n] "%(storage.expandpath(dirname,here=True)))
  if submit=='y':
    LOG.color("storage.rm(%r,verb=%d)"%(dirname,verb))
    try:
      storage.rm(dirname,verb=verb)
      storage.ls(verb=verb)
    except Exception as error:
      print error
  
  # HADD
  if hadd:
    LOG.header("hadd")
    infiles = [createdummyroot("testStorage1.root"),createdummyroot("testStorage2.root")]
    outfile = "testStorage.root"
    for tmpdir in [True,]: #False
      LOG.color("storage.hadd(%r,%r,tmpdir=%s,verb=%d)"%(infiles,outfile,tmpdir,verb))
      try:
        storage.hadd(infiles,outfile,tmpdir=tmpdir,verb=verb)
        storage.ls(verb=verb)
        storage.rm(outfile,verb=verb)
      except Exception as error:
        print error
  

def main(args):
  testStorage(args.path,readonly=args.readonly,hadd=args.dohadd,verb=args.verbosity)
  

if __name__ == "__main__":
  import sys
  from argparse import ArgumentParser
  argv = sys.argv
  description = """Test StorageSystem."""
  parser = ArgumentParser(prog="testStorage",description=description,epilog="Good luck!")
  parser.add_argument('path',             help="storage path on system to test" )
  parser.add_argument('-r', '--readonly', action='store_true', help="test only reading routines (no cp, rm, mkdir, etc.)" )
  parser.add_argument('-H', '--nohadd',   dest='dohadd', action='store_false', help="skip hadd test" )
  parser.add_argument('-v', '--verbose',  dest='verbosity', type=int, nargs='?', const=1, default=0, action='store',
                                          help="set verbosity" )
  args = parser.parse_args()
  LOG.verbosity = args.verbosity
  main(args)
  print "\n>>> Done."
  
