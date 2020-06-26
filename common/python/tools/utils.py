# Author: Izaak Neutelings (May 2020)
import os, sys
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
  

def isnumber(arg):
  return isinstance(arg,float) or isinstance(arg,int)
  
def islist(arg):
  """Check if argument is a list or tuple."""
  return isinstance(arg,list) or isinstance(arg,tuple)
  
def ensurelist(arg):
  """Ensure argument is a list, if it is not already a tuple or list."""
  if not islist(arg):
    arg = [arg]
  return arg
  
def unwrapargs(args):
  """Unwrap arguments from function's *args."""
  if len(args)==1 and islist(args[0]):
    args = args[0]
  return args
  
def repkey(string,**kwargs):
  """Replace keys with '$'."""
  for key, value in kwargs.iteritems():
    string = string.replace('$'+key,value)
  return string
  

def chunkify(iterable,chunksize):
  """Divide up iterable into chunks of a given size."""
  it     = iter(iterable)
  item   = list(islice(it,chunksize))
  chunks = [ ]
  while item:
    chunks.append(item)
    item = list(islice(it,chunksize))
  return chunks
  
