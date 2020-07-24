#! /usr/bin/env python
# Author: Izaak Neutelings (July 2020)
# Description: Test unwrapping of arguments for gethist and gethist2D
#   test/testUnwrapping.py
from TauFW.common.tools.log import color
from TauFW.Plotter.sample.utils import LOG, unwrap_gethist_args, unwrap_gethist2D_args
from TauFW.Plotter.plot.Variable import Variable
from TauFW.Plotter.plot.Selection import Selection
LOG.verbosity = 1


def colvar(string):
  for var in ['m_vis', 'pt_1', 'njets', ]:
    var = repr(var) 
    string = string.replace(var,color(var))
  for classname in ['Variable', 'Selection' ]:
    string = string.replace(classname,color(classname,'grey'))
  return string


def printIO(name,func,*args):
  print colvar(">>> %s(%s) returns "%(name,','.join(repr(a) for a in args)))
  for result in func(*args):
    print ">>>  ",colvar(repr(result))
  

def main():
  
  selections = [
    "",
    "pt_1>50 && pt_2>50",
    Selection("pt_1>50 && pt_2>50"),
  ] 
  mvisbins   = [0,30,40,50,60,70,75,80,90,100,120,200]
  pt_1bins   = [0,30,40,50,60,70,75,80,90,100,120,200]
  xvar       = Variable('m_vis', 40, 0,200)
  yvar       = Variable('pt_1',  40, 0,200)
  varlist1   = [
    Variable('m_vis', 40, 0,200),
    Variable('njets',  8, 0,  8),
  ]
  varlist2   = [
    ('m_vis', mvisbins),
    ('njets', 8, 0,  8),
  ]
  xvarlist1 = varlist1
  yvarlist1 = varlist1[::-1] # reverse
  xvarlist2 = varlist2
  yvarlist2 = varlist2[::-1] # reverse
  
  # UNWRAP args to gethist
  LOG.header("unwrap_gethist_args")
  name, func = "unwrap_gethist_args", unwrap_gethist_args
  for selection in selections:
    printIO(name,func,'m_vis',40,0,200,selection)
    printIO(name,func,'m_vis',mvisbins,selection)
    printIO(name,func,xvar,selection)
    printIO(name,func,varlist1,selection)
    printIO(name,func,varlist2,selection)
    print ">>> "
  
  # UNWRAP args to gethist2D
  LOG.header("unwrap_gethist2D_args")
  name, func = "unwrap_gethist2D_args", unwrap_gethist2D_args
  for selection in selections:
    printIO(name,func,'m_vis',40,0,200,'pt_1',40,0,200,selection)
    printIO(name,func,'m_vis',mvisbins,'pt_1',pt_1bins,selection)
    printIO(name,func,'m_vis',40,0,200,'pt_1',pt_1bins,selection)
    printIO(name,func,'m_vis',mvisbins,'pt_1',40,0,200,selection)
    printIO(name,func,xvar,yvar,selection)
    printIO(name,func,(xvar,yvar),selection)
    printIO(name,func,[(xvar,yvar)],selection)
    printIO(name,func,xvarlist1,yvarlist1,selection)
    printIO(name,func,xvarlist2,yvarlist2,selection)
    printIO(name,func,zip(xvarlist1,yvarlist1),selection)
    print ">>> "
  

if __name__ == "__main__":
  main()
  print
  
