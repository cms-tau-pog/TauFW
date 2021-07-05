# -*- coding: utf-8 -*-
# Author: Izaak Neutelings (2019)
# Description: Efficiently draw multiple histograms with one loop over all events in a TTree
#              This script injects a MultiDraw method into TTree when it is imported.
# Source: https://github.com/pwaller/minty/blob/master/minty/junk/MultiDraw.py
import os, re, traceback
from ROOT import gROOT, gDirectory, TObject, TTree, TObjArray, TTreeFormula,\
                 TH1D, TH2D, TH2, SetOwnership, TTreeFormulaManager
moddir = os.path.dirname(os.path.realpath(__file__))
macro  = os.path.join(moddir,"MultiDraw.cxx")
def error(string): # raise RuntimeError in red color
  return RuntimeError("\033[31m"+string+"\033[0m")

# LOAD MultiDraw macro
try:
  gROOT.ProcessLine(".L %s+O"%macro)
  from ROOT import MultiDraw as _MultiDraw
  from ROOT import MultiDraw2D as _MultiDraw2D
except:
  print traceback.format_exc()
  raise error('MultiDraw.py: Failed to import the MultiDraw macro "%s"'%macro)
  
def makeTObjArray(theList):
  """Turn a python iterable into a ROOT TObjArray"""
  # Make PyROOT give up ownership of the things that are being placed in the
  # TObjArary. They get deleted because of result.SetOwner()
  result = TObjArray()
  result.SetOwner()
  for item in theList:
    SetOwnership(item, False)
    result.Add(item)
  return result
  
varregex   = re.compile(r"(.*?)\s*>>\s*(.*?)\s*\(\s*(.*?)\s*\)$") # named, create new histogram
varregex2  = re.compile(r"(.*?)\s*>>\s*(.*?)\s*$") # unnamed; existing histogram
varregex2D = re.compile(r"^([^?]+)(?<!:)\s*:\s*(?!:)(.+)$") # look for single :, excluding double (e.g. TMath::Sqrt)
binregex   = re.compile(r"(\d+)\s*,\s*([+-]?\d*\.?\d*)\s*,\s*([+-]?\d*\.?\d*)")
binregex2D = re.compile(r"(\d+)\s*,\s*([+-]?\d*\.?\d*)\s*,\s*([+-]?\d*\.?\d*)\s*,\s*(\d+)\s*,\s*([+-]?\d*\.?\d*)\s*,\s*([+-]?\d*\.?\d*)")
def MultiDraw(self, varexps, selection='1', drawoption="", **kwargs):
    """Draws multiple histograms in one loop over a tree (self).
    Instead of:
      tree.Draw( "pt_1 >> a(100, 0, 100)", "weightA" )
      tree.Draw( "pt_2 >> b(100, 0, 100)", "weightB" )
    Do:
      tree.MultiDraw( ( "pt_1 >> a(100, 0, 100)", "weightA" ),
                      ( "pt_2 >> b(100, 0, 100)", "weightB" ) )
    This is significantly faster when there are many histograms to be drawn.
    The first parameter, commonWeight, decides a weight given to all histograms.
    An arbitrary number of additional histograms may be specified. They can 
    either be specified with just a string containing the formula to be 
    drawn, the histogram name and bin configuration. 
    Alternatively it can be a tuple, with  said string, and an additional
    string specifying the weight to be applied to that histogram only."""
    
    selection = kwargs.get('cut',       selection ) # selections cuts
    verbosity = kwargs.get('verbosity', 0         ) # verbosity
    poisson   = kwargs.get('poisson',   False     ) # kPoisson errors for data
    sumw2     = kwargs.get('sumw2',     False     ) # sumw2 for MC
    histlist  = kwargs.get('hists',     [ ]       ) # to not rely on gDirectory.Get(histname)
    
    hists     = { }
    results, xformulae, yformulae, weights = [ ], [ ], [ ], [ ]
    lastXVar, lastYVar, lastWeight = None, None, None
    
    # A weight common to everything being drawn
    commonFormula = TTreeFormula("commonFormula", selection, self)
    commonFormula.SetQuickLoad(True)
    
    if not commonFormula.GetTree():
      raise error("MultiDraw: TTreeFormula 'selection' did not compile:\n  selection:  %r\n  varexps:    %s"%(selection,varexps))
    
    for i, varexp in enumerate(varexps):
        #print '  Variable expression: %s'%(varexp,)
        yvar = None
        
        # EXPAND varexp
        weight = None
        if isinstance(varexp,(tuple,list)) and len(varexp)==2:
          varexp, weight = varexp
        elif not isinstance(varexp,str):
          raise IOError("MultiDraw: given varexp is not a string or tuple of length 2! Got varexp=%s (%s)"%(varexp,type(varexp)))
        if not varexp: varexp = '1'
        if not weight: weight = '1'
        
        # PREPARE histogram
        match = varregex.match(varexp)
        if match: # create new histogram: varexp = "x >> h(100,0,100)" or "y:x >> h(100,0,100,100,0,100)"
            xvar, name, binning = match.group(1), match.group(2), match.group(3)
            
            # CREATE HISTOGRAM
            vmatch = varregex2D.match(xvar)
            if not vmatch or xvar.replace('::','').count(':')==xvar.count('?'): # 1D, allow "(x>100 ? 1 : 0) >> h(2,0,2)"
              bmatch = binregex.match(binning)
              if not bmatch:
                raise error("MultiDraw: Could not parse formula for %r: %r"%(name,varexp))
              nxbins, xmin, xmax = int(bmatch.group(1)), float(bmatch.group(2)), float(bmatch.group(3))
              hist = TH1D(name,name,nxbins,xmin,xmax)
            elif vmatch: # 2D histogram
              yvar, xvar = vmatch.group(1), vmatch.group(2)
              bmatch = binregex2D.match(binning)
              if not bmatch:
                raise error('MultiDraw: Could not parse formula for %r to pattern %r: "%s"'%(name,binregex2D.pattern,varexp))
              nxbins, xmin, xmax = int(bmatch.group(1)), float(bmatch.group(2)), float(bmatch.group(3))
              nybins, ymin, ymax = int(bmatch.group(4)), float(bmatch.group(5)), float(bmatch.group(6))
              hist = TH2D(name,name,nxbins,xmin,xmax,nybins,ymin,ymax)
            else: # impossible
              raise error('MultiDraw: Could not parse variable %r for %r to pattern %r: %r'%(xvar,name,varregex2D.pattern,varexp))
            
        else: # get existing histogram: varexp = "x >> h" or "y:x >> h"
            match = varregex2.match(varexp)
            if not match:
              raise error('MultiDraw: Could not parse formula to pattern %r: %r'%(varregex2.pattern,varexp))
            xvar, name = match.groups()
            if name.startswith("+") and name[1:] in hists:
              hist = hists[name[1:]] # add content to existing histogram
            else:
              if i<len(histlist):
                hist = histlist[i]
                if hist.GetName()!=histlist[i].GetName():
                  raise error("MultiDraw: Hisogram mismatch: looking for %r, but found %r."%(hist.GetName(),histlist[i].GetName()))
              else:
                hist = gDirectory.Get(name)
                if not hist:
                  raise error("MultiDraw: Could not find histogram to fill %r in current directory (varexp %r)."%(name,varexp))
            
            # SANITY CHECKS
            vmatch = varregex2D.match(xvar)
            if not vmatch or xvar.replace('::','').count(':')==xvar.count('?'): # 1D, allow "(x>100 ? 1 : 0) >> h(2,0,2)"
              pass
            elif vmatch: # 2D histogram
              yvar, xvar = vmatch.group(1), vmatch.group(2)
              if not isinstance(hist,TH2):
                raise error("MultiDraw: Existing histogram with name %r is not 2D! Found xvar=%r, yvar=%r..."%(name,xvar,yvar))
            else: # impossible
              raise error('MultiDraw: Could not parse variable %r for %r to pattern %r: "%s"'%(xvar,name,varregex2D.pattern,varexp))
        
        if sumw2:
          hist.Sumw2()
        elif poisson:
          hist.SetBinErrorOption(TH1D.kPoisson)
        if drawoption:
          hist.SetDrawOption(drawoption)
        if name not in hists:
          hists[name] = hist
        results.append(hist)
        
        # CHECK that the next formula is different to the previous one.
        # If it is not, we add an ordinary TObject. In this way, the
        # dynamic cast in MultiDraw.cxx fails, giving 'NULL', and the previous
        # value is used. This saves the recomputing of identical values
        if xvar!=lastXVar:
          formula = TTreeFormula("formula%i"%i,xvar,self)
          if not formula.GetTree():
            raise error("MultiDraw: TTreeFormula 'xvar' did not compile for %r:\n  xvar:    %r\n  varexp:  %r"%(name,xvar,varexp))
          formula.SetQuickLoad(True)
          xformulae.append(formula)
        else:
          xformulae.append(TObject())
        
        if yvar!=None:
          if yvar!=lastYVar:
            formula = TTreeFormula("formula%i"%i,yvar,self)
            if not formula.GetTree():
              raise error("MultiDraw: TTreeFormula 'yvar' did not compile for %r:\n  yvar:    %r\n  varexp:  %r"%(name,yvar,varexp))
            formula.SetQuickLoad(True)
            yformulae.append(formula)
          else:
            yformulae.append(TObject())
        
        if weight!=lastWeight:
          formula = TTreeFormula("weight%i"%i,weight,self)
          if not formula.GetTree():
            raise error("MultiDraw: TTreeFormula 'weight' did not compile for %r:\n  weight:  %r\n  varexp:  %r"%(name,weight,varexp))
          formula.SetQuickLoad(True)
          weights.append(formula)
        else:
          weights.append(TObject())
        
        lastXVar, lastYVar, lastWeight = xvar, yvar, weight
    
    # CHECK that formulae are told when tree changes
    manager = TTreeFormulaManager()
    for formula in xformulae + yformulae + weights + [commonFormula]:
      if isinstance(formula,TTreeFormula):
        manager.Add(formula)
    
    manager.Sync()
    self.SetNotify(manager)
    
    # DRAW
    if verbosity>=2:
      print ">>> MultiDraw: xformulae=%s, yformulae=%s"%([x.GetTitle() for x in xformulae],[y.GetTitle() for y in yformulae])
      print ">>> MultiDraw: weights=%s, results=%s"%([w.GetTitle() for w in weights],results)
    if len(yformulae)==0:
      _MultiDraw(self,commonFormula,makeTObjArray(xformulae),makeTObjArray(weights),makeTObjArray(results),len(xformulae))
    elif len(xformulae)==len(yformulae):
      _MultiDraw2D(self,commonFormula,makeTObjArray(xformulae),makeTObjArray(yformulae),makeTObjArray(weights),makeTObjArray(results),len(xformulae))
    else:
      raise error("MultiDraw: Given a mix of arguments for 1D (%d) and 2D (%d) histograms!"%(len(xformulae),len(yformulae)))
    
    return results
    
TTree.MultiDraw = MultiDraw # add MultiDraw to TTree as a class method
