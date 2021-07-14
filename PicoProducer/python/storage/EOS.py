#! /usr/bin/env python
# Author: Izaak Neutelings (May 2020)
# https://cern.service-now.com/service-portal?id=kb_article&sys_id=fae8543fc9ed05006d218776d679b74a
import os
from TauFW.common.tools.utils import execute
from TauFW.PicoProducer.storage.StorageSystem import StorageSystem
import getpass, platform


class EOS(StorageSystem):
  
  def __init__(self,path,verb=0,ensure=False):
    """EOS is mounted on lxplus, so no special override are necessary."""
    super(EOS,self).__init__(path,verb=verb,ensure=False,eos=False)
    if not self.mounted: # EOS is mounted on lxplus
      if eos: # use EOS command
        # https://cern.service-now.com/service-portal?id=kb_article&n=KB0001998
        os.environ["EOS_MGM_URL"] = "root://eosuser.cern.ch"
        self.lscmd = "eos ls" # first do export EOS_MGM_URL=root://eosuser.cern.ch
      else: # use uberftp
        self.lscmd = "uberftp -ls"
        self.lsurl = "gsiftp://eoscmsftp.cern.ch/"
      self.cpcmd   = 'xrdcp -f'
      self.chmdprm = '2777'
      self.cpurl   = "root://eoscms.cern.ch/"
      self.fileurl = "root://eosuser.cern.ch/" #"root://eoscms/"
      #self.prefix  = "root://eoscms.cern.ch/"
    self.tmpdir  = '/tmp/$USER/'
    if ensure:
      self.ensuredir(self.path)
  
