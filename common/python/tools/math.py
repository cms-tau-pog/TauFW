# -*- coding: utf-8 -*-
# Author: Izaak Neutelings (August 2020)
from TauFW.common.math_helper import sqrt, log10, ceil, floor


def frange(start,end,step):
  """Return a list of numbers between start and end, for a given stepsize."""
  flist = [start]
  next = start+step
  while next<end:
    flist.append(next)
    next += step
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
  

def partition(list,nparts):
  """Partion list into n chunks, as evenly sized as possible."""
  nleft    = len(list)
  divider  = float(nparts)
  parts    = [ ]
  findex   = 0
  for i in range(0,nparts): # partition recursively
    nnew   = int(ceil(nleft/divider))
    lindex = findex + nnew
    parts.append(list[findex:lindex])
    nleft   -= nnew
    divider -= 1
    findex   = lindex
    #print nnew
  return parts
  

def reldiff(x,y):
  """Get relative difference."""
  if x==0:
    return 0 if y==0 else -1
  return abs(x-y)/float(x)
  
