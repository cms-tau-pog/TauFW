#! /usr/bin/env python
# Author: Izaak Neutelings (June 2020)
# Description: Create pseudo MC and data for quick and reproducible testing of Plotter tools
import time
import numpy as np
from TauFW.common.tools.utils import unwraplistargs
from TauFW.common.tools.file import ensuredir
from ROOT import TFile, TTree, TH1D, gRandom, TColor
from TauFW.Plotter.plot.utils import LOG


def makesamples(nevts=10000,**kwargs):
  """Create pseudo MC and data tree for quick and reproducible testing of Plotter tools."""
  
  outdir  = kwargs.get('outdir',  'plots' )
  channel = kwargs.get('channel', 'mutau' )
  samples = kwargs.get('sample',  [ ]     )
  scales  = kwargs.get('scales',  None    )
  samples = unwraplistargs(samples)
  
  scaledict = {
    'ZTT': 1.0,
    'QCD': 0.3,
    'TT':  0.2,
  }
  if scales:
    scaledict.update(scales)
  vardict = { # uncorrelated pseudo distributions for variables
    'm_vis': {
      'ZTT': lambda: gRandom.Gaus( 72, 9),
      'QCD': lambda: gRandom.Gaus( 80,60),
      'TT':  lambda: gRandom.Gaus(120,70),
    },
    'pt_1': {
      'ZTT': lambda: gRandom.Landau(30,2),
      'QCD': lambda: gRandom.Landau(30,5),
      'TT':  lambda: gRandom.Landau(40,6),
    },
    'pt_2': {
      'ZTT': lambda: gRandom.Landau(24,2),
      'QCD': lambda: gRandom.Landau(24,5),
      'TT':  lambda: gRandom.Landau(30,6),
    },
    'eta_1': {
      'ZTT': lambda: gRandom.Uniform(-2.5,2.5),
      'QCD': lambda: gRandom.Uniform(-2.5,2.5),
      'TT':  lambda: gRandom.Uniform(-2.5,2.5),
    },
    'eta_2': {
      'ZTT': lambda: gRandom.Uniform(-2.5,2.5),
      'QCD': lambda: gRandom.Uniform(-2.5,2.5),
      'TT':  lambda: gRandom.Uniform(-2.5,2.5),
    },
    'njets': {
      'ZTT': lambda: gRandom.Poisson(0.2,),
      'QCD': lambda: gRandom.Poisson(2.0,),
      'TT':  lambda: gRandom.Poisson(2.5,),
    },
    'weight': {
      'ZTT': lambda: gRandom.Gaus(1.0,0.10),
      'QCD': lambda: gRandom.Gaus(1.0,0.05),
      'TT':  lambda: gRandom.Gaus(1.0,0.08),
    },
  }
  
  # PREPARE TREES
  ensuredir(outdir)
  filedict = { }
  m_vis  = np.zeros(1,dtype='f')
  pt_1   = np.zeros(1,dtype='f')
  pt_2   = np.zeros(1,dtype='f')
  eta_1  = np.zeros(1,dtype='f')
  eta_2  = np.zeros(1,dtype='f')
  njets  = np.zeros(1,dtype='i')
  weight = np.zeros(1,dtype='f')
  def makesample(sample): # help function to create file with tree
    if samples and sample not in samples:
      return
    fname = "%s/%s_%s.root"%(outdir,sample,channel)
    file  = TFile(fname,'RECREATE')
    tree  = TTree('tree','tree')
    tree.Branch('m_vis',  m_vis,  'm_vis/F')
    tree.Branch('pt_1',   pt_1,   'pt_1/F')
    tree.Branch('pt_2',   pt_2,   'pt_2/F')
    tree.Branch('eta_1',  eta_1,  'eta_1/F')
    tree.Branch('eta_2',  eta_2,  'eta_2/F')
    tree.Branch('njets',  njets,  'njets/I')
    tree.Branch('weight', weight, 'weight/F')
    filedict[sample] = (file,tree)
  for sample in scaledict:
    makesample(sample)
  makesample('Data')
  
  def fill(sample,tree,nevts): # help function to fill trees
    for i in xrange(nevts):
      m_vis[0]  = vardict['m_vis'][sample]()
      pt_1[0]   = vardict['pt_1'][sample]()
      pt_2[0]   = vardict['pt_2'][sample]()
      if pt_1[0]<pt_1[0]:
        pt_1[0], pt_2[0] = pt_2[0], pt_1[0]
      eta_1[0]  = vardict['eta_1'][sample]()
      eta_2[0]  = vardict['eta_2'][sample]()
      njets[0]  = vardict['njets'][sample]()
      weight[0] = vardict['weight'][sample]() if sample!='Data' else 1.0
      tree.Fill()
  
  # PSEUDO MC
  print ">>> Generating pseudo MC..."
  #time0 = time.time()
  for sample, prob in scaledict.iteritems():
    if samples and sample not in samples:
      continue
    #print ">>>   %r"%(sample)
    file, tree = filedict[sample]
    file.cd()
    fill(sample,tree,nevts)
    tree.Write()
  #print ">>>   %.1f seconds"%(time.time()-time0)
  
  # PSEUDO DATA
  if not samples or 'Data' in samples:
    file, tree = filedict['Data']
    file.cd()
    print ">>> Generating pseudo data..."
    #time0 = time.time()
    for sample, prob in scaledict.iteritems():
      ndevts = int(prob*nevts)
      fill(sample,tree,ndevts)
    tree.Write()
    #print ">>>   %.1f seconds"%(time.time()-time0)
  
  return filedict
  
