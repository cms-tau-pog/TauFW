#! /usr/bin/env python
# Author: Izaak Neutelings (May 2020)
import os
from TauFW.PicoProducer.tools.utils import execute
from TauFW.PicoProducer.storage.Storage import StorageSystem
import getpass, platform


class EOS(StorageSystem):
  
  def __init__(self,path,verb=0,ensure=False):
    """EOS is mounted on lxplus, so no special override are necessary."""
    super(EOS,self).__init__(path,verb=verb,ensure=ensure)
    mounted = os.path.exists('/eos/')
    self.mounted   = mounted
    if not mounted:
      self.cpcmd   = 'xrdcp'
      self.chmdprm = '2777'
      self.tmpurl  = '/tmp/$USER/'
      self.prefix  = "root://eoscms.cern.ch/"
      self.fileurl = "root://eoscms/"
  
