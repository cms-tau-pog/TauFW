#! /usr/bin/env python
# Author: Izaak Neutelings (May 2020)
import os
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
  

def getstorage(path,verb=0):
  if path.startswith('/eos/'):
    from TauFW.PicoProducer.storage.EOS import EOS
    storage = EOS(path,verb=verb)
  #if path.startswith('/castor/'): return Castor(path,verb=verb)
  #if path.startswith('/pnfs/psi.ch/'): return PSI_T3(path,verb=verb)
  #if path.startswith('/pnfs/lcg.cscs.ch/'): return PSI_T2(path,verb=verb)
  #if path.startswith('/pnfs/iihe/'): return IIHE_T2(path,verb=verb)
  else:
    storage = Local(path,verb=verb)
  if verb>=2:
    print storage
  return storage


class StorageSystem(object):
  
  def __init__(self,path,verb=0,ensure=False):
    self.path    = path
    self.parent  = '/'+'/'.join(path.split('/')[:2])
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
    self.haddurl = ''
    self.tmpurl  = '/tmp/$USER/' # $TMPDIR
    self.prefix  = ""
    self.fileurl = ""
    self.verbosity = verb
    if ensure and not self.exists(path):
      self.mkdir(path)
  
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
      path  = os.path.join(*paths)
    else:
      path  = self.path
    if here and path[0] not in ['/','$']:
      path = os.path.join(self.path,path)
    if url and ('$PATH' in path or path.startswith(self.parent)):
      path = url+path
    return path.replace('$PATH',self.path)
  
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
    out  = self.execute(cmd).strip()
    return out=='1'
  
  def cd(self,*paths,**kwargs):
    #verb = kwargs.get('verb',self.verbosity)
    path = self.expandpath(*paths)
    ret  = os.chdir(path)
    #ret  = self.execute("%s %s%s"%(self.cdcmd,self.cdurl,path)).split('\n')
    return ret
  
  def ls(self,*paths,**kwargs):
    verb    = kwargs.get('verb',self.verbosity)
    path    = self.expandpath(*paths)
    retlist = self.execute("%s %s%s"%(self.lscmd,self.lsurl,path),verb=verb).split('\n')
    return retlist
  
  def cp(self,source,target=None,**kwargs):
    verb   = kwargs.get('verb',self.verbosity)
    source = self.expandpath(source,url=self.cpurl)
    target = self.expandpath(target,url=self.cpurl)
    return self.execute("%s %s %s"%(self.cpcmd,source,target),verb=verb)
  
  def hadd(self,sources,target=None,**kwargs):
    verb   = kwargs.get('verb',self.verbosity)
    target = self.expandpath(target)
    if isinstance(sources,str):
      sources = [ sources ]
    source = ""
    for i, file in enumerate(sources,1):
      source = self.haddurl+self.expandpath(file)
      if i<len(sources): source += " "
    return self.execute("%s %s %s"%(self.haddcmd,target,source))
  
  def rm(self,dirname,**kwargs):
    verb = kwargs.get('verb',self.verbosity)
    return self.execute("%s %s%s"%(self.rmcmd,self.rmurl,dirname))
  
  def mkdir(self,dirname='$PATH',**kwargs):
    verb    = kwargs.get('verb',self.verbosity)
    dirname = self.expandpath(dirname)
    return self.execute("%s %s%s"%(self.mkdrcmd,self.mkdrurl,dirname))
  
  def chmod(self,file,perm=None,**kwargs):
    verb = kwargs.get('verb',self.verbosity)
    if not perm: perm = self.chmdprm
    return self.execute("%s %s %s%s"%(self.chmdcmd,perm,self.chmdurl,file))
  

class Local(StorageSystem):
  
  def __init__(self,path,verb=0,ensure=False):
    super(Local,self).__init__(path,verb=verb,ensure=ensure)
  
