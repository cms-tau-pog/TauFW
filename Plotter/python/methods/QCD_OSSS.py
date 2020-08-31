# -*- coding: utf-8 -*-
# Author: Izaak Neutelings (July 2020)
# Description: Data-driven method to estimate QCD from SS region.
import os, re
from TauFW.Plotter.plot.string import invertcharge
from TauFW.Plotter.sample.SampleSet import LOG, SampleSet, Variable, deletehist, getcolor, makehistname
#from ctypes import c_double
#print ">>> Loading %s"%(__file__)
#gROOT.Macro(modulepath+'/QCD/QCD.C+')


def QCD_OSSS(self, variables, selection, **kwargs):
  """Substract MC from data with same sign (SS) selection of a lepton - tau pair
     and return a histogram of the difference."""
  verbosity      = LOG.getverbosity(kwargs)
  if verbosity>=2:
    LOG.header("Estimating QCD for variables %s"%(', '.join(v.filename for v in variables)))
    #LOG.verbose("\n>>> estimating QCD for variable %s"%(self.var),verbosity,level=2)
  cuts_OS        = selection.selection
  cuts_SS        = invertcharge(cuts_OS,to='SS')
  isjetcat       = re.search(r"(nc?btag|n[cf]?jets)",cuts_OS)
  #relax          = 'emu' in self.channel or isjetcat
  samples        = self.samples
  name           = kwargs.get('name',            'QCD'          )
  title          = kwargs.get('title',           "QCD multijet" )
  tag            = kwargs.get('tag',             ""             )
  #ratio_WJ_QCD   = kwargs.get('ratio_WJ_QCD_SS', False          )
  #doRatio_WJ_QCD = isinstance(ratio_WJ_QCD,      c_double       )
  weight         = kwargs.get('weight',          ""             )
  dataweight     = kwargs.get('dataweight',      ""             )
  replaceweight  = kwargs.get('replaceweight',   ""             )
  scale          = kwargs.get('scale',           None           ) # OS/SS ratio
  shift          = kwargs.get('shift',           0.0            ) #+ self.shiftQCD # for systematics
  #vetoRelax      = kwargs.get('vetoRelax',       relax          )
  #relax          = kwargs.get('relax',           relax          ) #and not vetoRelax
  #file           = kwargs.get('saveto',          None           )
  parallel       = kwargs.get('parallel',        False          )
  
  # SCALE
  if "q_1*q_2>0" in cuts_OS.replace(' ',''):
    scale = 1.0
  elif not scale:
    scale = 2.0 if "emu" in self.channel else 1.10
  scale          = scale*(1.0+shift) # OS/SS scale & systematic variation
  LOG.verbose("  QCD: scale=%s, shift=%s"%(scale,shift),verbosity,level=2)
  
  # CUTS: relax cuts for QCD_SS_SB
  # https://indico.cern.ch/event/566854/contributions/2367198/attachments/1368758/2074844/QCDStudy_20161109_HTTMeeting.pdf
  #QCD_OS_SR = 0
  #if relax:
  #  
  #  # GET yield QCD_OS_SR = SF * QCD_SS_SR
  #  if 'emu' in self.channel: # use weight instead of scale
  #    scale       = 1.0
  #    weight      = combineWeights("getQCDWeight(pt_2, pt_1, dR_ll)",weight)
  #    dataweight = "getQCDWeight(pt_2, pt_1, dR_ll)" # SF ~ 2.4 average
  #  kwargs_SR     = kwargs.copy()
  #  kwargs_SR.update({ 'scale':scale, 'weight':weight, 'dataweight':dataweight, 'relax':False })
  #  qcdhist_OS_SR = self.QCD(variables,selection,**kwargs_SR)
  #  QCD_OS_SR     = qcdhist_OS_SR.Integral(1,nbins) # yield
  #  scale         = 1.0
  #  deleteHist(qcdhist_OS_SR)
  #  if QCD_OS_SR < 10:
  #    LOG.warning('QCD: QCD_SR = %.1f < 10 for "%s"'%(QCD_OS_SR,cuts_OS))
  #  
  #  # RELAX cuts for QCD_OS_SB = SF * QCD_SS_SB
  #  tag         = "_isorel"+tag
  #  iso_relaxed = "iso_1>0.15 && iso_1<0.5 && iso_2_medium==1" #iso_2_medium
  #  if 'emu' in self.channel: iso_relaxed = "iso_1>0.20 && iso_1<0.5 && iso_2<0.5"
  #  elif isjetcat: cuts = relaxJetSelection(cuts)
  #  cuts = invertIsolation(cuts,to=iso_relaxed)
  #LOG.verbose("   QCD: cuts = %s %s"%(cuts,"(relaxed)" if relax else ""),verbosity,level=2)
  
  # GET SS HISTOGRAMS
  qcdhists = [ ]
  args  = variables, cuts_SS #Selection("same-sign",cuts_SS)
  hists = self.gethists(*args,weight=weight,dataweight=dataweight,replaceweight=replaceweight,tag=tag,task="Estimating QCD",
                              signal=False,split=False,blind=False,parallel=parallel,verbosity=verbosity-1)
  for variable, datahist, exphists in hists:
    
    ## GET WJ
    #histWJ = None
    #if doRatio_WJ_QCD:
    #  for hist in exphists:
    #    if ('WJ' in hist.GetName() or re.findall(r"w.*jets",hist.GetName(),re.IGNORECASE)):
    #      if histWJ:
    #        LOG.warning("SampleSet.QCD: more than one W+jets sample in SS region, going with first instance!",pre="  ")
    #        break
    #      else: histWJ = hist
    #  if not histWJ:
    #    LOG.warning("SampleSet.QCD: Did not find W+jets sample!",pre="  ")
    
    # CHECK data
    if not datahist:
      LOG.warning("SampleSet.QCD: No data to make DATA driven QCD!")
      return None
    
    # QCD HIST
    exphist = exphists[0].Clone('MC_SS')
    for hist in exphists[1:]:
      exphist.Add(hist)
    qcdhist = exphists[0].Clone(makehistname(variable.filename,name,tag)) # $VAR_$PROCESS$TAG
    qcdhist.Reset()
    qcdhist.Add(datahist)
    qcdhist.Add(exphist,-1)
    qcdhist.SetTitle(title)
    qcdhist.SetFillColor(getcolor('QCD'))
    qcdhist.SetOption('HIST')
    qcdhists.append(qcdhist)
    
    # ENSURE positive bins
    nneg = 0
    for i, bin in enumerate(qcdhist):
      if bin<0:
        qcdhist.SetBinContent(i,0)
        qcdhist.SetBinError(i,1)
        nneg += 1
    if nneg>0:
      LOG.warning("SampleSet.QCD_OSSS: %r has %d/%d negative bins! Set to 0 +- 1."%(variable.name,nneg,variable.nbins),pre="  ")
    
    # YIELDS
    #if relax:
    #  QCD_SS = qcdhist.Integral(1,nbins)
    #  if QCD_SS:
    #    scaleup = QCD_OS_SR/QCD_SS # normalizing to OS_SR
    #    LOG.verbose("   QCD: scaleup = QCD_OS_SR/QCD_SS_SB = %.1f/%.1f = %.3f"%(QCD_OS_SR,QCD_SS,scaleup),verbosity,level=2)
    #  else:
    #    LOG.warning("SampleSet.QCD_OSSS: QCD_SS_SB.Integral() == 0!")
    qcdhist.Scale(scale) # scale SS -> OS
    nexp  = exphist.Integral()
    ndata = datahist.Integral()
    nqcd  = qcdhist.Integral()
    
    ## WJ/QCD ratio in SS
    #if doRatio_WJ_QCD and histWJ and variables.index(variable)==0:
    #  WJ_SS  = histWJ.Integral()
    #  if QCD_SS: ratio_WJ_QCD.value = WJ_SS/QCD_SS
    #  else: LOG.warning("SampleSet.QCD - QCD integral is 0!",pre="  ")
    #  LOG.verbose("   QCD: ndata = %.1f, MC_SS = %.1f, QCD_SS = %.1f, scale=%.3f, WJ_SS = %.1f, ratio_WJ_QCD_SS = %.3f"%(ndata,MC_SS,QCD_SS,scale,WJ_SS,ratio_WJ_QCD.value),verbosity,level=2)
    #else:
    LOG.verbose("SampleSet.QCD_OSSS: SS yields: data=%.1f, exp=%.1f, qcd=%.1f, scale=%.3f"%(ndata,nexp,nqcd,scale),verbosity,level=2)
    
    # CLEAN
    deletehist([datahist,exphist]+exphists)
  
  return qcdhists
  

SampleSet.QCD_OSSS = QCD_OSSS # add as class method of SampleSet