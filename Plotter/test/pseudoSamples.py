#! /usr/bin/env python
# Author: Izaak Neutelings (June 2020)
# Description: Create pseudo MC and data for quick and reproducible testing of Plotter tools
import time
import numpy as np
from ROOT import TFile, TTree, TH1D, gRandom, TColor, kBlack, kWhite, kBlue, kOrange, kMagenta
from TauFW.Plotter.plot.utils import LOG, unwraplistargs, ensuredir


coldict = { # HTT / TauPOG colors
  'ZTT':      kOrange-4,   'QCD': kMagenta-10,
  'TT':       kBlue-8,     'WJ':  50,
  'ST':       kMagenta-8,  'VV':  TColor.GetColor(222,140,106),
  'Data':     kBlack,
  'Observed': kBlack,
}


def makesamples(nevts=10000,**kwargs):
  """Create pseudo MC and data tree for quick and reproducible testing of Plotter tools."""
  
  outdir  = kwargs.get('outdir',  'plots' )
  channel = kwargs.get('channel', 'mutau' )
  samples = kwargs.get('sample',  ['Data','ZTT','WJ','QCD','TT'])
  scales  = kwargs.get('scales',  None    )
  samples = unwraplistargs(samples)
  
  scaledict = { # relative contribtions to pseudo data
    'ZTT': 1.00,
    'WJ':  0.40,
    'QCD': 0.25,
    'TT':  0.15,
    'DYJets':  1.0,
    'DY1Jets': 0.5,
    'DY2Jets': 0.3,
    'DY3Jets': 0.2,
    'DY4Jets': 0.1,
  }
  if scales:
    scaledict.update(scales)
  scaledict.pop('Data',None)
  vardict = { # uncorrelated pseudo distributions for variables
    'm_vis': {
      '*':   lambda gm: gRandom.Gaus( 72, 9) if gm==5 else gRandom.Gaus( 91, 2), # default
      'ZTT': lambda gm: gRandom.Gaus( 72, 9),
      'WJ':  lambda gm: gRandom.Gaus( 65,28),
      'QCD': lambda gm: gRandom.Gaus( 80,44),
      'TT':  lambda gm: gRandom.Gaus(110,70),
    },
    'genmatch_2': { # chance that genmatch_2==5 (real tau)
      '*':   0.9, # default
      'ZTT': 1.0,
      'WJ':  0.5,
      'QCD': 0.5,
      'TT':  0.8,
    },
    'pt_1': {
      '*':   lambda: gRandom.Landau(30,2), # default
      'QCD': lambda: gRandom.Landau(30,5),
      'TT':  lambda: gRandom.Landau(40,6),
    },
    'pt_2': {
      '*':   lambda: gRandom.Landau(24,2), # default
      'WJ':  lambda: gRandom.Landau(24,2),
      'QCD': lambda: gRandom.Landau(24,5),
      'TT':  lambda: gRandom.Landau(30,6),
    },
    'eta_1': {
      '*': lambda: gRandom.Uniform(-2.5,2.5), # default
    },
    'eta_2': {
      '*': lambda: gRandom.Uniform(-2.5,2.5), # default
    },
    'dm_2': {
      '*':   lambda r: 0 if r<0.4 else 1 if r<0.6 else 10 if r<0.9 else 11, # default
    },
    'njets': {
      '*':   lambda: gRandom.Poisson(0.2,), # default
      'ZTT': lambda: gRandom.Poisson(0.2,),
      'WJ':  lambda: gRandom.Poisson(1.2,),
      'QCD': lambda: gRandom.Poisson(2.0,),
      'TT':  lambda: gRandom.Poisson(2.5,),
      'DYJets':  lambda: gRandom.Poisson(0.2,),
      'DY1Jets': lambda: 1,
      'DY2Jets': lambda: 2,
      'DY3Jets': lambda: 3,
      'DY4Jets': lambda: 4,
    },
    'NUP': {
      '*':   lambda: gRandom.Poisson(0.2,), # default
      'ZTT': lambda: gRandom.Poisson(0.2,),
      'WJ':  lambda: gRandom.Poisson(1.2,),
      'QCD': lambda: gRandom.Poisson(2.0,),
      'TT':  lambda: gRandom.Poisson(2.5,),
      'DYJets':  lambda: gRandom.Poisson(0.2,),
      'DY1Jets': lambda: 1,
      'DY2Jets': lambda: 2,
      'DY3Jets': lambda: 3,
      'DY4Jets': lambda: 4,
    },
    'weight': {
      '*':   lambda: gRandom.Gaus(1.0,0.10), # default
      'ZTT': lambda: gRandom.Gaus(1.0,0.10),
      'WJ':  lambda: gRandom.Gaus(1.0,0.10),
      'QCD': lambda: gRandom.Gaus(1.0,0.05),
      'TT':  lambda: gRandom.Gaus(1.0,0.08),
    },
  }
  
  # PREPARE TREES
  ensuredir(outdir)
  filedict   = { }
  histdict   = { }
  m_vis      = np.zeros(1,dtype='f')
  pt_1       = np.zeros(1,dtype='f')
  pt_2       = np.zeros(1,dtype='f')
  dm_2       = np.zeros(1,dtype='f')
  eta_1      = np.zeros(1,dtype='f')
  eta_2      = np.zeros(1,dtype='f')
  njets      = np.zeros(1,dtype='i')
  genmatch_2 = np.zeros(1,dtype='i') # genmatch_2: 5 = real tau; 0 = fake tau
  NUP        = np.zeros(1,dtype='i') # number of LHE-level partons for jet stitching
  weight     = np.zeros(1,dtype='f')
  def makesample(sample): # help function to create file with tree
    fname = "%s/%s_%s.root"%(outdir,sample,channel)
    file  = TFile(fname,'RECREATE')
    hist  = TH1D('cutflow','cutflow',20,0,20)
    tree  = TTree('tree','tree')
    tree.Branch('m_vis',      m_vis,      'm_vis/F')
    tree.Branch('pt_1',       pt_1,       'pt_1/F')
    tree.Branch('pt_2',       pt_2,       'pt_2/F')
    tree.Branch('dm_2',       dm_2,       'dm_2/I')
    tree.Branch('eta_1',      eta_1,      'eta_1/F')
    tree.Branch('eta_2',      eta_2,      'eta_2/F')
    tree.Branch('njets',      njets,      'njets/I')
    tree.Branch('genmatch_2', genmatch_2, 'genmatch_2/I')
    tree.Branch('NUP',        NUP,        'NUP/I')
    tree.Branch('weight',     weight,     'weight/F')
    tree.SetDirectory(file)
    hist.SetDirectory(file)
    hist.SetBinContent( 1,1)
    hist.SetBinContent(17,1)
    histdict[sample] = hist
    filedict[sample] = (file,tree)
  for sample in scaledict:
    makesample(sample)
  makesample('Data')
  
  def getgenerator(var,sample): # get random generator from dictionary
    if sample in vardict[var]: return vardict[var][sample]
    else: return vardict[var]['*']
  def fill(sample,tree,nevts): # help function to fill trees
    for i in xrange(nevts):
      genmatch_2[0] = 5 if gRandom.Uniform(1.)<getgenerator('genmatch_2',sample) else 0
      m_vis[0]      = getgenerator('m_vis',sample)(genmatch_2[0])
      pt_1[0]       = getgenerator('pt_1', sample)()
      pt_2[0]       = getgenerator('pt_2', sample)()
      if m_vis[0]<0 or pt_1[0]<0 or pt_2[0]<0: continue
      if pt_1[0]<pt_1[0]:
        pt_1[0], pt_2[0] = pt_2[0], pt_1[0]
      dm_2[0]   = getgenerator('dm_2', sample)(gRandom.Uniform(1.))
      eta_1[0]  = getgenerator('eta_1', sample)()
      eta_2[0]  = getgenerator('eta_2', sample)()
      njets[0]  = getgenerator('njets', sample)()
      weight[0] = getgenerator('weight',sample)() if sample!='Data' else 1.0
      tree.Fill()
  
  # PSEUDO MC
  print ">>> Generating pseudo MC..."
  #time0 = time.time()
  for sample in samples:
    if sample=='Data': continue
    #print ">>>   %r"%(sample)
    file, tree = filedict[sample]
    file.cd()
    fill(sample,tree,nevts)
    histdict[sample].Write()
    tree.Write()
  #print ">>>   %.1f seconds"%(time.time()-time0)
  
  # PSEUDO DATA
  if 'Data' in samples:
    print ">>> Generating pseudo data..."
    file, tree = filedict['Data']
    file.cd()
    #time0 = time.time()
    for sample in samples:
      if sample=='Data': continue
      prob = scaledict.get(sample,1.0)
      ndevts = int(prob*nevts) # relative contribtion to pseudo data
      fill(sample,tree,ndevts)
    histdict[sample].Write()
    tree.Write()
    #print ">>>   %.1f seconds"%(time.time()-time0)
  
  return filedict
  
