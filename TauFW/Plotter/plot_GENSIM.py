#! /usr/bin/env python
# Author: Izaak Neutelings (June 2022)
# Description: Compare distributions in GENSIM tuples
# Instructions
#   cd ../PicoProducer/utils
#   ./convertGENSIM.py GENSIM_*.root -o GENSIM_converted.root
#   cd ../../Plotter/
#   ./plot_GENSIM.py
import os
from TauFW.common.tools.log import bold
from TauFW.common.tools.math import frange
import TauFW.Plotter.plot.Plot as _Plot
import TauFW.Plotter.plot.CMSStyle as CMSStyle
from TauFW.Plotter.plot.Plot import Plot, deletehist
from TauFW.Plotter.plot.Plot import LOG as PLOG
from TauFW.Plotter.sample.utils import LOG, STYLE, ensuredir, ensurelist, ensureTFile,\
                                       setera, Sel, Var
from ROOT import TChain, kBlack, kRed, kBlue, kAzure, kGreen, kOrange, kMagenta, kYellow

colors = [ kRed+1, kBlue, kGreen+2, ]
# colors = [ kBlack, kRed+1, kAzure+5, kGreen+2, kOrange+1, kMagenta-4, kAzure+10, kOrange+10,
#            kRed+2, kAzure+5, kOrange-5, kGreen+2, kMagenta+2, kYellow+2,
#            kRed-7, kAzure-4, kOrange+6, kGreen-2, kMagenta-3, kYellow-2 ] #kViolet


class Sample:
  """Container class for sample files."""
  
  def __init__(self,name,title,fnames,tree=True,tname='event',
               data=False,cut=None,nfilemax=-1,scale=1,verb=0):
    fnames = ensurelist(fnames)
    for i, fname in enumerate(fnames): # expand glob patterns
      if any(c in fname for c in ['*','[',']']):
        if verb>=2:
          print(">>> Sample.__init__: Expanding %r..."%(fname))
        fnames.insert(i,glob.glob(fname))
    if nfilemax>0 and len(fnames)>nfilemax:
      fnames    = fnames[:nfilemax]
    self.name   = name
    self.title  = title
    self.fnames = fnames
    self.files  = { }
    self.tree   = None
    self.cut    = cut # extra cut
    self.scale  = scale
    self.isdata = data
    if verb>=1:
      print(">>> Sample %r (%r):"%(self.name,self.title))
      for fname in fnames:
        print(">>>   %s"%(fname))
    if tree:
      self.gettree(tname,verb=verb)
  
  def getfiles(self,verb=0):
    for fname in self.fnames:
      file = self.files.get(fname,None)
      if not file:
        file = ensureTFile(fname,'READ',verb=verb)
        self.files[fname] = file
      yield file
  
  def closefiles(self,verb=0):
    for fname, file in self.files.items():
      if file:
        if verb>=1:
          print(">>> Sample.close: Closing %s..."%(file.GetPath()))
        file.Close()
    self.files = { } # reset
  
  def gettree(self,tname='Events',refresh=False,verb=0):
    if not refresh and self.tree:
      return self.tree
    chain = TChain(tname)
    if verb>=1:
      print(">>> gettree(%r)"%(tname))
    for fname in self.fnames:
      if verb>=1:
        print(">>>   Adding %s..."%(fname))
      chain.Add(fname)
    self.tree = chain
    if verb>=2:
      print(">>> Sample.gettree: Number of entries: %5s over %s files for %s"%(self.tree.GetEntries(),len(self.fnames),self.name))
    return chain
  
  def gethist_from_file(self,hname,title=None,verb=0):
    hist = None
    for file in self.getfiles(verb=verb):
      if hist:
        hist_ = file.Get(hname)
        hist.Add(hist_)
      else:
        hist = file.Get(hname)
        if not hist:
          file.ls()
          raise IOError("Could not find %r in file %s"%(hname,file.GetPath()))
        hist.SetDirectory(0)
        hist.SetTitle(title)
    if self.scale!=1:
      #print ">>> Sample.gethists:   Scaling %s by %s"%(hname,self.scale)
      hist.Scale(self.scale)
    return hist
  
  def gethist(self,variable,selection,hname="$VAR_$NAME",verb=0):
    hname = hname.replace('$VAR',variable.filename).replace('$NAME',self.name)
    hist = variable.gethist(hname,self.title,sumw2=True)
    hist.SetDirectory(0)
    varexp = variable.drawcmd(hname)
    if not isinstance(selection,str):
      selection = selection.selection
    if self.cut:
      selection += " && "+self.cut
    if verb>=1:
      print(">>> %s.Draw(%r,%r)"%(tree.GetName(),varexp,selection))
    out = self.tree.Draw(varexp,selection,'HIST')
    if self.scale!=1:
      hist.Scale(self.scale)
    return hist
  
  def gethists(self,variables,selection,hname="$VAR_$NAME",verb=0):
    varexps = [ ]
    hists   = [ ]
    if not isinstance(selection,str):
      selection = selection.selection
    if self.cut:
      selection += " && "+self.cut
    for var in variables:
      hname_ = hname.replace('$VAR',var.filename).replace('$NAME',self.name)
      hist   = var.gethist(hname_,self.title,sumw2=True)
      varexp = var.drawcmd(hname_)
      hist.SetDirectory(0)
      hists.append(hist)
      varexps.append(varexp)
      if verb>=2:
        print(">>> Sample.gethists:   %r, %r"%(varexp,selection))
    out = self.tree.MultiDraw(varexps,selection,'HIST',hists=hists,verbosity=verb)
    if self.scale!=1:
      for hist in hists:
        hist.Scale(self.scale)
    return hists
  

# VARIABLES
qlabels = ['','#minus1','','#plus1','','','']
bins_st    = list(range(0,300,100)) + [300,500,1000,2000]
bins_met1  = list(range(0,400,40)) + [400,450,500,600,700,800,1000]
bins_met2  = list(range(0,600,50)) + [600,700,800,1000]
bins_met3  = list(range(0,800,50)) + [900,1000,1200,1500]
bins_jpt1  = list(range(0,1200,100)) + [1200,1500,2500]
bins_jpt2  = list(range(10,50,10)) + [50,70,100,150,300] #,1500,2500]
bins_tpt1  = list(range(0,1200,200)) + [1200,1500,2000,2800]
bins_pt1   = list(range(0,780,60)) + [780,860,1000,1400]
bins_pt2   = list(range(0,1040,80)) + [1040,1200,1600]
bins_pt3   = list(range(0,1040,80)) + [1040,1200,1500,1600,2000]
bins_pt    = list(range(0,600,60)) + list(range(600,1000,100)) + [1000,1200,1500,2000]
bins_ptvis = list(range(0,200,40)) + list(range(200,400,50)) + [400,500,800,1000,1500]
bins_eta   = [-6.0,-4.0] + frange(-2.5,2.5,0.5) + [2.5,4.0,6.0]
bins_dR    = [0,0.5,1.0,1.4,1.7] + frange(2.0,4.0,0.2) + [4.0,4.3,4.7,5.2,6.0] 
bins_dphi  = [-3.15,-2.8,-2.6,-2.4,-2.2,-2.0,-1.7,-1.3,-0.9,-0.3,0.3,0.9,1.3,1.7,2.0,2.2,2.4,2.6,2.8,3.15]
pt = "p_{#lower[-0.25]{T}}"
#pt2 = "p_{#kern[-0.2]{#lower[-0.25]{T}}}"
jpt = "p_{#lower[-0.32]{T}}^{#lower[0.24]{jet}}"
sumjet = "#lower[-0.40]{#scale[0.68]{#sum}}#kern[0.009]{#lower[-0.09]{%s (%s > 30 GeV, |#eta| < 4.7) [GeV]}}"%(jpt,jpt)
comvars = [ # common variables
#   Var('ntau',         7,   0,    7, title="Number of #tau leptons", ),
#   ###Var('ntgen',       7,    0,    7, title="Number of top quarks", ),
#   Var('ntau20',       7,   0,    7, title="Number of #tau leptons (%s > 20 GeV, |#eta| < 2.5)"%pt ),
#   Var('ntau50',       7,   0,    7, title="Number of #tau leptons (%s > 50 GeV, |#eta| < 2.5)"%pt ),
#   Var('tau1_pt',     20,   0, 1200, title="Leading tau "+pt ),
#   Var('tau1_pt',     15,   0,  600, title="Leading tau "+pt, fname="$VAR_zoom" ),
#   Var('tau1_pt',         bins_tpt1, title="Leading tau "+pt, logy=True, ymin=1e-7, fname="$VAR_log" ),
#   Var('tau1_ptvis',  20,   0, 1200, title="Leading tau %s^{#lower[0.25]{vis}}"%pt ),
#   Var('tau1_ptvis',  15,   0,  600, title="Leading tau %s^{#lower[0.25]{vis}}"%pt, fname="$VAR_zoom" ),
#   Var('tau2_pt',     20,   0, 1200, title="Subleading tau "+pt ),
#   Var('tau2_pt',     15,   0,  600, title="Subleading tau "+pt, fname="$VAR_zoom" ),
#   Var('tau2_pt',         bins_tpt1, title="Subleading tau "+pt, logy=True, ymin=1e-7, fname="$VAR_log" ),
#   Var('tau2_ptvis',  20,   0, 1200, title="Subleading tau %s^{#lower[0.25]{vis}}"%pt ),
#   Var('tau2_ptvis',  15,   0,  600, title="Subleading tau %s^{#lower[0.25]{vis}}"%pt, fname="$VAR_zoom" ),
#   Var('tau1_eta',    24,  -6,    6, title="Leading #tau lepton eta", ymargin=1.44, ncol=2, pos='LL' ),
#   Var('tau1_eta',         bins_eta, title="Leading #tau lepton eta", ymargin=1.44, ncol=2, pos='LL', fname="$VAR_rebin" ),
#   Var('abs(tau1_eta)', 10, 0,    5, title="Leading #tau lepton |eta|", fname="tau1_eta_abs" ),
#   Var('tau2_eta',    24,  -6,    6, title="Subleading #tau lepton eta", ymargin=1.44, ncol=2, pos='LL' ),
#   Var('tau2_eta',         bins_eta, title="Subleading #tau lepton eta", ymargin=1.44, ncol=2, pos='LL', fname="$VAR_rebin" ),
#   Var('abs(tau2_eta)', 10, 0,    5, title="Subleading #tau lepton |eta|", fname="tau2_eta_abs" ),
#   Var('m_ll',        25,   0, 2500, title="m_{#lower[-0.06]{#tau#tau}}", units='GeV' ),
#   Var('m_ll',        20,   0, 1200, title="m_{#lower[-0.06]{#tau#tau}}", units='GeV', fname="$VAR_zoom" ),
#   Var('mvis_ll',     25,   0, 2500, title="m^{#lower[0.15]{vis}}_{#lower[-0.06]{#tau#tau}}", units='GeV' ),
#   Var('mvis_ll',     20,   0, 1200, title="m^{#lower[0.15]{vis}}_{#lower[-0.06]{#tau#tau}}", units='GeV', fname="$VAR_zoom" ),
#   Var('dr_ll',             bins_dR, title="#DeltaR_{#lower[-0.15]{#tau#tau}}", ymargin=1.44, ncol=2, pos='LL' ),
#   Var('deta_ll',          bins_eta, title="#Delta#eta_{#lower[-0.25]{#tau#tau}}", ymargin=1.44, ncol=2, pos='LL' ),
#   Var('dphi_ll', 15, -3.142, 3.142, title="#Delta#phi_{#lower[-0.25]{#tau#tau}}", ymargin=1.2, pos='Cy=0.85' ),
#   Var('nbgen',        7,   0,    7, title="Number of b quarks" ),
#   Var('nbgen30',      7,   0,    7, title="Number of b quarks (%s > 30 GeV, |#eta| < 2.5)"%pt ),
#   Var('nbgen50',      7,   0,    7, title="Number of b quarks (%s > 50 GeV, |#eta| < 2.5)"%pt ),
  Var('njet',         9,   0,    9, title="Number of gen. jets (%s > 30 GeV, |eta| < 4.7)"%pt ),
  Var('njet50',       9,   0,    9, title="Number of gen. jets (%s > 50 GeV, |eta| < 4.7)"%pt ),
  Var('ncjet',        9,   0,    9, title="Number of gen. jets (%s > 30 GeV, |eta| < 2.5)"%pt ),
#   Var('jpt1',        40,   0, 2000, title="Leading gen. jet "+pt ),
#   Var('jpt1',        30,   0, 1200, title="Leading gen. jet "+pt, fname="$VAR_zoom" ),
#   Var('jpt1',        20,   0,  400, title="Leading gen. jet "+pt, fname="$VAR_zoom2" ),
#   ###Var('jpt1',           bins_jpt2, title="Leading gen. jet "+pt, fname="$VAR_zoom2" ),
#   ###Var('jpt1',           bins_jpt1, title="Leading gen. jet "+pt, logy=True, ymin=1e-5, fname="$VAR_log" ),
#   Var('jeta1',       24,  -6,    6, title="Leading gen. jet eta", ymargin=1.44, ncol=2, pos='LL' ),
#   Var('jeta1',            bins_eta, title="Leading gen. jet eta", ymargin=1.44, ncol=2, pos='LL', fname="$VAR_rebin" ),
#   Var('abs(jeta1)',  10,   0,    5, title="Leading gen. jet |eta|", fname="jeta1_abs" ),
#   Var('jpt2',        40,   0, 2000, title="Subleading gen. jet "+pt ),
#   Var('jpt2',        30,   0, 1200, title="Subleading gen. jet "+pt, fname="$VAR_zoom" ),
#   Var('jpt2',        20,   0,  400, title="Subleading gen. jet "+pt, fname="$VAR_zoom2" ),
#   ###Var('jpt2',            bins_jpt2, title="Subleading gen. jet "+pt, fname="$VAR_zoom2" ),
#   ###Var('jpt2',            bins_jpt1, title="Subleading gen. jet "+pt, logy=True, logyrange=6, fname="$VAR_log" ),
#   Var('jeta2',       24,  -6,    6, title="Subleading gen. jet eta", ymargin=1.44, ncol=2, pos='LL' ),
#   Var('jeta2',            bins_eta, title="Subleading gen. jet eta", ymargin=1.44, ncol=2, pos='LL', fname="$VAR_rebin" ),
#   Var('abs(jeta2)',  10,   0,    5, title="Subleading gen. jet |eta|", fname="jeta2_abs" ),
#   Var('met',         25,   0, 1000, title="MET" ),
#   Var('met',         26,   0,  400, title="MET", fname="$VAR_zoom" ),
#   Var('sumjet',      50,   0, 4000, title=sumjet, units=False ),
#   Var('sumjet',      20,   0,  400, title=sumjet, units=False, fname="$VAR_zoom" ),
#   Var('st',                bins_st, title="S_{#lower[-0.2]{T}}", logy=True, ymin=1e-8, addOverflowToLastBin=True ),
#   Var('stmet',             bins_st, title="S_{#lower[-0.2]{T}}^{MET}", logy=True, ymin=1e-8, addOverflowToLastBin=True ),
]
jetvars =  [
  Var('pt',     bins_pt1, title="Generator jet "+pt, fname="jet_pt" ),
  Var('pt',  30, 0, 1200, title="Generator jet "+pt, fname="jet_pt_zoom" ),
  Var('eta',    bins_eta, title="Generator jet eta", fname="jet_eta", ymargin=1.44, ncol=2, pos='LL' ),
]
varsets = [  
#   ( 'event', [
#     ( Sel("ntgen==0",title="LQ -> btau",weight='weight',fname=""),
#       comvars),
#     ###( Sel("ntgen==0 && tau1_ptvis>50 && tau2_ptvis>50 && jpt1>50 && mvis_ll>100", 
#     ###                 title="LQ -> btau, %s>50, %s>50"%(pt,jpt),weight='weight',fname=""),
#     ###  comvars),
#     ]),
  ( 'mother', [
    ( Sel("abs(dau)==5",title="LQ -> btau",weight='weight',fname=""), [
        ###Var('ndau',     15,    0,   15, title="Number of daughters", fname="LQ_ndau" ),
        ###Var('dau',      40,  -20,   20, title="LQ quark daughters",  fname="LQ_dau" ),
        Var('mass',     65,    0, 2600, title="LQ mass",             fname="LQ_mass", ymargin=1.44, ncol=2, pos='x=0.04', rmax=2.5, logy=True ),
        Var('pt',       37,    0, 2220, title="LQ "+pt,              fname="LQ_pt" ),
        Var('pt',              bins_pt, title="LQ "+pt,              fname="LQ_pt_rebin" ),
        ###var('pt',              bins_pt, title="LQ pT (low mass)",    fname="LQ_pt_lowmass", cut="mass < 500" ),
        Var('eta',      24,   -6,    6, title="LQ eta",              fname="LQ_eta", ymargin=1.44, ncol=2, pos='x=0.04' ), #pos='BC'
        ###Var('eta',            bins_eta, title="LQ eta",              fname="LQ_eta_rebin", ymargin=1.44, ncol=2, pos='L' ), #pos='BC'
        ###Var('phi',       8, -3.2,  3.2, title="LQ phi",              fname="LQ_phi", pos='BC' ),
        Var('dr_ll',           bins_dR, title="#DeltaR_{#lower[-0.15]{btau}}", fname="LQ_dr_btau", ymargin=1.44, ncol=2, pos='x=0.04' ),
        Var('deta_ll',        bins_eta, title="#Delta#eta_{#lower[-0.25]{btau}}", fname="LQ_deta_btau", ymargin=1.44, ncol=2, pos='x=0.04' ),
        Var('dphi_ll', 15, -3.142, 3.142, title="#Delta#phi_{#lower[-0.25]{btau}}", fname="LQ_dphi_btau", ymargin=1.24, pos='Cy=0.85' ),
        ###Var('dphi_ll',       bins_dphi, title="#Delta#phi_{#lower[-0.2]{btau}}", fname="LQ_dphi_btau", ymargin=1.3, pos='Cy=0.89' ),
      ]),
    ]),
#   ( 'decay', [
#     ( Sel("",title="LQ -> btau",weight='weight',fname=""), [
#         Var('pid',     36,  -18,   18, title="LQ daughters", fname="decay_PID", ymargin=1.44, ncol=2, pos='x=0.04' ),
#       ]),
#     ( Sel("abs(pid)==15",title="LQ -> btau",weight='weight',fname=""), [
#         Var('pt',      40,    0, 1600, title="#tau lepton (from LQ decay) "+pt, fname="decay_pt_tau" ),
#         Var('ptvis',   40,    0, 1200, title="#tau lepton (from LQ decay) %s^{#lower[0.25]{vis}}"%pt, fname="decay_ptvis_tau", ),
#         Var('ptvis',       bins_ptvis, title="#tau lepton (from LQ decay) %s^{#lower[0.25]{vis}}"%pt, fname="decay_ptvis_tau_rebin", ),
#         Var('eta',           bins_eta, title="#tau lepton (from LQ decay) eta", fname="decay_eta_tau", ymargin=1.44, ncol=2, pos='x=0.04' ),
#         ###Var('phi',      8, -3.2,  3.2, title="#tau lepton (from LQ decay) phi", fname="decay_phi_tau", pos='BC' ),
#       ]),
#     ( Sel("abs(pid)==5",title="LQ -> btau",weight='weight',fname=""), [
#         Var('pt',      40,    0, 1600, title="b quark (from LQ decay) "+pt, fname="decay_pt_b" ),
#         Var('pt',            bins_pt1, title="b quark (from LQ decay) "+pt, fname="decay_pt_b_rebin" ),
#         Var('eta',     24,   -6,    6, title="b quark (from LQ decay) eta", fname="decay_eta_b", ymargin=1.44, ncol=2, pos='x=0.04' ),
#         Var('eta',           bins_eta, title="b quark (from LQ decay) eta", fname="decay_eta_b_rebin", ymargin=1.44, ncol=2, pos='x=0.04' ),
#         ###Var('phi',      8, -3.2,  3.2, title="b quark (from LQ decay) phi", fname="decay_phi_b", pos='BC' ),
#       ]),
#     ]),
#   ( 'assoc', [
#     ( Sel("abs(pid)==15",title="pp -> LQtau",weight='weight',fname=""), [
#         Var('pt',      40,    0, 1200, title="#tau lepton (not from LQ decay) "+pt, fname="decay_pt_tau" ),
#         Var('pt',            bins_pt1, title="#tau lepton (not from LQ decay) "+pt, fname="assoc_pt_tau_rebin" ),
#         Var('ptvis',   25,    0, 1000, title="#tau lepton (not from LQ decay) %s^{#lower[0.2]{vis}}"%pt, fname="assoc_ptvis_tau" ),
#         Var('eta',     24,   -6,    6, title="#tau lepton (not from LQ decay) eta", fname="assoc_eta_tau", ymargin=1.44, ncol=2, pos='x=0.04' ),
#         Var('eta',           bins_eta, title="#tau lepton (not from LQ decay) eta", fname="assoc_eta_tau_rebin", ymargin=1.44, ncol=2, pos='x=0.04' ),
#         ###Var('phi',      8, -3.2,  3.2, title="#tau lepton (not from LQ decay) phi", fname="assoc_phi_tau", pos='BC' ),
#       ]),
#     ( Sel("abs(pid)==5",title="LQ -> btau",weight='weight',fname=""), [
#         Var('pt',      25,    0,  250, title="b quark (not from LQ decay) "+pt, fname="assoc_pt_b" ),
#         Var('eta',     20,   -6,    6, title="b quark (not from LQ decay) eta", fname="assoc_eta_b", ymargin=1.2, ncol=1, pos='BC' ),
#         ###Var('phi',     16, -3.2,  3.2, title="b quark (not from LQ decay) phi", fname="assoc_phi_b", pos='BC' ),
#       ])
#     ]),
#   ( 'jet', [
#     ( Sel("",title="all jets",weight='weight',fname=""), jetvars ),
#     ( Sel("pt>20 && abs(eta)<2.5",title="central jets (|#eta| < 2.5)",weight='weight',fname="central"), jetvars ),
#     ]),
]

def compare_LQ(name,title,samples,tag="",**kwargs):
  """Compare list of samples."""
  LOG.header("compare_LQ",pre=">>>")
  outdir   = kwargs.get('outdir', "plots/GENSIM" )
  norms    = kwargs.get('norm',   [True]         )
  exts     = kwargs.get('ext',    ['png']        ) # figure file extensions
  verb     = kwargs.get('verb',   0              )
  ensuredir(outdir)
  norms    = ensurelist(norms)
  CMSStyle.setCMSEra(era='Run 2',lumi=None,cme=13,thesis=True,extra="(CMS simulation)",verb=verb) #extra="Preliminary")
  #setera(era) # set era for plot style and lumi-xsec normalization
  ratio    = True and False
  denom    = 3 # use Scalar, M = 1400 GeV in denominator
  rrange   = 1.0 # ratio range
  
  # SELECTIONS
  selections = [
    #Sel('mutau', "ntau_hard>=2 && nmuon_tau>=1 && ntauh_hard>=1" ),
  ]
  
  # PLOT from trees
  for treename, selsets in varsets:
    if 'LQ-t' in samples[0].name and any(s in treename for s in ['decay','mother']):
      continue
    print(">>>\n>>> "+bold("Using tree %r for %r"%(treename,title)))
    trees = { }
    for sample in samples:
      sample.gettree(treename,refresh=True,verb=verb-1)
    for selection, varset in selsets:
      ###for selection in selections:
      if 'assoc' in treename and '==15' in selection.selection and any('LQ-'+p in samples[0].name for p in 'pt'):
        continue
      print(">>> %s: %r"%(selection.title,selection.selection))
      hdict = { }
      text  = ', '.join([title,selection.title]) #.replace('tau',"tau_{#lower[-0.2]{h}}")
      if 'nonres' in title.lower():
        text = text.replace(", LQ -> btau","")
      #vars  = [v for v in varset if v.plotfor(selection) and selection.plotfor(v)]
      for sample in samples:
        if verb>=1:
          print(">>> compare_LQ: Getting histogram from %s"%(sample.name))
        hists = sample.gethists(varset,selection,verb=verb)
        for var, hist in zip(varset,hists):
          hdict.setdefault(var,[ ]).append(hist)
      for var, hists in hdict.items():
        for norm in norms:
          ntag  = '_norm' if norm else "_lumi"
          fname = "%s/$VAR_%s_%s%s%s"%(outdir,name,selection.filename,tag,ntag)
          lsize = _Plot._lsize*(1.5 if var.name.endswith('_q') else 1)
          style = 1 #[1,1,2,1,1,1]
          ###ncol  = 1
          nxdiv = 510
          pos   = var.position
          logyrange = var.logyrange
          ymargin = var.ymargin
          twidth = 1.04 if var.ncols==1 else 1.0
          if var.xmax>=2000:
            nxdiv = 508
          if 'LQ-p' in samples[0].name: # Pair
            if any(s in var.filename for s in ['njet','ncjet']):
              pos = 'R'
              ymargin = 1.45 if var.filename=='njet' else 1.34
          elif 'LQ-s' in samples[0].name: # Single
            if var.logy and "LQ_eta" in var.filename:
              ymargin = 1.2
              pos = 'BC'
          elif 'LQ-t' in samples[0].name: # NonRes
            if var.logy and "jpt" in var.filename:
              logyrange = 7
          ###if (var.name=='eta' or '_eta' in var.name) and 'L' in pos:
          ###  ncol = 2
          ###  ###print var.name, ncol
          if not pos:
            pos = 'y=0.85'
            twidth *= 1.1
          elif not any(s in pos for s in 'yTB'):
            pos += 'y=0.89'
          plot  = Plot(var,hists,norm=norm,clone=True,ratio=ratio)
          plot.draw(xlabelsize=lsize,pair=True,ymargin=ymargin,denom=denom,colors=colors,
                    rrange=rrange,logyrange=logyrange,nxdiv=nxdiv,grid=False,width=700) #style=style,
          plot.drawlegend(margin=1.2,pos=pos,twidth=twidth) #header=title) #,entries=entries)
          plot.drawtext(text)
          plot.saveas(fname.replace('__','_'),ext=exts) #,tag=ntag,'pdf'
          plot.close()
        deletehist(hists)
  print(">>> ")
  

def main(args):
  fname     = None #"$PICODIR/$SAMPLE_$CHANNEL.root" # fname pattern
  parallel  = args.parallel
  varfilter = args.varfilter
  selfilter = args.selfilter
  pdf       = args.pdf
  outdir    = "plots/GENSIM"
  tag       = args.tag
  exts      = ['png','pdf'] if pdf else ['png']
  verbosity = args.verbosity
  
  # SAMPLE SETS
  indir  = "../PicoProducer/utils/"
  samset = [
    ('LQ_Single','s',"Single LQ production"),
    ('LQ_Pair',  'p',"LQ pair production"),
    ('LQ_NonRes','t',"Nonres. tautau production via LQ exchange"),
  ]
  for name, prod, title in samset:
    #title  = "LQ -> btau, "+title
    samples = [
      Sample('SLQ-%s_M600'%(prod), "Scalar, M = 600 GeV", indir+"GENSIM_converted_SLQ-%s_M600_L1p0.root"%(prod), verb=verbosity),
      Sample('VLQ-%s_M600'%(prod), "Vector, M = 600 GeV", indir+"GENSIM_converted_VLQ-%s_M600_L1p0.root"%(prod), verb=verbosity),
      Sample('SLQ-%s_M1400'%(prod),"Scalar, M = 1400 GeV",indir+"GENSIM_converted_SLQ-%s_M1400_L1p0.root"%(prod),verb=verbosity),
      Sample('VLQ-%s_M1400'%(prod),"Vector, M = 1400 GeV",indir+"GENSIM_converted_VLQ-%s_M1400_L1p0.root"%(prod),verb=verbosity),
      Sample('SLQ-%s_M2000'%(prod),"Scalar, M = 2000 GeV",indir+"GENSIM_converted_SLQ-%s_M2000_L1p0.root"%(prod),verb=verbosity),
      Sample('VLQ-%s_M2000'%(prod),"Vector, M = 2000 GeV",indir+"GENSIM_converted_VLQ-%s_M2000_L1p0.root"%(prod),verb=verbosity),
    ]
    compare_LQ(name,title,samples,tag=tag,outdir=outdir,ext=exts,verb=verbosity)
  

if __name__ == "__main__":
  import sys
  from argparse import ArgumentParser
  description = """Simple plotting script to compare distributions in GENSIM tuples"""
  parser = ArgumentParser(prog="plot_compare",description=description,epilog="Good luck!")
  parser.add_argument('-V', '--var',     dest='varfilter', nargs='+',
                                         help="only plot the variables passing this filter (glob patterns allowed)" )
  parser.add_argument('-S', '--sel',     dest='selfilter', nargs='+',
                                         help="only plot the selection passing this filter (glob patterns allowed)" )
  parser.add_argument('-s', '--serial',  dest='parallel', action='store_false',
                                         help="run Tree::MultiDraw serial instead of in parallel" )
  parser.add_argument('-p', '--pdf',     dest='pdf', action='store_true',
                                         help="create pdf version of each plot" )
  parser.add_argument('-t', '--tag',     default="", help="extra tag for output" )
  parser.add_argument('-v', '--verbose', dest='verbosity', type=int, nargs='?', const=1, default=0, action='store',
                                         help="set verbosity" )
  args = parser.parse_args()
  LOG.verbosity = args.verbosity
  PLOG.verbosity = args.verbosity
  main(args)
  print("\n>>> Done.")
  
