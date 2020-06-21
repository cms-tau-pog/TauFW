#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Izaak Neutelings (2019)
# Description: Efficiently draw multiple histograms with one loop over all events in a TTree
#              This script injects a MultiDraw method into TTree when it is imported.
# Source: https://github.com/pwaller/minty/blob/master/minty/junk/MultiDraw.py
import os, re
from time import time
from ROOT import gROOT, gSystem, gDirectory, TObject, TTree, TObjArray, TTreeFormula,\
    TH1D, TH2D, TH2, SetOwnership, TTreeFormulaManager
#from PlotTools import modulepath
modulepath = os.path.dirname(__file__)
gROOT.ProcessLine(".L %s/MultiDraw.cxx+O"%modulepath)
from ROOT import MultiDraw as _MultiDraw
from ROOT import MultiDraw2D as _MultiDraw2D

#gROOT.ProcessLine(".L PlotTools/fakeRate/fakeRate.cxx+0")
#gSystem.Load("PlotTools/fakeRate/fakeRate_C.so")

def MakeTObjArray(theList):
    """Turn a python iterable into a ROOT TObjArray"""
    # Make PyROOT give up ownership of the things that are being placed in the
    # TObjArary. They get deleted because of result.SetOwner()
    result = TObjArray()
    result.SetOwner()
    for item in theList:
      SetOwnership(item, False)
      result.Add(item)
    return result
    

varexppattern   = re.compile(r"(.*?)\s*>>\s*(.*?)\s*\(\s*(.*?)\s*\)$")
varexppattern2  = re.compile(r"(.*?)\s*>>\s*(.*?)\s*$")
binningpattern  = re.compile(r"(\d+)\s*,\s*([+-]?\d*\.?\d*)\s*,\s*([+-]?\d*\.?\d*)")
binningpattern2 = re.compile(r"(\d+)\s*,\s*([+-]?\d*\.?\d*)\s*,\s*([+-]?\d*\.?\d*)\s*,\s*(\d+)\s*,\s*([+-]?\d*\.?\d*)\s*,\s*([+-]?\d*\.?\d*)")
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
    
    verbose   = kwargs.get('verbosity', 0     )
    poisson   = kwargs.get('poisson',   False ) # kPoisson errors for data
    sumw2     = kwargs.get('sumw2',     False ) # sumw2 for MC
    histlist  = kwargs.get('hists',     [ ]   ) # to not rely on gDirectory.Get(histname)
    
    hists     = { }
    results, xformulae, yformulae, weights = [ ], [ ], [ ], [ ]
    lastXVar, lastYVar, lastWeight = None, None, None
    
    # A weight common to everything being drawn
    commonFormula = TTreeFormula("commonFormula", selection, self)
    commonFormula.SetQuickLoad(True)
    
    if not commonFormula.GetTree():
      raise RuntimeError('MultiDraw: TTreeFormula did not compile:\n  selection:  "%s"\n  varexps:    %s'%(selection,varexps))
    
    for i, varexp in enumerate(varexps):
        #print '  Variable expression: %s'%(varexp,)
        yvar = None
        
        # EXPAND varexp
        if isinstance(varexp,tuple):
          varexp, weight = varexp
        else:
          varexp, weight = varexp, '1'
        
        # PREPARE histogram
        match = varexppattern.match(varexp)
        if match:
            xvar, name, binning = match.group(1), match.group(2), match.group(3)
            
            # 1D histogram
            if xvar.count(':')==0:
              match = binningpattern.match(binning)
              if not match:
                raise RuntimeError('MultiDraw: Could not parse formula: "%s"'%varexp)
              nxbins, xmin, xmax = int(match.group(1)), float(match.group(2)), float(match.group(3))
              hist = TH1D(name, name, nxbins, xmin, xmax)
            
            # 2D histogram
            else:
              xvar, yvar = xvar.split(':')
              match = binningpattern2.match(binning)
              if not match:
                raise RuntimeError('MultiDraw: Could not parse formula: "%s"'%varexp)
              nxbins, xmin, xmax = int(match.group(1)), float(match.group(2)), float(match.group(3))
              nybins, ymin, ymax = int(match.group(4)), float(match.group(5)), float(match.group(6))
              hist = TH2D(name, name, nxbins, xmin, xmax, nybins, ymin, ymax)
            
        else:
            match = varexppattern2.match(varexp)
            if not match:
              raise RuntimeError('MultiDraw: Could not parse formula: "%s"'%varexp)
            xvar, name = match.groups()
            if name.startswith("+") and name[1:] in hists:
              hist = hists[name[1:]] # add content to existing histogram
            else:
              if i<len(histlist):
                hist = histlist[i]
                if hist.GetName()!=histlist[i].GetName():
                  raise RuntimeError('MultiDraw: Hisogram mismatch: looking for "%s", but found "%s".'%(hist.GetName(),histlist[i].GetName()))
              else:
                hist = gDirectory.Get(name)
                if not hist:
                  raise RuntimeError('MultiDraw: Could not find histogram to fill "%s" in current directory (varexp "%s").'%(name,varexp))
            
            # 2D histogram
            if xvar.count(':')!=xvar.count('?'):
              yvar, xvar = xvar.split(':')
              if not isinstance(hist,TH2):
                raise RuntimeError('MultiDraw: Existing histogram with name "%s" is not 2D! Found xvar="%s", yvar="%s"...'%(name,xvar,yvar))
        
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
            formula = TTreeFormula("formula%i"%i, xvar, self)
            if not formula.GetTree():
              raise RuntimeError('MultiDraw: TTreeFormula did not compile:\n  xvar:    "%s"\n  varexp:  "%s"'%(xvar,varexp))
            formula.SetQuickLoad(True)
            xformulae.append(formula)
        else:
            xformulae.append(TObject())
        
        if yvar!=None:
          if yvar!=lastYVar:
            formula = TTreeFormula("formula%i"%i, yvar, self)
            if not formula.GetTree():
              raise RuntimeError('MultiDraw: TTreeFormula did not compile:\n  yvar:    "%s"\n  varexp:  "%s"'%(yvar,varexp))
            formula.SetQuickLoad(True)
            yformulae.append(formula)
          else:
            yformulae.append(TObject())
        
        if weight!=lastWeight:
            formula = TTreeFormula("weight%i"%i, weight, self)
            if not formula.GetTree():
              raise RuntimeError('MultiDraw: TTreeFormula did not compile:\n  weight:  "%s"\n  varexp:  "%s"'%(weight,varexp))
            formula.SetQuickLoad(True)
            weights.append(formula)
        else:
            weights.append(TObject())
        
        lastXVar, lastYVar, lastWeight = xvar, yvar, weight
    
    # CHECK that formulae are told when tree changes
    #start = time()
    manager = TTreeFormulaManager()
    for formula in xformulae + yformulae + weights + [commonFormula, ]:
      if isinstance(formula,TTreeFormula):
        manager.Add(formula)
    
    manager.Sync()
    self.SetNotify(manager)
    
    # DRAW
    #print xformulae, yformulae, weights, results
    if len(yformulae)==0:
      _MultiDraw(self,commonFormula,MakeTObjArray(xformulae),MakeTObjArray(weights),MakeTObjArray(results),len(xformulae))
    elif len(xformulae)==len(yformulae):
      _MultiDraw2D(self,commonFormula,MakeTObjArray(xformulae),MakeTObjArray(yformulae),MakeTObjArray(weights),MakeTObjArray(results),len(xformulae))
    else:
      raise RuntimeError("MultiDraw: Given a mix of arguments for 1D (%d) and 2D (%d) histograms"%(len(xformulae),len(yformulae)))
    
    #print "Took %.2fs"%(time()-start)+' '*10
    return results
    
TTree.MultiDraw = MultiDraw
