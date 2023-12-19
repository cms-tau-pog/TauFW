# Author: Izaak Neutelings (June 2020)
# Description: Create pseudo MC and data for quick and reproducible testing of Plotter tools
import time
import numpy as np
from ROOT import TFile, TTree, TH1D, gRandom, TColor, kBlack, kWhite, kBlue, kOrange, kMagenta
from TauFW.Plotter.plot.utils import LOG, ensurelist, ensuredir
from TauFW.Plotter.sample.utils import join

coldict = { # HTT / TauPOG colors
  'ZTT':      kOrange-4,   'QCD': kMagenta-10,
  'TT':       kBlue-8,     'WJ':  50,
  'ST':       kMagenta-8,  'VV':  TColor.GetColor(222,140,106),
  'Data':     kBlack,
  'Observed': kBlack,
}


def getfname(outdir,sample,channel,tag=""):
  return "%s/%s_%s%s.root"%(outdir,sample,channel,tag)


def getsamples(sampleset=None,nevts=10000,**kwargs):
  """Get pseudosamples as Sample objects."""
  from TauFW.Plotter.sample.utils import setera, Sample #, CMSStyle
  verbosity  = kwargs.get('verb',    0       )
  scales     = kwargs.get('scales',  None    )
  split      = kwargs.get('split',   False   ) # split DY into subcomponents according to genmatch
  merge      = kwargs.get('merge',   [ ]     ) # merge DY*Jets samples
  vetoes     = kwargs.get('veto',    [ ]     ) # do not include these samples
  reuse      = kwargs.get('reuse',   False   ) # reuse previously generated samples
  outdir     = kwargs.setdefault('outdir',     'plots/test' )
  channel    = kwargs.setdefault('channel',    'mutau'      )
  scale_xsec = kwargs.setdefault('scale_xsec', 10 ) # arbitrary scale to get xsec (the larger, the more data will be generated)
  lumi       = kwargs.setdefault('lumi',       10 ) # [fb-1] to cancel xsec [pb]
  fnames     = { }
  if sampleset==None:
    if 'DY' in merge:
      sampleset = [
        ('DYJetsToLL',  "DY incl.",   1.00),
        ('DY1JetsToLL', "DY + 1 jet", 0.50),
        ('DY2JetsToLL', "DY + 2 jet", 0.30),
        ('DY3JetsToLL', "DY + 3 jet", 0.20),
        ('DY4JetsToLL', "DY + 4 jet", 0.10),
      ]
    else:
      sampleset = [
        #('ZTT',  "Z -> #tau_{mu}#tau_{h}", 1.00),
        ('DY', "Drell-Yan", 1.00),
      ]
    sampleset += [
      ('WJ',   "W + jets",     0.45),
      ('QCD',  "QCD multijet", 0.35),
      ('TT',   "t#bar{t}",     0.20),
      ('Data', "Observed",      -1 ),
    ]
  samples = kwargs.setdefault('sample', [n[0] for n in sampleset])
  samples = ensurelist(samples)
  vetoes  = ensurelist(vetoes)
  if reuse: # do not generate again, but take pre-existing files
    fnames = { s: getfname(outdir,s,channel,tag="") for s in samples }
  else: # generate from scratch
    kwargs['sample'] = sampleset
    filedict = makesamples(nevts,**kwargs)
    for sample in samples:
      file, tree = filedict[sample]
      fnames[sample] = file.GetName()
      file.Close()
  datasample = None
  expsamples = [ ]
  #CMSStyle.setCMSEra(2018)
  setera(2018,lumi)
  for name, title, scale in sampleset:
    if vetoes and name in vetoes:
      if verbosity>=1:
        print(">>> getsamples: Vetoing sample with name=%r..."%(name))
      continue
    fname = fnames[name]
    color = None #STYLE.getcolor(name,verb=2)
    if name.lower()=='data':
      datasample = Sample(name,title,fname,data=True,verbosity=verbosity)
    else:
      xsec = scale_xsec*scale
      sample = Sample(name,title,fname,xsec,color=color,data=False,weight='weight',verbosity=verbosity)
      #sample = Sample(name,title,fname,xsec,color=color,data=False,lumi=lumi,weight='weight')
      expsamples.append(sample)
  if 'DY' in merge: # merge DY*Jets
    expsamples = join(expsamples,"DY*Jets",name="DY_merged")
  if 'JTF' in merge: #  merge JTF = QCD + WJ
    expsamples = join(expsamples,['QCD','WJ'],name='JTF',title="j -> tau_h fakes")
  if 'nonDY' in merge: #  merge everything except DY
    expsamples = join(expsamples,['QCD','WJ','JTF','ST','TT'],name='nonDY',title="Non-DY")
  if split: # split DY into genmatch components
    for sample in expsamples:
      if 'DY' in sample.name:
        LOG.verb("getsamples: Splitting %r..."%(sample.name),verbosity,1)
        sample.split([
          ('ZTT',"Z -> #tau_{mu}#tau_{h}","genmatch_2==5"), # real tau
          ('ZL',"0<genmatch_2 && genmatch_2<5"), # lepton -> tau fake
          ('ZJ',"genmatch_2==0"), # j -> tau fake
        ])
      break
  return datasample, expsamples
  

def makesamples(nevts=10000,**kwargs):
  """Create pseudo MC and data tree for quick and reproducible testing of Plotter tools."""
  verbosity  = kwargs.get('verb',       0            )
  outdir     = kwargs.get('outdir',     'plots/test' )
  channel    = kwargs.get('channel',    'mutau'      )
  samples    = kwargs.get('sample',     ['Data','DY','WJ','QCD','TT'])
  scales     = kwargs.get('scales',     None         )
  lumi       = kwargs.get('lumi',       10           ) # [fb-1] to cancel xsec [pb]
  scale_xsec = kwargs.get('scale_xsec', 10           ) # arbitrary scale to get xsec (the larger, the more data will be generated)
  samples    = ensurelist(samples)
  if all(isinstance(s,tuple) for s in samples):
    scales = {n[0]: n[-1] for n in samples} # relative contribtions to pseudo data
    samples = [n[0] for n in samples]
  
  scaledict = { # relative contribtions to pseudo data
    'DY':      1.10,
    'ZTT':     1.00,
    'WJ':      0.40,
    'QCD':     0.25,
    'TT':      0.15,
    'DYJets':  1.00,
    'DY1Jets': 0.50,
    'DY2Jets': 0.30,
    'DY3Jets': 0.20,
    'DY4Jets': 0.10,
  }
  if scales:
    scaledict.update(scales)
  scaledict.pop('Data',None)
  vardict = { # uncorrelated pseudo distributions for variables
    'm_vis': {
      '*':   lambda gm: gRandom.Gaus( 80,44), # default
      'DY':  lambda gm: gRandom.Gaus( 72, 9) if gm==5 else gRandom.Gaus( 91, 2) if gm in [1,2,3,4] else gRandom.Gaus( 80,44),
      'ZTT': lambda gm: gRandom.Gaus( 72, 9),
      'WJ':  lambda gm: gRandom.Gaus( 65,28),
      'QCD': lambda gm: gRandom.Gaus( 80,44),
      'TT':  lambda gm: gRandom.Gaus(110,70),
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
    'q_1': { # charge = +1 or -1
      '*': lambda r: -1 if r<0.5 else 1, # default
    },
    'q_2': { # charge
      '*':   lambda r, q: q if r<0.10 else -q, # default: SS 10% of the time
      'DY':  lambda r, q: q if r<0.03 else -q, # default: SS 10% of the time
      'ZTT': lambda r, q: q if r<0.02 else -q, # default: SS 10% of the time
      'WJ':  lambda r, q: q if r<0.20 else -q, # SS 20% of the time
      'QCD': lambda r, q: q if r<0.45 else -q, # SS 45% of the time
    },
    'eta_1': {
      '*': lambda r: r+0.02*r**3, # default
    },
    'eta_2': {
      '*': lambda r: r+0.02*r**3, # default
    },
    'gm_2': { # gen match
      '*':    lambda r: 5, # default
      'DY':   lambda r: 0 if r<0.05 else 3 if r<0.08 else 4 if r<0.1 else 5, # default
      'ZTT':  lambda r: 5, # default
      'QCD':  lambda r: 0 if r<0.95 else 1 if r<0.96 else 2 if r<0.98 else 5, # default
      'WJ':   lambda r: 0 if r<0.82 else 1 if r<0.87 else 2 if r<0.92 else 5, # default
      'TT':   lambda r: 0 if r<0.10 else 3 if r<0.14 else 4 if r<0.18 else 5, # default
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
      '*':   lambda: gRandom.Gaus(1.0,0.05), # default
      'QCD': lambda: gRandom.Gaus(1.0,0.03),
      'TT':  lambda: gRandom.Gaus(1.0,0.04),
    },
    'idweight': {
      '*':   lambda: gRandom.Gaus(1.0,0.02), # default
    },
  }
  
  # PREPARE TREES
  ensuredir(outdir)
  filedict = { }
  histdict = { }
  m_vis    = np.zeros(1,dtype='f')
  pt_1     = np.zeros(1,dtype='f')
  pt_2     = np.zeros(1,dtype='f')
  q_1      = np.zeros(1,dtype='i')
  q_2      = np.zeros(1,dtype='i')
  dm_2     = np.zeros(1,dtype='f')
  eta_1    = np.zeros(1,dtype='f')
  eta_2    = np.zeros(1,dtype='f')
  njets    = np.zeros(1,dtype='i')
  gm_2     = np.zeros(1,dtype='i') # genmatch_2: 5 = real tau; 0 = fake tau
  NUP      = np.zeros(1,dtype='i') # number of LHE-level partons for jet stitching
  weight   = np.zeros(1,dtype='f')
  idweight = np.zeros(1,dtype='f')
  def makesample(sample): # help function to create file with tree
    fname = getfname(outdir,sample,channel)
    file  = TFile(fname,'RECREATE')
    hist  = TH1D('cutflow','cutflow',20,0,20)
    tree  = TTree('tree','tree')
    tree.Branch('m_vis',      m_vis,    'm_vis/F')
    tree.Branch('pt_1',       pt_1,     'pt_1/F')
    tree.Branch('pt_2',       pt_2,     'pt_2/F')
    tree.Branch('q_1',        q_1,      'q_1/I')
    tree.Branch('q_2',        q_2,      'q_2/I')
    tree.Branch('dm_2',       dm_2,     'dm_2/I')
    tree.Branch('eta_1',      eta_1,    'eta_1/F')
    tree.Branch('eta_2',      eta_2,    'eta_2/F')
    tree.Branch('njets',      njets,    'njets/I')
    tree.Branch('genmatch_2', gm_2,     'genmatch_2/I')
    tree.Branch('NUP',        NUP,      'NUP/I')
    tree.Branch('weight',     weight,   'weight/F')
    tree.Branch('idweight',   idweight, 'idweight/F')
    tree.SetDirectory(file)
    hist.SetDirectory(file)
    #hist.SetBinContent( 1,1)
    #hist.SetBinContent(17,1)
    histdict[sample] = hist
    filedict[sample] = (file,tree)
  for sample in samples:
    makesample(sample)
  makesample('Data')
  
  def getgenerator(var,sample): # get random generator from dictionary
    if 'DY' in sample:
      return vardict[var].get(sample,vardict[var].get('DY',vardict[var]['*']))
    else:
      return vardict[var].get(sample,vardict[var]['*'])
  def fill(sample,tree,nevts): # help function to fill trees
    if verbosity>=1:
      print(">>>   Generating %r (nevts=%s)..."%(sample,nevts))
    npass = 0
    gen_gm_2     = getgenerator('gm_2',    sample)
    gen_mvis     = getgenerator('m_vis',   sample)
    gen_pt_1     = getgenerator('pt_1',    sample)
    gen_pt_2     = getgenerator('pt_2',    sample)
    gen_q_1      = getgenerator('q_1',     sample)
    gen_q_2      = getgenerator('q_2',     sample)
    gen_dm_2     = getgenerator('dm_2',    sample)
    gen_eta_1    = getgenerator('eta_1',   sample)
    gen_eta_2    = getgenerator('eta_2',   sample)
    gen_njets    = getgenerator('njets',   sample)
    gen_weight   = getgenerator('weight',  sample)
    gen_idweight = getgenerator('idweight',sample)
    for i in range(nevts):
      gm_2[0]   = gen_gm_2(gRandom.Uniform(1.))
      m_vis[0]  = gen_mvis(gm_2[0])
      pt_1[0]   = gen_pt_1()
      pt_2[0]   = gen_pt_2()
      if m_vis[0]<0 or pt_1[0]<0 or pt_2[0]<0: # try again once more
        m_vis[0] = gen_mvis(gm_2[0])
        pt_1[0]  = gen_pt_1()
        pt_2[0]  = gen_pt_2()
        if m_vis[0]<0 or pt_1[0]<0 or pt_2[0]<0:
          continue
      if pt_1[0]<pt_1[0]: # swap
        pt_1[0], pt_2[0] = pt_2[0], pt_1[0]
      q_1[0]      = gen_q_1(gRandom.Uniform(1.))
      q_2[0]      = gen_q_2(gRandom.Uniform(1.),q_1[0]) # correlate charge
      dm_2[0]     = gen_dm_2(gRandom.Uniform(1.))
      eta_1[0]    = gen_eta_1(gRandom.Uniform(-2.8,2.8))
      eta_2[0]    = gen_eta_2(gRandom.Uniform(-2.8,2.8))
      njets[0]    = gen_njets()
      if sample!='Data':
        weight[0]   = gen_weight()
        idweight[0] = gen_idweight()
      else:
        weight[0]   = 1.0
        idweight[0] = 1.0
      histdict[sample].Fill(0.5,1) # bin 1
      histdict[sample].Fill(16.5,weight[0]) # bin 17
      tree.Fill()
      npass += 1
    return npass
  
  # PSEUDO MC
  print(">>> Generating pseudo MC...")
  #time0 = time.time()
  totxsec = 0
  for sample in samples:
    if sample=='Data': continue
    file, tree = filedict[sample]
    file.cd()
    fill(sample,tree,nevts)
    histdict[sample].Write()
    tree.Write()
    totxsec += scale_xsec*scaledict.get(sample,1.0) # [pb]
  #print ">>>   %.1f seconds"%(time.time()-time0)
  
  # PSEUDO DATA = SUM( MC )
  if 'Data' in samples:
    print(">>> Generating pseudo data for totxsec=%spb, lumi=%s/fb, nevts=%s..."%(totxsec,lumi,nevts))
    file, tree = filedict['Data']
    file.cd()
    #time0 = time.time()
    totevts = 0
    for sample in samples: # loop over MC samples
      if sample=='Data': continue
      xsec   = scale_xsec*scaledict.get(sample,1.0) # [pb]
      ndevts = int(xsec*lumi*1000) # relative contribtion to pseudo data
      totevts += fill(sample,tree,ndevts)
    histdict[sample].Write()
    tree.Write()
    #print ">>>   %.1f seconds"%(time.time()-time0)
    if verbosity>=1:
      print(">>>   Generated %s data events in total (lumi=%.4g)!"%(totevts,lumi))
  
  return filedict
  
