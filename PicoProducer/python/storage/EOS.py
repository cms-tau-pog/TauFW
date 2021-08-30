#! /usr/bin/env python
# Author: Izaak Neutelings (May 2020)
# https://cern.service-now.com/service-portal?id=kb_article&sys_id=fae8543fc9ed05006d218776d679b74a
import os
from TauFW.common.tools.utils import execute
from TauFW.PicoProducer.storage.StorageSystem import StorageSystem
import getpass, platform


class EOS(StorageSystem):
  
  def __init__(self,path,verb=0,ensure=False,eos=False):
    """EOS is mounted on lxplus, so no special override are necessary."""
    super(EOS,self).__init__(path,verb=verb,ensure=False)
    if not self.mounted: # EOS is mounted on lxplus
      if eos: # use EOS command
        # https://cern.service-now.com/service-portal?id=kb_article&n=KB0001998
        os.environ["EOS_MGM_URL"] = "root://eosuser.cern.ch"
        self.lscmd = "eos ls" # first do export EOS_MGM_URL=root://eosuser.cern.ch
        self.lscmd = "eos rm" # first do export EOS_MGM_URL=root://eosuser.cern.ch
      else: # use uberftp; NOTE: doest not work for /eos/user/...
        self.lscmd = "uberftp -ls"
        self.lsurl = "gsiftp://eoscmsftp.cern.ch/"
        self.lscol = -1 # take last column
        self.rmcmd = 'uberftp -rm'
        self.rmurl = 'gsiftp://eoscmsftp.cern.ch/'
        self.mkdir = self._mkdir # override default StorageSystem.mkdir
      self.cpcmd   = 'xrdcp -f'
      self.chmdprm = '2777'
      self.cpurl   = "root://eoscms.cern.ch/"
      self.fileurl = "root://eosuser.cern.ch/" #"root://eoscms/"
      #self.prefix  = "root://eoscms.cern.ch/"
    self.tmpdir    = '/tmp/$USER/'
    if ensure:
      self.ensuredir(self.path)
  
  #def _rm(self,*paths,**kwargs):
  #  path = self.expandpath(*paths,here=True)
  #  verb = kwargs.get('verb',self.verbosity)
  #  return self.execute("uberftp storage01.lcg.cscs.ch 'rm -r %s'"%(path),verb=verb)
  
  def _mkdir(self,dirname='$PATH',**kwargs):
    verb    = kwargs.get('verb',self.verbosity)
    dirname = self.expandpath(dirname,here=True)
    return self.execute("uberftp eoscmsftp.cern.ch 'mkdir %s'"%(dirname),verb=verb)