#! /usr/bin/env python
# Author: Izaak Neutelings (June 2022)
# Description: Compare distributions in GENSIM tuples to test stitching
# Sources:
#   https://twiki.cern.ch/twiki/bin/viewauth/CMS/MCStitching
#   https://github.com/IzaakWN/cmssw/blob/addDYToHepMCFilter/GeneratorInterface/Core/src/EmbeddingHepMCFilter.cc
# Instructions
#   cd ../PicoProducer/utils
#   ./convertGENSIM.py GENSIM_*.root -o GENSIM_converted.root
#   cd ../../Plotter/
#   ./plot_GENSIM.py
import os
import TauFW.Plotter.plot.Plot as _Plot
from TauFW.Plotter.plot.Plot import Plot, deletehist
from TauFW.Plotter.plot.Plot import LOG as PLOG
from TauFW.Plotter.sample.utils import LOG, STYLE, ensuredir, ensurelist, ensureTFile,\
                                       setera, Sel, Var
from ROOT import TChain

class Sample:
  """Container class for sample files."""
  
  def __init__(self,name,title,fnames,tree=True,tname='event',
               data=False,cut=None,nfilemax=-1,scale=1,verb=0):
    fnames = ensurelist(fnames)
    for i, fname in enumerate(fnames): # expand glob patterns
      if any(c in fname for c in ['*','[',']']):
        if verb>=2:
          print ">>> Sample.__init__: Expanding %r..."%(fname)
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
      print ">>> Sample %r (%r):"%(self.name,self.title)
      for fname in fnames:
        print ">>>   %s"%(fname)
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
    for fname, file in self.files.iteritems():
      if file:
        if verb>=1:
          print ">>> Sample.close: Closing %s..."%(file.GetPath())
        file.Close()
    self.files = { } # reset
  
  def gettree(self,tname='Events',verb=0):
    if self.tree:
      return self.tree
    chain = TChain(tname)
    if verb>=1:
      print ">>> gettree(%r)"%(tname)
    for fname in self.fnames:
      if verb>=1:
        print ">>>   Adding %s..."%(fname)
      chain.Add(fname)
    self.tree = chain
    if verb+2>=2:
      print ">>> Sample.gettree: Number of entries: %5s over %s files for %s"%(self.tree.GetEntries(),len(self.fnames),self.name)
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
      print ">>> %s.Draw(%r,%r)"%(tree.GetName(),varexp,selection)
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
        print ">>> Sample.gethists:   %r, %r"%(varexp,selection)
    out = self.tree.MultiDraw(varexps,selection,'HIST',hists=hists,verbosity=verb)
    if self.scale!=1:
      for hist in hists:
        #print ">>> Sample.gethists:   Scaling histograms %s by %s"%(hname,self.scale)
        hist.Scale(self.scale)
    return hists
  

def compare_mutau(tag="",**kwargs):
  """Compare list of samples."""
  LOG.header("compare_mutau",pre=">>>")
  outdir   = kwargs.get('outdir', "plots/GENSIM" )
  norms    = kwargs.get('norm',   [False,True]   )
  #entries  = kwargs.get('entries', [str(e) for e in eras] ) # for legend
  exts     = kwargs.get('ext',    ['png']        ) # figure file extensions
  verb     = kwargs.get('verb',   0              )
  ensuredir(outdir)
  norms    = ensurelist(norms)
  #setera(era) # set era for plot style and lumi-xsec normalization
  
  # SAMPLE SETS
  eosdir = "/eos/user/i/ineuteli/GENSIM/"
  sname  = "DYJetsToTauTauToMuTauh"
  header = "DYJetsToTauTauToMuTauh"
  ratio  = 2 # denominator w.r.t. patch
  sampleset = [
    Sample("buggy","10.6.19 (buggy FSR)",       eosdir+"GENSIM_converted_buggy.root",   scale=1,verb=verb), # 2e6
    Sample("patch","10.6.30_patch1",            eosdir+"GENSIM_converted_patch.root",   scale=1,verb=verb), # 2e6
    #Sample("debug","10.6.30_patch1, incl. DY",  eosdir+"GENSIM_converted_debug.root",   scale=1,verb=verb), # 2e6
    Sample("debug","10.6.30_patch1, incl. DY",  eosdir+"GENSIM_converted_debug2.root",  scale=1,verb=verb), # 2e6
    #Sample("nocut","10.6.30_patch1, no cuts",   eosdir+"GENSIM_converted_noptcut.root", scale=4,verb=verb), # 5e5 # redundant
    Sample("nofil","10.6.30_patch1, no filter", eosdir+"GENSIM_converted_nofilter.root",scale=4,verb=verb), # 5e5
  ]
  
  hnames = [ # ready-made histograms
    ('h_nmoth',          "Number of Z bosons"),
    ('h_ntau_all',       "Number of gen. #tau leptons (incl. copies)"),
    ('h_ntau_all2',      "Number of gen. #tau leptons (incl. copies)"),
    ('h_ntau_copy',      "Number of gen. #tau copies"),
    ('h_ntau_copy2',     "Number of gen. #tau copies"),
    ('h_ntau_fromZ',     "Number of gen. #tau leptons from Z -> #tau#tau"),
    ('h_ntau_fromZ2',    "Number of gen. #tau leptons from Z -> #tau#tau"),
    #('h_ntau_fromHard',  "Number of gen. #tau leptons from hard process" ),
    ('h_ntau_hard',      "Number of gen. #taus from hard process" ),
    ('h_ntau_prompt',    "Number of prompt gen. #taus"),
    ('h_ntau_brem',      "Number of gen. #tau leptons that radiate"),
    ('h_nelec_tau',      "Number of gen. electrons from tau decay"),
    ('h_nmuon_tau',      "Number of gen. muons from tau decay"),
    ('h_nmuon_tau2',     "Number of gen. muons from tau decay"),
    ('h_tau_brem_q',     "Gen. #tau lepton (that radiate) charge"),
    ('h_muon_tau_q',     "Gen. muons (from #tau decay) charge"),
    ('h_muon_tau_q2',    "Gen. muons (from #tau decay) charge"),
    ('h_muon_tau_brem_q',"Gen. muons (from radiating #tau) charge"),
  ]
  
  # SELECTIONS
  selections = [
    #Sel('nocuts', "", ),
    Sel('mutau', "ntau_hard>=2 && nmuon_tau>=1 && ntauh_hard>=1" ),
    Sel('mutau, pt > 16 GeV, |eta| < 2.5', "ntau_hard>=2 && nmuon_tau>=1 && ntauh_hard>=1 && muon_pt>16 && tauh_ptvis>16 && abs(muon_eta)<2.5 && abs(tauh_etavis)<2.5" ),
    Sel('mutau, pt > 18 GeV, |eta| < 2.5', "ntau_hard>=2 && nmuon_tau>=1 && ntauh_hard>=1 && muon_pt>18 && tauh_ptvis>18 && abs(muon_eta)<2.5 && abs(tauh_etavis)<2.5" ),
    #Sel('mutau, pt > 20 GeV, |eta| < 2.5', "ntau_hard>=2 && nmuon_tau>=1 && ntauh_hard>=1 && muon_pt>20 && tauh_ptvis>20 && abs(muon_eta)<2.5 && abs(tauh_etavis)<2.5" ),
    #Sel('mutau, pt > 18 GeV, |eta| < 2.5, from radiating tau', "ntau_hard>=2 && nmuon_tau>=1 && ntauh_hard>=1 && muon_pt>18 && tauh_ptvis>18 && abs(muon_eta)<2.5 && abs(tauh_etavis)<2.5 && muon_tau_brem", only=['muon'] ),
    #Sel('gen. mutaufilter', "mutaufilter", fname="baseline-genfilter"),
  ]
  
  # VARIABLES
  ptbins  = range(0,40,4) + range(40,60,5) + range(60,100,10) + [100,120,140]
  #ptbins  = range(10,50,2) + range(50,70,4) + range(70,100,10) + [100,120,140]
  Zptbins = range(0,40,4) + range(40,60,5) + range(60,100,10) + range(100,140,20) + [140,170,200]
  #Zptbins = range(0,60,3) + range(60,100,10) + range(100,140,20) + [140,170,200]
  Zmbins  = [0,50,70,76,81,85,88,91,94,97,101,106,112,130,150]
  qlabels = ['','#minus1','','#plus1','','','']
  variables = [
    Var('nmoth',       5, 0,   5, "Number of generator Z bosons"),
    Var('nmuon',       5, 0,   5, "Number of generator muons"),
    Var('nmuon_tau',   5, 0,   5, "Number of generator muons from tau decay"),
    Var('ntau',        8, 0,   8, "Number of generator tau leptons"),
    Var('ntau_all',   12, 0,  12, "Number of generator tau leptons (incl. copies)",logy=True,logyrange=3.8),
    Var('ntau_hard',   5, 0,   5, "Number of generator tau leptons from hard process"),
    Var('ntau_brem',   5, 0,   5, "Number of radiating tau leptons"),
    #Var('ntauh',       5, 0,   5, "Number of generator tauh "),
    Var('ntauh_hard'  ,5, 0,   5, "Number of generator tauh from hard process"),
    Var('muon_pt',    30,10, 130, "Muon pt", fname="$VAR" ),
    Var('muon_pt',        ptbins, "Muon pt", fname="$VAR_coarse" ),
    Var('muon_eta',   20,-3,   5, "Muon eta" ),
    Var('muon_q',      7,-2,   5, "Muon charge",labels=qlabels,ymarg=1.6,pos='y=0.96'),
    Var('tauh_pt',    30,10, 130, "tau_h pt", fname="$VAR" ),
    Var('tauh_pt',        ptbins, "tau_h pt", fname="$VAR_coarse" ),
    Var('tauh_ptvis', 30,10, 130, "Visible tau_h pt", fname="$VAR" ),
    Var('tauh_ptvis',     ptbins, "Visible tau_h pt", fname="$VAR_coarse" ),
    Var('tauh_eta',   20,-3,   5, "tau_h eta" ),
    Var('tauh_etavis',20,-3,   5, "Visible tau_h eta" ),
    Var('tauh_q',      7,-2,   5, "tau_h charge",labels=qlabels,ymarg=1.6,pos='y=0.96'),
    Var('tau1_pt',    30,10, 130, "Leading tau pt", fname="$VAR" ),
    Var('tau1_pt',        ptbins, "Leading tau pt", fname="$VAR_coarse" ),
    Var('tau1_eta',   20,-3,   5, "Leading tau eta" ),
    Var('tau2_pt',    30,10, 130, "Subleading tau pt", fname="$VAR" ),
    Var('tau2_pt',        ptbins, "Subleading tau pt", fname="$VAR_coarse" ),
    Var('tau2_eta',   20,-3,   5, "Subleading tau eta" ),
    Var('moth_pid',   50,-25, 25, "Mother PDG ID", pos='Ly=0.85',fname="$VAR_log",logy=True,logyrange=4),
    #Var('moth_m',     50, 0, 150, "Gen. Z boson mass", pos='Ly=0.83'),
    #Var('moth_m',     50, 0, 150, "Gen. Z boson mass", pos='Ly=0.83', fname="$VAR_log",logy=True,logyrange=3.8),
    Var('moth_m',     25, 0, 150, "Gen. Z boson mass", pos='Ly=0.83', fname="$VAR_coarse",logy=True,logyrange=3.8),
    Var('moth_m',         Zmbins, "Gen. Z boson mass", pos='Ly=0.83', fname="$VAR_rebin",logy=True,logyrange=3.8),
    #Var('m_ll',       50, 0, 150, "Gen. Z boson mass", pos='Ly=0.83'),
    #Var('m_ll',       50, 0, 150, "Gen. Z boson mass", pos='Ly=0.83', fname="$VAR_log",logy=True,logyrange=3.8),
    Var('m_ll',       25, 0, 150, "Gen. Z boson mass", pos='Ly=0.83', fname="$VAR_coarse",logy=True,logyrange=3.8),
    Var('m_ll',           Zmbins, "Gen. Z boson mass", pos='Ly=0.83', fname="$VAR_rebin",logy=True,logyrange=3.8),
    #Var('moth_pt',    50, 0, 150, "Gen. Z boson pt", pos='y=0.78'),
    #Var('moth_pt',    50, 0, 150, "Gen. Z boson pt", pos='y=0.78',fname="$VAR_log",logy=True,logyrange=3.2),
    Var('moth_pt',    20, 0, 160, "Gen. Z boson pt", pos='y=0.78',fname="$VAR_coarse",logy=True,logyrange=3.2),
    Var('moth_pt',       Zptbins, "Gen. Z boson pt", pos='y=0.78',fname="$VAR_rebin",logy=True,logyrange=3.2),
    #Var('pt_ll',      50, 0, 150, "Gen. Z boson pt", pos='y=0.78'),
    #Var('pt_ll',      50, 0, 150, "Gen. Z boson pt", pos='y=0.78',fname="$VAR_log",logy=True,logyrange=3.2),
    Var('pt_ll',      20, 0, 160, "Gen. Z boson pt", pos='y=0.78',fname="$VAR_coarse",logy=True,logyrange=3.2),
    Var('pt_ll',         Zptbins, "Gen. Z boson pt", pos='y=0.78',fname="$VAR_rebin",logy=True,logyrange=3.2),
  ]
  
  # PLOT from pre-made histograms
  for hname, xtitle in hnames:
    text  = xtitle.replace('tau',"tau_{#lower[-0.2]{h}}")
    fname = "%s/compare_GENSIM_%s%s$TAG"%(outdir,hname,tag)
    hists = [ ]
    for sample in sampleset:
      if verb>=1:
        print ">>> compare_mutau: Getting histogram from %s"%(sample.name)
      hist = sample.gethist_from_file(hname,sample.title,verb=verb)
      hists.append(hist)
    for norm in norms:
      ntag = '_norm' if norm else "_lumi"
      logy = False
      if '_q' in hname:
        pos     = 'L'
        lsize   = _Plot._lsize*1.1
        labels  = ['','#minus1','','#plus1',''] # 5,-2,3
        ymargin = 1.35 if 'h_muon_tau_brem_q' in hname else 1.52
      else:
        pos     = None
        lsize   = _Plot._lsize
        labels  = None
        ymargin = None
      if any(n in hname for n in ['ntau_all','ntau_copy']):
        logy    = True
      style = 1 #[1,1,2,1,1,1]
      plot  = Plot(xtitle,hists,norm=norm,clone=True)
      plot.draw(ratio=ratio,style=style,xlabelsize=lsize,
                binlabels=labels,ymargin=ymargin,logy=logy)
      plot.drawlegend(pos,header=None) #,entries=entries)
      plot.drawtext(header)
      plot.saveas(fname,ext=exts,tag=ntag) #,'pdf'
      plot.close()
    deletehist(hists)
  for sample in sampleset:
    sample.closefiles() # close files
  print ">>> "
  
  # PLOT from trees
  for selection in selections:
    print ">>> %s: %r"%(selection,selection.selection)
    hdict = { }
    text  = selection.title.replace('tau',"tau_{#lower[-0.2]{h}}")
    fname = "%s/compare_GENSIM_$VAR_%s_%s%s$TAG"%(outdir,sname,selection.filename,tag)
    vars  = [v for v in variables if v.plotfor(selection) and selection.plotfor(v)]
    for sample in sampleset:
      if verb>=1:
        print ">>> compare_mutau: Getting histogram from %s"%(sample.name)
      hists = sample.gethists(vars,selection,verb=verb)
      for variable, hist in zip(variables,hists):
        hdict.setdefault(variable,[ ]).append(hist)
    for variable, hists in hdict.iteritems():
      for norm in norms:
        ntag  = '_norm' if norm else "_lumi"
        lsize = _Plot._lsize*(1.5 if variable.name.endswith('_q') else 1)
        style = 1 #[1,1,2,1,1,1]
        plot  = Plot(variable,hists,norm=norm,clone=True)
        plot.draw(ratio=ratio,style=style,xlabelsize=lsize,rrange=0.62)
        plot.drawlegend(header=header) #,entries=entries)
        plot.drawtext(text)
        plot.saveas(fname,ext=exts,tag=ntag) #,'pdf'
        plot.close()
      deletehist(hists)
  print ">>> "
  

def main(args):
  fname    = None #"$PICODIR/$SAMPLE_$CHANNEL.root" # fname pattern
  parallel  = args.parallel
  varfilter = args.varfilter
  selfilter = args.selfilter
  pdf       = args.pdf
  outdir    = "plots/GENSIM"
  tag       = args.tag
  verbosity = args.verbosity
  if pdf:
    exts = ['png','pdf']
  
  compare_mutau(tag=tag,outdir=outdir,ext=exts,verb=verbosity)
  

if __name__ == "__main__":
  import sys
  from argparse import ArgumentParser
  argv = sys.argv
  description = """Simple plotting script to compare distributions in pico analysis tuples"""
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
  print "\n>>> Done."
  
