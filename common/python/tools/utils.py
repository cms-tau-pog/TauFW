# Author: Izaak Neutelings (May 2020)
from __future__ import print_function # for python3 compatibility
import os, sys, re
from itertools import islice
from subprocess import Popen, PIPE, STDOUT, CalledProcessError
from TauFW.common.tools.string import *


def execute(command,dry=False,fatal=True,verb=0):
  """Execute shell command."""
  command = str(command)
  out = ""
  if dry:
    print(">>> Dry run: %r"%(command))
  else:
    if verb>=1:
      print(">>> Executing: %r"%(command))
    try:
      process = Popen(command,stdout=PIPE,stderr=STDOUT,bufsize=0,shell=True) #,universal_newlines=True
      for line in iter(process.stdout.readline,b''): # read line by line
        line = str(line.decode('utf-8')) # decode/convert binary to str
        if verb>=1: # real time print out (does not work for python scripts without flush)
          print(line.rstrip())
        out += line
      process.stdout.close()
      retcode = process.wait()
      out = out.strip()
    except Exception as e:
      if verb<1:
        print(out) #">>> Output: %s"%(out)
      print(">>> Failed: %r"%(command))
      raise e
    if retcode and fatal:
      if verb<1:
        print(out)
      raise CalledProcessError(retcode,command)
      #raise Exception("Command '%s' ended with return code %s"%(command,retcode)) #,err)
  return out
  

def isnumber(obj):
  """Check if object is float or int."""
  return isinstance(obj,(float,int))
  

def islist(arg):
  """Check if argument is a list or tuple."""
  return isinstance(arg,(list,tuple))
  

def ensurelist(arg,nonzero=False):
  """Ensure argument is a list, if it is not already a tuple or list."""
  if isinstance(arg,set):
    arg = list(arg)
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
  

def chunkify(iterable,chunksize):
  """Divide up iterable into chunks of a given size."""
  it     = iter(iterable)
  item   = list(islice(it,chunksize))
  chunks = [ ]
  while item:
    chunks.append(item)
    item = list(islice(it,chunksize))
  return chunks
  

