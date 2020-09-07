# Author: Izaak Neutelings (May 2020)
import os, sys, re
from itertools import islice
from subprocess import Popen, PIPE, STDOUT, CalledProcessError


def execute(command,dry=False,fatal=True,verb=0):
  """Execute shell command."""
  command = str(command)
  out = ""
  if dry:
    print ">>> Dry run: %r"%(command)
  else:
    if verb>=1:
      print ">>> Executing: %r"%(command)
    try:
      #process = Popen(command.split(),stdout=PIPE,stderr=STDOUT) #,shell=True)
      process = Popen(command,stdout=PIPE,stderr=STDOUT,bufsize=1,shell=True) #,universal_newlines=True
      for line in iter(process.stdout.readline,""):
        if verb>=1: # real time print out (does not work for python scripts without flush)
          print line.rstrip()
        out += line
      process.stdout.close()
      retcode = process.wait()
      ##print 0, process.communicate()
      ##out     = process.stdout.read()
      ##err     = process.stderr.read()
      ##print out
      out = out.strip()
    except Exception as e:
      if verb<1:
        print out #">>> Output: %s"%(out)
      print ">>> Failed: %r"%(command)
      raise e
    if retcode and fatal:
      if verb<1:
        print out
      raise CalledProcessError(retcode,command)
      #raise Exception("Command '%s' ended with return code %s"%(command,retcode)) #,err)
  return out
  

def isnumber(obj):
  """Check if object is float or int."""
  return isinstance(obj,float) or isinstance(obj,int)
  

def convertstr(string):
  """Convert a string to a boolean, float or int if possible."""
  if isinstance(string,str):
    if string.isdigit():
      string = int(string)
    elif string=='True':
      string = True
    elif string=='False':
      string = False
    elif string.count('.')==1 and re.match(r"^[-+]?[\d.]+\d*$",string):
      string = float(string)
  return string
  

def quotestrs(strings):
  """Make summation of quoted strings."""
  return ", ".join(repr(s) for s in strings if s)
  

def isglob(string):
  """Return if string is likely a glob pattern."""
  return '*' in string or '?' in string or ('[' in string and ']' in string)
  

def islist(arg):
  """Check if argument is a list or tuple."""
  return isinstance(arg,list) or isinstance(arg,tuple)
  

def ensurelist(arg,nonzero=False):
  """Ensure argument is a list, if it is not already a tuple or list."""
  if not islist(arg):
    arg = [ ] if (nonzero and not arg) else [arg]
  elif nonzero:
    arg = [a for a in arg if a]
  return arg
  

def unwraplistargs(args):
  """Unwrap arguments from function's *args,
  works as long as expected args are not lists or tuples."""
  if len(args)==1 and islist(args[0]):
    args = args[0]
  if isinstance(args,tuple): # convert tuple to list
    args = list(args)
  return args
  

def repkey(string,**kwargs):
  """Replace keys with '$'."""
  for key, value in sorted(kwargs.items(),key=lambda x: -len(x[0])):
    if '${'+key in string: # BASH variable expansions
      matches = re.findall(r"\$\{%s:(\d*):(\d+)\}"%(key),string)
      for a, b in matches:
        substr = value[int(a or 0):int(b)]
        string = re.sub(r"\$\{%s:%s:%s\}"%(key,a,b),substr,string)
    string = string.replace('$'+key,str(value))
  return string
  

def rreplace(string,old,new='',count=-1):
  """Replace occurrences substring from right to left."""
  parts = string.rsplit(old,count)
  return new.join(parts)
  

def lreplace(string,old,new='',count=-1):
  """Replace occurrences substring from left to right."""
  parts = string.split(old,count)
  return new.join(parts)
  

def chunkify(iterable,chunksize):
  """Divide up iterable into chunks of a given size."""
  it     = iter(iterable)
  item   = list(islice(it,chunksize))
  chunks = [ ]
  while item:
    chunks.append(item)
    item = list(islice(it,chunksize))
  return chunks
  

def tryint(x):
  """Convert to integer, if it is possible."""
  try:
    return int(x)
  except ValueError:
    return x
  

def alphanum_key(string):
  """Turn a string into a list of string and number chunks,
  e.g. "z23a" -> ["z", 23, "a"]
  Useful for sorting a list of strings containing numbers 'naturally'/'alphanumerically',
  e.g. sorted(['z10','z1','z2','z20'],key=alphanum_key)"""
  # https://nedbatchelder.com/blog/200712/human_sorting.html
  return [ tryint(x) for x in re.split("([0-9]+)",string) ]
  

def getyear(string):
  """Recognize year from era string."""
  year = string
  if isinstance(string,str):
    matches = re.findall(r"(?:20)?[0-3]\d",string)
    if matches:
      matches.sort(key=lambda x: len(x),reverse=True)
      year = int(matches[0])
      if year<2000:
        year += 2000
  return year
  
