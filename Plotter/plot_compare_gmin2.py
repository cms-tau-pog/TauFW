#! /usr/bin/env python3
# Author: Izaak Neutelings (June 2023)
# Description: Compare distributions in pico analysis tuples
# Instructions:
#   ./plot_compare_gmin2.py -y UL2018 -m hs -L
#   ./plot_compare_gmin2.py -y UL2018 -m pu -L
print(">>> Importing...")
import os, re
from math import sqrt
import ctypes # for passing by reference
#from array import array
print(">>> Importing ROOT...")
import ROOT; ROOT.PyConfig.IgnoreCommandLineOptions = True
from ROOT import gStyle, TH2D, TLatex, TGraphErrors, TColor,\
                 kBlack, kGray, kRed, kBlue, kGreen, kMagenta, kSpring, kOrange
print(">>> Importing TauFW.sample...")
#from config.samples import * # for general getsampleset
import TauFW.Plotter.sample.utils as GLOB
from TauFW.Plotter.sample.utils import LOG; SLOG = LOG
from TauFW.Plotter.sample.utils import getsampleset as _getsampleset # for getsampleset_simple
from TauFW.Plotter.sample.utils import MC, SampleSet, MergedSample, getmcsample, setera, getyear, Sel, Var, joinweights
from TauFW.Plotter.sample.HistSet import HistSet
from TauFW.Plotter.plot.Plot import LOG as PLOG
from TauFW.Plotter.plot.Plot import Plot, deletehist
from TauFW.Plotter.plot.Plot2D import Plot2D
from TauFW.Plotter.plot.Stack import Stack
from TauFW.Plotter.plot.CMSStyle import lumi_dict, era_dict
from TauFW.Plotter.plot.utils import sumhists
from TauFW.common.tools.file import ensuredir
from TauFW.common.tools.utils import ensurelist, repkey
from TauFW.common.tools.root import ensureTFile, ensureTDirectory, rootrepr, loadmacro
from TauFW.common.tools.math import partition, frange
from TauFW.common.tools.RDataFrame import RDF
print(">>> Done importing...")
picodir = "/eos/user/i/ineuteli/analysis/g-2"

# COMMON CROSS SECTION for elastic signals
#xsec_mm = 0.324*0.328 #0.37553*0.33 # old samples with filter, alpha = 1/126
xsec_mm = 0.303 # new samples without filter, alpha = 1/137
xsec_tt = 1.048*0.0403 # new samples without filter, alpha = 1/137 (GGToTT_Ctb20)
#xsec_ww = 0.00692*0.368 #WRONG: 0.37553*0.33 # old samples with filter, alpha = 1/126
xsec_ww = 0.006561 # new samples without filter, alpha = 1/137

# CUSTOM COLOR
kMyFaintRed = TColor.GetColor(1.0,0.97,0.94) # kRed-10
kMyLightRed = TColor.GetColor(1.0,0.86,0.90) # 19, kRed-9


def integrate(hist,ilow,iup):
  """Help function to retrieve integral + uncertainty."""
  yerr = ctypes.c_double()
  yval = hist.IntegralAndError(ilow,iup,yerr)
  #assert yval==hist.Integral(ilow,iup)
  return yval, yerr.value
            

def getweight(channel,era,**kwargs):
  verb = kwargs.get('verb',0)#+1
  if 'weight' in kwargs:
    weight = kwargs['weight'] # override
  elif 'mutau' in channel:
    weight = "genweight*trigweight*puweight*idisoweight_1*idweight_2*ltfweight_2"
  elif 'mumu' in channel:
    weight = "genweight*trigweight*puweight*idisoweight_1*idisoweight_2"
  else:
    weight = "genweight*trigweight*puweight*idweight_1*idweight_2*ltfweight_1*ltfweight_2"
  LOG.verb(f"getweight: before {weight}",verb,3)
  if 'extraweight' in kwargs:
    weight += '*'+kwargs['extraweight']
  if '$ERA' in weight:
    from ROOT import getEraIndex # from python/corrections/g-2/ntracks_pileup.C
    weight = weight.replace('$ERA',str(getEraIndex(era)))
  LOG.verb(f"getweight: after {weight}",verb,3)
  return weight.strip('*')
  

def getbaseline(channel):
  if 'tautau' in channel:
    cuts_iso  = "idDeepTau2017v2p1VSjet_1>=16 && idDeepTau2017v2p1VSjet_2>=16"
    antilep   = "idDeepTau2017v2p1VSe_1>=2 && idDeepTau2017v2p1VSmu_1>=1 && idDeepTau2017v2p1VSe_2>=2 && idDeepTau2017v2p1VSmu_2>=1"
    baseline  = "q_1*q_2<0 && idDecayModeNewDMs_1 && idDecayModeNewDMs_2 && %s && %s && !lepton_vetos_noTau && metfilter"%(antilep,cuts_iso)
  elif 'mutau' in channel:
    idiso1   = "iso_1<0.15 && idMedium_1"
    idiso2   = "idDecayModeNewDMs_2 && idDeepTau2017v2p1VSjet_2>=16 && idDeepTau2017v2p1VSe_2>=2 && idDeepTau2017v2p1VSmu_2>=8"
    baseline = "q_1*q_2<0 && %s && %s && !lepton_vetoes_notau && metfilter"%(idiso1,idiso2)
  elif 'mumu' in channel:
    idiso1   = "iso_1<0.15" # && idMedium_1"
    idiso2   = "iso_2<0.15" # && idMedium_1"
    baseline = "q_1*q_2<0 && %s && %s && !lepton_vetoes && metfilter"%(idiso1,idiso2)
  return baseline
  

def makemcsample(group,sname,title,xsec,channel,era,tag="",verb=0,**kwargs):
  if era=='Run2':
    sample = MergedSample(sname,title,**kwargs)
    for era_ in ['UL2016_preVFP','UL2016_postVFP','UL2017','UL2018']:
      sample_ = makemcsample(group,sname,title,xsec,channel,era_,tag=tag,verb=verb,**kwargs)
      sample += sample_
    print(sample.row())
    return sample
  kwargs['lumi'] = lumi_dict[era]
  kwargs['weight'] = getweight(channel,era,**kwargs)
  kwargs.pop('extraweight')
  if 'e' in channel:
    channel = channel.replace('e','ele')
  fname   = "$PICODIR/$ERA/$GROUP/$SAMPLE_$CHANNEL$TAG.root"
  fname_  = repkey(fname,PICODIR=picodir,ERA=era,GROUP=group,SAMPLE=sname,CHANNEL=channel,TAG=tag)
  if not os.path.isfile(fname_):
    print(">>> Did not find %r"%(fname_))
  name   = sname+tag
  if verb>=1:
    print(">>> makemcsample: %s, %s, %s"%(name,sname,fname_))
  sample = MC(name,title,fname_,xsec,**kwargs)
  #sample.addalias('z_mumu',"pv_z+0.5*dz_1+0.5*dz_2",verb=verb)
  #sample.addalias('aco',"(1-abs(dphi_ll)/3.14159265)",verb=verb)
  sample.addaliases(**{
    'm_ll':          "m_vis",
    'aco':           "(1-abs(dphi_ll)/3.14159265)",
    'z_mumu':        "pv_z+0.5*dz_1+0.5*dz_2",
    #'bs_sigmaUp':    'bs_sigma+bs_sigmaErr',
    #'bs_sigmaDown':  'bs_sigma-bs_sigmaErr',
    'ntrack_all':    "ntrack_hs+ntrack_pu",
    'ntrack_all_raw':"ntrack_hs+ntrack_pu_raw",
    'ntrack_allUp':  "ntrack_hs+ntrack_puUp",
    'ntrack_allDown':"ntrack_hs+ntrack_puDown",
  },verb=0)
  
  return sample
  

def getsampleset(channel,era,**kwargs):
  """Simplified version of Plotter/config/samples.py:getsampleset"""
  # https://github.com/cecilecaillol/MyNanoAnalyzer/blob/aa4775b8478c9a4fdba263461a1ae4762a953809/NtupleAnalyzerCecile/FinalSelection_mumu.cc#L59-L113
  verb = kwargs.get('verb', 0)
  if era=='Run2':
    sampleset = SampleSet()
    for era_ in ['UL2016_preVFP','UL2016_postVFP','UL2017','UL2018']:
      sampleset += getsampleset(channel,era_,**kwargs)
    samplesF = sampleset.get('Run2016F',recursive=True,verb=verb)
    for t, sample in zip(['a','b'],samplesF):
      sample.name = sample.name.replace('2016F','2016F'+t)
    sampleset.printtable()
    return sampleset
  #fname     = "$PICODIR/$SAMPLE_$CHANNEL$TAG.root"
  fname     = f"{picodir}/$ERA/$GROUP/$SAMPLE_$CHANNEL$TAG.root"
  fname     = kwargs.get('fname',       fname   ) or fname # file name pattern of pico files
  tag       = kwargs.get('tag',         ""      )
  table     = kwargs.get('table',       True    ) # print sample set table
  loadcorrs = kwargs.get('loadcorrs',   False   ) # load special corrections for SMP-23-005
  mcweight  = kwargs.get('extraweight', ""      ) # extra weight for all MC
  dyweight  = kwargs.get('dyweight',    ""      ) # print sample set table
  showEra   = kwargs.get('showEra',     True    ) #and (era not in ['UL2017','UL2018'])
  extratext = kwargs.get('extra', "Preliminary" ) # extra CMS text
  filters   = kwargs.get('filter',      ['DY']  )
  year      = getyear(era) # get integer year
  setera(era,showEra=showEra,extra=extratext) # set era for plot style and lumi-xsec normalization
  
  # DEFINE CORRECTIONS
  if loadcorrs or 'getPUTrackWeight' in mcweight or 'getHSTrackWeight' in dyweight: # skip recreating histograms (fast!)
    print(">>> Loading PU track corrections...")
    loadmacro("python/corrections/g-2/corrs_ntracks.C",fast=True,verb=verb)
    from ROOT import loadPUTrackWeights, loadHSTrackWeights, getEraIndex
    iera = getEraIndex(era)
    if loadcorrs or 'getPUTrackWeight' in mcweight:
      loadPUTrackWeights(era,verb+1)
      if 'getPUTrackWeight' not in mcweight:
        mcweight = joinweights(mcweight,f"getPUTrackWeight(ntrack_pu,z_mumu,{iera})")
        #mcweight = joinweights(mcweight,"getPUTrackWeight(ntrack_pu,pv_z+0.5*dz_1+0.5*dz_2,{iera})")
    else:
      print(">>> Skip loading PU track corrections...")
    if loadcorrs or 'getHSTrackWeight' in dyweight:
      loadHSTrackWeights(era,verb+1)
      if 'getHSTrackWeight' not in dyweight:
        dyweight = joinweights(dyweight,f"getHSTrackWeight(ntrack_hs,aco,{iera})")
    else:
      print(">>> Skip loading HS track corrections...")
  else:
    print(">>> Skip loading PU & HS track corrections...")
  if loadcorrs or 'getAcoWeight' in dyweight:
    print(">>> Loading acoplanarity corrections...")
    loadmacro("python/corrections/g-2/aco.C",fast=True,verb=verb)
    from ROOT import loadAcoWeights, getEraIndex2
    loadAcoWeights(era,verb+1)
    iera = getEraIndex2(era)
    if 'getAcoWeight' not in dyweight:
      dyweight = joinweights(dyweight,f"getAcoWeight(aco,pt_1,pt_2,{iera})")
    if '$ERA' in dyweight:
      dyweight = dyweight.replace('$ERA',str(getEraIndex2(era)))
    print(">>> Done loading corrections!")
  else:
    print(">>> Skip loading aco corrections...")
  #kwargs['extraweight'] = joinweights(kwargs.get('extraweight',''),wgt_mc)
  kwargs['extraweight'] = mcweight
  weight = getweight(channel,era,**kwargs)
  if '$ERA' in weight or '$ERA' in dyweight:
    loadmacro("python/corrections/g-2/corrs_ntracks.C",fast=True,verb=verb+1)
    from ROOT import getEraIndex # from python/corrections/g-2/ntracks_pileup.C
    weight   = weight.replace('$ERA',str(getEraIndex(era)))
    dyweight = dyweight.replace('$ERA',str(getEraIndex(era)))
  if verb+2>=1:
    print(f">>> dyweight = {dyweight!r}")
    print(f">>> mcweight = {mcweight!r}")
    print(f">>> weight   = {weight!r}")
  
  # DEFINE SAMPLE LIST
  if 'UL' in era: # UltraLegacy
    xsec_dy_lo   = 5343.0
    xsec_dy_nnlo = 6077.22
    xsec_dy      = xsec_dy_nnlo*0.318 #*0.98
    expsamples = [ # table of MC samples to be converted to Sample objects
      # https://github.com/cecilecaillol/MyNanoAnalyzer/blob/master/NtupleAnalyzerCecile/FinalSelection_etau.cc#L99C37-L99C49
      # GROUP NAME                     TITLE                 XSEC      EXTRA OPTIONS
      ( 'DY', "DYJetsToLL_M-50",       "Drell-Yan",         xsec_dy, {'extraweight': dyweight} ), # apply k-factor in stitching
      ###( 'DY', "DY1JetsToLL_M-50",      "Drell-Yan 1J 50",      877.8, {'extraweight': dyweight} ),
      ###( 'DY', "DY2JetsToLL_M-50",      "Drell-Yan 2J 50",      304.4, {'extraweight': dyweight} ),
      ###( 'DY', "DY3JetsToLL_M-50",      "Drell-Yan 3J 50",      111.5, {'extraweight': dyweight} ),
      ###( 'DY', "DY4JetsToLL_M-50",      "Drell-Yan 4J 50",      44.05, {'extraweight': dyweight} ),
      ###( 'WJ', "WJetsToLNu",            "W + jets",           52940.0  ),
      ###( 'WJ', "W1JetsToLNu",           "W + 1J",              8104.0  ),
      ###( 'WJ', "W2JetsToLNu",           "W + 2J",              2793.0  ),
      ###( 'WJ', "W3JetsToLNu",           "W + 3J",               992.5  ),
      ###( 'WJ', "W4JetsToLNu",           "W + 4J",               544.3  ),
      ###( 'VV', "WWTo2L2Nu",             "WW",            118.7*0.3*0.3*0.397 ), # 8.95*0.397
      ###( 'VV', "ZZTo2L2Nu",             "ZZ",                   3.0*0.302 ),
      ( 'VV', "VVTo2L2Nu",             "VVTo2L2Nu",             12.0638*0.392 ), # 11.09+0.9738, 11.950
      ( 'VV', "WZTo3LNu",              "WZTo3LNu",               5.213*0.341  ),
      ( 'VV', "WZTo2Q2L",              "WZTo2Q2L",               6.419*0.341  ),
      ( 'VV', "ZZTo2Q2L",              "ZZTo2Q2L",               3.220*0.373  ),
      ( 'VV', "ZZTo4L",                "ZZTo4L",                 1.325*0.304  ),
      ###( 'ST', "ST_t-channel_top",      "ST t-channel t",       136.02 ),
      ###( 'ST', "ST_t-channel_antitop",  "ST t-channel at",       80.95 ),
      ###( 'ST', "ST_tW_top",             "ST tW",                 35.85 ),
      ###( 'ST', "ST_tW_antitop",         "ST atW",                35.85 ),
#       ( 'TT', "TTTo2L2Nu",             "ttbar 2l2#nu",          88.29*0.657 ), #, {'extraweight': 'ttptweight'}
#       ( 'TT', "TTToHadronic",          "ttbar hadronic",       377.96*0.170 ), #, {'extraweight': 'ttptweight'}
#       ( 'TT', "TTToSemiLeptonic",      "ttbar semileptonic",   365.35*0.401 ), #, {'extraweight': 'ttptweight'}
    ]
  
  else:
    LOG.throw(IOError,"Did not recognize era %r!"%(era))
  datasamples = { # table of data samples (per channel) to be converted to Sample objects
    'mutau':  ('Data', "SingleMuon_Run%s?"%year),
    'mumu':   ('Data', "SingleMuon_Run%s?"%year),
    ###'etau':   ('Data', "SingleElectron_Run%s?"%year),
    ###'tautau': ('Data', "Tau_Run%s?"%year),
  }
  if filters:
    expsamples = [s for s in expsamples if s[0] in filters]
  
  # SAMPLE SET
  sampleset = _getsampleset(datasamples,expsamples,channel=channel,era=era,weight=weight,file=fname)
  ###sampleset.stitch("DY*J*M-50", incl='DYJ', name="DY_M50", npart='NUP' )
  ###sampleset.stitch("W*Jets",    incl='WJ',  name='WJ',     npart='NUP' )
  ###sampleset.join('TT')
  ###sampleset.join('DY', name='DY'  )
  sampleset.join('VV','WZ','WW','ZZ', name='VV' ) # Diboson
  ###sampleset.addalias('z_mumu',"pv_z+0.5*dz_1+0.5*dz_2",verb=verb+4)
  ###sampleset.addalias('aco',"(1-abs(dphi_ll)/3.14159265)",verb=verb+4)
  ###sampleset.addalias('ntrack_all',"ntrack_hs+ntrack_pu",verb=verb+4)
  sampleset.addaliases(**{
    'm_ll':          "m_vis",
    'aco':           "(1-abs(dphi_ll)/3.14159265)",
    'z_mumu':        "pv_z+0.5*dz_1+0.5*dz_2",
    #'bs_sigmaUp':    'bs_sigma+bs_sigmaErr',
    #'bs_sigmaDown':  'bs_sigma-bs_sigmaErr',
    'ntrack_all':    "ntrack_hs+ntrack_pu",
    'ntrack_all_raw':"ntrack_hs+ntrack_pu_raw",
    #'ntrack_allUp':  "ntrack_hs+ntrack_puUp",
    #'ntrack_allDown':"ntrack_hs+ntrack_puDown",
  },verb=verb)
  if table:
    sampleset.printtable()
  return sampleset
  

def gethname(var0,var,sample,subdir=None,verb=0):
  """Help function to get histogram name."""
  dname = var0.filename #.replace('_raw','')
  if subdir:
    dname += '/'+(subdir.filename if hasattr(subdir,'filename') else subdir)
  sname = sample.name if hasattr(sample,'name') else sample
  if verb>=1:
    print(f">>> gethname: sname={sname!r}, var.filename={var.filename!r}, var0.filename={var0.filename!r}, dname={dname!r}")
  hname = sname + var.filename.replace(var0.filename,'')
  return dname, hname
  

def savehist(hist,hfile,var,var0,sample,subdir=None,verb=0):
  """Save hists to file for later use."""
  if isinstance(var0,dict):
    var0 = var0.get(var,var)
  dname, hname = gethname(var0,var,sample,subdir=subdir)
  hdir = ensureTDirectory(hfile,dname,cd=True,verb=verb)
  LOG.verb("Writing %s/%s to %s..."%(dname,hname,hfile.GetName()),verb,level=4)
  hist.Write(hname,hist.kOverwrite)
  

def loadhist(hfile,var,var0,sample,subdir=None,verb=0):
  """Load hists from file."""
  if isinstance(var0,dict):
    var0 = var0.get(var,var)
  #if isinstance(var0,list):
  #  var0 = var
  dname, hname = gethname(var0,var,sample,subdir=subdir)
  hname = "%s/%s"%(dname,hname)
  LOG.verb("Loading %s..."%(hname),verb,level=2)
  subdir = hfile.Get(dname)
  if not subdir:
    hfile.ls()
    raise IOError("Could not find subdir %s/%s..."%(hfile.GetName(),dname))
  hist = hfile.Get(hname)
  if not hist:
    subdir.ls()
    raise IOError("Could not find hist %s:%s..."%(hfile.GetName(),hname))
  hist.SetDirectory(0)
  return hist
  

def loadallhists(hfile,vars,vars0,sample,subdir=None,**kwargs):
  if isinstance(subdir,list): # return nested dictionary { selection: { variable: hist } }
    return { s: loadallhists(hfile,vars,vars0,sample,subdir=s,**kwargs) for s in subdir }
  elif isinstance(vars0,list): # return dictionary { variable: hist }
    return { v: loadhist(hfile,v,v0,sample,subdir=subdir,**kwargs) for v, v0 in zip(vars,vars0) }
  else: # return dictionary { variable: hist }
    return { v: loadhist(hfile,v,vars0,sample,subdir=subdir,**kwargs) for v in vars }
  

def measure_ntracks_pu(era,channel,tag="",**kwargs):
  """Measure correction to number of PU tracks."""
  LOG.header("measure_ntracks_pu",pre=">>>")
  outdir    = kwargs.get('outdir',    "plots/g-2/ntracks_pu" )
  plotonly  = kwargs.get('plotonly',  False   ) or True # plot only without changing 2D histogram
  loadhists = kwargs.get('loadhists', False   ) or plotonly #True and False
  norms     = kwargs.get('norm',      [True]  )
  #entries   = kwargs.get('entries',  [str(e) for e in eras] ) # for legend
  exts      = kwargs.get('exts',      ['png','pdf'] ) # figure file extensions
  extratext = kwargs.get('extra',     "Preliminary" ) # extra CMS text
  logx      = kwargs.get('logx',      False   ) or True
  verbosity = kwargs.get('verb',      1       )
  chunk     = kwargs.get('chunk',     -1      )
  ensuredir(outdir)
  norms     = ensurelist(norms)
  rtitle    = "Obs. / Sim."
  hfname    = "%s/corrs_ntracks_pu_%s.root"%(outdir,era)
  #ntitle    = "Number of pileup tracks"
  ntitle    = "#it{N}_{#lower[-0.18]{tracks}}^{#lower[0.25]{PU}}"
  #print(verbosity); exit(0)
  
  # SELECTIONS
  baseline   = getbaseline(channel)
  selections = [
    #Sel('baseline', baseline),
    Sel('|m_{#lower[-0.3]{#mu#mu}} #minus m_{#lower[-0.05]{Z}}| < 15 GeV', baseline+" && abs(m_ll-91.1876)<15", logyrange=5.5, fname="baseline-ZMM"),
  ]
  
  # VARIABLES
  bs_z      = Var('bs_z',         200, -3,  3, fname="bs_z_logy", title="Beam spot z", pos='Ly=0.85', units='cm', ymarg=1.36, logyrange=5, logy=True, data=True) #ymin=2e-6, ymax=5e-1,
  bs_zRaw   = Var('bs_z_raw',     200, -3,  3, fname="$VAR_logy", title="Beam spot z", data=False)
  bs_sig    = Var('bs_sigma',      55,2.5,4.9, fname="$VAR_logy", title="Beam spot width #sigma_{z}", pos='y=0.92', units='cm', ymarg=1.36, logyrange=5, logy=True, data=True)
  bs_sigRaw = Var('bs_sigma_raw',  55,2.5,4.9, fname="$VAR_logy", title="Beam spot width #sigma_{z}", data=False)
  bs_sigUp  = Var('bs_sigmaUp',    55,2.5,4.9, fname="$VAR_logy", title="Beam spot width #sigma_{z}", data=False)
  bs_sigDn  = Var('bs_sigmaDown',  55,2.5,4.9, fname="$VAR_logy", title="Beam spot width #sigma_{z}", data=False)
  vardict   = {
    bs_z: bs_z,     bs_zRaw: bs_z,
    bs_sig: bs_sig, bs_sigRaw: bs_sig, bs_sigUp: bs_sig, bs_sigDn: bs_sig,
  }
  variables = [
    ###Var('m_vis', 23,  0, 460, fname="m_mumu", cbins={'91.18':(20,70,110)}),
    Var('m_vis', 23, 0, 460, fname="m_mumu_logy", title="m_{#lower[-0.2]{#mu#mu}}", logy=True, cbins={'91.18':(20,70,110)}),
    bs_zRaw, bs_z,
    bs_sigRaw, bs_sigDn, bs_sigUp, bs_sig,
    ###Var('ntrack_pu_0p1[100]',  50, 0,  50, title="Number of tracks", addof=True, int=True),
    ###Var('pt_1',   "Leading tau_h pt",    18, 0, 270),
    ###Var('pt_2',   "Subleading tau_h pt", 18, 0, 270),
    ###Var('jpt_1',  18, 0, 270),
    ###Var('jpt_2',  18, 0, 270),
    ###Var('met',    20, 0, 300),
  ]
  
  # GET SAMPLES
  sampleset  = getsampleset(channel,era,**kwargs)
  sample_obs = sampleset.get('Observed',unique=True,verb=verbosity-1)
  sample_dy  = sampleset.get('DY',unique=True,verb=verbosity-1)
  #print("sample_dy.title",sample_dy.title)
  sample_dy.title = "Z -> mumu"
  samples    = [
    sample_dy,
    sample_obs,
  ]
  
  if era=='UL2016_postVFP':
    bs_z_raw     = 0.8818893432617188
    bs_sigma_raw = 3.623931884765625
  elif era=='UL2016_preVFP':
    bs_z_raw     = 0.8818893432617188
    bs_sigma_raw = 3.623931884765625
  elif era=='UL2017':
    bs_z_raw     = 0.7898941040039062
    bs_sigma_raw = 3.497802734375
  else:
    bs_z_raw     = 0.024875402450561523
    bs_sigma_raw = 3.49884033203125
  
  for sample in samples:
    #print(sample,sample.isdata)
    sample.addaliases(
      ###bs_z_corr    = 'bs_z' if sample.isdata else 'bs_z+0.02488',
      ###bs_z_raw     = '0+0.02488',
      ###bs_sigma_raw = '0+3.498',
      bs_z_raw     = '0+%s'%bs_z_raw,     # hack
      bs_sigma_raw = '0+%s'%bs_sigma_raw, # hack
      bs_sigmaUp   = 'bs_sigma+bs_sigmaErr',
      bs_sigmaDown = 'bs_sigma-bs_sigmaErr',
      verb         = verbosity,
    )
  
  # 2D histogram
  ztitle = "Pileup track correction"
  xbins  = list(range(0,30,1))+list(range(30,50,2))+[50] # bin edges for ntracks
  xbins2 = list(range(0,16,1))+list(range(16,38,2))+list(range(38,50,4))+[50] # coarser binning at high |z|
  xvar   = Var('ntrack_pu_0p1',ntitle,xbins,logy=True,addof=True)
  yvar   = Var('z',"z",200,-10,10,units='cm') #fname="bs_z"
  hists2d = {
    'Nom':  xvar.gethist2D(yvar,'corr',ztitle=ztitle),
    'Up':   xvar.gethist2D(yvar,'corrUp',ztitle=ztitle),
    'Down': xvar.gethist2D(yvar,'corrDown',ztitle=ztitle),
    'raw':  xvar.gethist2D(yvar,'corr_raw',ztitle=ztitle),
  }
  
  variables = [ ]
  ifirst   = 0
  ilast    = 200
  nmax_nt  = 50
  if chunk>=1:
    ifirst = (chunk-1)*nmax_nt # e.g.  0,  50, 100, 150
    ilast  = ifirst+nmax_nt    # e.g. 50, 100, 150, 200
    hfname = hfname.replace(".root","_%s.root"%(chunk)) # split hist file to avoid conflict
  if chunk>=2 or plotonly:
    variables = [ ]
  print(">>> Add ntrack variables %s-%s"%(ifirst,ilast))
  systs = {
    '_raw': 'uncorr',
    'Down': 'down',
    'Up':   'up',
  }
  for i in range(ifirst,ilast):
    zmin    = -10+i*0.1
    zmax    = zmin+0.1
    if plotonly and not any(abs(zmin-z)<1e-4 for z in [-7,-3.5,0,3.4,6.9]):
      continue
    if abs(zmax)<1e-10:
      zmax = 0
    vtext   = ("%.1f <= z < %.1f cm"%(zmin,zmax)).replace(".0",'').replace('-','#minus')
    vname   = "ntrack_pu_0p1[%s]"%(i)     # BS-corrected
    fname   = "ntrack_pu_0p1_"+str(i).zfill(3) # e.g. 000, 001, ..., 023, ..., 199
    cut     = "%s<200"%(vname)
    xbins_  = xbins if abs(zmin+0.05)<=9 else xbins2 # coarser at high |z|
    var0    = Var(vname, xbins_, title=ntitle, fname=fname, flag=vtext, cut=cut, logy=True, ymin=3e-6, ymax=7, addof=True, int=True, data=True)
    var0.iy = i+1 # index for TH2D #hist2d.GetXaxis().FindBin(0,(zmin+zmax)/2)
    print(">>> %r, %r"%(vname,vtext))
    for syst in systs: # uncorrected, up/down variations
      if syst in ['Down','Up']: continue
      vname_ = "ntrack_pu_0p1%s[%s]"%(syst,i)
      fname_ = fname+syst
      var_   = Var(vname_, xbins_, title=ntitle, fname=fname_, flag=vtext, cut=cut, logy=True, ymin=3e-6, ymax=7, addof=True, int=True, data=False)
      variables.append(var_)
      vardict[var_] = var0
    variables.append(var0)
  print(">>> len(variables)=%s"%(len(variables)))
  
  # FOR STORING HISTS
  ropt  = 'READ' if plotonly else 'UPDATE'
  hfile = ensureTFile(hfname,ropt) # back up histograms for reuse
  
  # PLOT
  header = None #samples[0].title
  for selection in selections:
    print(">>> %s: %r"%(selection,selection.selection))
    hdict = { }
    
    # LOOP over SAMPLES
    for sample in samples:
      LOG.header("Sample %s (%r)"%(sample.name,sample.title),pre=">>>")
      #print(">>> Sample %s (%r)"%(sample.name,sample.title))
      vars_ = [v for v in variables if v.data or not sample.isdata]
      for var in vars_:
        var.changecontext(selection,verb=verbosity-1)
      
      # SPLIT INTO CHUNKS
      nmax = 1e6 if loadhists else 105 
      if sample.isdata: # maximum 100 variables simultaneously
        nmax *= 2
      varsets = partition(vars_,nmax=nmax) # chunkify
      print(">>> len(vars_)=%s, nmax=%s, len(varsets)=%s"%(len(vars_),nmax,len(varsets)))
      for iset, vars in enumerate(varsets):
        print(">>> Chunk %s/%s [%s:%s]"%(iset+1,len(varsets),vars_.index(vars[0]),vars_.index(vars[-1])))
        
        # DRAW / LOAD HIST
        if loadhists: # skip recreating histograms (fast!)
          hists = loadallhists(hfile,vars,vardict,sample,verb=verbosity)
        else: # create histograms from scratch (slow...)
          hists = sample.gethist(vars,selection,verb=verbosity)
        
        # REODER HISTS
        assert len(vars)==len(hists), "len(vars)=%s, len(hists)=%s"%(len(vars),len(hists))
        for var, hist in hists.items():
          htitle = hist.GetTitle()
          var0 = vardict.get(var,var) # reuse nominal / corrected var
          for syst in systs: # add systematic label to hist title for legend
            if syst in var.name:
              if systs[syst] not in htitle:
                htitle = htitle.replace(" (BS-corr.)","")+" (%s)"%systs[syst].replace('corr','corr.')
                hist.SetTitle(htitle)
              break # skip 'else'
          else:
            if not sample.isdata and any(s in var.name for s in ['bs_','track']) and\
               var0==var0 and not 'corr' in htitle: #not any(s in htitle for s in systs.values()):
              htitle += " (BS-corr.)"
              hist.SetTitle(htitle)
          hdict.setdefault(var0,[ ]).append(hist)
          
          # SAVE HIST for later
          if not loadhists:
            savehist(hist,hfile,var,var0,sample,verb=verbosity)
    
    # PLOT all hists
    for var, hists in hdict.items():
      print(">>> %r -> %s"%(var.name,', '.join(h.GetName() for h in hists)))
      fname = "%s/%s_%s_%s%s$TAG"%(outdir,var.filename,selection.filename,era,tag)
      text  = [selection.title]
      ymarg = var.ymargin or 1.3
      lpos  = var.position or 'y=0.85'
      #text  = "%s": %s"%(channel.replace("tau","tau_{h}"),selection.title)
      if var.flag:
        text.append(var.flag)
      for norm in norms:
        scales = [1.0]*len(hists) if norm else False
        if 'bs' in var.name and norm:
          scales[0] = (hists[-1].GetMaximum()/hists[-1].Integral())/(hists[0].GetMaximum()/hists[0].Integral()) # constant value
          scales[0] *= (3 if var.logy else 1.14)
        #denom   = 1 #1 if 'bs' in var.name else 2 # denominator
        num     = -1 # always use observed data as numerator
        rmin    = 0.55
        rmax    = 1.45
        tsize   = 0.054
        xmin    = var.xmin
        ymin    = var.ymin
        ymax    = var.ymax
        ntag    = '' if norm else "_lumi"
        opts    = ['E1 HIST']*(len(hists)-1)+['E1']
        mstyles = ['hist']*(len(hists)-1)+['data']
        errbars = True
        if logx:
          ntag += "_logx"
          xmin  = 0.55
          ymin  = 3e-5
          ymax  = 15
          ymarg = 1.55
        if 'ntrack' in var.name:
          rmax  = 2.0 if '2017' in era else 1.7
          tsize = 0.061
          opts  = ['HIST']*(len(hists)-1)+['E1']
          errbars = False
        if len(hists)>=4:
          lcols = [kRed,kMagenta+1,kBlue,kSpring-6][:len(hists)-1]+[kBlack]
        elif len(hists)>=3:
          #lcols = [kRed,kSpring-6][:len(hists)-1]+[kBlack] # not good for color blind
          lcols = [kRed,kBlue][:len(hists)-1]+[kBlack] # not good for color blind
        else:
          lcols = [kGreen-2][:len(hists)-1]+[kBlack]
        plot    = Plot(var,hists,norm=scales,xmin=xmin,ymin=ymin,ymax=ymax)
        plot.draw(options=opts,colors=lcols,mstyles=mstyles,lstyle=1,grid=False,errbars=errbars,
                  ratio=True,rmin=rmin,rmax=rmax,num=num,xtitleoffset=0.88,rtitle=rtitle,ymargin=ymarg,logx=logx)
        plot.drawlegend(pos=lpos,tsize=tsize,reverse=True,header=header)
        plot.drawtext(text,size=tsize) #.replace('-','#minus'))
        plot.saveas(fname,ext=exts,tag=ntag)
        plot.close(keep=True)
        
        # STORE in hist2D
        if hasattr(var,'iy') and not plotonly:
          iy = var.iy
          obshist = hists[-1]
          assert 'Observed' in obshist.GetTitle(), f"title={obshist.GetTitle()} not 'Observed'!"
          for syst, hist2d in hists2d.items():
            exphist = None
            for hist in hists:
              #if '_raw' in hist.GetName():
              #  continue
              if syst in hist.GetName():
                exphist = hist
                break
              elif syst=='Nom' and 'BS-corr' in hist.GetTitle():
                exphist = hist
                break
            #assert exphist, f"Did not find histogram for {syst}!"
            if not exphist:
              if verbosity>=2:
                print(">>> Could not find %r for 2D hist. IGNORING!"%(syst))
              continue
            LOG.verb("Taking ratio Obs. / Sim. = %r / %r for %r, iy=%s"%(
              rootrepr(obshist),rootrepr(exphist),var.filename,iy),verbosity,level=2)
            for ix in range(1,hist2d.GetXaxis().GetNbins()+1):
              # in case binning does not match (assume 2D hist has same or finer binning)
              ix_ = obshist.GetXaxis().FindBin(hist2d.GetXaxis().GetBinCenter(ix))
              obs = obshist.GetBinContent(ix_)
              sim = exphist.GetBinContent(ix_)
              ratio = obs/sim if sim>0 else 1.0
              LOG.verb("  ix=%2d, ix_=%2d, iy=%2d, obs / sim = %8.6f / %8.6f = %6.2f"%(
                ix,ix_,iy,obs,sim,ratio),verbosity,level=3)
              hist2d.SetBinContent(ix,iy,ratio)
              if ix>=hist2d.GetXaxis().GetNbins():
                hist2d.SetBinContent(ix+1,iy,ratio) # set x=ntrack overflow
              if iy==1:
                hist2d.SetBinContent(ix,0,ratio) # set y=ztrack underflow
              if iy==hist2d.GetYaxis().GetNbins():
                hist2d.SetBinContent(ix,iy+1,ratio) # set y=ztrack overflow
        
        ## REDRAW ZOOMED IN
        #if 'ntrack' in var.name:
        #  plot = Plot(var,hists,norm=scales)
        #  plot.draw(options=opts,colors=lcols,mstyles=mstyles,lstyle=1,rrange=0.13,
        #            ratio=True,num=num,rtitle=rtitle,logy=False,ymargin=1.29,xmin=0,xmax=3.8)
        #  plot.drawlegend(pos=lpos,tsize=0.053,reverse=True,header=header)
        #  plot.drawtext(text,size=0.055)
        #  plot.saveas(fname,ext=['png','pdf'],tag="_zoom"+ntag)
        #  plot.close(keep=True)
        
        # REDRAW without logy
        elif 'bs_' in var.name and '_logy' in fname:
          #scales[0] *= 0.85 #if 'sigma' in var.name else 0.058 # constant value
          if var.logy:
            scales[0] *= 1.14/3.
          if 'sigma' in var.name:
            xmin, xmax = 2.8, 4.7 #var.xmax
          else: # zoom in
            xmin, xmax = -2, 2
          plot = Plot(var,hists,norm=scales)
          plot.draw(options=opts,colors=lcols,mstyles=mstyles,lstyle=1,ratio=True,num=num,
                    rtitle=rtitle,logy=False,ymargin=1.23,xmin=xmin,xmax=xmax,ymin=0,ymax=None)
          plot.drawlegend(pos=lpos,tsize=0.053,reverse=True,header=header)
          plot.drawtext(text,size=0.055)
          plot.saveas(fname.replace('_logy',''),ext=['png','pdf'],tag=ntag)
          plot.close(keep=True)
        
        # CLEAN MEMORY
        deletehist(hists)
  
  # DRAW 2D histogram
  print(">>> ")
  if not extratext:
    extratext = "Supplementary"
  setera(era,showEra=True,extra=extratext) # set era for plot style and lumi-xsec normalization
  hfile.cd()
  for syst, hist2d in hists2d.items():
    nxbins = hist2d.GetXaxis().GetNbins()
    nybins = hist2d.GetYaxis().GetNbins()
    hname  = hist2d.GetName()
    fname  = "%s/%s_z-ntracks_pu_%s%s"%(outdir,hname,era,tag)
    if plotonly:
      hist2d = hfile.Get(hname) #loadhist(hfile,var,var0,sample,subdir=None,verb=0)
    if not hist2d or hist2d.GetEntries()==0:
      continue
    print(f">>> 2D: hname={hname}, syst={syst}")
    hist2d.SetOption('COLZ')
    hist2d.SetBinContent(nxbins+1,nybins+1,hist2d.GetBinContent(nxbins,nybins))
    if not plotonly:
      hist2d.Write(hname,hist2d.kOverwrite)
    plot = Plot2D(xvar,yvar,hist2d)
    plot.draw(zmin=0.4,zmax=1.5,logz=False,grid=True,zoffset=5.5)
    plot.saveas(fname,ext=exts)
  hfile.Close()
  

def measure_ntracks_hs(era,channel,tag="",**kwargs):
  """Compare number of track."""
  LOG.header("measure_ntracks_hs",pre=">>>")
  outdir    = kwargs.get('outdir',    "plots/g-2/ntracks_hs" )
  loadhists = kwargs.get('loadhists', False   ) #True and False
  domass    = kwargs.get('domass',    False   )
  norms     = kwargs.get('norm',      [True]  )
  exts      = kwargs.get('exts',      ['png'] ) # figure file extensions
  verbosity = kwargs.get('verb',      2       )
  chunk     = kwargs.get('chunk',     -1      )
  ensuredir(outdir)
  norms     = ensurelist(norms)
  hfname    = "%s/corrs_ntracks_hs_%s%s.root"%(outdir,era,tag)
  hfile     = ensureTFile(hfname,'READ' if loadhists else 'UPDATE') # back up histograms for reuse
  lsize     = 0.041 # legend text size
  tsize     = 0.044 # corner text size
  print(f">>> hfname = {hfname} (loadhists={loadhists!r})")
  
  # COLOR PALETTE
  # https://root.cern.ch/doc/master/classTColor.html#C06
  from ROOT import gStyle, TColor, kBird, kBlackBody
  #gStyle.SetPalette(kBlackBody)
  gStyle.SetPalette(kBird)
  
  # SELECTIONS
  mZ          = 91.1876
  baseline    = getbaseline(channel)
  zmmtitle    = "|m_{#lower[-0.25]{#mu#mu}} #minus m_{#lower[-0.05]{Z}}| < 15 GeV"
  zmmtitle2   = zmmtitle.replace(' 15 ',' 30 ')
  zmmcuts     = f"{baseline} && abs(m_ll-{mZ})<15"
  zmmcuts2    = zmmcuts.replace(')<15',')<30')
  sel_acobin1 = Sel(zmmtitle, zmmcuts+" && aco<0.015",  flag="A < 0.015", fname="ZMM-Alt0p015")
  sel_acobin2 = Sel(zmmtitle, zmmcuts+" && aco>=0.015", flag="A >= 0.015", fname="ZMM-Agt0p015")
  sel_acobin1.iy = 1
  sel_acobin2.iy = 2
  if domass: # do mass-dependence study (split into m_mumu bins)
    selections  = [
      Sel(zmmtitle2, zmmcuts2+" && aco<0.015",  flag="A < 0.015", fname="ZMM30-Alt0p015"),
    ]
  else: # split in acoplanarity bins
    selections  = [
      #Sel('baseline', baseline),
#       Sel(zmmtitle, zmmcuts, fname="ZMM"),
      sel_acobin1,
      sel_acobin2,
    ]
  
  # Z MASS BINS
  ###massbins = [-30,-15,0,15,30,60,100] # m_mumu - m_Z
  massbins = [60,75,91,105,120,150,190] # m_mumu
  if domass:
    for i, mmin in enumerate(massbins[:-1],1):
      mmax   = massbins[i]
      ###stitle = "%s < m_{#lower[-0.25]{#mu#mu}} #minus m_{#lower[-0.05]{Z}} <= %s GeV"%(
      ###         str(mmin).replace('-','#minus'),str(mmax).replace('-','#minus'))
      stitle = "%s < m_{#lower[-0.25]{#mu#mu}} <= %s GeV"%(mmin,mmax)
      ###scuts  = f"{baseline} && {mmin}<m_ll-{mZ} && m_ll-{mZ}<={mmax} && aco<0.015"
      scuts  = f"{baseline} && {mmin}<m_ll && m_ll<={mmax} && aco<0.015"
      fname  = f"ZMM{mmin}to{mmax}-Alt0p015"
      sel    = Sel(stitle, scuts, flag="A < 0.015", fname=fname)
      sel.iy = i # for 2D hist
      selections.append(sel)
      if verbosity>=1:
        print(f">>> i={i}, mmin={mmin}, mmax={mmax}, fname={fname!r}, scuts={scuts!r}")
  
  # GET SAMPLES
  #print(">>> GLOB.lumi=%s"%(GLOB.lumi))
  #sigwgt = "( ntrack_all==0 ? 3.1 : ntrack_all==1 ? 2.3 : 1 )" # old rescaling: measured by Cecile
  #sigwgt = "( ntrack_all==0 ? 2.703 : ntrack_all==1 ? 2.711 : 1 )" # new rescaling: measured by Izaak
  #sigwgt = "( ntrack_all==0 ? 2.359+0.0034*m_ll : ntrack_all==1 ? 2.377+0.00316*m_ll : 1 )" # new mass-dependent rescaling: measured by Izaak
  sigwgt = "( ntrack_all==0 ? 2.359+0.0034*m_ll : 2.377+0.00316*m_ll )" # new mass-dependent rescaling: measured by Izaak
  sigwgt += "*getPUTrackWeight(ntrack_pu,z_mumu,$ERA)"
  kwargs['dyweight'] = 'getAcoWeight(aco,pt_1,pt_2,$ERA)'
  kwargs['extraweight'] = 'getPUTrackWeight(ntrack_pu,z_mumu,$ERA)'
  if era in [2017,2018]:
    kwargs['filter'] = ['DY','VV']
  sampleset  = getsampleset(channel,era,loadcorrs=False,**kwargs)
  sample_obs = sampleset.get('Observed',unique=True,verb=verbosity-1)
  sample_dy  = sampleset.get('DY',unique=True,verb=verbosity-1)
  sample_vv  = sampleset.get('VV',unique=True,verb=verbosity-1)
  #sample_tt  = sampleset.get('DY',title="Z -> mumu",unique=True,verb=verbosity-1)
  sample_mm = makemcsample('Signal','GGToMuMu',"#gamma#gamma -> #mu#mu", # (elastic)
                            xsec_mm,channel,era,tag="",extraweight=sigwgt,lumi=GLOB.lumi,verb=6)
  sample_ww  = makemcsample('VV','GGToWW',"#gamma#gamma -> WW", # (elastic)
                            xsec_ww,channel,era,tag="",extraweight=sigwgt,lumi=GLOB.lumi,verb=6)
  #sample_sig = MergedSample("signal","Bkg. (#gamma#gamma -> #mu#mu, WW)",[sample_mm,sample_ww])
  #sample_obs.title = "Obs. #minus Bkg."
  sample_dy.title = "Z -> mumu"
  samples     = [
    sample_dy,
    sample_obs,
    #sample_sig, # GGToMuMu + GGToWW
    sample_mm, # GGToMuMu
    sample_ww, # GGToWW
    sample_vv,
  ]
  
  # ADD HS CUTS: split DY into ntracks_hs bins to be stacked
  tit_nhs = "N(reco HS)"
  ttitle  = "#it{N}_{#lower[-0.20]{tracks}}" #"Number of tracks"
  ztitle  = "HS track correction"
  tbins   = (31, 0, 31)
  tbins2  = list(range(0,20,1))+[20,22.5,25,27.5,30,31] # merged binning
  hs_bins  = [ # ntrack_hs binning (for splitting DY and measuring corrections)
    0, 1, 2, 3, 4,
    (5,10), (10,15), (15,20), (20,25), (25,30),
    (30,999)
  ]
  xmax     = hs_bins[-1][0]+5 # for overflow
  xbins    = [b if isinstance(b,int) else b[0] for b in hs_bins]+[xmax] #[40]
  tvar     = Var('ntrack_all', ttitle, *tbins, logy=True, ymargin=1.52, ymin=3e-6, addof=True, int=True) #, cbins={'1.0<m_ll':tbins2})
  xvar     = Var('ntrack_hs', "Number of HS tracks", xbins)
  varsets = [
    [tvar],
  ]
  vardict  = { }
  for varset in varsets:
    var0 = varset[0]
    for bin in hs_bins:
      if isinstance(bin,int): # single-valued, integer bins
        cut   = f"ntrack_hs=={bin}"
        title = str(bin)
        fname = f"$VAR_{bin}"
      elif bin[1]<100: # integer range
        cut   = f"{bin[0]}<=ntrack_hs && ntrack_hs<{bin[1]}"
        title = f"{bin[0]}#minus{bin[1]-1}"
        fname = f"$VAR_{bin[0]}-{bin[1]}"
      else: # incl. infinity
        cut   = f"{bin[0]}<=ntrack_hs"
        title = f">={bin[0]}"
        fname = f"$VAR_{bin[0]}"
      var = Var('ntrack_all',title,*tbins,fname=fname,addof=True,int=True,cut=cut,flag=title,data=False) #, cbins={'1.0<m_ll':tbins2})
      varset.append(var)
      vardict[var] = var0
    title = "Drell-Yan (BS uncorrected)"
    var   = Var('ntrack_all_raw',title,*tbins,fname='ntrack_all_raw',addof=True,int=True,flag=title,data=False) #, cbins={'1.0<m_ll':tbins2})
    varset.append(var)
    vardict[var] = var0
    print(">>> len(varset)=%s"%(len(varset)))
  print(">>> len(varsets)=%s"%(len(varsets)))
  
  # 2D corrections
  hists2d = { }
  if domass: # do mass-dependence study (split into m_mumu bins)
    #mvar = Var('dm_mumu', "m_{#lower[-0.2]{#mu#mu}} #minus m_{#lower[-0.05]{Z}}", massbins)
    mvar = Var('m_mumu', "m_{#lower[-0.16]{#mu#mu}}", massbins)
    hists2d['mass'] = xvar.gethist2D(mvar,'correction_map_zmass',ztitle=ztitle)
    hists2d['mass'].yvar = mvar # y axis = m_mumu
  else: # split in acoplanarity bins
    avar  = Var('aco', "Acoplanarity A", [0,0.015,1], ymin=0.01)
    hists2d['incl'] = xvar.gethist2D(avar,'correction_map',ztitle=ztitle)
    hists2d['incl'].yvar = avar # y axis = acoplanarity
  
  # STEP 1: CREATE HISTOGRAMS for all selections
  LOG.color("Step 1: Creating hists...",b=True)
  vars_obs = [v for s in varsets for v in s if v.data]
  vars_exp = [v for s in varsets for v in s if not v.data]
  allhists = { } # { sample: { selection: { variable: hist } } }
  for sample in samples:
    vars = vars_exp if sample==sample_dy else vars_obs
    LOG.color("Sample %s (%r) for %s variables, and %s selections"%(
      sample.name,sample.title,len(vars),len(selections)),c='grey',b=True)
    if loadhists: # skip recreating histograms (fast!)
      allhists[sample] = loadallhists(hfile,vars,vardict,sample,selections,verb=verbosity)
    else: # create histograms from scratch (slow...)
      allhists[sample] = sample.gethist(vars,selections,preselect=baseline,verb=verbosity)
  
  # STEP 2: PLOT
  LOG.color("Step 2: Plotting...",b=True)
  for selection in selections:
    LOG.header("Selection %r"%(selection.selection.replace(baseline+" && ",'')),pre=">>>")
    histsets = { v: HistSet() for v in vars_obs }
    
    # STEP 2a: LOOP over SAMPLES to regroup histograms into obs, exp (=dy stack), sig (=bkgs to be overlaid)
    LOG.color("Step 2a: Regrouping histograms...",b=True)
    for sample in samples:
      vars  = vars_exp if sample==sample_dy else vars_obs
      hists = allhists[sample][selection]
      assert len(vars)==len(hists), "len(vars)=%s, len(hists)=%s"%(len(vars),len(hists))
      istack = 0
      nstack = sum([1 for v in vars if not v.data and not 'corr' in v.flag])
      for var, hist in hists.items():
        var0 = vardict.get(var,var)
        if sample.isdata: # for observed data
          assert var0==var
          histsets[var0].data = hist
        elif sample==sample_dy: # DY
          if 'corr' in var.flag: # DY for overlay (not in stack)
            hist.SetTitle(var.title)
            histsets[var0].sig.append(hist) # draw overlay as "signal"
          else: # for DY stack
            icol   = int(round(istack*(TColor.GetNumberOfColors()-1)/(nstack-1)))
            icol_  = istack*(TColor.GetNumberOfColors()-1)/(nstack-1)
            fcolor = TColor.GetColorPalette(icol)
            if verbosity>=1:
              print(">>> i=%s, icol_=%s, icol=%s, fcolor=%s, ncols=%s, var.title=%r"%(
                istack,icol_,icol,fcolor,TColor.GetNumberOfColors(),var.title))
            hist.SetTitle(var.title)
            hist.SetFillColor(fcolor)
            histsets[var0].exp.append(hist)
            istack += 1
        else: #if sample in [sample_mm,sample_ww,sample_vv]: # for gg -> mumu, WW signal + other backgrounds
          assert var0==var
          histsets[var0].sig.append(hist) # draw overlay as "signal"
        #else:
        #  raise IOError("Did not recognize sample %r"%(sample))
        
        # SAVE HIST for later
        if not loadhists:
          savehist(hist,hfile,var,var0,sample,selection,verb=verbosity)
    
    # HELP FUNCTIONS
    def printSigSubtraction(dhist,shist):
      """Help function."""
      print(">>> Subtraction: %r - %r"%(dhist.GetTitle(),shist.GetTitle()))
      #print(">>> Subtraction: %r - %r =>  %.1f - %.3f"%(dhist.GetTitle(),shist.GetTitle(),dhist.Integral(),shist.Integral()))
      yobstot, ysigtot = 0, 0
      ntracks = [0,1,2]
      for nt in ntracks: # first three ntracks bins
        nbin = dhist.GetXaxis().FindBin(nt)
        yobs = dhist.GetBinContent(nbin)
        ysig = shist.GetBinContent(nbin)
        yobstot += yobs
        ysigtot += ysig
        print(">>>      ntracks==%s: sig / obs = %7.3f / %.1f = %.2f%%"%(nt,ysig,yobs,100.*ysig/yobs))
      print(">>>   %s<=ntracks<=%s: sig / obs = %7.3f / %.1f = %.2f%%"%(ntracks[0],ntracks[-1],ysigtot,yobstot,100.*ysigtot/yobstot))
    
    # STEP 2b SUBTRACT TOTAL SIGNAL from OBSERVED DATA
    LOG.color("Step 2b: Subtract total signal from observed data...",b=True)
    for var in histsets:
      obshist = histsets[var].data
      assert obshist, "Observed hist not created before signal subtraction..."
      dyhist   = None # total DY uncorrected
      sighists = [ ]  # GGToMuMu + GGToWW
      bkghists = [ ]  # other background histograms (VV, ...)
      for hist in histsets[var].sig[:]:
        if 'corr' in hist.GetTitle().lower(): # DY uncorrected
          assert dyhist==None, f"DY histogram already set! dyhist={dyhist!r}"
          dyhist = hist
          continue
        if 'gamma' in hist.GetTitle().lower(): # GGToMuMu + GGToWW
          print(f">>> Adding background {hist!r} to sighists")
          sighists.append(hist)
        else: # other backgrounds (VV, ...)
          print(f">>> Adding background {hist!r} to bkghists")
          bkghists.append(hist)
        printSigSubtraction(obshist,hist) # before (single histogram to check relative contribution)
      sighist = sumhists(sighists,f"sigtot_{var.filename}_{selection.filename}","Bkg. (#gamma#gamma -> #mu#mu, WW)",verb=verbosity+2) # total signal histogram (GGToMuMu + GGToWW)
      bkghist = sumhists(bkghists,f"bkgtot_{var.filename}_{selection.filename}","Bkg. (#gamma#gamma -> #mu#mu, WW, VV)",verb=verbosity+2) # total background histogram (GGToMuMu, GGToWW, VV, ...)
      printSigSubtraction(obshist,sighist) # after (total background subtraction)
      printSigSubtraction(obshist,bkghist) # after (total background subtraction)
      obshist.Add(sighist,-1) # subtract total signal from observed data
      #obshist.SetTitle("Obs. #minus (#gamma#gamma -> #mu#mu, WW)")
      obshist.SetTitle("Obs. #minus Bkg.")
      histsets[var].sig = [dyhist,sighist]+bkghists # "signal" histograms to be overlaid over DY MC stack
      if not loadhists:
        savehist(obshist,hfile,var,var0,sample_obs.name+"_min_sigtot",selection,verb=verbosity)
        savehist(sighist,hfile,var,var0,"sigtot",selection,verb=verbosity)
        savehist(bkghist,hfile,var,var0,"bkgtot",selection,verb=verbosity)
    
    # STEP 2c: PLOT all hists
    LOG.color("Step 2c: Plotting histograms before corrections...",b=True)
    for var, histset in histsets.items():
      obshist, dyhists, sighists = histset.data, histset.exp, histset.sig
      if verbosity+1>=1:
        print(">>> var      = %r, %r"%(var.name,var.title))
        print(">>> obshist  = %s"%(rootrepr(obshist)))
        print(">>> dyhists  = %s"%(rootrepr(dyhists)))
        print(">>> sighists = %s"%(rootrepr(sighists)))
      
      # GET TOTAL MC HIST
      dyname   = dyhists[0].GetName().replace("_0_","_tot_")
      sumhist0 = dyhists[0].Clone(dyname+'_uncorr') # DY uncorrected
      sumhist  = dyhists[0].Clone(dyname+'_corr')   # DY corrected
      ###sumhist0.Reset()
      ###sumhist.Reset()
      sumhist0.SetTitle("Drell-Yan (HS uncorrected)")
      sumhist.SetTitle("Drell-Yan (HS corrected)")
      for hist in dyhists[1:]: # add others DY components
        sumhist0.Add(hist) # total uncorrected (for plotting)
      sigscales = [1.0]*len(sighists) # for normalizing histograms
      for i, sighist in enumerate(sighists):
        if not 'gamma' in sighist.GetTitle(): continue # skip non-signals (i.e. DY)
        if len(sighists)>=2: # scale signal to DY
          sigscales[i] = sighist.Integral()/sumhist0.Integral()
        print(f">>> sighist.GetBinContent(0)={sighist.GetBinContent(0)}, sighist.GetBinContent(1)={sighist.GetBinContent(1)}")
        sighist.SetBinContent(0,sighist.GetBinContent(1)) # avoid vertical line on y axis !
      if verbosity+1>=1:
        print(f">>> scale signals: sigscales={sigscales} for normalization")
      
      # PLOT
      fname = "%s/$VAR_%s_%s%s$TAG"%(outdir,selection.filename,era,tag)
      plot  = plot_ntracks_hs(fname,var,selection,obshist,dyhists,sighists,sigscales,
                              exts=exts,tag=tag,hs_bins=hs_bins,verb=verbosity)
      
      # STEP 3: MAKE MEASUREMENT
      #any(zmmcuts+" && "+s in selection.selection for s in ['aco<0.015','aco>=0.015']) or\
      if hasattr(selection,'iy'):
        iy = selection.iy
        ###ismass = f"<m_ll-{mZ} && m_ll-{mZ}<" in selection.selection
        ismass = f"<m_ll && m_ll<" in selection.selection
        hist2d = hists2d['mass' if ismass else 'incl']
        LOG.color(f"Step 3: Measure HS track corrections (iy={iy}, ismass={ismass!r}, hist={hist2d!r})...",b=True)
        for bin, dyhist in zip(hs_bins,dyhists): # scale bins from left to right to match data
          if isinstance(bin,int):
            ix   = hist2d.GetXaxis().FindBin(bin+0.5)
            ilow = dyhist.GetXaxis().FindBin(bin+0.5)
            iup  = ilow
          elif bin[1]<100: # (xlow,xup)
            ix   = hist2d.GetXaxis().FindBin(bin[0]+0.5) # hist2d bin index
            ilow = dyhist.GetXaxis().FindBin(bin[0]+0.5) # dyhist lower bin index
            iup  = dyhist.GetXaxis().FindBin(bin[1]-0.5) # dyhist upper bin index
          else: # (xlow,inf)
            ix   = hist2d.GetXaxis().FindBin(bin[0]+0.5)
            ilow = dyhist.GetXaxis().FindBin(bin[0]+0.5)
            iup  = dyhist.GetXaxis().GetNbins()
          ysum, esum = integrate(sumhist,ilow,iup) # sum of all corrected dyhists in last iterations
          yexp, eexp = integrate(dyhist,ilow,iup) # current dyhist to be fitted to observed data
          yobs, eobs = integrate(obshist,ilow,iup) # observed data (minus backgrounds)
          scale  = (yobs-ysum)/yexp # correction weight to fit dyhist (this mtracks_hs bin in DY) to observed data
          totunc = 0
          if yobs!=ysum:
            totunc += (eobs**2+esum**2)/abs(yobs-ysum)**2
          else:
            print(f">>> Warning! yobs={yobs}=={ysum}=ysum")
          if yexp!=0:
            totunc += eexp**2/abs(yexp)**2
          else:
            print(f">>> Warning! yexp=={yexp}")
          totunc = scale * sqrt( totunc ) # total stat.+syst. uncertainty
          print(f">>> bin={bin}, dyhist={dyhist.GetTitle()!r}, (yobs-ysum)/yexp = ({yobs:.4f}-{ysum:.4f})/{yexp:.4f} = {scale:.4f}"
                f" +- {totunc:.4f} in ix={ix}, ilow={ilow}, iup={iup}")
          dyhist.Scale(scale) # scale for next iteration
          sumhist.Add(dyhist) # total corrected (for next iteration)
          hist2d.SetBinContent(ix,iy,scale)
          hist2d.SetBinError(ix,iy,totunc)
          if ix==hist2d.GetXaxis().GetNbins():
            hist2d.SetBinContent(ix+1,iy,scale) # overflow
          if iy==hist2d.GetYaxis().GetNbins():
            hist2d.SetBinContent(ix,iy+1,scale) # overflow
        
        # STEP 3a: PLOT AGAIN after correction
        LOG.color("Step 3a: Plot histograms after corrections...",b=True)
        sighists_ = [sumhist0,] # DY uncorrected
        for sighist in sighists:
          if sighist!=sumhist0:
            sighists_.append(sighist)
        plot2 = plot_ntracks_hs(fname,var,selection,obshist,dyhists,sighists_,sigscales,
                                exts=exts,tag="_corr"+tag,hs_bins=hs_bins,verb=verbosity)
        plot2.close(keep=True)
      
      plot.close(keep=False)
  
  # STEP 3b: WRITE 2D HIST
  for hist2d in hists2d.values():
    hname = hist2d.GetName()
    print(">>> ")
    if any(hist2d.GetBinContent(*b)==0 for b in [(1,1),(2,2)]):
      print(f">>> Ignoring 2D histogram {hname!r}")
      continue
    LOG.color(f"Step 3b: Write 2D correction hist {hname!r}...",b=True)
    fname  = "%s/%s_aco-ntrack_hs_%s%s"%(outdir,hname,era,tag)
    nxbins = hist2d.GetXaxis().GetNbins()
    nybins = hist2d.GetYaxis().GetNbins()
    yvar   = hist2d.yvar
    ymin   = yvar.xmin
    xmax   = xvar.xmax
    zmin   = 0.5
    zmax   = 1.3
    if 'aco' in yvar.name:
      ymin = 0.01
      logy = True #and False
    else:
      logy = False
    hist2d.SetOption('COLZTEXT55')
    hist2d.SetBinContent(nxbins+1,nybins+1,hist2d.GetBinContent(nxbins,nybins))
    plot2d = Plot2D(xvar,yvar,hist2d,logy=logy,xmax=xmax,ymin=ymin,zmin=zmin,zmax=zmax)
    plot2d.draw('COLZTEXT55',tcolor=kRed,logz=False,grid=False,zoffset=5.5,verb=verbosity)
    if 'aco' in yvar.name:
      #plot2d.frame.GetYaxis().SetBinLabel(0,'< 0.015')
      #plot2d.frame.GetYaxis().SetBinLabel(1,'#geq 0.015')
      plot2d.frame.GetYaxis().SetNdivisions(3,False)
    latex = TLatex()
    latex.SetTextSize(0.04)
    if 'aco' in yvar.name:
      latex.SetTextAlign(32)
      latex.DrawLatex(-0.6,0.015,"0.015")
    else: # mass dependence (assume A < 0.015 applied)
      latex.SetTextAlign(13)
      text = "A < 0.015" #yvar.flag
      x = xvar.xmin+0.04*(xvar.xmax-xvar.xmin)
      y = yvar.xmax-0.04*(yvar.xmax-yvar.xmin)
      latex.DrawLatex(x,y,text)
    if not loadhists:
      hfile.cd()
      hist2d.Write(hname,hist2d.kOverwrite)
    plot2d.saveas(fname,ext=['.png','.pdf'])
    plot2d.close(keep=True)
    
    # STEP 3c: PLOT 1D HIST of mass dependence
    if 'aco' not in yvar.name:
      LOG.color(f"Step 3c: Plot 1D correction graph {hname!r}...",b=True)
      graphs = [ ]
      fname  = "%s/%s_ntrack_hs_%s%s"%(outdir,hname,era,tag)
      nxbins = 3
      nybins = hist2d.GetXaxis().GetNbins()
      for ix in range(1,nxbins+1):
        #graph = TGraphAsymmErrors()
        graph = TGraphErrors()
        graph.SetTitle("#it{N}_{#lower[-0.18]{tracks}}^{#lower[0.29]{HS,reco}} = %s"%(ix-1))
        graphs.append(graph)
        for i, iy in enumerate(range(1,nybins+1)):
          yval = hist2d.GetYaxis().GetBinCenter(iy)
          yerr = hist2d.GetYaxis().GetBinWidth(iy)/2
          zval = hist2d.GetBinContent(ix,iy)
          zerr = hist2d.GetBinError(ix,iy)
          print(f">>> (i,iy)=({i},{iy}): yval={yval:4.1f} +- {yerr:4.1f}, zval={zval:5.3f} +- {zerr:5.3f}")
          graph.SetPoint(i,yval,zval)
          graph.SetPointError(i,yerr,zerr) # xerr,yerr
          #graph.SetPointError(i,xerr,xerr,yerr,yerr) # xl,xh,yl,yh
      lcols = [kRed,kBlue,kSpring-6,kMagenta+1,kBlack]
      plot  = Plot(yvar,graphs,dividebins=False,verbosity=verbosity) #,ymin=0,ymax=zmax
      plot.draw(option='PE0',ymin=0.1,ymax=1.25,ytitle=ztitle,colors=lcols,lstyle=1,mstyle=8,ratio=False)
      plot.drawlegend(pos='BL',theight=1.2,tsize=1.1*tsize) #,header="lol")
      plot.drawtext(text,size=1.1*tsize)
      plot.saveas(fname,ext=exts)
      #plot.close(keep=True) # prevent segfault ?
  
  # CLOSE
  hfile.Close()
  

def plot_ntracks_hs(fname,var,selection,obshist,dyhists,sighists,sigscales,
                    hs_bins=[ ],exts=['png','pdf'],tag="",norm=True,lcols=None,verb=0):
  lsize     = 0.044 # legend text size
  tsize     = 0.044 # corner text size
  lcols     = [kGreen+1,kOrange+1,kMagenta+1]
  tag       = tag+'' if norm else "_lumi"
  rhists    = ['stack',sighists[0],'data'] # sighists[0] = DY uncorrected
  #rtitle    = "Obs. / Sim." #"Sim. / Obs."
  #rtitle    = "#frac{Obs. #minus (#gamma#gamma #rightarrow #mu#mu, WW)}{Drell-Yan}    "
  rtitle    = "#frac{Obs. #minus Bkg.}{Drell-Yan}  "
  corr      = 'HS' if '_corr' in tag else 'BS'
  header    = "Drell-Yan in #it{N}_{#lower[-0.18]{tracks}}^{#lower[0.29]{HS,reco}} bins" # legend header
  header   += f" ({corr} corrected)"
  hists_dy  = dyhists # for first DY legend
  hists_oth = [obshist]+sighists # for second data/sig legend
  texts = [selection.title]
  if var.flag:
    texts.append(var.flag)
  if selection.flag:
    texts.append(selection.flag)
  texts.append("|z_{#lower[-0.25]{track}} #minus z_{#lower[-0.06]{mumu}}| < 0.05 cm")
  rmin, rmax = 0.60, 1.40
  if '_corr' in tag: # HS-corrected
    lcols[0] = kRed # replace DY color green (corr.) -> red (uncorr.)
  else: # HS-uncorrected
    lcols[0] = kGreen+1
  plot = Stack(var,obshist,dyhists,sighists,norm=norm)  
  
  # EXTRA LINES & BOXES in ratio panel
  if 'A < 0.015' in selection.flag: # draw SR box on ratio pad (behind histograms)
    plot.drawbox(0.01,rmin+0.008,2,rmax-0.004,pad=2,color=kMyFaintRed) # light red
  for bins in hs_bins: # draw vertical lines on ratio pad (behind histograms)
    x = bins if isinstance(bins,int) else bins[0]
    plot.drawline(x,0,x,2,pad=2,color=kMyLightRed,width=1) # light gray #color=19, kRed-9
  
  # DRAW HISTOGRAMS
  plot.draw(lcolors=lcols,reversestack=True,staterr=False,option='HIST ][',soption='HIST ][',
            sigscale=sigscales,ymin=7e-6,ymax=8e2,rmin=rmin,rmax=rmax,
            ratio=True,num=-1,rhists=rhists,rtitle=rtitle,rtitlesize=1.15*tsize,rtitleoffset=1.02)
            #ratio=True,num=-1,rhists=rhists,rtitle=rtitle,rtitlesize=0.033,rtitleoffset=1.16)
  
  # DRAW LEGEND & EXTRA TEXT
  plot.drawlegend(pos='x=0.41,y=0.67',tsize=lsize,band=False,hists=hists_oth) # obs & sig
  plot.drawlegend(pos='x=0.41,y=0.95',tsize=lsize,band=False,hists=hists_dy, # stacked DY
                  ncols=4,colsep=0.12,width=0.49,margin=1.1,header=header,bold=False,verb=verb)
  plot.drawtext(texts,size=tsize) # text on main panel
  if 'A < 0.015' in selection.flag: # draw SR box on ratio pad (behind histograms)
    plot.drawtext("SR",x=0.016,y=0.92,align=13,color=kOrange+6,size=tsize,pad=2) # text on ratio panel
  #plot.ratio.drawratios(verb=verb) # draw ratio again
  plot.canvas.cd(2)
  rhists = plot.ratio.ratios
  rhists[0].SetTitle(f"{corr} corrected")
  rhists[1].SetTitle(f"{corr} uncorrected")
  plot.drawlegend(hists=rhists,pos='x=0.49,y=0.35',tsize=lsize,theight=1.1,band=False,pad=2) # ratio legend
  #plot.canvas.GetPad(2).RedrawAxis()
  #plot.canvas.ls()
  plot.canvas.cd()
  
  #### DRAW RATIO Y TITLE MANUALLY
  ###latex = TLatex()
  ###latex.SetTextSize((0.9 if 'Bkg' in rtitle else 0.69)*tsize)
  ####latex.SetTextColor(kBlack)
  ###latex.SetTextAngle(90)
  ###latex.SetTextAlign(22)
  ###latex.DrawLatexNDC(0.051,0.215,rtitle.strip())
  
  # SAVE
  ###if 'ZMM-Alt0p015_UL2018' in fname:
  ###  exts = exts+['.C']
  plot.saveas(fname,ext=exts,tag=tag) #,'pdf'
  #plot.close(keep=True)
  return plot
  

def compare_samples(era,channel,tag="",**kwargs):
  """Compare samples."""
  LOG.header("compare_samples",pre=">>>")
  outdir    = kwargs.get('outdir',   "plots/g-2/compare" )
  norms     = kwargs.get('norm',     [True]  )
  exts      = kwargs.get('exts',     ['png'] ) # figure file extensions
  verbosity = kwargs.get('verb',     8       )
  chunk     = kwargs.get('chunk',    -1      )
  ensuredir(outdir)
  norms     = ensurelist(norms)
  rtitle    = "Obs. / Sim."
  
  # SELECTIONS
  baseline   = getbaseline(channel)
  selections = [
    #Sel('baseline', baseline),
    Sel('|m_{#lower[-0.3]{#mu#mu}} #minus m_{#lower[-0.05]{Z}}| < 15 GeV', baseline+" && abs(m_ll-91.1876)<15", fname="baseline-ZMM"),
    Sel('|m_{#lower[-0.3]{#mu#mu}} #minus m_{#lower[-0.05]{Z}}| < 15 GeV, N_{{#lower[-0.20]{tracks}} < 20', baseline+" && abs(m_ll-91.1876)<15 && ntrack<20", fname="baseline-ZMM-ntracklt20"),
  ]
  
  #### VARIABLES
  ###variables = [
  ###  ###Var('m_vis', 23,  0, 460, fname="m_mumu", cbins={'91.18':(20,70,110)}),
  ###  Var('m_vis',   23,  0, 460, fname="m_mumu_logy", title="m_{#lower[-0.2]{#mu#mu}}", logy=True, cbins={'91.18':(20,70,110)}),
  ###  ###Var('pt_1',   "Leading tau_h pt",    18, 0, 270),
  ###  ###Var('pt_2',   "Subleading tau_h pt", 18, 0, 270),
  ###  ###Var('jpt_1',  18, 0, 270),
  ###  ###Var('jpt_2',  18, 0, 270),
  ###  ###Var('met',    20, 0, 300),
  ###]
  ###
  #### NTRACK PU
  ###for i in [98,99,100,101]:
  ###  vname = "ntrack_pu_0p1[%s]"%i
  ###  text  = ("%.3g <= z < %.3g cm"%(-10+i*0.1,-10+(i+1)*0.1)).replace('-','#minus')
  ###  variables += [
  ###    Var(vname, 50, 0, 50, fname="$VAR_logy", title="Number of tracks", flag=text, logy=True), #logyrange=5.5
  ###    Var(vname, 10, 0, 10, fname="$VAR_zoom", title="Number of tracks", flag=text, logy=False), #logyrange=5.5
  ###  ]
  ###
  #### GET SAMPLES
  ###dytitle    = "Z -> mumu"
  ###sampleset  = getsampleset(channel,era,loadcorrs=True,**kwargs)
  ###sample_obs = sampleset.get('Observed',unique=True,verb=verbosity-1)
  ###sample_dy  = sampleset.get('DY',title="Z -> mumu",unique=True,verb=verbosity-1)
  ###sample_dy.title = dytitle+" fix" #(track |eta| <= 2.5)"
  ####sample_dy2 = makemcsample('DY','DYJetsToLL_M-50',dytitle+" (no track eta cut)",5343.0,channel,era,tag="_noeta",extraweight='zptweight',verb=2)
  ###sample_dy2 = makemcsample('DY','DYJetsToLL_M-50',dytitle+" bug",5343.0,channel,era,tag="_nodefault",extraweight='zptweight',verb=2)
  ###samples    = [
  ###  sample_dy2,
  ###  sample_dy,
  ###  sample_obs,
  ###]
  
  # VARIABLES
  variables = [
    #Var('ntrack',      "Number of tracks",    50, 0,  50, logy=False, logyrange=2.0),
    Var('ntrack_all',  "Number of tracks",    80, 0,  80, logy=False, logyrange=2.0, ymargin=1.28),
    Var('ntrack_pu',   "Number of PU tracks", 80, 0,  80, logy=True,  logyrange=5.1, ymargin=1.28, data=False),
    Var('ntrack_hs',   "Number of HS tracks", 80, 0,  80, logy=False, logyrange=2.0, ymargin=1.28, data=False),
    Var('track_pt[0]', "Leading track pt",    20, 0, 100, fname="track_pt1",      cut="ntrack>=1", logy=True, logyrange=4.1),
    Var('track_pt[0]', "Leading track pt",    25, 0,  50, fname="track_pt1_zoom", cut="ntrack>=1", logy=True, logyrange=2.5),
    Var('track_pt[1]', "Subleading track pt", 20, 0, 100, fname="track_pt2",      cut="ntrack>=2", logy=True, logyrange=5.0),
    Var('track_pt[1]', "Subleading track pt", 25, 0,  50, fname="track_pt2_zoom", cut="ntrack>=2", logy=True, logyrange=3.5),
    Var('MaxIf$(track_pt,track_ishs)',  "Leading HS track pt", 20, 0, 100, fname="track_hs_pt1",      cut="track_ishs",  logy=True, logyrange=3.4, data=False),
    Var('MaxIf$(track_pt,track_ishs)',  "Leading HS track pt", 25, 0,  50, fname="track_hs_pt1_zoom", cut="track_ishs",  logy=True, logyrange=3.4, data=False),
    Var('MaxIf$(track_pt,!track_ishs)', "Leading PU track pt", 20, 0, 100, fname="track_pu_pt1",      cut="!track_ishs", logy=True, logyrange=5.1, data=False),
    Var('MaxIf$(track_pt,!track_ishs)', "Leading PU track pt", 25, 0,  50, fname="track_pu_pt1_zoom", cut="!track_ishs", logy=True, logyrange=5.1, data=False),
  ]
  for var in variables:
    var.flag = "|z_{#lower[-0.25]{track}} - z_{#lower[-0.1]{#mu#mu}}| < 0.05 cm"
  
  # GET SAMPLES
  dytitle    = "Z -> mumu"
  putit      = "N_{#lower[-0.20]{PU}}"
  hstit      = "N_{#lower[-0.15]{HS}}"
  sampleset  = getsampleset(channel,era,loadcorrs=True,**kwargs)
  sample_obs = sampleset.get('Observed',unique=True,verb=verbosity-1)
  sample_dy1 = sampleset.get('DY',title=dytitle,unique=True,verb=verbosity-1)
  sample_dy2 = sample_dy1.clone()
  sample_dy2.extraweight = re.sub(r"getHSTrackWeight\([^)]+\)",'',sample_dy2.extraweight).strip('*') # remove HS corr
  sample_dy3 = sample_dy2.clone()
  sample_dy3.weight = re.sub(r"getPUTrackWeight\([^)]+\)",'',sample_dy3.weight).strip('*') # remove PU corr
  sample_dy4 = sample_dy3.clone()
  sample_dy4.extraweight = re.sub(r"getAcoWeight\([^)]+\)",'',sample_dy4.extraweight).strip('*') # remove PU corr
  print(f">>> sample_dy1 = {sample_dy1.weight!r} + {sample_dy1.extraweight!r}")
  print(f">>> sample_dy2 = {sample_dy2.weight!r} + {sample_dy2.extraweight!r}")
  print(f">>> sample_dy3 = {sample_dy3.weight!r} + {sample_dy3.extraweight!r}")
  print(f">>> sample_dy4 = {sample_dy4.weight!r} + {sample_dy4.extraweight!r}")
  sample_dy4.title = dytitle+", no corrs."
  sample_dy3.title = dytitle+", aco corrs."
  sample_dy2.title = dytitle+f", aco + {putit} corrs."
  sample_dy1.title = dytitle+f", aco + {putit} + {hstit} corrs."
  samples = [
    sample_dy1,
    sample_dy2,
    sample_dy3,
    sample_dy4,
    sample_obs,
  ]
  
  # PLOT
  header = None #samples[0].title
  nmc = sum(not s.isdata for s in samples)
  for selection in selections:
    print(">>> %s: %r"%(selection,selection.selection))
    hdict = { }
    
    # LOOP over SAMPLES
    for sample in samples:
      LOG.header("Sample %s (%r)"%(sample.name,sample.title),pre=">>>")
      
      vars = [v for v in variables if v.data or not sample.isdata]
      for var in vars:
        var.changecontext(selection,verb=verbosity-1)
              
      # DRAW
      hists = sample.gethist(vars,selection,verb=verbosity)
      
      # REODER HISTS
      assert len(vars)==len(hists), "len(vars)=%s, len(hists)=%s"%(len(vars),len(hists))
      for var, hist in zip(vars,hists):
        hdict.setdefault(var,[ ]).append(hist) # draw with hists of other samples
    
    # PLOT all hists
    for var, hists in hdict.items():
      print(">>> %r -> %s"%(var.name,', '.join(h.GetName() for h in hists)))
      fname = f"{outdir}/compareSamples_{var.filename}_{selection.filename}-{era}{tag}$TAG"
      text  = [selection.title]
      if var.flag:
        text.append(var.flag)
      for norm in norms:
        ntag    = '' if norm else "_lumi"
        opts    = ['E1 HIST']*nmc+['E1']
        mstyles = ['hist']*nmc+['data']
        #pos     = 'x=0.44;y=0.85'
        pos     = 'x=0.42;y=0.89'
        lcols   = [kRed,kBlue,kSpring-6,kMagenta+1][:len(hists)-1]+[kBlack]
        plot    = Plot(var,hists,norm=norm)
        plot.draw(options=opts,colors=lcols,mstyles=mstyles,lstyle=1,
                  ratio=True,num=-1,rtitle=rtitle)
        plot.drawlegend(pos=pos,tsize=0.053,reverse=True,header=header)
        plot.drawtext(text,size=0.055)
        plot.saveas(fname,ext=['png','pdf'],tag=ntag)
        plot.close(keep=False)
  

def compare_vars(era,channel,tag="",**kwargs):
  """Compare number of track."""
  LOG.header("compare_vars",pre=">>>")
  outdir    = kwargs.get('outdir',    "plots/g-2/compare" )
  loadhists = kwargs.get('loadhists', True    ) and False
  norms     = kwargs.get('norm',      [False] )
  exts      = kwargs.get('exts',      ['png'] ) # figure file extensions
  verbosity = kwargs.get('verb',      8       )
  chunk     = kwargs.get('chunk',     -1      )
  ensuredir(outdir)
  norms     = ensurelist(norms)
  wgt_dy    = ""
  
  # FOR STORING HISTS
  hfname  = "%s/compareVars_m_mumu_%s.root"%(outdir,era)
  hfile   = ensureTFile(hfname,'UPDATE') # back up histograms for reuse
  vardict = { }
  
  # SELECTIONS
  baseline   = getbaseline(channel)
  selections = [
    #Sel('baseline', baseline),
  ]
  
#  # VARIABLES for ntracks
#   selections = [
#     Sel('|m_{#lower[-0.3]{#mu#mu}} #minus m_{#lower[-0.05]{Z}}| < 15 GeV', baseline+" && abs(m_ll-91.1876)<15", fname="baseline-ZMM"),
#   ]
#   xt = lambda i: ("%d: %-4.3g <= z < %-4.3g cm"%(i,-10+i*0.1,-10+(i+1)*0.1)).replace('-','#minus')
#   varsets = [
#     ( Var('ntrack_pu_0p1_090-100', 50, 0, 50, title="Number of tracks", logy=True, logyrange=5.5),
#       [Var('ntrack_pu_0p1[%d]'%(i), 50, 0, 50, title=xt(i), addof=True, int=True) for i in range(90,100)]
#     ),
#     ( Var('ntrack_pu_0p1_100-110', 50, 0, 50, title="Number of tracks", logy=True, logyrange=5.5),
#       [Var('ntrack_pu_0p1[%d]'%(i), 50, 0, 50, title=xt(i), addof=True, int=True) for i in range(100,110)]
#     ),
#   ]
  
#   # VARIABLES for track pt
#   selections = [
#     Sel('|m_{#lower[-0.3]{#mu#mu}} #minus m_{#lower[-0.05]{Z}}| < 15 GeV', baseline+" && abs(m_ll-91.1876)<15 && ntrack>=1", fname="baseline-ZMM"),
#   ]
#   varsets = [
#     ( Var('track_pt[0]', 60, 0, 120, title="Leading track pt", logy=True, logyrange=5.5),
#       [ Var('track_pt[0]', 60, 0, 120, title="No corr.", weight=""),
#         Var('track_pt[0]', 60, 0, 120, title="PU track corr.", weight="putrack"), ]
#     ),
#   ]
  
  # VARIABLES for m_mumu in differen ntrack bins
  norms  = [True]
  tit_nt = "N_{#lower[-0.21]{tracks}}"
  selections = [
    Sel(f"A < 0.015", f"{baseline} && aco<0.015", fname="acolt0p015"),
  ]
  varsets = [ ]
  mbins1 = list(range(50,80,10))+list(range(80,100,5))+list(range(100,120,10))+list(range(120,160,20))+[160,200]
  mbins2 = list(range(50,80,10))+list(range(80,100,5))+list(range(100,120,10))+list(range(120,160,20))+\
           list(range(160,200,40))+list(range(200,300,50))+list(range(300,400,100))+[400,600] #,500,600,800]
  mvars = [
    Var('m_ll', "m_mumu", mbins1, fname="m_mumu_lin", pos='x=0.37,y=0.9', logy=False, ymargin=1.2 ),
    Var('m_ll', "m_mumu", mbins2, fname="m_mumu_log", pos='x=0.37,y=0.9', logy=True, ymargin=1.24, logyrange=4.2 ),
  ]
  for mvar in mvars[:]:
    mvars = [ ]
    tbins = [
      (0,1), (2,3), (4,5), (6,7),
      (3,7), (5,10), (8,10), (0,10),
    ]
    vardict[mvar] = mvar
    for tmin, tmax in tbins: # loop over
      if tmin==0:
        ttit  = f"{tit_nt} <= {tmax}"
        tcut  = f"ntrack_all<={tmax}"
        fnam  = f"$VAR_ntrack{tmin}-{tmax}"
      else:
        ttit  = f"{tmin} <= {tit_nt} <= {tmax}"
        tcut  = f"{tmin}<=ntrack_all && ntrack_all<={tmax}"
        fnam  = f"$VAR_ntrack{tmin}-{tmax}"
      mvar_ = mvar.clone(title=ttit,fname=fnam,cut=tcut)
      mvars.append(mvar_) # create new variable with extra cut
      vardict[mvar_] = mvar # for renaming histogram to be written to ROOT fle
    varsets.append(( mvar, mvars )) # overwrite
  
  # GET SAMPLES
  dytitle    = "Drell-Yan MC" #Z -> mumu"
  sampleset  = getsampleset(channel,era,loadcorrs=True,**kwargs)
  sample_obs = sampleset.get('Observed',unique=True,verb=verbosity-1)
  sample_dy  = sampleset.get('DY',unique=True,verb=verbosity-1+3)
  sample_ww  = sampleset.get('WW',unique=True,verb=verbosity-1+3)
  sample_dy.title = "Drell-Yan MC"
  sample_ww.title = "WW MC"
  samples    = [
    sample_dy,
    sample_ww,
    #sample_obs,
  ] #+sample_obs.samples #[:2]
  ###for sample in samples:
  ###  sample.addalias('z_mumu',"pv_z+0.5*dz_1+0.5*dz_2",verb=verbosity)
  ###  sample.addalias('aco',"(1-abs(dphi_ll)/3.14159265)",verb=verbosity)
  
  # PLOT
  setera(era) # set era for plot style and lumi-xsec normalization
  for selection in selections:
    print(">>> %s: %r"%(selection,selection.selection))
    hdict = { } # dictionary of all histograms
    
    # LOOP over SAMPLES
    for sample in samples:
      vars = [v for v0, vs in varsets for v in vs if v.data or not sample.isdata]
      
      # DRAW / LOAD HIST
      if loadhists: # skip recreating histograms (fast!)
        hists = loadallhists(hfile,vars,vardict,sample,verb=verbosity)
      else: # create histograms from scratch (slow...)
        hists = sample.gethist(vars,selection,verb=verbosity+4)
      for var, hist in zip(vars,hists):
        hist.SetTitle(var.title)
      
      # SAVE HIST for later
      for var, hist in zip(vars,hists):
        hdict[var] = hist # save for plotting in next step
        if not loadhists: # store for later
          savehist(hist,hfile,var,vardict,sample,verb=verbosity)
      
      for var0, varset in varsets:
        LOG.header("Sample %s (%r) and %s"%(sample.name,sample.title,var0.filename),pre=">>>")
        
        # PLOT all hists
        hists = [hdict[v] for v in varset if v.data or not sample.isdata]
        fname = "%s/compareVars_%s_%s-%s_%s%s$TAG"%(outdir,var0.filename,selection.filename,era,sample.name,tag)
        text  = [selection.title,sample.title]
        ncols = 2 if len(hists)>=5 else 1
        pos   = var0.position or 'y=0.85'
        for norm in norms:
          plot = Plot(var0,hists,norm=norm)
          plot.draw(lstyle=1,ratio=True,staterr=True,msize=0.5,rmin=0.4,rmax=1.5,enderrorsize=3,verb=verbosity+1)
          plot.drawlegend(pos=pos,ncols=ncols,tsize=0.053,colsep=0.01,reverse=False)
          plot.drawtext(text,size=0.055)
          plot.saveas(fname,ext=['png','pdf'])
          plot.close(keep=False)
  
  #### CLOSE
  ###from ROOT import closeAcoWeights
  ###closeAcoWeights()
  

def compare_dz(era='UL2018',tag="",**kwargs):
  """Compare dz cut."""
  LOG.header("compare_dz",pre=">>>")
  outdir    = kwargs.get('outdir',    "plots/g-2/compare" )
  loadhists = kwargs.get('loadhists', True    ) and False
  exts      = kwargs.get('exts',      ['png'] ) # figure file extensions
  verbosity = kwargs.get('verb',      8       )
  chunk     = kwargs.get('chunk',     -1      )
  norms     = [True]
  stitle    = "Drell-Yan MC"
  ensuredir(outdir)
  setera(era) # set era for plot style and lumi-xsec 
  
  # GET TREES
  tauh  = "#tau_{#lower[-0.2]{h}}"
  trees = [ ]
  fnames = [
    ('#mu#mu',       'tree',   "data/gmin2/pico_mumu_UL2018_DYJetsToLL_M-50.root"),
    (f'#mu{tauh}',   'dz_tree',"data/gmin2/Izaak_mutaudz.root"),
    (f'{tauh}{tauh}','dz_tree',"data/gmin2/Izaak_tautaudz.root"),
  ]
  for chan, tname, fname in fnames:
    file  = ensureTFile(fname,'READ')
    tree  = file.Get(tname)
    tree.file = file
    tree.chan = chan
    tree.SetAlias('z_mumu',"pv_z+0.5*dz_1+0.5*dz_2")
    tree.SetTitle(chan)
    trees.append(tree)
  
  # SELECTIONS
  selsets = [
    ( Sel("no dz cut", "", fname="nodzcut"),
      Sel("no dz cut", "" ),
      Sel("no dz cut", "" ),
    ),
    ( Sel("dz cut", f"abs(dz_1-dz_2)<0.2", fname="dzcut"),
      Sel("dz cut", f"abs(mudz_-taudz_)<0.2" ),
      Sel("dz cut", f"abs(tau1dz_-tau2dz_)<0.2" ),
    ),
    ( Sel("dz cut", f"abs(dz_1-dz_2)<0.2", fname="dzcut2"),
      Sel("dz cut", f"abs(mudz_-taudz_)<0.1" ),
      Sel("dz cut", f"abs(tau1dz_-tau2dz_)<0.1" ),
    )
  ]
  
  # VARIABLES for m_mumu in differen ntrack bins
  titdz   = "|z_{#lower[-0.26]{PV}}^{#lower[0.26]{gen}} #minus (z_{#lower[-0.22]{1}}+z_{#lower[0.0]{2}})/2| [cm]"
  dzbins  = frange(0,0.03,0.005)+[0.03,0.04,0.06,0.10,0.15,0.20]
  dzbins2 = frange(0,0.03,0.005)+[0.03,0.04,0.06,0.10]
  varsets = [
    ( Var('abs(pv_z_gen-z_mumu)', titdz, dzbins, fname='dz_pv', pos='TR', logyrange=5.5, ymargin=1.15 ),
      Var('abs(GenVtx_z_-recoDitau_z_)', dzbins ),
      Var('abs(GenVtx_z_-recoDitau_z_)', dzbins ),
    ),
    ( Var('abs(pv_z_gen-z_mumu)', titdz, dzbins2, fname='dz_pv_zoom', pos='TR', logyrange=3.5, ymargin=1.15 ),
      Var('abs(GenVtx_z_-recoDitau_z_)', dzbins2 ),
      Var('abs(GenVtx_z_-recoDitau_z_)', dzbins2 ),
    )
  ]
  
  # PLOT
  for selset in selsets:
    #LOG.header("Sample %s (%r) and %s"%(sample.name,sample.title,var0.filename),pre=">>>")
    sel0 = selset[0]
    
    for varset in varsets:
      var0 = varset[0]
      print(">>> %s: %r, %r"%(sel0.filename,sel0.selection,var0.filename))
      
      # LOOP over TREES
      hists = [ ]
      for i, (tree, var, sel) in enumerate(zip(trees,varset,selset)):
        hname = f"{var0.filename}_{i}"
        hist  = var.gethist(hname,tree.chan)
        dcmd  = f"{var.name} >> {hname}"
        scmd  = sel.selection
        out   = tree.Draw(dcmd,scmd,'gOff')
        hists.append(hist)
      
      # PLOT all hists
      text  = [stitle]
      ncols = 2 if len(hists)>=5 else 1
      pos   = var0.position or 'y=0.85'
      for logy in [True,False]:
        fname = f"{outdir}/compare_{var0.filename}_{sel0.filename}-{era}_DY{'_logy' if logy else ''}{tag}$TAG"
        plot = Plot(var0,hists,norm=True,clone=True,logy=logy)
        plot.draw(ratio=1,staterr=True,rmin=0,rmax=4,
                  lstyle=1,msize=0.5,enderrorsize=3,verb=verbosity+1)
        plot.drawlegend(pos=pos,ncols=ncols,tsize=0.053,colsep=0.01,reverse=False)
        plot.drawtext(text,size=0.055)
        plot.saveas(fname,ext=['png','pdf'])
        plot.close(keep=False)
  
  # CLOSE FILES
  for tree in trees:
    tree.file.Close()
  

def compare_aco(era='UL2018',tag="",**kwargs):
  """Compare aco at gen-level."""
  LOG.header("compare_aco",pre=">>>")
  outdir    = kwargs.get('outdir',    "plots/g-2/compare" )
  loadhists = kwargs.get('loadhists', True    ) and False
  exts      = kwargs.get('exts',      ['png'] ) # figure file extensions
  verbosity = kwargs.get('verb',      8       )
  chunk     = kwargs.get('chunk',     -1      )
  norms     = [True]
  stitle    = "#gamma#gamma #rightarrow #mu#mu"
  ensuredir(outdir)
  setera(era) # set era for plot style and lumi-xsec 
  
  # GET TREES
  tname = 'tree'
  fname = "../PicoProducer/genAnalyzer_gmin2_mumu.root"
  file  = ensureTFile(fname,'READ')
  tree  = file.Get(tname)
  tree.file = file
  tree.SetAlias('nleptons', "nelecs+nmuons+ntaus")
  #tree.SetAlias('nfsr',     "nphotons_lep1+nphotons_lep2")
  tree.SetAlias('aco', "(1-abs(dphi_ll)/3.14159265)") # acoplanarity
  
  # SELECTIONS
  selsets = [
    ( Sel("No FSR", "nfsr==0", fname="fsr", veto='nfsr'),
      Sel("1 FSR photon",      "nfsr==1"),
      Sel("#geq2 FSR photons", "nfsr>=2"),
    ),
    Sel("#mu^{+}#mu^{#minus}", "pid_lep1*pid_lep2<0", fname="os", veto='aco'),
  ]
  
  # VARIABLES for m_mumu in differen ntrack bins
  acobins  = frange(0,0.06,0.01)+frange(0.06,0.20,0.02)+frange(0.20,0.40,0.04)+[0.40,0.50,0.60,1.00]
  acobins2 = frange(0,0.04,0.02)+frange(0.04,0.16,0.04)+[0.16,0.22,0.30,0.40,0.60,1.00]
  acobins3 = frange(0,0.06,0.01)+frange(0.06,0.20,0.02)+[0.20]
  acobins4 = frange(0,0.04,0.005)+[0.04,0.05,0.07,0.10]
  varsets = [
    Var('aco', "Acoplanarity A", 80, 0, 1, fname='aco', pos='TR', logyrange=3.4, ymargin=1.15 ),
    Var('aco', "Acoplanarity A", acobins,  fname='aco_rebin', pos='TR', logyrange=4.5, ymargin=1.08 ),
    Var('aco', "Acoplanarity A", acobins2, fname='aco_coarse', pos='TR', logyrange=4.5, ymargin=1.08 ),
    Var('aco', "Acoplanarity A", acobins3, fname='aco_zoom', pos='TR', logyrange=3.7, ymargin=1.15 ),
    Var('aco', "Acoplanarity A", acobins4, fname='aco_zoom2', pos='TR', logyrange=3.7, ymargin=1.15 ),
#     ( Var('nfsr', "Number of FSR photons from muon", 8, 0, 8, fname='nfsr', pos='TR', logyrange=4.5, ymargin=1.15 ),
#       Var('nphotons_lep1', "Leading muon",    8, 0, 8 ),
#       Var('nphotons_lep2', "Subleading muon", 8, 0, 8 ),
#     ),
  ]
  
  # PLOT
  for varset in varsets:
    varset = [varset] if isinstance(varset,Var) else varset
    var0   = varset[0]
    LOG.header(f"Variable {var0.filename!r} ({var0.title!r})",pre=">>>")
    for selset in selsets:
      selset = [selset] if isinstance(selset,Sel) else selset
      sel0   = selset[0]
      if not sel0.plotfor(var0): continue
      print(">>> %s: %r, %r"%(sel0.filename,sel0.selection,var0.filename))
      
      # LOOP over TREES
      hists = [ ]
      for i, var in enumerate(varset):
        for j, sel in enumerate(selset):
          title = var.title if i>=1 else sel.title
          hist  = var0.gethist(f"{var.filename}_{sel.filename}",title=title)
          dcmd  = f"{var.name} >> {hist.GetName()}"
          scmd  = f"({sel.selection})*genweight"
          #print(f">>>   dcmd={dcmd!r}, scmd={scmd!r}")
          nout  = tree.Draw(dcmd,scmd,'gOff')
          hists.append(hist)
          if nout>0 and 'aco' in var0.name:
            ibin = hist.GetXaxis().FindBin(0.01499)
            nevts = hist.Integral(1,ibin)
            nall  = hist.Integral(0,hist.GetXaxis().GetNbins()+1)
            print(f">>> Integral aco in [{hist.GetXaxis().GetBinLowEdge(1)},{hist.GetXaxis().GetBinUpEdge(ibin):.3g}]"
                  f"= {nevts:.2f} / {nall:.2f} = {100*nevts/nall:.1f}%")
      
      # PLOT all hists
      text  = [stitle]
      ncols = 2 if len(hists)>=5 else 1
      pos   = var0.position or 'y=0.85'
      rmax  = 6 if 'aco' in var0.name else 2
      ratio = 1 if 'nfsr' in var0.name else 2
      for logy in [True,False]:
        fname = f"{outdir}/compare_{var0.filename}_{sel0.filename}-{era}_GGToMuMu{'_logy' if logy else ''}{tag}$TAG"
        plot = Plot(var0,hists,norm=True,clone=True,logy=logy)
        plot.draw(ratio=ratio,staterr=True,rmin=0,rmax=rmax,
                  lstyle=1,msize=0.5,enderrorsize=3,verb=verbosity)
        plot.drawlegend(pos=pos,ncols=ncols,tsize=0.053,colsep=0.01,reverse=False)
        plot.drawtext(text,size=0.055)
        plot.saveas(fname,ext=['png','pdf'])
        plot.close(keep=False)
      deletehist(hists)
  
  # CLOSE FILE
  file.Close()
  

def main(args):
  fname     = None #"$PICODIR/$SAMPLE_$CHANNEL.root" # fname pattern
  eras      = args.eras #['UL2018']pattern
  methods   = args.methods
  plotonly  = args.plotonly
  loadhists = args.loadhists or plotonly
  extratext = args.extratext # "Preliminary" or ""
  channels  = ['mumu',] #'tautau'
  outdir    = "plots/g-2"
  tag       = args.tag
  chunk     = args.chunk
  nthreads  = args.nthreads
  verbosity = args.verbosity
  RDF.SetNumberOfThreads(nthreads,verb=verbosity+1) # set nthreads globally
  exts = ['png','pdf','root'] if plotonly else ['png','pdf']
  
  #### COMPARE SELECTIONS
  ###for era in eras:
  ###  for channel in channels:
  ###    #sampleset = getsampleset(channel,era,fname=fname)
  ###    sampleset = getsampleset_simple(channel,era,fname=fname)
  ###    compare_cuts(sampleset,channel,tag="",outdir="plots")
  ###    sampleset.close()
  
  #### COMPARE ERAS
  ###eras = ['UL2016_preVFP','UL2016_postVFP'] # eras to compare
  ###for channel in channels:
  ###  samplesets = { }
  ###  for era in eras:
  ###    #samplesets[era] = getsampleset(channel,era,fname=fname,weight="")
  ###    samplesets[era] = getsampleset_simple(channel,era,fname=fname,weight="")
  ###  compare_eras(eras,samplesets,channel=channel,tag=tag,outdir="plots")
  ###  for era in eras:
  ###    samplesets[era].close()
  
  # COMPARE NTRACKS
  for era in eras:
    setera(era) # set era for plot style and lumi-xsec normalization
    era_dict[era] = era_dict.get(era,era).strip('UL')
    showEra = True #'2017' not in era
    #showEra = (era not in ['UL2017','UL2018'])
    for channel in channels:
      if 'pu' in methods:
        measure_ntracks_pu(era,channel,tag=tag,outdir=outdir+"/ntracks_pu",extra=extratext,loadhists=loadhists,showEra=showEra,exts=exts,plotonly=plotonly,chunk=chunk,verb=verbosity)
      if 'hs' in methods:
        measure_ntracks_hs(era,channel,tag=tag,outdir=outdir+"/ntracks_hs",extra=extratext,loadhists=loadhists,showEra=showEra,exts=exts,domass=args.domass,verb=verbosity)
      if 'sam' in methods:
        compare_samples(era,channel,tag=tag,outdir=outdir+"/compare",verb=verbosity)
      if 'var' in methods:
        compare_vars(era,channel,tag=tag,outdir=outdir+"/compare",loadhists=loadhists,verb=verbosity)
      if 'dz' in methods:
        compare_dz(era,outdir=outdir+"/compare",verb=verbosity)
      if 'aco' in methods:
        compare_aco(era,outdir=outdir+"/compare",verb=verbosity)
  

if __name__ == "__main__":
  from argparse import ArgumentParser
  description = """Simple plotting script to compare distributions in pico analysis tuples"""
  parser = ArgumentParser(description=description,epilog="Good luck!")
  methods = ['pu','hs','sam','var','dz','aco']
  parser.add_argument('-m', '--method',    dest='methods', choices=methods, nargs='+', default=['pu'],
                                           help="routine" )
  parser.add_argument('-M', '--domass',    dest='domass', action='store_true',
                                           help="do mass dependence study" )
  parser.add_argument('-g', '--chunk',     type=int, default=-1,
                                           help="only run chunk of variables" )
  parser.add_argument('-y', '--era',       dest='eras', nargs='*', default=['UL2018'],
                                           help="set era" )
  parser.add_argument('-e', '--extratext', default="Preliminary",
                                           help="extra CMS text, default=%(default)r" )
  parser.add_argument('-t', '--tag',       default="",
                                           help="extra tag for output" )
  parser.add_argument('-p', '--plotonly',  action='store_true',
                                           help="plot only (load hists, do not write)" )
  parser.add_argument('-L', '--loadhists', action='store_true',
                                           help="load histograms from ROOT file" )
  parser.add_argument('-n', '--nthreads',  type=int, nargs='?', const=10, default=10, action='store',
                                           help="run RDF in parallel instead of in serial, default=%(default)r" )
  parser.add_argument('-v', '--verbose',   dest='verbosity', type=int, nargs='?', const=1, default=0, action='store',
                                           help="set verbosity" )
  args = parser.parse_args()
  LOG.verbosity  = args.verbosity
  PLOG.verbosity = args.verbosity-1
  SLOG.verbosity = args.verbosity
  main(args)
  print("\n>>> Done.")
  
