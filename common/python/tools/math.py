# -*- coding: utf-8 -*-
# Author: Izaak Neutelings (August 2020)
from TauFW.common.math_helper import sqrt, log10, ceil, floor


def frange(start,end,step,scale=1000):
  """Return a list of numbers between start and end, for a given stepsize."""
  flist = [start]
  next = start+step
  i = 1
  while next<end:
    i += 1
    flist.append(next)
    next = start+(scale*i)*step/scale # safer against rounding errors than next += step
  return flist
  

def magnitude(x):
  """Get magnitude of a number. E.g. 45 is 2, 2304 is 4, 0.84 is -1"""
  if x==0: return 0
  if x==1: return 1
  logx = round(log10(abs(x))*1e6)/1e6
  if x%10==0: return int(logx)+1
  if x<1: return int(floor(logx))
  return int(ceil(logx))
  

def round2digit(x,digit=1,multiplier=1):
  """Round off number x to first signicant digit."""
  x = float(x)/multiplier
  precision = (digit-1)-magnitude(x)
  if multiplier!=1 and int(x*10**precision)==1: precision += 1
  return multiplier*round(x,precision)
  

def ceil2digit(x,digit=1,multiplier=1):
  """Round up number x to first signicant digit."""
  if x==0: return 0
  x = float(x)
  e = int(floor(log(abs(x),10)))-(digit-1)
  if multiplier>1: e = e - ceil(log(multiplier,10))
  return ceil(x/multiplier/(10.**e))*(10.**e)*multiplier
  

def columnize(oldlist,ncol=2):
  """Transpose lists into n columns, useful for TLegend,
  e.g. [1,2,3,4,5,6,7] -> [1,5,2,6,3,7,4] for ncol=2."""
  if ncol<2:
    return oldlist
  parts   = partition(oldlist,ncol)
  collist = [ ]
  row     = 0
  assert len(parts)>0, "len(parts)==0"
  while len(collist)<len(oldlist):
    for part in parts:
      if row<len(part):
        collist.append(part[row])
    row += 1
  return collist
  

def partition(mylist,nparts=None,nmax=None):
  """Partion list into given number of chunks, as evenly sized as possible."""
  if nmax!=None:
    nparts = ceil(len(mylist)/float(nmax)) # chunk can contain nmax elements at most 
  elif nparts==None:
    raise IOError("partition: Please pass nparts or nmax (both are None)!")
  nleft    = len(mylist)
  divider  = float(nparts)
  parts    = [ ]
  findex   = 0
  for i in range(0,nparts): # partition recursively
    nnew   = int(ceil(nleft/divider))
    lindex = findex + nnew
    parts.append(mylist[findex:lindex])
    nleft   -= nnew
    divider -= 1
    findex   = lindex
    #print("partition: nnew=%r"%(nnew))
  return parts
  

def partition_by_max(mylist,nmax):
  """Partition list by grouping elements
  with sum below or equal to given maximum."""
  mylist.sort(reverse=True)
  inputs = mylist[:]
  result = [ ]
  while len(inputs)>0:
    first = inputs[0]
    tot   = first
    result.append([first])
    inputs.remove(first)
    for x in inputs[:]:
      if tot+x<=nmax:
        result[-1].append(x)
        inputs.remove(x)
        if tot+x==nmax: break
        tot += x
      else:
        continue
  return result
  

def reldiff(x,y):
  """Get relative difference."""
  if x==0:
    return 0 if y==0 else -1
  return abs(x-y)/float(x)
  

def scalevec(a,b,r,log=False):
  """Scale vector ab by r."""
  if log:
    assert a!=0, "scale: Cannot logarithmically scale ab vector if a=0!"
    assert a*b>0, "scale: Cannot logarithmically scale ab vector if a and b do not have the same sign! a=%s, b=%s"%(a,b)
    span = abs(r*log10(b/a)) # get magnitude range
    return a*(10**span)
  return a+r*(b-a)
  
