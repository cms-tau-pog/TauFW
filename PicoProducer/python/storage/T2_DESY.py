#! /usr/bin/env python
# Author: Andrea Cardini (September 2020)
import os
import glob
from TauFW.common.tools.utils import execute
from TauFW.PicoProducer.storage.StorageSystem import StorageSystem


class T2_DESY(StorageSystem):
  
  def __init__(self,path,verb=0,ensure=False):
    """dCache at DESY"""
    super(T2_DESY,self).__init__(path,verb=verb,ensure=False)
    self.lscmd   = "ls"
    self.lsurl   = ""
    self.rmcmd   = "srmrm"
    self.rmurl   = ""
    self.mkdrcmd = "srmmkdir"
    self.mkdrurl = ''
    self.cpcmd   = 'srmcp'
    self.cpurl   = ""
    self.tmpdir  = ''
    self.fileurl = ""
    if ensure:
      self.ensuredir(self.path)
    
    # uberftp -rm  gsiftp://t3se01.psi.ch/pnfs/psi.ch/cms//trivcat/store/user/username/directory
    # gfal-rm -r --force root://t3dcachedb03.psi.ch//pnfs/psi.ch/cms/trivcat/store/username/directory
    # uberftp storage01.lcg.cscs.ch 'rm -r /pnfs/lcg.cscs.ch/cms/trivcat/store/user/...'
  
  def rm(self,paths,**kwargs):
    verb = kwargs.get('verb',self.verbosity)
    paths=glob.glob(paths)
    for path in paths:
      pathname = self.expandpath(path,here=True)
      verb = kwargs.get('verb',self.verbosity)
      isfile = '.' in os.path.basename(pathname)
      if isfile:
        self.execute('srmrm "srm://dcache-se-cms.desy.de:8443/srm/managerv2?SFN=%s"'%(pathname),verb=verb)
      else:
        self.execute('srmrmdir -recursive "srm://dcache-se-cms.desy.de:8443/srm/managerv2?SFN=%s"'%(pathname),verb=verb)
    return
    
  def mkdir(self,dirname='$PATH',**kwargs):
    verb    = kwargs.get('verb',self.verbosity)
    dirname = self.expandpath(dirname,here=True)
    return self.execute('srmmkdir "srm://dcache-se-cms.desy.de:8443/srm/managerv2?SFN=%s"'%(dirname),verb=verb)

  def cp(self,source,target=None,**kwargs):
    """Copy files."""
    source=glob.glob(source)
    dryrun = kwargs.get('dry', False)
    verb   = kwargs.get('verb',self.verbosity)
    print source
    print target
    if isinstance(source,list):
      for source_ in source:
        print source_
        source_ = self.expandpath(source_,url=self.cpurl)
        target = self.expandpath(target,url=self.cpurl)
        self.rm('%s/%s'%(os.path.abspath(target),source_))
        self.execute('srmcp -2 "file:%s srm://dcache-se-cms.desy.de:8443/%s/%s"'%(os.path.abspath(source_),os.path.abspath(target),source_),dry=dryrun,verb=verb)
      return
    else:
      print source
      source = self.expandpath(source,url=self.cpurl)
      target = self.expandpath(target,url=self.cpurl)
      self.rm('%s/%s'%(os.path.abspath(target),source))
      return self.execute('srmcp -2 "file:%s srm://dcache-se-cms.desy.de:8443/%s/%s"'%(os.path.abspath(source),os.path.abspath(target),source),dry=dryrun,verb=verb)
    
  def hadd(self,sources,target,**kwargs):
    """Hadd files. Create intermediate target file if needed."""
    htarget = self.expandpath(target,here=False)
    target  = self.expandpath(target,here=True)
    dryrun  = kwargs.get('dry',    False)
    verb    = kwargs.get('verb',   self.verbosity)
    fileurl = kwargs.get('url',    self.fileurl)
    tmpdir  = kwargs.get('tmpdir', target.startswith(self.parent) and self.cpurl!='')
    if isinstance(sources,basestring):
      sources = [ sources ]
    source = ""
    for i, file in enumerate(sources,1):
      fname = os.path.basename(file)
      if '$PATH' in file and fileurl and isglob(fname): # expand glob pattern
        parent = os.path.dirname(file)
        files  = self.getfiles(parent,filter=fname,url=fileurl)
        source += ' '.join(files)+' '
      else:
        source += self.expandpath(file,url=fileurl)+' '
    source = source.strip()
    if verb>=2:
      print ">>> %-10s = %r"%('sources',sources)
      print ">>> %-10s = %r"%('source',source)
      print ">>> %-10s = %r"%('target',target)
      print ">>> %-10s = %r"%('htarget',htarget)
    out = self.execute("%s %s %s"%(self.haddcmd,htarget,source),dry=dryrun,verb=verb)
    cpout = self.cp(htarget,os.path.dirname(target),dry=dryrun,verb=verb)
    if not dryrun:
      self.execute("rm %s"%htarget)
    return out
