#! /usr/bin/env python
# Author: Izaak Neutelings (November 2023)
# Description: Compare distributions in nanoAOD tuples
# Instructions
#   ./plot_gen_LQ.py
import os
from TauFW.common.tools.log import bold
from TauFW.common.tools.math import frange
import TauFW.Plotter.plot.Plot as _Plot
import TauFW.Plotter.plot.CMSStyle as CMSStyle
from TauFW.Plotter.plot.CMSStyle import lumi_dict
from TauFW.Plotter.plot.Plot import Plot, deletehist
from TauFW.Plotter.plot.Plot import LOG as PLOG
from TauFW.Plotter.sample.utils import LOG, STYLE, ensuredir, ensurelist, ensureTFile,\
                                       setera, MC, MergedSample, Sel, Var, repkey
from ROOT import kBlack, kRed, kBlue, kAzure, kGreen, kOrange, kMagenta, kYellow
from TauFW.common.tools.RDataFrame import RDF

colors = [ kRed+1, kBlue, kGreen+2, kOrange+1, kMagenta-4, kBlack ]
# colors = [ kBlack, kRed+1, kAzure+5, kGreen+2, kOrange+1, kMagenta-4, kAzure+10, kOrange+10,
#            kRed+2, kAzure+5, kOrange-5, kGreen+2, kMagenta+2, kYellow+2,
#            kRed-7, kAzure-4, kOrange+6, kGreen-2, kMagenta-3, kYellow-2 ] #kViolet

# VARIABLES
qlabels    = ['','#minus1','','#plus1','','','']
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
bins_dpt   = [-3,-2,-1,-0.7] + frange(-0.6,-0.05,0.05) + [-0.05,-0.02,
              0,0.02,0.05,0.1,0.2,0.3,0.5,0.7,1,2] #,4] # resolution
bins_dphi  = [-3.15,-2.8,-2.6,-2.4,-2.2,-2.0,-1.7,-1.3,-0.9,-0.3,0.3,0.9,1.3,1.7,2.0,2.2,2.4,2.6,2.8,3.15]
bins_dmet  = [-0.6,-0.4,-0.3,-0.2,-0.15,-0.1,-0.05,-0.02,-0.01,-0.005,0,0.005,0.01,0.02,0.05,0.1,0.15,0.2,0.3,0.4,0.6]
pt     = "p_{#lower[-0.25]{T}}"
#pt2    = "p_{#kern[-0.2]{#lower[-0.25]{T}}}"
jpt    = "p_{#lower[-0.32]{T}}^{#lower[0.24]{jet}}"
lpt    = "p_{#lower[-0.32]{T}}^{#lower[0.24]{l}}"
tpt    = "p_{#lower[-0.32]{T}}^{#lower[0.24]{#tau}}"
vpt    = "p_{#lower[-0.32]{T,vis}}^{#lower[0.24]{#tau}}"
met    = "p_{#lower[-0.32]{T,vis}}^{#lower[0.24]{miss}}"
st     = "S_{#lower[-0.2]{T}}"
stmet  = "S_{#lower[-0.2]{T}}^{MET}"
stv    = "S_{#lower[-0.2]{T,vis}}"
stvmet = "S_{#lower[-0.2]{T,vis}}^{MET}"
stsum  = "p_{#lower[-0.32]{T}}^{#lower[0.24]{l1}} + p_{#lower[-0.32]{T}}^{#lower[0.24]{l1}} + p_{#lower[-0.32]{T}}^{#lower[0.24]{jet}}"
sttsum = "p_{#lower[-0.32]{T}}^{#lower[0.24]{#tau1}} + p_{#lower[-0.32]{T}}^{#lower[0.24]{#tau2}} + p_{#lower[-0.32]{T}}^{#lower[0.24]{jet}}"
stvsum = "p_{#lower[-0.32]{T}}^{#lower[0.24]{#tau1,vis}} + p_{#lower[-0.32]{T}}^{#lower[0.24]{#tau2,vis}} + p_{#lower[-0.32]{T}}^{#lower[0.24]{jet}}"
ht     = "H_{#lower[-0.10]{T}} = #lower[-0.40]{#scale[0.68]{#sum}}#kern[0.009]{#lower[-0.09]{%s (%s > 20 GeV, |#eta| < 4.7) [GeV]}}"%(jpt,jpt)
dmtt   = "(m_{#lower[-0.15]{#tau#tau}}^{vis} #minus m_{#tau#tau})/m_{#lower[0.2]{#tau#tau}}"
njets  = "N_{#lower[-0.1]{jets}}^{#lower[0.1]{gen}}" #"Number of gen. jets" 
nbjets = "N_{#lower[-0.1]{b jets}}^{#lower[0.1]{gen}}" #"Number of gen. jets" 
variables = [ # common variables
#   Var('ntau',         7,   0,    7, title="Number of #tau leptons", ),
#   ###Var('ntgen',       7,    0,    7, title="Number of top quarks", ),
  ###Var('nelecs',       9,   0,    9, title="Number of electrons" ),
  ###Var('nmuons',       9,   0,    9, title="Number of muons" ),
  Var('ntaus20',      7,   0,    7, title=f"Number of #tau leptons ({pt} > 20 GeV, |eta| < 2.5)" ),
  Var('ntaus50',      7,   0,    7, title=f"Number of #tau leptons ({pt} > 50 GeV, |eta| < 2.5)" ),
  #Var('pt_lep1',     15,   0,  600, title="Leading lepton "+pt, fname="$VAR_600" ),
  Var('pt_lep1',     20,   0, 1200, title="Leading lepton "+pt, fname="$VAR_1200" ),
  #Var('pt_lep2',     15,   0,  600, title="Subleading lepton "+pt, fname="$VAR_600" ),
  Var('pt_lep2',     20,   0, 1200, title=f"Subleading lepton {pt}", fname="$VAR_1200" ),
  Var('eta_lep1',    24,  -6,    6, title="Leading lepton eta", ymargin=1.50, ncol=2, pos='LL' ),
  Var('eta_lep2',    24,  -6,    6, title="Subleading lepton eta", ymargin=1.50, ncol=2, pos='LL' ),
  #Var('pt_tau1',     15,   0,  600, title=f"Leading tau {pt}", fname="$VAR_600",  only=['tau'] ),
  Var('pt_tau1',     20,   0, 1200, title=f"Leading tau {pt}", fname="$VAR_1200", only=['tau'] ),
  Var('pt_tau1',         bins_tpt1, title=f"Leading tau {pt}", fname="$VAR_log", only=['tau'], logy=True, ymin=1e-7 ),
  #Var('ptvis_tau1',  15,   0,  600, title=f"Leading tau {vpt}", fname="$VAR_600",  only=['tau'] ),
  Var('ptvis_tau1',  20,   0, 1200, title=f"Leading tau {vpt}", fname="$VAR_1200", only=['tau'] ),
  #Var('pt_tau2',     15,   0,  600, title=f"Subleading tau {pt}", fname="$VAR_600",  only=['tau'] ),
  Var('pt_tau2',     20,   0, 1200, title=f"Subleading tau {pt}", fname="$VAR_1200", only=['tau'] ),
  Var('pt_tau2',         bins_tpt1, title=f"Subleading tau {pt}", fname="$VAR_log", only=['tau'], logy=True, ymin=1e-7 ),
  #Var('ptvis_tau2',  15,   0,  600, title=f"Subleading tau {vpt}", fname="$VAR_600" ),
  Var('ptvis_tau2',  20,   0, 1200, title=f"Subleading tau {vpt}", fname="$VAR_1200" ),
  Var('eta_tau1',    24,  -6,    6, title="Leading #tau lepton eta", ymargin=1.50, ncol=2, pos='LL' ),
  ###Var('eta_tau1',         bins_eta, title="Leading #tau lepton eta", ymargin=1.50, ncol=2, pos='LL', fname="$VAR_rebin" ),
  Var('eta_tau2',    24,  -6,    6, title="Subleading #tau lepton eta", ymargin=1.50, ncol=2, pos='LL' ),
  ###Var('eta_tau2',         bins_eta, title="Subleading #tau lepton eta", ymargin=1.50, ncol=2, pos='LL', fname="$VAR_rebin" ),
  Var('eta_vistau1', 24,  -6,    6, title="Leading vis. #tau lepton eta", ymargin=1.50, ncol=2, pos='LL' ),
  Var('eta_vistau2', 24,  -6,    6, title="Sublead. vis. #tau lepton eta", ymargin=1.50, ncol=2, pos='LL' ),
  Var('m_ll',        20,   0, 1200, title="m_{#lower[-0.06]{ll}}", units='GeV', fname="m_ll_1200", only=['lep'] ),
  Var('m_ll',        30,   0, 3000, title="m_{#lower[-0.06]{ll}}", units='GeV', fname="m_ll_3000", only=['lep'] ),
  Var('m_tt',        20,   0, 1200, title="m_{#lower[-0.06]{#tau#tau}}", units='GeV', fname="m_tt_1200", only=['tau'] ),
  Var('m_tt',        30,   0, 3000, title="m_{#lower[-0.06]{#tau#tau}}", units='GeV', fname="m_tt_3000", only=['tau'] ),
  Var('mvis_tt',     20,   0, 1200, title="m^{#lower[0.15]{vis}}_{#lower[-0.06]{#tau#tau}}", units='GeV', fname="mvis_tt_1200", only=['tau'] ),
  Var('mvis_tt',     30,   0, 3000, title="m^{#lower[0.15]{vis}}_{#lower[-0.06]{#tau#tau}}", units='GeV', fname="mvis_tt_3000", only=['tau'] ),
  Var('(mvis_tt-m_tt)/m_tt', bins_dpt, title = f"{dmtt}", fname="dm_tt", cut="m_tt>0", only=['tau'] ),
  ###Var('(mvis_tt-m_tt)/m_tt', bins_dpt, title = f"{dmtt} (fully lep. decay, {tpt} > 20 GeV)", fname="dm_tt_fulllep", cut="dm_tt==1 && m_tt>0" ),
  ###Var('(mvis_tt-m_tt)/m_tt', bins_dpt, title = f"{dmtt} (semilep. decay, {tpt} > 20 GeV)",   fname="dm_tt_semilep", cut="dm_tt==2 && m_tt>0" ),
  ###Var('(mvis_tt-m_tt)/m_tt', bins_dpt, title = f"{dmtt} (fully had. decay, {tpt} > 20 GeV)", fname="dm_tt_fullhad", cut="dm_tt==3 && m_tt>0" ),
  Var('dR_ll',             bins_dR, title="#DeltaR_{#lower[-0.15]{ll}}", ymargin=1.50, ncol=2, pos='LL' ),
  Var('dR_tt',             bins_dR, title="#DeltaR_{#lower[-0.15]{#tau#tau}}", ymargin=1.50, ncol=2, pos='LL' ),
#   Var('deta_ll',          bins_eta, title="#Delta#eta_{#lower[-0.25]{#tau#tau}}", ymargin=1.50, ncol=2, pos='LL' ),
#   Var('dphi_ll', 15, -3.142, 3.142, title="#Delta#phi_{#lower[-0.25]{#tau#tau}}", ymargin=1.2, pos='Cy=0.85' ),
  Var('nleps',       11,   0,   11, title="Number of leptons" ),
  Var('nleps20',     11,   0,   11, title=f"Number of leptons ({pt} > 20 GeV, |eta| < 2.5)" ),
  Var('nleps50',     11,   0,   11, title=f"Number of leptons ({pt} > 50 GeV, |eta| < 2.5)" ),
  Var('nbots',        7,   0,    7, title="Number of b quarks" ),
  Var('nbots20',      7,   0,    7, title=f"Number of b quarks ({pt} > 20 GeV, |eta| < 2.5)" ),
  Var('njets',       11,   0,   11, title=f"{njets}", ymargin=1.50, ncol=2 ),
  Var('njets50',     11,   0,   11, title=f"{njets} ({pt} > 50 GeV, |eta| < 4.7)" ),
  Var('ncjets20',     9,   0,    9, title=f"{njets} ({pt} > 20 GeV, |eta| < 2.5)" ),
  Var('ncjets50',     9,   0,    9, title=f"{njets} ({pt} > 50 GeV, |eta| < 2.5)" ),
  Var('nfjets20',     9,   0,    9, title=f"{njets} ({pt} > 20 GeV, 2.5 < |eta| < 4.7)" ),
  Var('nfjets50',     9,   0,    9, title=f"{njets} ({pt} > 50 GeV, 2.5 < |eta| < 4.7)" ),
  Var('nbjets20',     9,   0,    9, title=f"{nbjets} ({pt} > 20 GeV, |eta| < 2.5)" ),
  Var('nbjets50',     9,   0,    9, title=f"{nbjets} ({pt} > 50 GeV, |eta| < 2.5)" ),
  #Var('pt_jet1',     20,   0,  400, title="Leading gen. jet "+pt, fname="$VAR_400"  ),
  Var('pt_jet1',     30,   0, 1200, title="Leading gen. jet "+pt, fname="$VAR_1200" ),
  Var('pt_jet1',     40,   0, 2000, title="Leading gen. jet "+pt, fname="$VAR_2000" ),
  ###Var('jpt1',           bins_jpt2, title="Leading gen. jet "+pt, fname="$VAR_zoom2" ),
  ###Var('jpt1',           bins_jpt1, title="Leading gen. jet "+pt, logy=True, ymin=1e-5, fname="$VAR_log" ),
  Var('eta_jet1',    24,  -6,    6, title="Leading gen. jet eta", ymargin=1.50, ncol=2, pos='LL' ),
  ###Var('eta_jet1',         bins_eta, title="Leading gen. jet eta", ymargin=1.50, ncol=2, pos='LL', fname="$VAR_rebin" ),
  #Var('pt_jet2',     20,   0,  400, title="Subleading gen. jet "+pt, fname="$VAR_400"  ),
  Var('pt_jet2',     30,   0, 1200, title="Sublead. gen. jet "+pt, fname="$VAR_1200" ),
  Var('pt_jet2',     40,   0, 2000, title="Sublead. gen. jet "+pt, fname="$VAR_2000" ),
  Var('eta_jet2',    24,  -6,    6, title="Sublead. gen. jet eta", ymargin=1.50, ncol=2, pos='LL' ),
  ###Var('eta_jet2',         bins_eta, title="Sublead. gen. jet eta", ymargin=1.50, ncol=2, pos='LL', fname="$VAR_rebin" ),
  Var('met',         26,   0,  400, title="MET", fname="$VAR_400"  ),
  Var('met',         25,   0, 1000, title="MET", fname="$VAR_1000" ),
  Var('ht',          20,   0,  400, title=ht, units=False, fname="$VAR_400" ),
  Var('ht',          50,   0, 4000, title=ht, units=False, fname="$VAR_4000" ),
  Var('pt_lep1+pt_lep2+pt_jet1',           bins_st, title=f"{st} = {stsum}",            fname="st",           logy=True, ymin=1e-8, addOverflowToLastBin=True, only=['lep'] ),
  Var('pt_lep1+pt_lep2+pt_jet1+met',       bins_st, title=f"{stmet} = {stsum} + {met}", fname="stmet",        logy=True, ymin=1e-8, addOverflowToLastBin=True, only=['lep'] ),
  Var('pt_tau1+pt_tau2+pt_jet1',           bins_st, title=f"{st} = {sttsum}",           fname="st-tau",       logy=True, ymin=1e-8, addOverflowToLastBin=True, only=['tau'] ),
  Var('pt_tau1+pt_tau2+pt_jet1+met',       bins_st, title=f"{stmet} = {sttsum} + {met}",fname="stmet-tau",    logy=True, ymin=1e-8, addOverflowToLastBin=True, only=['tau'] ),
  Var('pt_vistau1+pt_vistau2+pt_jet1',     bins_st, title=f"{stv} = {stvsum} + ",       fname="st-tauvis",    logy=True, ymin=1e-8, addOverflowToLastBin=True, only=['tau'] ),
  Var('pt_vistau1+pt_vistau2+pt_jet1+met', bins_st, title=f"{stvmet} = {stvsum}",       fname="stmet-tauvis", logy=True, ymin=1e-8, addOverflowToLastBin=True, only=['tau'] ),
]


def makemcsample(group,sname,title,xsec,era,channel='lq',weight='genweight',tag="",verb=0,**kwargs):
  ###if era=='Run2':
  ###  sample = MergedSample(sname,title,**kwargs)
  ###  for era_ in ['2016','2017','2018']:
  ###    sample_ = makemcsample(group,sname,title,xsec,channel,era_,tag=tag,verb=verb,**kwargs)
  ###    sample += sample_
  ###  print(sample.row())
  ###  return sample
  kwargs['lumi'] = lumi_dict[era]
  picodir = kwargs.get('picodir',"/eos/user/i/ineuteli/analysis/g-2")
  name    = sname+tag
  fname   = "$PICODIR/$ERA/$GROUP/$SAMPLE_$CHANNEL$TAG.root"
  fname_  = repkey(fname,PICODIR=picodir,ERA=era,GROUP=group,SAMPLE=sname,CHANNEL=channel,TAG=tag)
  if not os.path.isfile(fname_):
    print(">>> Did not find %r"%(fname_))
  if verb>=1:
    print(">>> makemcsample: %s, %s, %s"%(name,sname,fname_))
  sample = MC(name,title,fname_,xsec,**kwargs)
  sample.addaliases(verb=verb-2,**{
    'dm_tt':    "(dm_tau1==3 && dm_tau2==3) ? 3 : (dm_tau1==3 || dm_tau2==3) ? 2 : 1", # 1: full lep, 2: semilep, 3: full had
    #'ll':       "1<=dm_vistau1 && dm_vistau1<=2 && 1<=dm_vistau2 && dm_vistau2<=2", # fully leptonic tau decay
    #'etau':     "(dm_vistau1==1 && dm_vistau2>=3) || (dm_vistau2==1 && dm_vistau1>=3)", # electronic tau decay
    #'mutau':    "(dm_vistau1==2 && dm_vistau2>=3) || (dm_vistau2==2 && dm_vistau1>=3)", # muonic tau decay
    #'ltau':     "((dm_vistau1==1||dm_vistau1==2) && dm_vistau2>=3) || ((dm_vistau2==1||dm_vistau2==2) && dm_vistau1>=3)", # semileptonic tau decay
    #'tautau':   "dm_vistau1>=3 && dm_vistau2>=3", # fully hadronic tau decay
    #'st':       "pt_tau1+pt_tau2+pt_jet1", # scalar sum pT with full tau
    #'stmet':    "pt_tau1+pt_tau2+pt_jet1+met", # scalar sum pT with full tau
    #'stvis':    "pt_vistau1+pt_vistau2+pt_jet1", # scalar sum pT (visible)
    #'stmetvis': "pt_vistau1+pt_vistau2+pt_jet1+met", # scalar sum pT (visible)
    #'nleps':    "nelecs+nmuons", # all leptonic decays
    #'nleps':    "nelecs+nmuons+ntaus", # all leptonic decays
    'njets20':  "nfjets20+ncjets20", # all jets with pT > 20 GeV, |eta|<4.7
    'njets50':  "nfjets50+ncjets50", # all jets with pT > 50 GeV, |eta|<4.7
    'nljets20': "nfjets20+ncjets20-nbjets20", # number of light jets with pT > 20 GeV, |eta|<4.7
    'nljets50': "nfjets50+ncjets50-nbjets50", # number of light jets with pT > 50 GeV, |eta|<4.7
    #'chi':      "exp(abs(eta_tau1-eta_tau2))",
    #'chivis':   "exp(abs(eta_vistau1-eta_vistau2))",
  })
  return sample
  

def compare_LQ(name,title,samples,tag="",**kwargs):
  """Compare list of samples."""
  LOG.header("compare_LQ",pre=">>>")
  outdir   = kwargs.get('outdir', "plots/LQ/gen" )
  norms    = kwargs.get('norm',   [True]         )
  exts     = kwargs.get('ext',    ['png']        ) # figure file extensions
  verb     = kwargs.get('verb',   0              )
  ensuredir(outdir)
  norms    = ensurelist(norms)
  CMSStyle.setCMSEra(era='Run 2',lumi=None,cme=13,thesis=False,extra="Simulation",verb=verb) #extra="Preliminary")
  #CMSStyle.setCMSEra(era='Run 2',lumi=None,cme=13,thesis=True,extra="(CMS simulation)",verb=verb) #extra="Preliminary")
  ratio    = True #and False
  rrange   = 1.0 # ratio range
  if 'LQ' in name:
    pair   = True
    denom  = 3 # use Scalar, M = 1400 GeV in denominator
  else:
    pair   = True
    denom  = -2 # use DY in denominator
  
  # SELECTIONS
  tvars = ['_tau','_vistau','_tt']
  presel = None #"pt_tau1>20 && pt_tau2>20"
  if 'LQ' in name:
    selections = [
      Sel('nocuts',            "", title="no cuts" ),
      #Sel('2t-allchan-ptgt20',"pt_tau1>20 && pt_tau2>20", title="#tau#tau, p_{T}^{#tau} > 20 GeV" ),
      Sel('2t-allchan-ptgt50',"pt_tau1>50 && pt_tau2>50", title="#tau#tau, p_{T}^{#tau} > 50 GeV" ),
      Sel('2t-semilep-ptgt50',"pt_tau1>50 && pt_tau2>50 && dm_tt==2", title="#tau#tau -> l#tau_{h}, p_{T}^{#tau} > 50 GeV",veto=['jet']),
      Sel('2t-fullhad-ptgt50',"pt_tau1>50 && pt_tau2>50 && dm_tt==3", title="#tau#tau -> #tau_{h}#tau_{h}, p_{T}^{#tau} > 50 GeV",veto=['jet']),
    ]
  else:
    selections = [
      Sel('nocuts',            "", title="no cuts", veto=tvars+['_ll'] ),
      Sel('2l-pt50',           "pt_lep1>50 && pt_lep2>50", title="ll, p_{T} > 50 GeV", veto=tvars ),
      Sel('2l-pt50-0j-pt50',   "pt_lep1>50 && pt_lep2>50 && njets20==0", title="ll (p_{T} > 50 GeV), 0j (p_{T} > 50 GeV, |eta|<4.7)", veto=tvars ),
      Sel('2l-pt50-geq1j-pt50',"pt_lep1>50 && pt_lep2>50 && njets20>=1", title="ll (p_{T} > 50 GeV), >=1j (p_{T} > 50 GeV, |eta|<4.7)", veto=tvars ),
    ]
  if 'HNL' in name:
    selections = [s for s in selections if '-0j-' not in selections.name]
  
  # CREATE HISTS
  #LOG.color("Step 0: Creating hists...",b=True)
  allhists = { } # { sample: { selection: { variable: hist } } }
  for sample in samples:
    LOG.color("Sample %s (%r) for %s variables, and %s selections"%(
      sample.name,sample.title,len(variables),len(selections)),c='grey',b=True)
    #if loadhists: # skip recreating histograms (fast!)
    #  allhists[sample] = loadallhists(hfile,variables,variables,sample,subdir=selections,verb=verb)
    #elif hasattr(sample,'gethist'): # create histograms from scratch (slow...)
    print(f">>>   Creating hist for {sample.name}...")
    allhists[sample] = sample.gethist(variables,selections,verb=verb)
  
  # LOOP over SELECTIONS & VARIABLES
  for selection in selections:
    LOG.color("%s: %r"%(selection.title,selection.selection),b=True)
    for variable in variables:
      if variable not in allhists[samples[0]][selection]: continue
      variable.changecontext(selection,verb=verb)
      
      # REORDER hists
      hists = [ ]
      for sample in samples:
        hists.append(allhists[sample][selection][variable])
      
      # PLOT
      fname = ("%s/$VAR_%s_%s$TAG"%(outdir,selection.filename,name)).replace('__','_')
      text = ', '.join(s for s in [title,selection.title] if s)
      if 'nonres' in title.lower():
        text = text.replace(", LQ -> btau","")
      for norm in norms:
        ntag  = tag+('_norm' if norm else "_lumi")
        lsize = 0.055 #_Plot._lsize*(1.5 if var.name.endswith('_q') else 1)
        tsize = 0.046
        style = 1 #[1,1,2,1,1,1]
        nxdiv = 510
        pos   = variable.position
        logyrange = variable.logyrange
        ymargin = variable.ymargin
        twidth = 1.04 if variable.ncols==1 else 1.0
        ###if variable.xmax>=2000:
        ###  nxdiv = 508
        ###if 'LQ-p' in samples[0].name: # Pair
        ###  if any(s in variable.filename for s in ['njet','ncjet']):
        ###    pos = 'R'
        ###    ymargin = 1.45 if variable.filename=='njet' else 1.34
        ###elif 'LQ-s' in samples[0].name: # Single
        ###  if variable.logy and "LQ_eta" in variable.filename:
        ###    ymargin = 1.2
        ###    pos = 'BC'
        ###elif 'LQ-t' in samples[0].name: # NonRes
        ###  if variable.logy and "jpt" in variable.filename:
        ###    logyrange = 7
        ###if (variable.name=='eta' or '_eta' in variable.name) and 'L' in pos:
        ###  ncol = 2
        ###  ###print variable.name, ncol
        ###if not pos:
        ###  pos = 'y=0.85'
        ###  twidth *= 1.1
        ###elif not any(s in pos for s in 'yTB'):
        ###  pos += 'y=0.89'
        plot  = Plot(variable,hists,norm=norm,clone=True,ratio=ratio)
        plot.draw(xlabelsize=lsize,pair=pair,ymargin=ymargin,denom=denom,colors=colors,
                  rrange=rrange,logyrange=logyrange,nxdiv=nxdiv,grid=False,width=700) #style=style,
        plot.drawlegend(margin=1.2,pos=pos,twidth=twidth) #header=title) #,entries=entries)
        plot.drawtext(text,tsize=tsize)
        plot.saveas(fname,ext=exts,tag=ntag)
        plot.close()
      deletehist(hists)
  print(">>> ")
  

def main(args):
  verbosity = args.verbosity
  outdir     = "plots/LQ/gen"
  fname      = None #"$PICODIR/$SAMPLE_$CHANNEL.root" # fname pattern
  nthreads   = args.nthreads
  samplesets = args.samplesets
  #varfilter = args.varfilter
  #selfilter = args.selfilter
  tag        = args.tag
  exts       = ['png','pdf'] #if pdf else ['png']
  RDF.SetNumberOfThreads(nthreads,verb=verbosity+1) # set nthreads globally
  era = '2018'
  setera(era,extra="Simulation") # set era for plot style and lumi-xsec normalization
  
  # COMPARE MIX
  if 'mix' in samplesets:
    dysample = makemcsample('DY','DYJetsToLL_M-50', "Z/#gamma* -> ll, M > 50 GeV",6077.22,era,verb=verbosity+4)
    ttsample = MergedSample('TT',"t#bar{t}",[
      makemcsample('TT',"TTTo2L2Nu",       "ttbar 2l2#nu",       88.29,era,verb=verbosity+4),
      makemcsample('TT',"TTToHadronic",    "ttbar hadronic",    377.96,era,verb=verbosity+4),
      makemcsample('TT',"TTToSemiLeptonic","ttbar semileptonic",365.35,era,verb=verbosity+4)
    ])
    compare_LQ('mix',"",[
       makemcsample('LQ', 'SLQ-t_M2000', "Nonres. LQ_{S}, 2 TeV",1,era,verb=verbosity+2),
       makemcsample('LQ', 'VLQ-t_M2000', "Nonres. LQ_{V}, 2 TeV",1,era,verb=verbosity+2),
       makemcsample('HNL','WRtoNLtoLLJJ_WR2000_N1600',       "W' -> lN, 2/1.6 TeV",1,era,verb=verbosity+2),
       makemcsample('HNL','WRtoNLtoLLJJ_WR4000_N1600',       "W' -> lN, 4/1.6 TeV",1,era,verb=verbosity+2),
       makemcsample('HNL','ZptoNN_EEJJJJ_Zp2000_N500_WR5000',"Z' -> NN, 2/0.5 TeV",1,era,verb=verbosity+2),
       makemcsample('HNL','ZptoNN_EEJJJJ_Zp4000_N500_WR5000',"Z' -> NN, 4/0.5 TeV",1,era,verb=verbosity+2),
       dysample,
       ttsample,
    ],tag=tag,outdir=outdir,ext=exts,verb=verbosity)
  
  # COMPARE LQs
  if 'lq' in samplesets:
    samset = [
      #('LQ-single','s',"Single LQ production"),
      #('LQ-pair',  'p',"LQ pair production"),
      ('LQ-nonres','t',"Nonres. LQ"), #Nonres. tautau production via LQ exchange"
    ]
    for name, prod, title in samset:
      #title  = "LQ -> btau, "+title
      compare_LQ(name,title,[
        makemcsample('LQ',f'SLQ-{prod}_M600',  "Scalar, 600 GeV", 1,era,tag="",verb=verbosity+4),
        makemcsample('LQ',f'VLQ-{prod}_M500',  "Vector, 500 GeV", 1,era,tag="",verb=verbosity+4),
        makemcsample('LQ',f'SLQ-{prod}_M1400', "Scalar, 1400 GeV",1,era,tag="",verb=verbosity+4),
        makemcsample('LQ',f'VLQ-{prod}_M1400', "Vector, 1400 GeV",1,era,tag="",verb=verbosity+4),
        makemcsample('LQ',f'SLQ-{prod}_M2000', "Scalar, 2000 GeV",1,era,tag="",verb=verbosity+4),
        makemcsample('LQ',f'VLQ-{prod}_M2000', "Vector, 2000 GeV",1,era,tag="",verb=verbosity+4),
      ],tag=tag,outdir=outdir,ext=exts,verb=verbosity)
  
  # COMPARE single HNL
  if 'hnl' in samplesets:
    compare_LQ('HNL-s',"W' -> lN -> lljj",[
      makemcsample('HNL','WRtoNLtoLLJJ_WR2000_N100',  "2/0.1 TeV",1,era,verb=verbosity+2),
      makemcsample('HNL','WRtoNLtoLLJJ_WR2000_N1600', "2/1.6 TeV",1,era,verb=verbosity+2),
      makemcsample('HNL','WRtoNLtoLLJJ_WR4000_N100',  "4/0.1 TeV",1,era,verb=verbosity+2),
      makemcsample('HNL','WRtoNLtoLLJJ_WR4000_N1600', "4/1.6 TeV",1,era,verb=verbosity+2),
      makemcsample('HNL','WRtoNLtoLLJJ_WR4000_N3600', "4/3.6 TeV",1,era,verb=verbosity+2),
    ],tag=tag,outdir=outdir,ext=exts,verb=verbosity)
    
  # COMPARE pair HNL
  if 'hnl' in samplesets:
    compare_LQ('HNL-p',"Z' -> NN -> eejjjj",[
       makemcsample('HNL','ZptoNN_EEJJJJ_Zp2000_N100_WR5000', "2/0.1 TeV",1,era,verb=verbosity+2),
       makemcsample('HNL','ZptoNN_EEJJJJ_Zp2000_N500_WR5000', "2/0.5 TeV",1,era,verb=verbosity+2),
       makemcsample('HNL','ZptoNN_EEJJJJ_Zp4000_N100_WR5000', "4/0.1 TeV",1,era,verb=verbosity+2),
       makemcsample('HNL','ZptoNN_EEJJJJ_Zp4000_N500_WR5000', "4/0.5 TeV",1,era,verb=verbosity+2),
       makemcsample('HNL','ZptoNN_EEJJJJ_Zp4000_N1500_WR5000',"4/1.5 TeV",1,era,verb=verbosity+2),
    ],tag=tag,outdir=outdir,ext=exts,verb=verbosity)
  

if __name__ == "__main__":
  from argparse import ArgumentParser
  description = """Simple plotting script to compare distributions in pico analysis tuples."""
  parser = ArgumentParser(description=description,epilog="Good luck!")
  #parser.add_argument('-V', '--var',       dest='varfilter', nargs='+',
  #                                         help="only plot the variables passing this filter (glob patterns allowed)" )
  #parser.add_argument('-S', '--sel',       dest='selfilter', nargs='+',
  #                                         help="only plot the selection passing this filter (glob patterns allowed)" )
  #parser.add_argument('-s', '--serial',    dest='parallel', action='store_false',
  #                                         help="run Tree::MultiDraw serial instead of in parallel" )
  #parser.add_argument('-p', '--parallel',  action='store_true',
  #                                         help="run Tree::MultiDraw in parallel instead of in serial" )
  parser.add_argument('-s', '--sample',    dest='samplesets', nargs='+', default=['lq'],
                                           help="only plot these sampleset" )
  parser.add_argument('-n', '--nthreads',  type=int, nargs='?', const=10, default=10, action='store',
                                           help="run RDF in parallel instead of in serial, nthreads=%(default)r" )
  parser.add_argument('-t', '--tag',       default="", help="extra tag for output" )
  parser.add_argument('-v', '--verbose',   dest='verbosity', type=int, nargs='?', const=1, default=0, action='store',
                                           help="set verbosity" )
  args = parser.parse_args()
  LOG.verbosity = args.verbosity
  PLOG.verbosity = args.verbosity
  main(args)
  print("\n>>> Done.")
  
