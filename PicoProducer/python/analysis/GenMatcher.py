#! /usr/bin/env python
# Author: Izaak Neutelings (April 2022)
# Description: Study genmatch algorithms in nanoAOD
# HTT gen-matching:
#   https://twiki.cern.ch/twiki/bin/viewauth/CMS/HiggsToTauTauWorking2016#MC_Matching
#   https://indico.cern.ch/event/439324/#19-studies-on-background-categ
# NanoAOD genPartFlav:
#   https://github.com/cms-sw/cmssw/blob/master/PhysicsTools/NanoAOD/plugins/CandMCMatchTableProducer.cc
#   https://github.com/cms-sw/cmssw/blob/master/DataFormats/HepMCCandidate/interface/GenParticle.h#L59-L61
#   isDirectPromptTauDecayProductFinalState      = status==1 && isDirectPromptTauDecayProduct
#   isDirectHardProcessTauDecayProductFinalState = status==1 && isDirectHardProcessTauDecayProduct
# Previous bug in nanoAOD genPartFlav:
#   https://indico.cern.ch/event/801245/#3-data-mc-agreement-in-run-2-t
#   https://github.com/cms-sw/cmssw/issues/26163
# Instructions:
#   pico.py channel genmatch GenMatcher
#   pico.py run -c genmatch -s DYJetsToLL_M-50 -y UL2018 -m 1000
#   pico.py submit -c genmatch -s DYJetsToLL_M-50 -y UL2018
#   pico.py status -c genmatch -s DYJetsToLL_M-50 -y UL2018
#   pico.py hadd -c genmatch -s DYJetsToLL_M-50 -y UL2018
#   python/analysis/GenMatcher.py DYJetsToLL_M-50_genmatch.root
#   tree->Draw("genmatch_HTT:genmatch >> h(7,0,7,7,0,7)","","COLZ TEXT")
#   tree->Draw("genmatch_HTT:genmatch >> h(7,0,7,7,0,7)","idDeepTau2017v2p1VSe>=2 && idDeepTau2017v2p1VSmu>=2 && idDeepTau2017v2p1VSjet>=8 && pt>40","COLZ TEXT")
# Results:
#   https://ineuteli.web.cern.ch/ineuteli/TauPOG/plots/genmatch/?match=genmatch+ptgt20+TightVSjet+VSmu_+UL2018
import ROOT; ROOT.PyConfig.IgnoreCommandLineOptions = True
import re
from ROOT import TH2D, gStyle, kRed
from TreeProducer import TreeProducer
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module
from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection, Event
from TauFW.PicoProducer.analysis.utils import hasbit


class GenMatcher(Module):
  """Simple module to check genmatching algorithms."""
  
  def __init__(self,fname,**kwargs):
    self.out = TreeProducerGenMatcher(fname,self)
    
  def endJob(self):
    """Wrap up after running on all events and files"""
    self.out.endJob()
    
  def analyze(self, event):
    """Process event, return True (pass, go to next module) or False (fail, go to next event)."""
    self.out.cutflow.fill('none')
    
    # TAU
    # https://cms-nanoaod-integration.web.cern.ch/integration/master-102X/mc102X_doc.html#Tau
    taus = [ ] # selected tau candidates
    for tau in Collection(event,'Tau'):
      if tau.pt<20: continue
      if abs(tau.eta)>2.3: continue
      #if abs(tau.dz)>0.2: continue
      #if tau.decayMode not in [0,1,10,11]: continue
      #if abs(tau.charge)!=1: continue
      if tau.idDeepTau2017v2p1VSe<1: continue # VVVLoose
      if tau.idDeepTau2017v2p1VSmu<1: continue # VLoose
      if tau.idDeepTau2017v2p1VSjet<1: continue # VVVLoose
      taus.append(tau)
    if len(taus)==0:
      return False
    self.out.cutflow.fill('tau')
    if len(taus)>=2:
      self.out.cutflow.fill('taus')
    #tau = max(taus,key=lambda t: t.pt) # select tau with highest pT
    
    # MUON
    muons = [ ] # selected muon candidates
    for muon in Collection(event,'Muon'):
      if muon.pt<20: continue
      if abs(muon.eta)>2.3: continue
      if not muon.mediumId: continue
      if muon.pfRelIso04_all>0.5: continue
      muons.append(muon)
    if len(muons)>=1:
      self.out.cutflow.fill('muon')
    
    # STORE EACH TAU
    for tau in taus:
      
      # HTT GENMATCH ALGORITHMS
      genmatch_nano      = tau.genPartFlav # default nanoAOD genmatch
      genmatch_HTT       = genmatch(tau,event,cutpt=True, status=False)
      genmatch_HTT_nopt  = genmatch(tau,event,cutpt=False,status=False)
      genmatch_HTT_stat  = genmatch(tau,event,cutpt=True, status=True)
      genmatch_nopt_stat = genmatch(tau,event,cutpt=False,status=True)
      
      # FILL HISTOGRAMS
      self.out.h_gm_HTT_vs_nano.Fill(genmatch_nano,genmatch_HTT)
      self.out.h_gm_HTT_nopt_vs_nano.Fill(genmatch_nano,genmatch_HTT_nopt)
      self.out.h_gm_HTT_stat_vs_nano.Fill(genmatch_nano,genmatch_HTT_stat)
      self.out.h_gm_HTT_vs_HTT_nopt.Fill(genmatch_HTT_nopt,genmatch_HTT)
      self.out.h_gm_HTT_vs_HTT_stat.Fill(genmatch_HTT_stat,genmatch_HTT)
      
      # FILL TREE BRANCHES
      self.out.pt[0]                     = tau.pt
      self.out.eta[0]                    = tau.eta
      self.out.phi[0]                    = tau.phi
      self.out.m[0]                      = tau.mass
      self.out.q[0]                      = tau.charge
      self.out.dm[0]                     = tau.decayMode
      self.out.genmatch[0]               = genmatch_nano # default nanoAOD genmatch
      self.out.genmatch_HTT[0]           = genmatch_HTT
      self.out.genmatch_HTT_nopt[0]      = genmatch_HTT_nopt
      self.out.genmatch_HTT_stat[0]      = genmatch_HTT_stat
      self.out.genmatch_nopt_stat[0]     = genmatch_nopt_stat
      self.out.idDecayMode[0]            = tau.idDecayMode
      self.out.idDecayModeNewDMs[0]      = tau.idDecayModeNewDMs
      self.out.idDeepTau2017v2p1VSe[0]   = tau.idDeepTau2017v2p1VSe
      self.out.idDeepTau2017v2p1VSmu[0]  = tau.idDeepTau2017v2p1VSmu
      self.out.idDeepTau2017v2p1VSjet[0] = tau.idDeepTau2017v2p1VSjet
      self.out.ntau[0]                   = len(taus)
      self.out.nmuon[0]                  = sum(tau.DeltaR(m)>0.5 for m in muons) # remove overlap
      self.out.fill()
    
    return True
    

def genmatch(tau,event,cutpt=True,status=False):
  """HTT-prescribed genmatching for reconstructed taus to generator electrons, muons and taus."""
  # https://twiki.cern.ch/twiki/bin/viewauth/CMS/HiggsToTauTauWorking2016#MC_Matching
  genmatch = 0 # gen-match code, default: 0 (or 6) = no match (assumed from jet)
  dRmin    = 0.2
  ###gmobj    = None # matched object
  
  # FAKE lepton -> tau
  for particle in Collection(event,'GenPart'):
    pid = abs(particle.pdgId)
    if status and particle.status!=1: continue # nanoAOD: status==1 for isDirectPromptTauDecayProduct
    if cutpt and particle.pt<8: continue # nanoAOD: no pT cut used
    if pid not in [11,13]: continue
    dR = tau.DeltaR(particle)
    if dR<dRmin:
      # https://cms-nanoaod-integration.web.cern.ch/integration/master-102X/mc102X_doc.html#GenPart
      if hasbit(particle.statusFlags,0): # isPrompt
        if   pid==11: genmatch = 1; dRmin = dR; ###gmobj = particle
        elif pid==13: genmatch = 2; dRmin = dR; ###gmobj = particle
      elif hasbit(particle.statusFlags,5): # isDirectPromptTauDecayProduct
        if   pid==11: genmatch = 3; dRmin = dR; ###gmobj = particle
        elif pid==13: genmatch = 4; dRmin = dR; ###gmobj = particle
  
  # REAL (visible system of the) tau leptons
  # Gen-tau jet, rebuilt from sum of 4-momenta of visible gen tau decay products, excluding electrons and muons
  for gentau in Collection(event,'GenVisTau'):
    if cutpt and gentau.pt<15: continue
    dR = tau.DeltaR(gentau)
    if dR<dRmin:
      dRmin = dR
      genmatch = 5
      ###gmobj = gentau
  
  return genmatch ###, gmobj
  

class TreeProducerGenMatcher(TreeProducer):
  
  def __init__(self, filename, module, **kwargs):
    """Class to create and prepare a custom output file & tree."""
    super(TreeProducerGenMatcher,self).__init__(filename,module,**kwargs)
    
    # ONLY JOB (no hadd)
    self.localjob = bool(re.search(r"(-\d+|[^\d])$",filename.replace(".root","")))
    self.onlyjob = self.localjob or bool(re.search(r"_0$",filename.replace(".root","")))
    print ">>> filename = %r"%(filename)
    print ">>> localjob = %r"%(self.localjob)
    print ">>> onlyjob  = %r"%(self.onlyjob)
    
    # CUTFLOW
    self.cutflow.addcut('none', "no cut" )
    self.cutflow.addcut('tau',  "tau"    )
    self.cutflow.addcut('taus', "#geq2 taus" )
    self.cutflow.addcut('muon', "muon" )
    
    # PRE-MADE HISTOGRAMS
    bins = (7,0,7,7,0,7)
    self.h_gm_HTT_vs_nano      = TH2D('h_gm_HTT_vs_nano',     ";Tau gen-match nanoAOD;Tau gen-match HTT;Taus",*bins)
    self.h_gm_HTT_nopt_vs_nano = TH2D('h_gm_HTT_nopt_vs_nano',";Tau gen-match nanoAOD;Tau gen-match HTT (no pT cut);Taus",*bins)
    self.h_gm_HTT_stat_vs_nano = TH2D('h_gm_HTT_stat_vs_nano',";Tau gen-match nanoAOD;Tau gen-match HTT (status=1);Taus",*bins)
    self.h_gm_HTT_vs_HTT_nopt  = TH2D('h_gm_HTT_vs_HTT_nopt', ";Tau gen-match HTT (no pT cut);Tau gen-match HTT;Taus",*bins)
    self.h_gm_HTT_vs_HTT_stat  = TH2D('h_gm_HTT_vs_HTT_stat', ";Tau gen-match HTT (status=1);Tau gen-match HTT;Taus",*bins)
    self.hists = [
      self.h_gm_HTT_vs_nano,
      self.h_gm_HTT_nopt_vs_nano,self.h_gm_HTT_stat_vs_nano,
      self.h_gm_HTT_vs_HTT_nopt,self.h_gm_HTT_vs_HTT_stat,
    ]
    
    # TREE BRANCHES
    self.addBranch('pt',                     'f')
    self.addBranch('eta',                    'f')
    self.addBranch('phi',                    'f')
    self.addBranch('m',                      'f')
    self.addBranch('q',                      'f', title="Charge")
    self.addBranch('dm',                     'i')
    self.addBranch('genmatch',               'i', title="gen-match, default nanoAOD (Tau_genPartFlav)")
    self.addBranch('genmatch_HTT',           'i', title="gen-match, HTT-prescription, incl. pT cuts")
    self.addBranch('genmatch_HTT_nopt',      'i', title="gen-match, HTT-prescription, no pT cuts")
    self.addBranch('genmatch_HTT_stat',      'i', title="gen-match, HTT-prescription, status=1 gen leptons")
    self.addBranch('genmatch_nopt_stat',     'i', title="gen-match, no pT cuts, status=1 gen leptons")
    self.addBranch('idDecayMode',            '?', title="oldDecayModeFinding")
    self.addBranch('idDecayModeNewDMs',      '?', title="newDecayModeFinding")
    self.addBranch('idDeepTau2017v2p1VSe',   'i')
    self.addBranch('idDeepTau2017v2p1VSmu',  'i')
    self.addBranch('idDeepTau2017v2p1VSjet', 'i')
    self.addBranch('ntau',                   'i', title="number of selected tau candidates in this event")
    self.addBranch('nmuon',                  'i', title="number of selected muon candidates in this event")
    ###self.addBranch('genpt',                  'f', title="pt of gen-matched object")
    ###self.addBranch('genid',                  'f', title="id of gen-matched object")
    ###self.addBranch('genstatus',              'f', title="status of gen-matched object")
    
  def endJob(self):
    """Write and close files after the job ends."""
    
    # PREPARE HISTOGRAMS
    self.outfile.cd()
    self.hnorms = [ ] # store new histograms before writing
    for hist in self.hists:
      setbinlabels(hist)
      hist.SetMarkerColor(kRed)
      hist.SetMarkerSize(1.5)
      hist.GetXaxis().SetLabelSize(0.058)
      hist.GetYaxis().SetLabelSize(0.058)
      hist.GetXaxis().SetLabelOffset(0.003)
      hist.GetYaxis().SetLabelOffset(0.002)
      hist.GetXaxis().SetTitleSize(0.048)
      hist.GetYaxis().SetTitleSize(0.048)
      hist.GetZaxis().SetTitleSize(0.048)
      hist.GetZaxis().SetTitle("Taus")
      hist.SetOption('COLZ TEXT22') # preset default draw option
      if self.localjob:
        h_col = normalize(hist,hist.GetName()+"_col",'col') # normalize columns
        h_row = normalize(hist,hist.GetName()+"_row",'row') # normalize rows
        h_col.SetDirectory(self.outfile) # ensure write to ouput file
        h_row.SetDirectory(self.outfile) # ensure write to ouput file
        self.hnorms.append(h_col) # store new histograms before writing
        self.hnorms.append(h_row) # store new histograms before writing
    
    # WRITE
    if self.onlyjob: # only store for first job output
      #gStyle.SetOptTitle(False) # don't make title on top of histogram
      gStyle.SetOptStat(False)  # don't make stat. box
      gStyle.SetPaintTextFormat('d') # integer (events)
      gStyle.Write("style_evts")
      gStyle.SetPaintTextFormat('.1f') # percentage (fraction)
      gStyle.Write("style_frac")
    super(TreeProducerGenMatcher,self).endJob()
    

def setbinlabels(hist):
  """Set bin labels and check under-/overflow for hidden entries."""
  nxbins = hist.GetXaxis().GetNbins()
  nybins = hist.GetYaxis().GetNbins()
  for ix in range(1,nxbins+1): # loop over columns
    hist.GetXaxis().SetBinLabel(ix,str(ix-1)) # set alphanumerical bin label
    if hist.GetBinContent(ix,0)!=0: # check underflow
      print ">>> WARNING!!! Underflow in (ix,0)=(%s,0) of %r"%(ix,hist.GetName())
    if hist.GetBinContent(ix,nybins+1)!=0: # check overflow
      print ">>> WARNING!!! Overflow in (ix,nybins+1)=(%s,%s) of %r"%(ix,nybins+1,hist.GetName())
  for iy in range(1,nybins+1): # loop over rows
    hist.GetYaxis().SetBinLabel(iy,str(iy-1)) # set alphanumerical bin label
    if hist.GetBinContent(0,iy)!=0: # check underflow
      print ">>> WARNING!!! Underflow in (0,iy)=(0,%s) of %r"%(iy,hist.GetName())
    if hist.GetBinContent(nxbins+1,iy)!=0: # check overflow
      print ">>> WARNING!!! Overflow in (nxbins+1,iy)=(%s,%s) of %r"%(nxbins+1,iy,hist.GetName())
  hist.GetXaxis().SetNdivisions(10)
  hist.GetYaxis().SetNdivisions(10)
  return hist
  

def normalize(hist,hname=None,direction=None):
  """Normalize rows (row=True) or columns (row=False) of 2D histogram."""
  if hname: # create new histogram
    hist = hist.Clone(hname)
  nxbins = hist.GetXaxis().GetNbins()
  nybins = hist.GetYaxis().GetNbins()
  hist.SetMarkerSize(2) # draw with "COLZ TEXT"
  hist.SetTitle("Normalized columns")
  hist.SetOption('COLZ TEXT') # preset default draw option
  if not direction or 'all' in direction: # default
    hist.GetZaxis().SetTitle("Fraction of #kern[-0.3]{#tau_{#lower[-0.25]{h}}} [%]")
    ntot = hist.Integral() # sum of all entries inside bin range
    if ntot>0:
      for ix in range(1,nxbins+1):
        for iy in range(1,nybins+1):
          frac = 100.0*hist.GetBinContent(ix,iy)/ntot # fraction of all entries
          hist.SetBinContent(ix,iy,frac) # overwrite number of entries with fraction
    else:
      print ">>> normalize: Cannot normalize: ntot=%s"%(ntot)
  elif 'row' in direction:
    hist.GetZaxis().SetTitle("Row fraction [%]")
    for iy in range(1,nybins+1): # loop over rows
      ntot = sum(hist.GetBinContent(ix,iy) for ix in range(1,nxbins+1)) # sum row at iy
      if ntot<=0: continue
      for ix in range(1,nxbins+1): # normalize rows
        frac = 100.0*hist.GetBinContent(ix,iy)/ntot # fraction of column
        hist.SetBinContent(ix,iy,frac) # overwrite number of entries with fraction
  else: # 'col' in direction
    hist.GetZaxis().SetTitle("Column fraction [%]")
    for ix in range(1,nxbins+1): # loop over columns
      ntot = sum(hist.GetBinContent(ix,iy) for iy in range(1,nybins+1)) # sum column at ix
      if ntot<=0: continue
      for iy in range(1,nybins+1): # normalize rows
        frac = 100.0*hist.GetBinContent(ix,iy)/ntot # fraction of column
        hist.SetBinContent(ix,iy,frac) # overwrite number of entries with fraction
  return hist
  

def formatvar(var):
  """Help function to construct variable (file) name & title."""
  vtitle = "Tau gen-match "
  if any(s in var for s in ['HTT','_nopt_stat']):
    vname   = var.replace('genmatch_','') # for file names
    vtitle += vname.replace('_',' ').replace('nopt','(no p_{#kern[-0.7]{#lower[-0.25]{T}}} cut)').replace('stat','(status=1)').replace(') (',', ')
    return vname, vtitle
  return 'nano', vtitle+'nanoAOD' # default
  

# QUICK PLOTTING SCRIPT
if __name__ == '__main__':
  from ROOT import gROOT, TFile, TCanvas, TLatex
  from argparse import ArgumentParser
  gROOT.SetBatch(True)      # don't open GUI windows
  gStyle.SetOptTitle(False) # don't make title on top of histogram
  gStyle.SetOptStat(False)  # don't make stat. box
  gStyle.SetPaintTextFormat('.2f') # integer (events)
  description = """Make histograms from output file."""
  parser = ArgumentParser(prog="GenMatcher",description=description,epilog="Good luck!")
  parser.add_argument('file', help="final (hadd'ed) ROOT file")
  parser.add_argument('-t',"--tag", default="", help="extra tag for output file")
  args = parser.parse_args()
  file = TFile.Open(args.file)
  hists = [ ] # 2D histograms to plot
  
  # GET PRE-MADE HISTOGRAMS
  hnames = [
    #'h_gm_HTT_vs_nano','h_gm_HTT_nopt_vs_nano', 'h_gm_HTT_stat_vs_nano',
    #'h_gm_HTT_vs_HTT_nopt', 'h_gm_HTT_vs_HTT_stat'
  ]
  print ">>> Retrieve histograms..."
  for hname in hnames:
    hist = file.Get(hname)
    hist.SetTitle("pt>20 GeV, VVVLoose VSjet, VVVLoose VSe, VLoose VSmu")
    if hist:
      hists.append(hist)
    else:
      print ">>> WARNING! Could not find histogram %r! Ignoring..."%(hname)
  
  # DRAW NEW HISTOGRAMS
  selections = [
    ("pt>20 GeV, VVVLoose VSjet, VVVLoose VSe, VLoose VSmu","pt>20 && idDeepTau2017v2p1VSjet>=1 && idDeepTau2017v2p1VSe>=1 && idDeepTau2017v2p1VSmu>=1"),
    ("pt>30 GeV, VVVLoose VSjet, VVVLoose VSe, VLoose VSmu","pt>30 && idDeepTau2017v2p1VSjet>=1 && idDeepTau2017v2p1VSe>=1 && idDeepTau2017v2p1VSmu>=1"),
    ("pt>20 GeV, Medium VSjet, VVLoose VSe, Tight VSmu","pt>20 && idDeepTau2017v2p1VSjet>=16 && idDeepTau2017v2p1VSe>=2 && idDeepTau2017v2p1VSmu>=8"),
    ("pt>30 GeV, Medium VSjet, VVLoose VSe, Tight VSmu","pt>30 && idDeepTau2017v2p1VSjet>=16 && idDeepTau2017v2p1VSe>=2 && idDeepTau2017v2p1VSmu>=8"),
    ("pt>20 GeV, Tight VSjet, VVLoose VSe, Tight VSmu", "pt>20 && idDeepTau2017v2p1VSjet>=32 && idDeepTau2017v2p1VSe>=2 && idDeepTau2017v2p1VSmu>=8"),
    ("pt>30 GeV, Tight VSjet, VVLoose VSe, Tight VSmu", "pt>30 && idDeepTau2017v2p1VSjet>=32 && idDeepTau2017v2p1VSe>=2 && idDeepTau2017v2p1VSmu>=8"),
    ("pt>20 GeV, Tight VSjet, VVLoose VSe, Tight VSmu, #geq1#mu", "pt>20 && idDeepTau2017v2p1VSjet>=32 && idDeepTau2017v2p1VSe>=2 && idDeepTau2017v2p1VSmu>=8 && nmuon>=1"),
    ("pt>30 GeV, Tight VSjet, VVLoose VSe, Tight VSmu, #geq1#mu", "pt>30 && idDeepTau2017v2p1VSjet>=32 && idDeepTau2017v2p1VSe>=2 && idDeepTau2017v2p1VSmu>=8 && nmuon>=1"),
  ]
  tree = file.Get('tree')
  for stitle, sstring in selections:
    sname = stitle.replace(' ','').replace(',','-').replace('>','gt').replace('#','').replace('GeV','')
    print ">>> Drawing %r..."%(stitle) #,sstring)
    vars = [ # (xvar, yvar)
      ('genmatch',    'genmatch_HTT'),
      ('genmatch',    'genmatch_HTT_nopt'),
      ('genmatch',    'genmatch_nopt_stat'),
      ('genmatch_HTT','genmatch_HTT_nopt'),
    ]
    for xvar, yvar in vars:
      xname, xtitle = formatvar(xvar)
      yname, ytitle = formatvar(yvar)
      hname = "h_gm_%s_vs_%s_%s"%(yname,xname,sname)
      title = "%s;%s;%s;Taus"%(stitle,xtitle,ytitle)
      dcmd  = "%s:%s >> %s"%(yvar,xvar,hname)
      hist  = TH2D(hname,title,7,0,7,7,0,7)
      #hist.SetDirectory(0)
      print ">>>   tree.Draw(%r,%r,'gOff')"%(dcmd,sstring)
      out   = tree.Draw(dcmd,sstring,'gOff')
      print ">>>   %10s taus passed"%(out)
      hists.append(hist)
  
  # PLOT HISTOGRAMS
  print ">>> Plotting..."
  for hist in hists:
    if not hist:
      print ">>> WARNING!!! Empty hist %r! Ignoring..."%(hist)
      continue
    hname  = hist.GetName()
    htitle = hist.GetTitle()
    setbinlabels(hist)
    hist.GetXaxis().SetLabelSize(0.075)
    hist.GetYaxis().SetLabelSize(0.075)
    hist.GetZaxis().SetLabelSize(0.046)
    hist.GetXaxis().SetTitleSize(0.054)
    hist.GetYaxis().SetTitleSize(0.054)
    hist.GetZaxis().SetTitleSize(0.054)
    hist.GetXaxis().SetTitleOffset(0.95)
    hist.GetYaxis().SetTitleOffset(0.80)
    hist.GetZaxis().SetTitleOffset(0.95)
    hist.GetXaxis().SetLabelOffset(0.005)
    hist.GetYaxis().SetLabelOffset(0.004)
    hist.SetMarkerColor(kRed)
    hist.SetMarkerSize(1.5)
    hist.SetOption('COLZ TEXT22') # preset default draw option
    for direction in ['all','row','col']: # normalize row or columns
      pname = "%s_%s%s"%(hname.replace("h_gm","genmatch"),direction,args.tag)
      hnorm = normalize(hist,pname,direction) # create new normalized histogram
      canvas = TCanvas('canvas','canvas',100,100,800,600)
      canvas.SetMargin(0.09,0.15,0.11,0.02) # LRBT
      hnorm.SetMaximum(100)
      hnorm.Draw('COLZ TEXT')
      if htitle:
        latex = TLatex()
        latex.SetTextSize(0.045)
        latex.SetTextAlign(13)
        latex.SetTextFont(42)
        #latex.SetNDC(True)
        latex.DrawLatex(0.2,6.8,htitle.replace('pt',"p_{#lower[-0.25]{T}}"))
      canvas.SaveAs(pname+".png")
      canvas.SaveAs(pname+".pdf")
      canvas.Close()
  file.Close()
  print ">>> Done."
  
