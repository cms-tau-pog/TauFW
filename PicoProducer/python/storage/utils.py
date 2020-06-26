# Author: Izaak Neutelings (May 2020)
import os
import getpass, platform
from TauFW.PicoProducer import basedir
from TauFW.common.tools.log import Logger
LOG = Logger('Storage')


def getsedir():
  """Guess the storage element path for a given user and host."""
  user  = getpass.getuser()
  host  = platform.node()
  sedir = ""
  if 'lxplus' in host:
    sedir = "/eos/user/%s/%s/"%(user[0],user)
  elif "t3" in host and "psi.ch" in host:
    sedir = "/pnfs/psi.ch/cms/trivcat/store/user/%s/"%(user)
  return sedir
  

def gettmpdir():
  """Guess the temporary directory for a given user and host."""
  user  = getpass.getuser()
  host  = platform.node()
  sedir = ""
  if 'lxplus' in host:
    sedir = "/eos/user/%s/%s/"%(user[0],user)
  elif "t3" in host and "psi.ch" in host:
    sedir = basedir #output/$ERA/$CHANNEL/$SAMPLE/ #"/scratch/%s/"%(user)
  return sedir
  

def getstorage(path,verb=0,ensure=False):
  """Guess the storage system based on the path."""
  if path.startswith('/eos/'):
    from TauFW.PicoProducer.storage.EOS import EOS
    storage = EOS(path,ensure=ensure,verb=verb)
  #elif path.startswith('/castor/'):
  #  storage = Castor(path,verb=verb)
  elif path.startswith('/pnfs/psi.ch/'):
    from TauFW.PicoProducer.storage.T3_PSI import T3_PSI
    storage = T3_PSI(path,ensure=ensure,verb=verb)
  #elif path.startswith('/pnfs/lcg.cscs.ch/'):
  #  storage = T2_PSI(path,verb=verb)
  #elif path.startswith('/pnfs/iihe/'):
  #  return T2_IIHE(path,verb=verb)
  else:
    from TauFW.PicoProducer.storage.StorageSystem import Local
    storage = Local(path,ensure=ensure,verb=verb)
  if verb>=2:
    print ">>> getstorage(%r), %r"%(path,storage)
  return storage
  
