#! /usr/bin/env python
# Author: Izaak Neutelings (May 2020)
from TauFW.PicoProducer.storage.StorageSystem import StorageSystem


class T3_PSI(StorageSystem):
  
  def __init__(self,path,verb=0,ensure=False):
    """T3 SE on PSI."""
    super(T3_PSI,self).__init__(path,verb=verb,ensure=False)
    self.rmcmd   = 'uberftp -rm'
    self.rmurl   = 'gsiftp://t3se01.psi.ch/'
    self.mkdrcmd = "LD_LIBRARY_PATH='' PYTHONPATH='' gfal-mkdir -p"
    self.mkdrurl = 'gsiftp://t3se01.psi.ch/'
    self.cpcmd   = 'xrdcp -f'
    self.cpurl   = "root://t3dcachedb03.psi.ch/"
    self.tmpdir  = '/scratch/$USER/'
    self.fileurl = "root://t3dcachedb03.psi.ch/"
    if ensure:
      self.ensuredir(self.path)
    
    # uberftp -rm  gsiftp://t3se01.psi.ch/pnfs/psi.ch/cms//trivcat/store/user/username/directory
    # gfal-rm -r --force root://t3dcachedb03.psi.ch//pnfs/psi.ch/cms/trivcat/store/username/directory
    # uberftp t3se01.psi.ch 'rm -r /pnfs/psi.ch/cms/trivcat/store/user/username/directory'
  
