# Author: Izaak Neutelings (May 2020)

tcol_dict = { 'black':  30,  'red':     31, 'green': 32,
              'yellow': 33,  'orange':  33, 'blue':  34,
              'purple': 35,  'magenta': 36, 'white': 37,
              'grey':   90,  'none':     0 }
bcol_dict = {k: (10+v if v else v) for k,v in tcol_dict.iteritems()}
def color(string,c='green',b=False,**kwargs):
  tcol_key   = kwargs.get('color',     c     )
  bcol_key   = kwargs.get('background','none')
  bold_code  = "\033[1m" if kwargs.get('bold',b) else ""
  tcol_code  = "\033[%dm"%tcol_dict[tcol_key] if tcol_key!='none' else ""
  bcol_code  = "\033[%dm"%bcol_dict[bcol_key] if bcol_key!='none' else ""
  stop_code  = "\033[0m"
  reset_code = stop_code if kwargs.get('reset',False) else ""
  return kwargs.get('pre',"") + reset_code + bcol_code + bold_code + tcol_code + string + stop_code
  

def warning(string,**kwargs):
  return color(kwargs.get('exclam',"Warning! ")+string, color="yellow", bold=True, pre=kwargs.get('pre',">>> "))
  

def error(string,**kwargs):
  return color(kwargs.get('exclam',"ERROR! ")+string, color="red", bold=True, pre=kwargs.get('pre',">>> "))
  

def green(string,**kwargs):
  return "\033[32m%s\033[0m"%string
  

def error(string,**kwargs):
  print ">>> \033[1m\033[91m%sERROR! %s\033[0m"%(kwargs.get('pre',""),string)
  

def warning(string,**kwargs):
  print ">>> \033[1m\033[93m%sWarning!\033[0m\033[93m %s\033[0m"%(kwargs.get('pre',""),string)
  

def bold(string):
  return "\033[1m%s\033[0m"%(string)
  

_headeri = 0
def header(*strings):
  global _headeri
  title  = ', '.join([str(s).lstrip('_') for s in strings if s])
  string = ("\n\n" if _headeri>0 else "\n") +\
           "   ###%s\n"    % ('#'*(len(title)+3)) +\
           "   #  %s  #\n" % (title) +\
           "   ###%s\n"    % ('#'*(len(title)+3))
  _headeri += 1
  return string
  


class Logger(object):
  """Class to customly log program."""
  
  def __init__(self, name="unnamed", verb=0, **kwargs):
    self.name      = name
    self.verbosity = verb
    self.pre       = ">>> "
    self._table    = None
  
  def getverb(self,*args):
    """Set verbosity level of each module."""
    verbosities = [ self.verbosity ]
    for arg in args:
      if isinstance(arg,dict):
        verbosity = arg.get('verb',0) or 0
      else:
        verbosity = arg or 0
      verbosities.append(verbosity)
    return max(verbosities)
  
  def info(self,string,**kwargs):
    """Info"""
    print self.pre+string
  
  def color(self,*args,**kwargs):
    """Print color."""
    print self.pre+color(*args,**kwargs)
  
  def warning(self,string,trigger=True,**kwargs):
    """Print warning if triggered."""
    if trigger:
      exclam  = color(kwargs.get('exclam',"Warning! "),'yellow',b=True,pre=self.pre+kwargs.get('pre',""))
      message = color(string,'yellow',pre="")
      print exclam+message
  
  def title(self,*args,**kwargs):
    print header(*args,**kwargs)
  
  def header(self,*args,**kwargs):
    print header(*args,**kwargs)
  
  def error(self,string,trigger=True,**kwargs):
    """Print error if triggered without throwing an exception."""
    if trigger:
      exclam  = color(kwargs.get('exclam',"ERROR! "),'red',b=True,pre=self.pre+kwargs.get('pre',""))
      message = color(string,'red',pre="")
      print exclam+message
  
  def fatal(self,*args,**kwargs):
    """Fatal error by throwing an exception."""
    self.error(*args,**kwargs)
    raise Exception
  
  def throw(self,error,string,**kwargs):
    """Fatal error by throwing an exception."""
    string = color(string,'red',**kwargs)
    raise error(string)
  
  def verbose(self,string,verb=None,level=None,**kwargs):
    """Check verbosity and print if verbosity level is matched."""
    if verb==None:
      verb   = self.verbosity
    if level==None:
      level  = False
      kwargs['pre'] = self.pre+kwargs.get('pre',"")
      printVerbose(string,verbosity,level,**kwargs)
  
  #def table(self,format,**kwargs):
  #  """Initiate new table."""
  #  self._table = Table(format)
  #
  #def theader(self,*args):
  #  """Print header of table."""
  #  self._table.header(*args)
  #
  #def row(self,*args):
  #  """Print row of table."""
  #  self._table.row(*args)
  

