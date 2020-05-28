#! /usr/bin/env python
# Author: Izaak Neutelings (May 2020)
import os
from TauFW.PicoProducer.tools.utils import execute
from TauFW.PicoProducer.storage.StorageSystem import StorageSystem
import getpass, platform


class T2_PSI(StorageSystem):
  
  def __init__(self,path,verb=0,ensure=False):
    """T2 SE on PSI."""
    super(T2_PSI).__init__(path,verb=verb,ensure=False)
    self.lscmd   = "uberftp -ls"
    self.lsurl   = "gsiftp://storage01.lcg.cscs.ch/"
    self.rmcmd   = "uberftp -rm"
    self.rmurl   = "gsiftp://t3se01.psi.ch/"
    self.mkdrcmd = "LD_LIBRARY_PATH='' PYTHONPATH='' gfal-mkdir -p"
    self.mkdrurl = 'gsiftp://t3se01.psi.ch/'
    self.cpcmd   = 'xrdcp -f'
    self.cpurl   = "root://storage01.lcg.cscs.ch/"
    self.tmpdir  = '/scratch/$USER/'
    self.fileurl = "root://storage01.lcg.cscs.ch/"
    if ensure:
      self.ensuredir(self.path)
    
    # uberftp -rm  gsiftp://t3se01.psi.ch/pnfs/psi.ch/cms//trivcat/store/user/username/directory
    # gfal-rm -r --force root://t3dcachedb03.psi.ch//pnfs/psi.ch/cms/trivcat/store/username/directory
    # uberftp storage01.lcg.cscs.ch 'rm -r /pnfs/lcg.cscs.ch/cms/trivcat/store/user/...'
  
  def rm(self,dirname,**kwargs):
    verb = kwargs.get('verb',self.verbosity)
    return self.execute("uberftp storage01.lcg.cscs.ch 'rm -r %s'"%(dirname),verb=verb)