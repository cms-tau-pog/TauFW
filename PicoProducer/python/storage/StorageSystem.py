#! /usr/bin/env python
# Author: Izaak Neutelings (May 2020)
import os
from fnmatch import fnmatch # for glob pattern
from TauFW.PicoProducer.tools.utils import execute
import getpass, platform


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
  

def getstorage(path,verb=0,ensure=False):
  if path.startswith('/eos/'):
    from TauFW.PicoProducer.storage.EOS import EOS
    storage = EOS(path,ensure=ensure,verb=verb)
  #elif path.startswith('/castor/'):
  #  return Castor(path,verb=verb)
  elif path.startswith('/pnfs/psi.ch/'):
    from TauFW.PicoProducer.storage.T3_CH_PSI import T3_CH_PSI
    return PSI_T3(path,ensure=ensure,verb=verb)
  #elif path.startswith('/pnfs/lcg.cscs.ch/'):
  #  return PSI_T2(path,verb=verb)
  #elif path.startswith('/pnfs/iihe/'):
  #  return IIHE_T2(path,verb=verb)
  else:
    storage = Local(path,ensure=ensure,verb=verb)
  if verb>=2:
    print storage
  return storage


class StorageSystem(object):
  
  def __init__(self,path,verb=0,ensure=False):
    self.path    = path
    self.lscmd   = 'ls'
    self.lsurl   = ''
    self.cdcmd   = 'cd'
    self.cdurl   = ''
    self.cpcmd   = 'cp'
    self.cpurl   = ''
    self.rmcmd   = 'rm -rf'
    self.rmurl   = ''
    self.mkdrcmd = 'mkdir -p'
    self.mkdrurl = ''
    self.chmdprm = '777'
    self.chmdcmd = 'chmod'
    self.chmdurl = ''
    self.haddcmd = 'hadd -f'
    self.tmpdir  = '/tmp/$USER/' # $TMPDIR
    self.fileurl = ""
    self.verbosity = verb
    if path.startswith('/'):
      self.parent = '/'.join(path.split('/')[:3])
    else:
      self.parent = '/'+'/'.join(path.split('/')[:2])
    self.mounted  = os.path.exists(self.parent)
  
  def __str__(self):
    return self.path
  
  def __repr__(self):
    return '<%s("%s") at %s>'%(self.__class__.__name__,self.path,hex(id(self)))
  
  def execute(self,cmd,dry=False,**kwargs):
    verb = kwargs.get('verb',self.verbosity)
    return execute(cmd,dry=dry,verb=verb)
  
  def expandpath(self,*paths,**kwargs):
    """Help function to replace variables in given path, or set default to own path."""
    #verb = kwargs.get('verb',self.verbosity)
    here  = kwargs.get('here',False)
    url   = kwargs.get('url', "")
    paths = [p for p in paths if p]
    if paths:
      path = os.path.join(*paths)
    else:
      path = self.path
    if here and path[0] not in ['/','$']:
      path = os.path.join(self.path,path)
    if url and ('$PATH' in path or path.startswith(self.parent)):
      path = url+path
    path = path.replace('$PATH',self.path)
    return path
  
  def file(self,*paths,**kwargs):
    ensure  = kwargs.get('ensure',False)
    path    = self.expandpath(*paths,here=True)
    file_   = self.fileurl + path
    if ensure:
      if not self.exists(path):
        raise IOError("Did not find %s."%(path))
    return file_
  
  def exists(self,*paths,**kwargs):
    verb = kwargs.get('verb',self.verbosity)
    path = self.expandpath(*paths,here=True)
    cmd  = "if `%s %s%s >/dev/null 2>&1`; then echo 1; else echo 0; fi"%(self.lscmd,self.lsurl,path)
    out  = self.execute(cmd,verb=verb).strip()
    return out=='1'
  
  def ensuredir(self,*paths,**kwargs):
    """Ensure path exists."""
    verb = kwargs.get('verb',self.verbosity)
    path = self.expandpath(*paths)
    if not self.exists(path,verb=verb):
      self.mkdir(path,verb=verb)
    return True
  
  def cd(self,*paths,**kwargs):
    #verb = kwargs.get('verb',self.verbosity)
    path = self.expandpath(*paths)
    ret  = os.chdir(path)
    #ret  = self.execute("%s %s%s"%(self.cdcmd,self.cdurl,path)).split('\n')
    return ret
  
  def ls(self,*paths,**kwargs):
    verb    = kwargs.get('verb',self.verbosity)
    dryrun  = kwargs.get('dry', False)
    filter  = kwargs.get('filter',None) # filter with glob pattern, like '*' or '[0-9]' wildcards
    path    = self.expandpath(*paths)
    retlist = self.execute("%s %s%s"%(self.lscmd,self.lsurl,path),dry=dryrun,verb=verb).split('\n')
    if filter:
      for file in retlist[:]:
        if not fnmatch(file,filter):
          retlist.remove(file)
    return retlist
  
  def getfiles(self,*paths,**kwargs):
    """Get list of files in a given path.
    Return list of files with full path name, and if needed, a file URL.
    Use the 'filter' option to filter the list of file names with some pattern."""
    verb     = kwargs.get('verb',self.verbosity)
    path     = self.expandpath(*paths)
    filelist = self.ls(path,**kwargs)
    url      = self.fileurl if path.startswith(self.parent) else ""
    for i, file in enumerate(filelist):
      filelist[i] = url+os.path.join(path,file)
    return filelist
  
  def cp(self,source,target=None,**kwargs):
    verb   = kwargs.get('verb',self.verbosity)
    source = self.expandpath(source,url=self.cpurl)
    target = self.expandpath(target,url=self.cpurl)
    return self.execute("%s %s %s"%(self.cpcmd,source,target),verb=verb)
  
  def hadd(self,sources,target,**kwargs):
    target  = self.expandpath(target,here=True)
    verb    = kwargs.get('verb',self.verbosity)
    usetmp  = kwargs.get('tmp', self.cpurl!='') and not target.startswith('/')
    htarget = target
    if usetmp:
      htarget = os.path.join(self.tmpdir,os.path.basename(target))
    if isinstance(sources,basestring):
      sources = [ sources ]
    source = ""
    for i, file in enumerate(sources,1):
      source += self.expandpath(file,url=self.fileurl)+' '
    source = source.strip()
    if verb>=2:
      print ">>> %-10s = %r"%('sources',sources)
      print ">>> %-10s = %r"%('source',source)
      print ">>> %-10s = %r"%('target',target)
      print ">>> %-10s = %r"%('htarget',htarget)
    out = self.execute("%s %s %s"%(self.haddcmd,htarget,source),verb=verb)
    if usetmp:
    
      cpout = self.cp(htarget,target,verb=verb)
    return out
  
  def rm(self,dirname,**kwargs):
    verb = kwargs.get('verb',self.verbosity)
    return self.execute("%s %s%s"%(self.rmcmd,self.rmurl,dirname),verb=verb)
  
  def mkdir(self,dirname='$PATH',**kwargs):
    verb    = kwargs.get('verb',self.verbosity)
    dirname = self.expandpath(dirname)
    return self.execute("%s %s%s"%(self.mkdrcmd,self.mkdrurl,dirname),verb=verb)
  
  def chmod(self,file,perm=None,**kwargs):
    verb = kwargs.get('verb',self.verbosity)
    if not perm: perm = self.chmdprm
    return self.execute("%s %s %s%s"%(self.chmdcmd,perm,self.chmdurl,file),verb=verb)
  

class Local(StorageSystem):
  
  def __init__(self,path,verb=0,ensure=False):
    super(Local,self).__init__(path,verb=verb,ensure=ensure)
  
