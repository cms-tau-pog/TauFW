# -*- coding: utf-8 -*-
# Author: Izaak Neutelings (July 2020)
# Description: Data-driven method to estimate QCD from SS region.
import os, re
from TauFW.Plotter.plot.string import invertcharge
from TauFW.Plotter.sample.SampleSet import LOG, SampleSet, Variable, deletehist, getcolor, makehistname #, HistDict
#from ctypes import c_double
#print ">>> Loading %s"%(__file__)
#gROOT.Macro(modulepath+'/QCD/QCD.C+')


def QCD_OSSS(self, variables, selections, **kwargs):
  """Substract MC from data with same sign (SS) selection of a lepton - tau pair
     and return a histogram of the difference."""
  verbosity      = LOG.getverbosity(kwargs)
  if verbosity>=2:
    LOG.header("Estimating QCD for variables %s"%(', '.join(v.filename for v in variables)))
    #LOG.verbose("\n>>> estimating QCD for variable %s"%(self.var),verbosity,level=2)
  samples       = self.samples
  name          = kwargs.get('name',            'QCD'          )
  title         = kwargs.get('title',           "QCD multijet" )
  tag           = kwargs.get('tag',             ""             )
  weight        = kwargs.get('weight',          ""             )
  dataweight    = kwargs.get('dataweight',      ""             )
  replaceweight = kwargs.get('replaceweight',   ""             )
  scale         = kwargs.get('scale',           None           ) # OS/SS ratio (SS -> OS extrapolation scale)
  shift         = kwargs.get('shift',           0.0            ) #+ self.shiftQCD # for systematics
  parallel      = kwargs.get('parallel',        False          )
  negthres      = kwargs.get('negthres',        0.25           ) # threshold for warning about negative QCD bins
  
  # INVERT OS -> SS CHARGE SELECTIONS
  scale_dict = { }
  selections_SS = [ ]
  for selection_OS in selections:
    
    # SELECTION STRING
    selection_SS = selection_OS.invertcharge(to='SS') # q_1*q_2<0 (OS) -> q_1*q_2>0 (SS)
    #isjetcat = re.search(r"(nc?btag|n[cf]?jets)",cuts_OS)
    selection_SS.OS = selection_OS # cache for reuse
    selections_SS.append(selection_SS)
    
    # OS/SS RATIO (SS -> OS extrapolation scale)
    if "q_1*q_2>0" in selection_OS.selection.replace(' ',''):
      scale = 1.0 # already SS: no extra scale
    elif not scale:
      scale = 2.0 if "emu" in self.channel else 1.10
    scale_dict[selection_OS] = scale
    LOG.verbose("SampleSet.QCD_OSSS: scale=%s, shift=%s, OS=%r -> SS=%r"%(
      scale,shift,selection_OS.selection,selection_SS.selection),verbosity,level=2)
  
  # GET SS HISTOGRAMS
  hists = self.gethists(variables,selections_SS,weight=weight,dataweight=dataweight,replaceweight=replaceweight,tag=tag,
                        signal=False,split=False,blind=False,task="Estimating QCD: ",verbosity=verbosity-1)
  
  # CREATE QCD HISTS
  qcdhists = { } #HistDict()
  for selection_SS in hists:
    selection_OS = selection_SS.OS
    qcdhists[selection_OS] = { }
    for variable, histset in hists[selection_SS].items():
      datahist = histset.data
      exphists = histset.exp
      
      # CHECK data
      if not datahist:
        LOG.warning("SampleSet.QCD: No data to make DATA driven QCD!")
        return None
      
      # QCD HIST = DATA - MC
      exphist = exphists[0].Clone('MC_SS')
      for hist in exphists[1:]:
        exphist.Add(hist)
      qcdhist = exphists[0].Clone(makehistname(variable,selection_OS,name,tag).rstrip('_')) # $VAR_$SEL_$PROCESS$TAG
      qcdhist.Reset() # set all bin content to zero
      qcdhist.Add(datahist) # QCD = observed data in SS
      qcdhist.Add(exphist,-1) # subtract total MC expectation in SS
      qcdhist.SetTitle(title)
      qcdhist.SetFillColor(getcolor('QCD'))
      qcdhist.SetOption('HIST')
      qcdhists[selection_OS][variable] = qcdhist
      
      # ENSURE positive bins
      nneg = 0
      nbins = qcdhist.GetXaxis().GetNbins()+2 # include under-/overflow
      for i in range(0,nbins):
        bin = qcdhist.GetBinContent(i)
        if bin<0:
          qcdhist.SetBinContent(i,0)
          qcdhist.SetBinError(i,1)
          nneg += 1
      if nbins and nneg/nbins>negthres:
        LOG.warning("SampleSet.QCD_OSSS: %r has %d/%d>%.1f%% negative bins! Set to 0 +- 1."%(variable.name,nneg,nbins,100.0*negthres),pre="  ")
      
      # SCALE SS -> OS
      scale = scale_dict[selection_OS]*(1.0+shift) # OS/SS scale & systematic variation
      qcdhist.Scale(scale) # scale SS -> OS
      
      # YIELDS
      if verbosity>=2:
        nexp  = exphist.Integral()
        ndata = datahist.Integral()
        nqcd  = qcdhist.Integral()
        LOG.verbose("SampleSet.QCD_OSSS: SS yields: data=%.1f, exp=%.1f, qcd=%.1f, scale=%.3f"%(ndata,nexp,nqcd,scale),verbosity,level=2)
      
      # CLEAN
      if not parallel: # avoid segmentation faults for parallel
        deletehist([datahist,exphist]+exphists) # clean histogram from memory
  
  return qcdhists
  

SampleSet.QCD_OSSS = QCD_OSSS # add as class method of SampleSet
