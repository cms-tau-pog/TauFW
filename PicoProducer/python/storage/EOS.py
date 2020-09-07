#! /usr/bin/env python
# Author: Izaak Neutelings (May 2020)
import os
from TauFW.common.tools.utils import execute
from TauFW.PicoProducer.storage.StorageSystem import StorageSystem
import getpass, platform


class EOS(StorageSystem):
  
  def __init__(self,path,verb=0,ensure=False):
    """EOS is mounted on lxplus, so no special override are necessary."""
    super(EOS,self).__init__(path,verb=verb,ensure=False)
    if not self.mounted: # EOS is mounted on lxplus
      # https://cern.service-now.com/service-portal?id=kb_article&n=KB0001998
      self.cpcmd   = 'xrdcp -f'
      self.chmdprm = '2777'
      self.cpurl   = "root://eoscms.cern.ch/"
      self.fileurl = "root://eoscms/"
      #self.prefix  = "root://eoscms.cern.ch/"
    self.tmpdir  = '/tmp/$USER/'
    if ensure:
      self.ensuredir(self.path)
  

