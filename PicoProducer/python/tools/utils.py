# Author: Izaak Neutelings (May 2020)
import itertools
from subprocess import Popen, PIPE, STDOUT


def execute(command,dry=False,verb=0):
  """Execute shell command."""
  out = ""
  if dry:
    print ">>> Dry run: %r"%(command)
  else:
    if verb>=1:
      print ">>> Executing: %r"%(command)
    try:
      #process = Popen(command.split(),stdout=PIPE,stderr=STDOUT) #,shell=True)
      process = Popen(command,stdout=PIPE,stderr=STDOUT,shell=True)
      for line in iter(process.stdout.readline,""):
        out += line
      process.stdout.close()
      #print 0, process.communicate()
      #out     = process.stdout.read()
      #err     = process.stderr.read()
      retcode = process.wait()
      #print out
      out = out.strip()
    except Exception as e:
      print out #">>> Output: %s"%(out)
      print ">>> Failed: %r"%(command)
      raise e
    if verb>=1:
      print out
    if retcode:
      if verb<1:
        print out
      raise Exception("Command '%s' ended with return code %s"%(command,retcode)) #,err)
  return out
  

def repkey(string,**kwargs):
  """Replace keys with '$'."""
  for key, value in kwargs.iteritems():
    string = string.replace('$'+key,value)
  return string
  

def chunkify(iterable,chunksize):
  """Divide up iterable into chunks of a given size."""
  it     = iter(iterable)
  item   = list(itertools.islice(it,chunksize))
  chunks = [ ]
  while item:
    chunks.append(item)
    item = list(itertools.islice(it,chunksize))
  return chunks
  
