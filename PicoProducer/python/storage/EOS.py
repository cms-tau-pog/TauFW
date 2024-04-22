#! /usr/bin/env python
# Author: Izaak Neutelings (May 2020)
# https://cern.service-now.com/service-portal?id=kb_article&sys_id=fae8543fc9ed05006d218776d679b74a
import os
from TauFW.common.tools.utils import execute
from TauFW.PicoProducer.storage.utils import host
from TauFW.PicoProducer.storage.StorageSystem import StorageSystem


class EOS(StorageSystem):
  
  def __init__(self,path,verb=0,ensure=False,eos=False,**kwargs):
    """EOS is mounted on lxplus, so no special overload are necessary."""
    super(EOS,self).__init__(path,verb=verb,ensure=False,**kwargs)
    if not self.mounted: # EOS is mounted on lxplus
      if eos: # use EOS command
        # https://cern.service-now.com/service-portal?id=kb_article&n=KB0001998
        os.environ["EOS_MGM_URL"] = "root://eosuser.cern.ch"
        self.lscmd = "eos ls" # first do export EOS_MGM_URL=root://eosuser.cern.ch
        self.lscmd = "eos rm" # first do export EOS_MGM_URL=root://eosuser.cern.ch
      else: # NOTE: uberftp no longer supported for EOS...
        unset = "" if 'ucl' in host else "LD_LIBRARY_PATH='' PYTHONPATH='' " # unset libraries that break gFal tools
        self.lscmd = unset+"gfal-ls -l"
        self.lsurl = "root://eoscms.cern.ch/"
        self.lscol = -1 # take last column
        self.mkdrcmd = unset+"gfal-mkdir -p"
        self.mkdrurl = "root://eosuser.cern.ch/"
        self.rmcmd = unset+"gfal-rm -r"
        self.rmurl = "root://eosuser.cern.ch/"
      self.cpcmd   = 'xrdcp -f'
      self.chmdprm = '2777'
      self.cpurl   = "root://eoscms.cern.ch/"
      self.fileurl = "root://eosuser.cern.ch/" #"root://eoscms/"
      #self.prefix  = "root://eoscms.cern.ch/"
    self.tmpdir    = '/tmp/$USER/'
    if ensure:
      self.ensuredir(self.path)
    