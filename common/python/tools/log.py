# Author: Izaak Neutelings (May 2020)

tcol_dict = { 'black':  30,  'red':     31, 'green': 32,
              'yellow': 33,  'orange':  33, 'blue':  34,
              'purple': 35,  'magenta': 36, 'white': 37,
              'grey':   90,  'none':     0 }
bcol_dict = {k: (10+v if v else v) for k,v in tcol_dict.iteritems()}
def color(string,c='green',b=False,ul=False,**kwargs):
  tcol_key   = kwargs.get('color',     c       )
  bcol_key   = kwargs.get('bg',        None    )
  bcol_key   = kwargs.get('background',bcol_key)
  bold_code  = "\033[1m" if kwargs.get('bold',b) else ""
  ul_code    = "\033[4m" if ul else ""
  tcol_code  = "\033[%dm"%tcol_dict[tcol_key] if tcol_key!=None else ""
  bcol_code  = "\033[%dm"%bcol_dict[bcol_key] if bcol_key!=None else ""
  stop_code  = "\033[0m"
  reset_code = stop_code if kwargs.get('reset',False) else ""
  return kwargs.get('pre',"") + reset_code + bcol_code + bold_code + ul_code + tcol_code + str(string) + stop_code
  

def warning(string,**kwargs):
  return color(kwargs.get('exclam',"Warning! ")+string, color="yellow", bold=True, pre=kwargs.get('pre',">>> "))
  

def error(string,**kwargs):
  return color(kwargs.get('exclam',"ERROR! ")+string, color="red", bold=True, pre=kwargs.get('pre',">>> "))
  

def green(string,**kwargs):
  return "\033[32m%s\033[0m"%string
  

def bold(string,**kwargs):
  return kwargs.get('pre',"") + "\033[1m%s\033[0m"%(string)
  

def underlined(string,**kwargs):
  return kwargs.get('pre',"") + "\033[4m%s\033[0m"%(string)
  

#_headeri = 0
def header(*strings,**kwargs):
  #global _headeri
  prefix = kwargs.get('pre',"")
  title  = ', '.join([str(s) for s in strings if s]) #.lstrip('_')
  string = prefix+"\n" +\
           prefix+"   ###%s\n"    % ('#'*(len(title)+3)) +\
           prefix+"   #  %s  #\n" % (title) +\
           prefix+"   ###%s\n"    % ('#'*(len(title)+3)) + prefix
  #_headeri += 1
  return string
  


class Logger(object):
  """Class to customly log program."""
  
  def __init__(self, name="LOG", verb=0, **kwargs):
    self.name      = name
    self.verbosity = verb
    self.pre       = kwargs.get('pre',">>> ")
    self._table    = None
    if  kwargs.get('showname',False):
      self.pre += self.name + ": "
  
  def getverbosity(self,*args):
    """Decide verbosity level based on maximum of own verbosity and given arguments."""
    verbs = [ self.verbosity ]
    for arg in args:
      if isinstance(arg,(int,float,long)):
        verbosity = int(arg)
      elif isinstance(arg,dict):
        verbosity = arg.get('verb',0) + arg.get('verbosity',0)
      elif hasattr(arg,'verbosity'):
        verbosity = arg.verbosity
      else:
        verbosity = int(bool(arg) or 0)
      verbs.append(verbosity)
    return max(verbs)
  
  def setverbosity(self,*args):
    """Set own verbosity based with getverbosity."""
    self.verbosity = self.getverbosity(*args)
  
  def info(self,string,**kwargs):
    """Info"""
    print self.pre+string
  
  def verbose(self,string,verb=None,level=1,**kwargs):
    """Check verbosity and print if verbosity level is matched."""
    if verb==None:
      verb = self.verbosity
    elif isinstance(verb,dict):
      verb = self.getverbosity(verb)
    if verb>=level:
      pre  = self.pre+kwargs.get('pre',"")
      col  = kwargs.get('c',False)
      col  = kwargs.get('color',col)
      ul   = kwargs.get('ul',False) # undeline
      if col:
        string = color(string,col) if isinstance(col,str) else color(string)
      if ul:
        string = underlined(string)
      print pre+string
      return True
    return False
  
  def verb(self,*args,**kwargs):
    """Alias for Logger.verbose."""
    return self.verbose(*args,**kwargs)
  
  def getcolor(self,*args,**kwargs):
    """Get color."""
    return color(*args,**kwargs)
  
  def color(self,*args,**kwargs):
    """Print color."""
    print self.pre+color(*args,**kwargs)
  
  def underlined(self,*args,**kwargs):
    """Print underlined."""
    print self.pre+underlined(*args,**kwargs)
  
  def ul(self,*args,**kwargs):
    """Print underlined."""
    return self.underlined(*args,**kwargs)
  
  def warning(self,string,trigger=True,**kwargs):
    """Print warning if triggered."""
    if trigger:
      exclam  = color(kwargs.get('exclam',"Warning! "),'yellow',b=True,pre=self.pre+kwargs.get('pre',""))
      message = color(string,'yellow',pre="")
      print exclam+message
  
  def warn(self,*args,**kwargs):
    """Alias for Logger.warn."""
    return self.warning(*args,**kwargs)
  
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
    return trigger
  
  def fatal(self,string,trigger=True,**kwargs):
    """Fatal error by throwing an exception."""
    return self.throw(Exception,string,trigger=trigger,**kwargs)
  
  def throw(self,error,string,trigger=True,**kwargs):
    """Fatal error by throwing a specified exception."""
    if trigger:
      string = color(string,'red',**kwargs)
      raise error(string)
    return trigger
  
  def insist(self,condition,string,error=AssertionError,**kwargs):
    """Assert condition throwing an exception."""
    return self.throw(error,string,trigger=(not condition),**kwargs)
  
  def table(self,*args,**kwargs):
    """Initiate new table."""
    self._table = Table(*args,**kwargs)
    return self._table
  
  def tableheader(self,*args):
    """Print header of table."""
    self._table.printheader(*args)
  
  def row(self,*args):
    """Print row of table."""
    self._table.printrow(*args)
  
LOG = Logger('Global')
from TauFW.common.tools.Table import Table
