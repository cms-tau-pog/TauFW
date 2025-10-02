# -*- coding: utf-8 -*-
# Author: Konstantinos Christoforou (February 2022)
# Description: Data-driven method to estimate mis-id taus (apply jet-to-tau FakeRates)
import os, re
import ROOT
from TauFW.Plotter.plot.string import invertcharge
from TauFW.Plotter.sample.SampleSet import LOG, SampleSet, Variable, deletehist, getcolor, makehistname

from TauFW.Plotter.sample.utils import LOG, STYLE, ensuredir, repkey, joincuts, joinweights, ensurelist, setera, getyear, loadmacro, Sel
import TauFW.Plotter.corrections.JetToTauFR.tools.fakeFactors as fakeFactors


def JetToTau_MisID(self, variables, selection, **kwargs):
  """Substract genuine-tau MC from data with loose-not-tightVsjet tau 
     and return a histogram of the difference, scaled by the appropriate FakeFactor """
  verbosity      = LOG.getverbosity(kwargs)
  if verbosity>=2:
    LOG.header("Estimating jet-to-tau misidentification for variables %s"%(', '.join(v.filename for v in variables)))
    #LOG.verbose("\n>>> estimating QCD for variable %s"%(self.var),verbosity,level=2)
  cuts_Tight        = selection.selection
  LooseNotTight_to_Tight = True
  if LooseNotTight_to_Tight:
    # cuts_LnotTFake    = cuts_Tight.replace("id_tau >= 16","id_tau >= 1 && id_tau <= 16").replace("TauIsGenuine","!TauIsGenuine") ## for Loose-not-Tight histos, 
    # this should be like this, not as above, correct???
    cuts_LnotTFake    = cuts_Tight.replace("id_tau >= 8","id_tau >= 1 && id_tau < 8").replace("TauIsGenuine","!TauIsGenuine") ## for Loose-not-Tight histos, 
  else:
    cuts_LnotTFake    = cuts_Tight.replace("id_tau >= 16","id_tau >= 1").replace("TauIsGenuine","!TauIsGenuine") ## for Loose  histos
    # this should be like this,    not as above, correct???
    #cuts_LnotTFake    = cuts_Tight.replace("id_tau >= 16","id_tau >= 1 && id_tau <= 16").replace("TauIsGenuine","!TauIsGenuine") ## for Loose  histos
  #isjetcat       = re.search(r"(nc?btag|n[cf]?jets)",cuts_OS)
  #relax          = 'emu' in self.channel or isjetcat
  samples        = self.samples
  name           = kwargs.get('name',            'MisIDtau'            )
  title          = kwargs.get('title',           "Mis-ID #tau_h (Data)")
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
  negthres       = kwargs.get('negthres',        0.25           ) # threshold for warning about negative Mis-ID bins
  

  ## Calculate the Mis-ID #tau_h (Data) contribution
  selections_LnotTFake_forFRbins = []
  FRkeylist = []
  maxPt = 120
  etas = ["Barrel","Endcap"]#["Barrel","Endcap"] #[""]
  prongs = [""]#["1prong","3prong"]
  ptList = [20, 25 , 30 , 35, 40 , 50 , 70]
  UseAbsoluteFR = True

  #dirList = ["plots/UL2016_preVFP/mumutau/TauFakeRate_UL2016_preVFP_mumutau"]
  #dirList = ["plots/UL2016_preVFP/eetau/TauFakeRate_UL2016_preVFP_eetau"]
  #dirList = ["plots/UL2016_postVFP/mumutau/TauFakeRate_UL2016_postVFP_mumutau"]
  #dirList = ["plots/UL2016_postVFP/eetau/TauFakeRate_UL2016_postVFP_eetau"]
  #dirList = ["plots/UL2017/mumutau/TauFakeRate_UL2017_mumutau"]
  #dirList = ["plots/UL2017/eetau/TauFakeRate_UL2017_eetau"]
  #dirList = ["plots/UL2018/mumutau/TauFakeRate_UL2018_mumutau"]
  #dirList = ["plots/UL2018/eetau/TauFakeRate_UL2018_eetau"]
  #dirList = ["plots/UL2018/mumettau/TauFakeRate_UL2018_Medium_mumettau"]
  dirList = ["plots/UL2018/mumettau/TauFakeRate_UL2018_Loose_mumettau"]
  FRDict = {}

  ## Selections for prong-eta-pT bins, read the values for FakeRates for each prong-eta bin
  ## then read the value for each prong-eta-pT bin and store it in a dictionary with key the same 
  ## string as the title of the specific prong-eta-pT selection
  ## prong bins
  for prong in prongs:
    name_ = "%s"%(prong)
    tit_  = "%s"%(prong)
    if prong == "1prong":
      cut_  = "%s && TauDM<5"%(cuts_LnotTFake)
    elif prong == "3prong":
      cut_  = "%s && TauDM>5"%(cuts_LnotTFake)
    else:
      cut_  = cuts_LnotTFake
    ## eta bins        
    for eta in etas:
      name__ = "%s_eta%s"%(name_,eta)
      tit__  = "%s, %s"%(tit_,eta)
      if UseAbsoluteFR:
        if eta =="Barrel":
          cut__ = "%s && abs(JetEta)<1.5"%(cut_)
        elif eta =="Endcap":
          cut__ = "%s && abs(JetEta)>1.5 && abs(JetEta)<2.4"%(cut_)
        else:
          cut__ = cut_
      else:
        if eta =="Barrel":
          cut__ = "%s && abs(TauEta)<1.5"%(cut_)
        elif eta =="Endcap":
          cut__ = "%s && abs(TauEta)>1.5 && abs(TauEta)<2.4"%(cut_)
        else:
          cut__ = cut_
      #FakeRates = fakeFactors.FakeFactors(dirList, "Data", prong, eta, None, "eetau") ## read the values for FakeRates for each prong-eta bin
      #FakeRates = fakeFactors.FakeFactors(dirList, "Data", prong, eta, None, "mumutau") ## read the values for FakeRates for each prong-eta bin
      FakeRates = fakeFactors.FakeFactors(dirList, "Data", prong, eta, None, "mumettau") ## read the values for FakeRates for each prong-eta bin
      FRDictinPt  = {}
      FRDictinPt  = FakeRates.valuesDict
      FRinPtBins  = list(FRDictinPt.values())[0]
      for i, ptlow in enumerate(ptList):
        if i<len(ptList)-1: # ptlow < pt < ptup 
          ptup = ptList[i+1]
          name___ = "%s_pt%d-%d"%(name__,ptlow,ptup)
          tit___  = "%s, %d < pt < %d GeV"%(tit__,ptlow,ptup)
          if UseAbsoluteFR:
            cut___  = "%s && %s<JetPt && JetPt<%s"%(cut__,ptlow,ptup)
          else:
            cut___  = "%s && %s<TauPt && TauPt<%s"%(cut__,ptlow,ptup)
        else: # pt > ptlow (no upper pt cut)  
          name___ = "%s_pt%d_%s"%(name__,ptlow,maxPt)
          tit___  = "%s, %d < pt < %d GeV"%(tit__,ptlow,maxPt)
          if UseAbsoluteFR:
            cut___  = "%s && %s<JetPt && JetPt<%s"%(cut__,ptlow,maxPt)
          else:
            cut___  = "%s && %s<TauPt && TauPt<%s"%(cut__,ptlow,maxPt)
        selections_LnotTFake_forFRbins.append(Sel(name___,tit___,cut___)) # pt-DM-eta bins 
        FRDict[tit___] = FRinPtBins[i] #store the FR value in the dictionary using the title of the specific prong-eta-pT selection as key
        
  misIDhists = [ ]
  b_misIDhists_init = False
  
  for selection in selections_LnotTFake_forFRbins:
    FRDict_keyName = selection.title.replace("p_{T}","pt") ## there must be somewhere an automated replace of pt with p_{T} in the title of the selection
    FakeRate = FRDict[FRDict_keyName] ## the FakeRate value for this specific pt-eta-prong bin, which will be used to weight the "fake" Data (=incl. Data - genuine MC)
    
    ## Initialize the Inclusive in pT_prong_eta bins data histos
    if not b_misIDhists_init:
      args = variables, cuts_LnotTFake
      misIDhistos = self.gethists(*args,weight=weight,dataweight=dataweight,replaceweight=replaceweight,tag=tag,
                                  task=" ", signal=False,split=False,blind=False,parallel=parallel,verbosity=verbosity-1)
      for variable, datahist, exphists in misIDhistos:
        exphist = exphists[0].Clone('MC_LnotTFake')
        misIDhist = exphists[0].Clone(makehistname(variable.filename,name,tag)) # $VAR_$PROCESS$TAG 
        misIDhist.Reset()
        misIDhist.SetTitle(title)
        misIDhist.SetFillColor(ROOT.kOrange-2)
        misIDhist.SetOption('HIST')
        misIDhists.append(misIDhist)
        b_misIDhists_init = True
    ##############################################################

    # Now, for each variable, you should calculate the contribution of the fakes and add it to the above histos # Maybe use datahist instead of exphist to initialize above?
    args_LnotTFake  = variables, selection.selection #cuts_Tight
    hists_LnotTFake = self.gethists(*args_LnotTFake,weight=weight,dataweight=dataweight,replaceweight=replaceweight,tag=tag,
                                       task="Estimating jet-to-tau misIdentification", signal=False,split=False,blind=False,parallel=parallel,verbosity=verbosity-1)

    args_LnotTGenuine  = variables, selection.selection.replace("!TauIsGenuine","TauIsGenuine") #cuts_Tight
    hists_LnotTGenuine = self.gethists(*args_LnotTGenuine,weight=weight,dataweight=dataweight,replaceweight=replaceweight,tag=tag,
                                       task="Estimating jet-to-tau misIdentification", signal=False,split=False,blind=False,parallel=parallel,verbosity=verbosity-1)
    
    j_counter = 0
    for variable, datahist, exphists in hists_LnotTGenuine:
      if not datahist:
        LOG.warning("SampleSet.MisIDtau :  No data to make DATA driven jet-to-tau misID!")
        return None
      
      # misIDhist 
      exphist = exphists[0].Clone('MC_LnotTFake')
      for hist in exphists[1:]:
        exphist.Add(hist)
      misIDhist = exphists[0].Clone(makehistname(variable.filename,name,tag)) # $VAR_$PROCESS$TAG
      misIDhist.Reset()
      for variable_fake, datahist_fake, exphists_fake in hists_LnotTFake:
        if variable_fake == variable:
          misIDhist.Add(datahist_fake)
      # misIDhist.Add(datahist)
      misIDhist.Add(exphist,-1)
      misIDhist.SetTitle(title)
      misIDhist.SetFillColor(ROOT.kOrange-2)#getcolor('QCD'))
      misIDhist.SetOption('HIST')
      # misIDhists.append(misIDhist)
    
      # ENSURE positive bins
      nneg = 0
      nbins = misIDhist.GetXaxis().GetNbins()+2 # include under-/overflow
      for i in range(0,nbins):
        binContent = misIDhist.GetBinContent(i)
        if binContent<0:
          misIDhist.SetBinContent(i,0)
          misIDhist.SetBinError(i,1)
          nneg += 1
      if nbins and nneg/nbins>negthres:
        LOG.warning("SampleSet.MisIDtau: %r has %d/%d>%.1f%% negative bins! Set to 0 +- 1."%(variable.name,nneg,nbins,100.0*negthres),pre="  ")
    
      ## So, at this point misIDhist has the LnotT Data minus the Genuine LnotT MC
      ## Now, you should just apply the tau FakeRates on the LnotT "fake" Data
      if LooseNotTight_to_Tight:
        FRweight = FakeRate/(1.0-FakeRate) ## you want the LooseNotTight -> Tight weight.  FakeRate is the Loose->Tight one
      else:
        FRweight = FakeRate  ## for Loose -> Tight
      misIDhist.Scale(FRweight) # scale LnotT -> Tight
      misIDhists[j_counter].Add(misIDhist)
      j_counter += 1
    
      # CLEAN
      deletehist([datahist,exphist]+exphists)

  return misIDhists

SampleSet.JetToTau_MisID = JetToTau_MisID # add as class method of SampleSet
