#! /usr/bin/env python
# Author: Izaak Neutelings (July 2021)
# Description: Quickly compare distributions in NanoAOD samples
import os, glob, re
from TauFW.Plotter.sample.utils import LOG, STYLE, setera, ensuredir, ensurelist, Var, Sel, repkey
import TauFW.Plotter.plot.Plot as PLOT
from TauFW.Plotter.plot.Plot import Plot, deletehist, _lcolors
from TauFW.Plotter.plot.Plot import LOG as PLOG
from TauFW.Plotter.plot.MultiDraw import MultiDraw
from TauFW.Plotter.plot.MultiThread import MultiProcessor
from ROOT import TChain, TFile
#from collections import namedtuple
#Sample = namedtuple('Sample',['name','title','files'])


class Sample:
  """Container class for sample files."""
  
  def __init__(self,name,title,fnames,tree=True,tname='Events',data=False,cut=None,nfilemax=-1,verb=0):
    fnames = ensurelist(fnames)
    for i, fname in enumerate(fnames): # expand glob patterns
      if any(c in fname for c in ['*','[',']']):
        if verb>=2:
          print ">>> Sample.__init__: expanding %r..."%(fname)
        fnames.insert(i,glob.glob(fname))
    if nfilemax>0 and len(fnames)>nfilemax:
      fnames    = fnames[:nfilemax]
    self.name   = name
    self.title  = title
    self.fnames = fnames
    self.tree   = None
    self.cut    = cut # extra cut
    self.isdata = data
    if verb>=1:
      print ">>> Sample %r (%r):"%(self.name,self.title)
      for fname in fnames:
        print ">>>   %s"%(fname)
    if tree:
      self.gettree(tname,verb=verb)
  
  def gettree(self,tname='Events',verb=0):
    if self.tree: return
    chain = TChain(tname)
    if verb>=1:
      print ">>> gettree(%r)"%(tname)
    for fname in self.fnames:
      if verb>=1:
        print ">>>   adding %s..."%(fname)
      chain.Add(fname)
    self.tree = chain
    return chain
  
  def gethist(self,variable,selection,hname,verb=0):
    hname = hname.replace('$VAR',variable.filename).replace('$NAME',self.name)
    hist = variable.gethist(hname,self.title,sumw2=True)
    hist.SetDirectory(0)
    varexp = variable.drawcmd(hname)
    if self.cut:
      selection += " && "+self.cut
    if verb>=1:
      print ">>> %s.Draw(%r,%r)"%(tree.GetName(),varexp,selection)
    out = self.tree.Draw(varexp,selection,'HIST')
    return hist
  
  def gethists(self,variables,selection,hname,verb=0):
    varexps = [ ]
    hists   = [ ]
    if self.cut:
      selection += " && "+self.cut
    for var in variables:
      hname  = hname.replace('$VAR',var.filename).replace('$NAME',self.name)
      hist   = var.gethist(hname,self.title,sumw2=True)
      varexp = var.drawcmd(hname)
      hist.SetDirectory(0)
      hists.append(hist)
      varexps.append(varexp)
      if verb>=2:
        print ">>>   %r, %r"%(varexp,selection)
    out = self.tree.MultiDraw(varexps,selection,'HIST',hists=hists,verbosity=verb)
    return hists
  

def compare_nano(samplesets,tag="",**kwargs):
  """Compare distributions in NanoAOD samples."""
  LOG.header("compare",pre=">>>")
  tname     = kwargs.get('tree',     "Events" )
  colors    = kwargs.get('colors',   None     )
  outdir    = kwargs.get('outdir',   "plots"  )
  parallel  = kwargs.get('parallel', True     ) #and False
  norms     = kwargs.get('norm',     [True]   )
  entries   = kwargs.get('entries',  [ ]      ) # for legendt
  exts      = kwargs.get('exts',     ['png']  ) # figure file extensions
  verbosity = kwargs.get('verb',     0        )
  ensuredir(outdir)
  norms    = ensurelist(norms)
  
  # SELECTIONS
  baseline = "Muon_pt>24 && Tau_pt>20 && Tau_idDeepTau2017v2p1VSjet>=1"
  selections = [
#     Sel('pt(mu) > 24 GeV', "Muon_pt>24", fname="mu"),
#     Sel('pt(mu) > 28 GeV', "Muon_pt>28", fname="mu"),
    Sel('pt(mu) > 24 GeV, pt(tau) > 20 GeV, VVVLoose VSjet', baseline, fname="mutau-VVVLoose"),
    Sel('pt(mu) > 24 GeV, pt(tau) > 20 GeV, VVVLoose VSjet,\n21-25 vertices',
                                                            baseline+" && PV_npvs>20 && PV_npvs<=25", fname="mutau-VVVLoose-npv20to25"),
    Sel('pt(mu) > 24 GeV, pt(tau) > 20 GeV, VVVLoose VSjet,\n26-30 vertices',
                                                            baseline+" && PV_npvs>25 && PV_npvs<=30", fname="mutau-VVVLoose-npv25to30"),
  ]
  
  # GENMATCH SPLIT
  gms = [
    ('realtau',"real #tau_{h}","Tau_genPartFlav==5"),
    #('faketau',"fake #tau_{h}","Tau_genPartFlav<5"),
    ('ltf',    "l #rightarrow #tau_{h}","Tau_genPartFlav>0 && Tau_genPartFlav<5"),
    ('jtf',    "j #rightarrow #tau_{h}","Tau_genPartFlav<=0"),
  ]
  oldselections = selections[:]
  #selections = [ ] # don't run inclusive selections
  for gmname, gmtitle, gmcut in gms:
    for oldsel in oldselections[:]:
      if 'Tau' not in oldsel.selection: continue
      stitle = oldsel.title+", "+gmtitle
      selstr = oldsel.selection+" && "+gmcut
      sfname = oldsel.filename+"_"+gmname.replace(' ','')
      newsel = Sel(stitle,selstr,fname=sfname)
      selections.append(newsel)
  
  # VARIABLES
  variables = [
    Var('PV_npvs', "Number of primary vertices", 40, 0, 80),
    Var('Muon_pfRelIso04_all', "Muon #Delta#beta-corrected relative isolation", 25, 0.00, 10, logy=True,ymin=6e-6),
    Var("log10(max(0.001,Muon_pfRelIso04_all))", "log_{10} muon #Delta#beta-corrected relative isolation",
                                                 16, -2, 2, fname="Muon_pfRelIso04_all_log", logy=True,ymin=6e-6),
    Var('Tau_pt', "Leading tau_h pt", 18, 0, 270, only=['Tau']),
    Var('Tau_decayMode', "tau_h decay mode", 14, 0, 14, logy=True,only=['Tau']),
    Var('Tau_rawIso', "#Delta#beta-corrected tau_h isolation", 30, 0.00, 60, logy=True,ymin=6e-6,only=['Tau']),
    Var('Tau_neutralIso', "Neutral tau_h isolation", 50, 0.00, 100, logy=True,ymin=6e-6,only=['Tau']),
    Var('Tau_chargedIso', "Charged tau_h isolation", 50, 0.00, 100, logy=True,ymin=6e-6,only=['Tau']),
    Var('log10(max(0.001,Tau_rawIso))', "log_{10} #Delta#beta-corrected tau_h isolation",
                                                     28, -3, 4, fname="Tau_rawIso_log", logy=True,ymin=6e-6,only=['Tau']),
    Var('Tau_neutralIso>0.5?log10(Tau_neutralIso):-1', "log_{10} neutral tau_h isolation",
                                                     30, -1, 2, fname="Tau_neutralIso_log", logy=True,ymin=6e-6,only=['Tau']),
    Var('Tau_chargedIso>0.5?log10(Tau_chargedIso):-1', "log_{10} charged tau_h isolation",
                                                     30, -1, 2, fname="Tau_chargedIso_log", logy=True,ymin=6e-6,only=['Tau']),
    Var('Tau_rawDeepTau2017v2p1VSe',   "rawDeepTau2017v2p1VSe",    30, 0.70, 1, fname="$VAR_zoom",logy=True,ymin=8e-4,pos='L;y=0.84',only=['Tau']),
    Var('Tau_rawDeepTau2017v2p1VSmu',  "rawDeepTau2017v2p1VSmu",   20, 0.80, 1, fname="$VAR_zoom",logy=True,ymin=8e-4,pos='L;y=0.84',only=['Tau']),
    Var('Tau_rawDeepTau2017v2p1VSjet', "rawDeepTau2017v2p1VSjet",  40, 0.20, 1, fname="$VAR",     logy=True,ymin=8e-4,pos='L;y=0.84',only=['Tau']),
    Var('Tau_rawDeepTau2017v2p1VSjet', "rawDeepTau2017v2p1VSjet",  20, 0.80, 1, fname="$VAR_zoom",logy=True,ymin=8e-4,pos='L;y=0.84',only=['Tau']),
  ]
  
  # BRANCH STATUS to speed up
  branches = set() # use set to avoid duplicates
  branchexp = re.compile(r"(?<!\w)([A-Z][A-Za-z]+_)\w+")
  for object in selections+variables:
    string  = object.selection if isinstance(object,Sel) else object.name
    matches = branchexp.findall(string)
    if verbosity>=2:
      print ">>> branch matches in %r: '%s'"%(string,"', '".join(set(matches)))
    for match in matches:
      branch = match+'*' # to be on safe side, include all branchs of this type
      branches.add(branch)
  if verbosity>=2:
    print ">>> activating branches: '%s'"%("', '".join(branches))
  for setname, samples in samplesets.items():
    for sample in samples:
      sample.tree.SetBranchStatus('*',0) # deactivate everything
      for branch in branches:
        sample.tree.SetBranchStatus(branch,1) # activate only these
  
  # PLOT
  for setname, samples in samplesets.items():
    print ">>> %s"%(setname)
    header = setname
    if not entries:
      entries = [s.title for s in samples]
    for selection in selections:
      #vars = [v for v in variables if 'Tau' not in v or not selection.contains('Tau')]
      vars = [v for v in variables if v.plotfor(selection)]
      print ">>> %s: %r"%(selection,selection.selection)
      if 'genpart' in selection.selection.lower() and any(s.isdata for s in samples): continue
      hdict = { }
      text  = selection.title
      fname = "%s/compare_nano_$VAR_%s_%s%s$TAG"%(outdir,setname,selection.filename,tag)
      hname = "$VAR_%s_$NAME"%(selection.filename)
      hargs = (vars,selection.selection,hname)
      hkws  = { 'verb': verbosity }
      if parallel: # run in parallel
        processor = MultiProcessor()
        for sample in samples:
          sample.gettree(verb=verbosity)
          processor.start(sample.gethists,hargs,hkws,name=sample.title)
        for process in processor:
          if verbosity>=1:
            print ">>> joining process %r..."%(process.name)
          hists = process.join()
          for var, hist in zip(vars,hists):
            hdict.setdefault(var,[ ]).append(hist)
      else: # run sequentially
        for sample in samples:
          sample.gettree(verb=verbosity)
          hname = "$VAR_$NAME"
          hists = sample.gethists(*hargs,**hkws)
          for var, hist in zip(vars,hists):
            hdict.setdefault(var,[ ]).append(hist)
      for var, hists in hdict.iteritems():
        pos = var.position or "y=0.88"
        for norm in norms:
          ntag = '_norm' if norm else ""
          plot = Plot(var,hists,norm=norm,colors=colors)
          plot.draw(ratio=True,lstyle=1)
          plot.drawlegend(pos,header=header,entries=entries)
          plot.drawtext(text)
          plot.saveas(fname,ext=exts,tag=ntag)
          plot.close(keep=True)
        deletehist(hists)
    print ">>> "
  

def main(args):
  #files     = args.files
  verbosity = args.verbosity
  filters   = args.samples
  vetoes    = args.vetoes
  nfilemax  = args.nfilemax  # maximum number of files
  parallel  = True #and False
  eosurl    = "root://eosuser.cern.ch/"
  dasurl    = "root://xrootd-cms.infn.it/" # DAS, use in Europe & Asia
  #dasurl    = "root://cms-xrd-global.cern.ch/" # DAS, global
  eosdir    = eosurl+"/eos/cms/store/group/phys_tau/TauFW/nano/"
  t3dir     = "/pnfs/psi.ch/cms/trivcat/store/user/ineuteli/samples/tmp/"
  tag       = ""
  
  # FILESET
  #   export EOS_MGM_URL=root://eosuser.cern.ch
  #   eos ls /eos/cms/store/group/phys_tau/TauFW/nano/UL2016_preVFP"
  samplesets = { }
  
  # SINGLE MUON
  files_Run2016G = [
    eosdir+"UL2016_postVFP/SingleMuon/Run2016G-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/029B4A32-6898-A147-8E18-8AF81D34EDB2_skimrejec_0.root",
    eosdir+"UL2016_postVFP/SingleMuon/Run2016G-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/029B4A32-6898-A147-8E18-8AF81D34EDB2_skimrejec_1.root",
    eosdir+"UL2016_postVFP/SingleMuon/Run2016G-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/029B4A32-6898-A147-8E18-8AF81D34EDB2_skimrejec_2.root",
    eosdir+"UL2016_postVFP/SingleMuon/Run2016G-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/029B4A32-6898-A147-8E18-8AF81D34EDB2_skimrejec_3.root",
    eosdir+"UL2016_postVFP/SingleMuon/Run2016G-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/029B4A32-6898-A147-8E18-8AF81D34EDB2_skimrejec_4.root",
    eosdir+"UL2016_postVFP/SingleMuon/Run2016G-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/029B4A32-6898-A147-8E18-8AF81D34EDB2_skimrejec_5.root",
    eosdir+"UL2016_postVFP/SingleMuon/Run2016G-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/029B4A32-6898-A147-8E18-8AF81D34EDB2_skimrejec_6.root",
    eosdir+"UL2016_postVFP/SingleMuon/Run2016G-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/036DA94A-F880-EE43-92C1-17FDABAED302_skimrejec_0.root",
    eosdir+"UL2016_postVFP/SingleMuon/Run2016G-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/036DA94A-F880-EE43-92C1-17FDABAED302_skimrejec_1.root",
    eosdir+"UL2016_postVFP/SingleMuon/Run2016G-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/036DA94A-F880-EE43-92C1-17FDABAED302_skimrejec_2.root",
    eosdir+"UL2016_postVFP/SingleMuon/Run2016G-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/036DA94A-F880-EE43-92C1-17FDABAED302_skimrejec_3.root",
    eosdir+"UL2016_postVFP/SingleMuon/Run2016G-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/036DA94A-F880-EE43-92C1-17FDABAED302_skimrejec_4.root",
    eosdir+"UL2016_postVFP/SingleMuon/Run2016G-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/036DA94A-F880-EE43-92C1-17FDABAED302_skimrejec_5.root",
    eosdir+"UL2016_postVFP/SingleMuon/Run2016G-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/1009F1A4-3C85-CF4F-9C46-D21742B8C761_skimrejec_0.root",
    eosdir+"UL2016_postVFP/SingleMuon/Run2016G-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/1009F1A4-3C85-CF4F-9C46-D21742B8C761_skimrejec_1.root",
    eosdir+"UL2016_postVFP/SingleMuon/Run2016G-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/1009F1A4-3C85-CF4F-9C46-D21742B8C761_skimrejec_2.root",
    eosdir+"UL2016_postVFP/SingleMuon/Run2016G-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/1009F1A4-3C85-CF4F-9C46-D21742B8C761_skimrejec_3.root",
    eosdir+"UL2016_postVFP/SingleMuon/Run2016G-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/1009F1A4-3C85-CF4F-9C46-D21742B8C761_skimrejec_4.root",
    eosdir+"UL2016_postVFP/SingleMuon/Run2016G-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/1009F1A4-3C85-CF4F-9C46-D21742B8C761_skimrejec_5.root",
    eosdir+"UL2016_postVFP/SingleMuon/Run2016G-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/1009F1A4-3C85-CF4F-9C46-D21742B8C761_skimrejec_6.root",
  ]
  files_Run2016H = [
    eosdir+"UL2016_postVFP/SingleMuon/Run2016H-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/008E248E-4BD8-5C44-AF84-B8ABD32A3A16_skimrejec_0.root",
    eosdir+"UL2016_postVFP/SingleMuon/Run2016H-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/008E248E-4BD8-5C44-AF84-B8ABD32A3A16_skimrejec_1.root",
    eosdir+"UL2016_postVFP/SingleMuon/Run2016H-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/008E248E-4BD8-5C44-AF84-B8ABD32A3A16_skimrejec_2.root",
    eosdir+"UL2016_postVFP/SingleMuon/Run2016H-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/008E248E-4BD8-5C44-AF84-B8ABD32A3A16_skimrejec_3.root",
    eosdir+"UL2016_postVFP/SingleMuon/Run2016H-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/008E248E-4BD8-5C44-AF84-B8ABD32A3A16_skimrejec_4.root",
    eosdir+"UL2016_postVFP/SingleMuon/Run2016H-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/008E248E-4BD8-5C44-AF84-B8ABD32A3A16_skimrejec_5.root",
    eosdir+"UL2016_postVFP/SingleMuon/Run2016H-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/008E248E-4BD8-5C44-AF84-B8ABD32A3A16_skimrejec_6.root",
    eosdir+"UL2016_postVFP/SingleMuon/Run2016H-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/008E248E-4BD8-5C44-AF84-B8ABD32A3A16_skimrejec_7.root",
    eosdir+"UL2016_postVFP/SingleMuon/Run2016H-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/008E248E-4BD8-5C44-AF84-B8ABD32A3A16_skimrejec_8.root",
    eosdir+"UL2016_postVFP/SingleMuon/Run2016H-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/019C5BA1-3D7B-7747-BE3D-A09CF37A4ADA_skimrejec_0.root",
    eosdir+"UL2016_postVFP/SingleMuon/Run2016H-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/019C5BA1-3D7B-7747-BE3D-A09CF37A4ADA_skimrejec_1.root",
    eosdir+"UL2016_postVFP/SingleMuon/Run2016H-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/019C5BA1-3D7B-7747-BE3D-A09CF37A4ADA_skimrejec_2.root",
    eosdir+"UL2016_postVFP/SingleMuon/Run2016H-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/019C5BA1-3D7B-7747-BE3D-A09CF37A4ADA_skimrejec_3.root",
    eosdir+"UL2016_postVFP/SingleMuon/Run2016H-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/019C5BA1-3D7B-7747-BE3D-A09CF37A4ADA_skimrejec_4.root",
    eosdir+"UL2016_postVFP/SingleMuon/Run2016H-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/019C5BA1-3D7B-7747-BE3D-A09CF37A4ADA_skimrejec_5.root",
    eosdir+"UL2016_postVFP/SingleMuon/Run2016H-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/019C5BA1-3D7B-7747-BE3D-A09CF37A4ADA_skimrejec_6.root",
    eosdir+"UL2016_postVFP/SingleMuon/Run2016H-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/019C5BA1-3D7B-7747-BE3D-A09CF37A4ADA_skimrejec_7.root",
    eosdir+"UL2016_postVFP/SingleMuon/Run2016H-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/019C5BA1-3D7B-7747-BE3D-A09CF37A4ADA_skimrejec_8.root",
    eosdir+"UL2016_postVFP/SingleMuon/Run2016H-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/019C5BA1-3D7B-7747-BE3D-A09CF37A4ADA_skimrejec_9.root",
    eosdir+"UL2016_postVFP/SingleMuon/Run2016H-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/096A9F8E-3896-A047-A6B4-2DE2B710E353_skimrejec_0.root",
  ]
  samplesets['SingleMuon'] = [
    Sample("SingleMuon_2016_preVFP","UL2016 pre-VFP",[
      eosdir+"UL2016_preVFP/SingleMuon/Run2016C-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/03B4FF22-8E28-D34E-AFF2-663BC77F882C_skimrejec_0.root",
      eosdir+"UL2016_preVFP/SingleMuon/Run2016C-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/03B4FF22-8E28-D34E-AFF2-663BC77F882C_skimrejec_1.root",
      eosdir+"UL2016_preVFP/SingleMuon/Run2016C-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/03B4FF22-8E28-D34E-AFF2-663BC77F882C_skimrejec_2.root",
      eosdir+"UL2016_preVFP/SingleMuon/Run2016C-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/03B4FF22-8E28-D34E-AFF2-663BC77F882C_skimrejec_3.root",
      eosdir+"UL2016_preVFP/SingleMuon/Run2016C-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/03B4FF22-8E28-D34E-AFF2-663BC77F882C_skimrejec_4.root",
      eosdir+"UL2016_preVFP/SingleMuon/Run2016C-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/03B4FF22-8E28-D34E-AFF2-663BC77F882C_skimrejec_5.root",
      eosdir+"UL2016_preVFP/SingleMuon/Run2016B-ver2_HIPM_UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/05F01599-E62C-4A41-B587-0ECCFA09C51B_skimrejec_6.root",
      eosdir+"UL2016_preVFP/SingleMuon/Run2016B-ver2_HIPM_UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/05F01599-E62C-4A41-B587-0ECCFA09C51B_skimrejec_7.root",
      eosdir+"UL2016_preVFP/SingleMuon/Run2016B-ver2_HIPM_UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/05F01599-E62C-4A41-B587-0ECCFA09C51B_skimrejec_10.root",
      eosdir+"UL2016_preVFP/SingleMuon/Run2016B-ver2_HIPM_UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/05F01599-E62C-4A41-B587-0ECCFA09C51B_skimrejec_11.root",
      eosdir+"UL2016_preVFP/SingleMuon/Run2016C-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/0A7BD477-4598-3343-B84C-65B8081264A5_skimrejec_0.root",
      eosdir+"UL2016_preVFP/SingleMuon/Run2016C-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/0A7BD477-4598-3343-B84C-65B8081264A5_skimrejec_1.root",
      eosdir+"UL2016_preVFP/SingleMuon/Run2016C-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/0A7BD477-4598-3343-B84C-65B8081264A5_skimrejec_2.root",
      eosdir+"UL2016_preVFP/SingleMuon/Run2016C-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/0A7BD477-4598-3343-B84C-65B8081264A5_skimrejec_3.root",
      eosdir+"UL2016_preVFP/SingleMuon/Run2016D-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/098F790E-C894-304B-A390-971D4E9089B4_skimrejec_0.root",
      eosdir+"UL2016_preVFP/SingleMuon/Run2016D-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/098F790E-C894-304B-A390-971D4E9089B4_skimrejec_1.root",
      eosdir+"UL2016_preVFP/SingleMuon/Run2016D-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/098F790E-C894-304B-A390-971D4E9089B4_skimrejec_2.root",
      eosdir+"UL2016_preVFP/SingleMuon/Run2016D-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/098F790E-C894-304B-A390-971D4E9089B4_skimrejec_3.root",
      eosdir+"UL2016_preVFP/SingleMuon/Run2016D-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/098F790E-C894-304B-A390-971D4E9089B4_skimrejec_4.root",
      eosdir+"UL2016_preVFP/SingleMuon/Run2016D-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/098F790E-C894-304B-A390-971D4E9089B4_skimrejec_5.root",
      eosdir+"UL2016_preVFP/SingleMuon/Run2016D-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/09F8FBEA-DC83-E548-A35E-5D53659290D7_skimrejec_0.root",
      eosdir+"UL2016_preVFP/SingleMuon/Run2016D-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/09F8FBEA-DC83-E548-A35E-5D53659290D7_skimrejec_1.root",
      eosdir+"UL2016_preVFP/SingleMuon/Run2016D-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/09F8FBEA-DC83-E548-A35E-5D53659290D7_skimrejec_2.root",
      eosdir+"UL2016_preVFP/SingleMuon/Run2016D-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/09F8FBEA-DC83-E548-A35E-5D53659290D7_skimrejec_3.root",
      eosdir+"UL2016_preVFP/SingleMuon/Run2016E-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/01426D7F-B118-874C-A92A-4077E3DB328F_skimrejec_0.root",
      eosdir+"UL2016_preVFP/SingleMuon/Run2016E-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/01426D7F-B118-874C-A92A-4077E3DB328F_skimrejec_1.root",
      eosdir+"UL2016_preVFP/SingleMuon/Run2016E-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/01426D7F-B118-874C-A92A-4077E3DB328F_skimrejec_2.root",
      eosdir+"UL2016_preVFP/SingleMuon/Run2016E-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/01426D7F-B118-874C-A92A-4077E3DB328F_skimrejec_3.root",
      eosdir+"UL2016_preVFP/SingleMuon/Run2016E-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/01426D7F-B118-874C-A92A-4077E3DB328F_skimrejec_4.root",
      eosdir+"UL2016_preVFP/SingleMuon/Run2016E-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/01426D7F-B118-874C-A92A-4077E3DB328F_skimrejec_5.root",
      eosdir+"UL2016_preVFP/SingleMuon/Run2016E-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/01426D7F-B118-874C-A92A-4077E3DB328F_skimrejec_6.root",
      eosdir+"UL2016_preVFP/SingleMuon/Run2016E-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/07534557-A25E-3047-B73C-670F166DD2A1_skimrejec_0.root",
      eosdir+"UL2016_preVFP/SingleMuon/Run2016E-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/07534557-A25E-3047-B73C-670F166DD2A1_skimrejec_1.root",
      eosdir+"UL2016_preVFP/SingleMuon/Run2016E-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/07534557-A25E-3047-B73C-670F166DD2A1_skimrejec_2.root",
      eosdir+"UL2016_preVFP/SingleMuon/Run2016F-HIPM_UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/028ECDA9-7935-F34A-B3D2-CA48EC406BBD_skimrejec_0.root",
      eosdir+"UL2016_preVFP/SingleMuon/Run2016F-HIPM_UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/028ECDA9-7935-F34A-B3D2-CA48EC406BBD_skimrejec_1.root",
      eosdir+"UL2016_preVFP/SingleMuon/Run2016F-HIPM_UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/028ECDA9-7935-F34A-B3D2-CA48EC406BBD_skimrejec_2.root",
      eosdir+"UL2016_preVFP/SingleMuon/Run2016F-HIPM_UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/028ECDA9-7935-F34A-B3D2-CA48EC406BBD_skimrejec_3.root",
      eosdir+"UL2016_preVFP/SingleMuon/Run2016F-HIPM_UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/028ECDA9-7935-F34A-B3D2-CA48EC406BBD_skimrejec_4.root",
      eosdir+"UL2016_preVFP/SingleMuon/Run2016F-HIPM_UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/028ECDA9-7935-F34A-B3D2-CA48EC406BBD_skimrejec_5.root",
      eosdir+"UL2016_preVFP/SingleMuon/Run2016F-HIPM_UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/028ECDA9-7935-F34A-B3D2-CA48EC406BBD_skimrejec_6.root",
      eosdir+"UL2016_preVFP/SingleMuon/Run2016F-HIPM_UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/028ECDA9-7935-F34A-B3D2-CA48EC406BBD_skimrejec_7.root",
      eosdir+"UL2016_preVFP/SingleMuon/Run2016F-HIPM_UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/0C05D6DF-210B-6943-B5C6-B30EAB0ADF21_skimrejec_0.root",
      eosdir+"UL2016_preVFP/SingleMuon/Run2016F-HIPM_UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD/0C05D6DF-210B-6943-B5C6-B30EAB0ADF21_skimrejec_1.root",
    ],nfilemax=nfilemax,data=True,verb=verbosity),
    Sample("SingleMuon_2016_postVFP","UL2016 post-VFP",[
      eosdir+"UL2016_postVFP/SingleMuon/Run2016F-UL2016_MiniAODv1_NanoAODv2-v4/NANOAOD/4C97E39F-FB8B-1748-AE5E-45AED14C0C88_skimrejec_0.root",
      eosdir+"UL2016_postVFP/SingleMuon/Run2016F-UL2016_MiniAODv1_NanoAODv2-v4/NANOAOD/4C97E39F-FB8B-1748-AE5E-45AED14C0C88_skimrejec_1.root",
      eosdir+"UL2016_postVFP/SingleMuon/Run2016F-UL2016_MiniAODv1_NanoAODv2-v4/NANOAOD/4C97E39F-FB8B-1748-AE5E-45AED14C0C88_skimrejec_2.root",
      eosdir+"UL2016_postVFP/SingleMuon/Run2016F-UL2016_MiniAODv1_NanoAODv2-v4/NANOAOD/4C97E39F-FB8B-1748-AE5E-45AED14C0C88_skimrejec_3.root",
      eosdir+"UL2016_postVFP/SingleMuon/Run2016F-UL2016_MiniAODv1_NanoAODv2-v4/NANOAOD/4C97E39F-FB8B-1748-AE5E-45AED14C0C88_skimrejec_4.root",
      eosdir+"UL2016_postVFP/SingleMuon/Run2016F-UL2016_MiniAODv1_NanoAODv2-v4/NANOAOD/4C97E39F-FB8B-1748-AE5E-45AED14C0C88_skimrejec_5.root",
      eosdir+"UL2016_postVFP/SingleMuon/Run2016F-UL2016_MiniAODv1_NanoAODv2-v4/NANOAOD/6253CE88-11C1-5046-AE92-AC9CB585B6E5_skimrejec_0.root",
      eosdir+"UL2016_postVFP/SingleMuon/Run2016F-UL2016_MiniAODv1_NanoAODv2-v4/NANOAOD/6253CE88-11C1-5046-AE92-AC9CB585B6E5_skimrejec_1.root",
      eosdir+"UL2016_postVFP/SingleMuon/Run2016F-UL2016_MiniAODv1_NanoAODv2-v4/NANOAOD/6253CE88-11C1-5046-AE92-AC9CB585B6E5_skimrejec_2.root",
      eosdir+"UL2016_postVFP/SingleMuon/Run2016F-UL2016_MiniAODv1_NanoAODv2-v4/NANOAOD/6253CE88-11C1-5046-AE92-AC9CB585B6E5_skimrejec_3.root",
    ]+files_Run2016G+files_Run2016H,nfilemax=nfilemax,verb=verbosity),
    #Sample("SingleMuon_2016G_postVFP","UL2016G post-VFP",files_Run2016G,nfilemax=nfilemax,data=True,verb=verbosity),
    #Sample("SingleMuon_2016H_postVFP","UL2016H post-VFP",files_Run2016H,nfilemax=nfilemax,data=True,verb=verbosity),
    Sample("SingleMuon_2017","UL2017",[
      eosdir+"UL2017/SingleMuon/Run2017B-UL2017_MiniAODv1_NanoAODv2-v1/NANOAOD/0243BEE7-CEAC-C845-A533-C5D50D202056_skimjec_0.root",
      eosdir+"UL2017/SingleMuon/Run2017B-UL2017_MiniAODv1_NanoAODv2-v1/NANOAOD/0243BEE7-CEAC-C845-A533-C5D50D202056_skimjec_1.root",
      eosdir+"UL2017/SingleMuon/Run2017B-UL2017_MiniAODv1_NanoAODv2-v1/NANOAOD/0293C28C-EC9A-6843-8050-C140244B9108_skimjec_0.root",
      eosdir+"UL2017/SingleMuon/Run2017B-UL2017_MiniAODv1_NanoAODv2-v1/NANOAOD/0293C28C-EC9A-6843-8050-C140244B9108_skimjec_1.root",
      eosdir+"UL2017/SingleMuon/Run2017B-UL2017_MiniAODv1_NanoAODv2-v1/NANOAOD/0293C28C-EC9A-6843-8050-C140244B9108_skimjec_2.root",
      eosdir+"UL2017/SingleMuon/Run2017B-UL2017_MiniAODv1_NanoAODv2-v1/NANOAOD/0293C28C-EC9A-6843-8050-C140244B9108_skimjec_3.root",
      eosdir+"UL2017/SingleMuon/Run2017B-UL2017_MiniAODv1_NanoAODv2-v1/NANOAOD/0293C28C-EC9A-6843-8050-C140244B9108_skimjec_4.root",
      eosdir+"UL2017/SingleMuon/Run2017B-UL2017_MiniAODv1_NanoAODv2-v1/NANOAOD/0293C28C-EC9A-6843-8050-C140244B9108_skimjec_5.root",
      eosdir+"UL2017/SingleMuon/Run2017B-UL2017_MiniAODv1_NanoAODv2-v1/NANOAOD/0293C28C-EC9A-6843-8050-C140244B9108_skimjec_6.root",
      eosdir+"UL2017/SingleMuon/Run2017B-UL2017_MiniAODv1_NanoAODv2-v1/NANOAOD/0293C28C-EC9A-6843-8050-C140244B9108_skimjec_7.root",
      eosdir+"UL2017/SingleMuon/Run2017C-UL2017_MiniAODv1_NanoAODv2-v1/NANOAOD/003BBB0F-ED90-FA47-8A1A-9E196850AB51_skimjec_0.root",
      eosdir+"UL2017/SingleMuon/Run2017C-UL2017_MiniAODv1_NanoAODv2-v1/NANOAOD/003BBB0F-ED90-FA47-8A1A-9E196850AB51_skimjec_1.root",
      eosdir+"UL2017/SingleMuon/Run2017C-UL2017_MiniAODv1_NanoAODv2-v1/NANOAOD/003BBB0F-ED90-FA47-8A1A-9E196850AB51_skimjec_2.root",
      eosdir+"UL2017/SingleMuon/Run2017C-UL2017_MiniAODv1_NanoAODv2-v1/NANOAOD/003BBB0F-ED90-FA47-8A1A-9E196850AB51_skimjec_3.root",
      eosdir+"UL2017/SingleMuon/Run2017C-UL2017_MiniAODv1_NanoAODv2-v1/NANOAOD/003BBB0F-ED90-FA47-8A1A-9E196850AB51_skimjec_4.root",
      eosdir+"UL2017/SingleMuon/Run2017C-UL2017_MiniAODv1_NanoAODv2-v1/NANOAOD/003BBB0F-ED90-FA47-8A1A-9E196850AB51_skimjec_5.root",
      eosdir+"UL2017/SingleMuon/Run2017C-UL2017_MiniAODv1_NanoAODv2-v1/NANOAOD/003BBB0F-ED90-FA47-8A1A-9E196850AB51_skimjec_6.root",
      eosdir+"UL2017/SingleMuon/Run2017C-UL2017_MiniAODv1_NanoAODv2-v1/NANOAOD/04C23298-E23F-AC44-B857-DD2AD09B7569_skimjec_0.root",
      eosdir+"UL2017/SingleMuon/Run2017C-UL2017_MiniAODv1_NanoAODv2-v1/NANOAOD/04C23298-E23F-AC44-B857-DD2AD09B7569_skimjec_1.root",
      eosdir+"UL2017/SingleMuon/Run2017C-UL2017_MiniAODv1_NanoAODv2-v1/NANOAOD/04C23298-E23F-AC44-B857-DD2AD09B7569_skimjec_2.root",
      eosdir+"UL2017/SingleMuon/Run2017D-UL2017_MiniAODv1_NanoAODv2-v1/NANOAOD/022795D4-5232-6849-B389-37C2FF8F0C38_skimjec_0.root",
      eosdir+"UL2017/SingleMuon/Run2017D-UL2017_MiniAODv1_NanoAODv2-v1/NANOAOD/022795D4-5232-6849-B389-37C2FF8F0C38_skimjec_1.root",
      eosdir+"UL2017/SingleMuon/Run2017D-UL2017_MiniAODv1_NanoAODv2-v1/NANOAOD/022795D4-5232-6849-B389-37C2FF8F0C38_skimjec_2.root",
      eosdir+"UL2017/SingleMuon/Run2017D-UL2017_MiniAODv1_NanoAODv2-v1/NANOAOD/022795D4-5232-6849-B389-37C2FF8F0C38_skimjec_3.root",
      eosdir+"UL2017/SingleMuon/Run2017D-UL2017_MiniAODv1_NanoAODv2-v1/NANOAOD/022795D4-5232-6849-B389-37C2FF8F0C38_skimjec_4.root",
      eosdir+"UL2017/SingleMuon/Run2017D-UL2017_MiniAODv1_NanoAODv2-v1/NANOAOD/022795D4-5232-6849-B389-37C2FF8F0C38_skimjec_5.root",
      eosdir+"UL2017/SingleMuon/Run2017D-UL2017_MiniAODv1_NanoAODv2-v1/NANOAOD/044612F6-9361-E14B-95C5-68AE8763BBDF_skimjec_0.root",
      eosdir+"UL2017/SingleMuon/Run2017D-UL2017_MiniAODv1_NanoAODv2-v1/NANOAOD/044612F6-9361-E14B-95C5-68AE8763BBDF_skimjec_1.root",
      eosdir+"UL2017/SingleMuon/Run2017D-UL2017_MiniAODv1_NanoAODv2-v1/NANOAOD/044612F6-9361-E14B-95C5-68AE8763BBDF_skimjec_2.root",
      eosdir+"UL2017/SingleMuon/Run2017D-UL2017_MiniAODv1_NanoAODv2-v1/NANOAOD/044612F6-9361-E14B-95C5-68AE8763BBDF_skimjec_3.root",
      eosdir+"UL2017/SingleMuon/Run2017E-UL2017_MiniAODv1_NanoAODv2-v2/NANOAOD/00439FC5-7F11-D048-96FF-9AC7DB4D5615_skimjec_0.root",
      eosdir+"UL2017/SingleMuon/Run2017E-UL2017_MiniAODv1_NanoAODv2-v2/NANOAOD/00439FC5-7F11-D048-96FF-9AC7DB4D5615_skimjec_1.root",
      eosdir+"UL2017/SingleMuon/Run2017E-UL2017_MiniAODv1_NanoAODv2-v2/NANOAOD/00439FC5-7F11-D048-96FF-9AC7DB4D5615_skimjec_2.root",
      eosdir+"UL2017/SingleMuon/Run2017E-UL2017_MiniAODv1_NanoAODv2-v2/NANOAOD/00439FC5-7F11-D048-96FF-9AC7DB4D5615_skimjec_3.root",
      eosdir+"UL2017/SingleMuon/Run2017E-UL2017_MiniAODv1_NanoAODv2-v2/NANOAOD/00439FC5-7F11-D048-96FF-9AC7DB4D5615_skimjec_4.root",
      eosdir+"UL2017/SingleMuon/Run2017E-UL2017_MiniAODv1_NanoAODv2-v2/NANOAOD/00439FC5-7F11-D048-96FF-9AC7DB4D5615_skimjec_5.root",
      eosdir+"UL2017/SingleMuon/Run2017E-UL2017_MiniAODv1_NanoAODv2-v2/NANOAOD/00439FC5-7F11-D048-96FF-9AC7DB4D5615_skimjec_6.root",
      eosdir+"UL2017/SingleMuon/Run2017E-UL2017_MiniAODv1_NanoAODv2-v2/NANOAOD/01B534DE-D2A6-A041-A005-41963479AE10_skimjec_0.root",
      eosdir+"UL2017/SingleMuon/Run2017E-UL2017_MiniAODv1_NanoAODv2-v2/NANOAOD/01B534DE-D2A6-A041-A005-41963479AE10_skimjec_1.root",
      eosdir+"UL2017/SingleMuon/Run2017E-UL2017_MiniAODv1_NanoAODv2-v2/NANOAOD/01B534DE-D2A6-A041-A005-41963479AE10_skimjec_2.root",
      eosdir+"UL2017/SingleMuon/Run2017F-UL2017_MiniAODv1_NanoAODv2-v2/NANOAOD/002D3DE0-05EE-E747-BB76-4FB84262EE3F_skimjec_0.root",
      eosdir+"UL2017/SingleMuon/Run2017F-UL2017_MiniAODv1_NanoAODv2-v2/NANOAOD/002D3DE0-05EE-E747-BB76-4FB84262EE3F_skimjec_1.root",
      eosdir+"UL2017/SingleMuon/Run2017F-UL2017_MiniAODv1_NanoAODv2-v2/NANOAOD/002D3DE0-05EE-E747-BB76-4FB84262EE3F_skimjec_2.root",
      eosdir+"UL2017/SingleMuon/Run2017F-UL2017_MiniAODv1_NanoAODv2-v2/NANOAOD/002D3DE0-05EE-E747-BB76-4FB84262EE3F_skimjec_3.root",
      eosdir+"UL2017/SingleMuon/Run2017F-UL2017_MiniAODv1_NanoAODv2-v2/NANOAOD/002D3DE0-05EE-E747-BB76-4FB84262EE3F_skimjec_4.root",
      eosdir+"UL2017/SingleMuon/Run2017F-UL2017_MiniAODv1_NanoAODv2-v2/NANOAOD/002D3DE0-05EE-E747-BB76-4FB84262EE3F_skimjec_5.root",
      eosdir+"UL2017/SingleMuon/Run2017F-UL2017_MiniAODv1_NanoAODv2-v2/NANOAOD/002D3DE0-05EE-E747-BB76-4FB84262EE3F_skimjec_6.root",
      eosdir+"UL2017/SingleMuon/Run2017F-UL2017_MiniAODv1_NanoAODv2-v2/NANOAOD/016F5501-26EB-4147-AEF7-F4C9F6EFE308_skimjec_0.root",
      eosdir+"UL2017/SingleMuon/Run2017F-UL2017_MiniAODv1_NanoAODv2-v2/NANOAOD/016F5501-26EB-4147-AEF7-F4C9F6EFE308_skimjec_1.root",
      eosdir+"UL2017/SingleMuon/Run2017F-UL2017_MiniAODv1_NanoAODv2-v2/NANOAOD/016F5501-26EB-4147-AEF7-F4C9F6EFE308_skimjec_2.root",
    ],nfilemax=nfilemax,data=True,verb=verbosity),
    Sample("SingleMuon_2018","UL2018",[
      eosdir+"UL2018/SingleMuon/Run2018A-UL2018_MiniAODv1_NanoAODv2-v1/NANOAOD/00326F0B-0474-8C46-A6E1-B5952ECC4F05_skimjec_0.root",
      eosdir+"UL2018/SingleMuon/Run2018A-UL2018_MiniAODv1_NanoAODv2-v1/NANOAOD/00326F0B-0474-8C46-A6E1-B5952ECC4F05_skimjec_1.root",
      eosdir+"UL2018/SingleMuon/Run2018A-UL2018_MiniAODv1_NanoAODv2-v1/NANOAOD/00326F0B-0474-8C46-A6E1-B5952ECC4F05_skimjec_2.root",
      eosdir+"UL2018/SingleMuon/Run2018A-UL2018_MiniAODv1_NanoAODv2-v1/NANOAOD/00326F0B-0474-8C46-A6E1-B5952ECC4F05_skimjec_3.root",
      eosdir+"UL2018/SingleMuon/Run2018A-UL2018_MiniAODv1_NanoAODv2-v1/NANOAOD/00326F0B-0474-8C46-A6E1-B5952ECC4F05_skimjec_4.root",
      eosdir+"UL2018/SingleMuon/Run2018A-UL2018_MiniAODv1_NanoAODv2-v1/NANOAOD/00326F0B-0474-8C46-A6E1-B5952ECC4F05_skimjec_5.root",
      eosdir+"UL2018/SingleMuon/Run2018A-UL2018_MiniAODv1_NanoAODv2-v1/NANOAOD/00326F0B-0474-8C46-A6E1-B5952ECC4F05_skimjec_6.root",
      eosdir+"UL2018/SingleMuon/Run2018A-UL2018_MiniAODv1_NanoAODv2-v1/NANOAOD/00326F0B-0474-8C46-A6E1-B5952ECC4F05_skimjec_7.root",
      eosdir+"UL2018/SingleMuon/Run2018A-UL2018_MiniAODv1_NanoAODv2-v1/NANOAOD/007715D7-3CA1-A74D-805D-C886743359DB_skimjec_0.root",
      eosdir+"UL2018/SingleMuon/Run2018A-UL2018_MiniAODv1_NanoAODv2-v1/NANOAOD/007715D7-3CA1-A74D-805D-C886743359DB_skimjec_1.root",
      eosdir+"UL2018/SingleMuon/Run2018B-UL2018_MiniAODv1_NanoAODv2-v1/NANOAOD/07E34CA9-9EDD-6F4C-96E8-6B93D30D4AD8_skimjec_0.root",
      eosdir+"UL2018/SingleMuon/Run2018B-UL2018_MiniAODv1_NanoAODv2-v1/NANOAOD/07E34CA9-9EDD-6F4C-96E8-6B93D30D4AD8_skimjec_1.root",
      eosdir+"UL2018/SingleMuon/Run2018B-UL2018_MiniAODv1_NanoAODv2-v1/NANOAOD/07E34CA9-9EDD-6F4C-96E8-6B93D30D4AD8_skimjec_2.root",
      eosdir+"UL2018/SingleMuon/Run2018B-UL2018_MiniAODv1_NanoAODv2-v1/NANOAOD/07E34CA9-9EDD-6F4C-96E8-6B93D30D4AD8_skimjec_3.root",
      eosdir+"UL2018/SingleMuon/Run2018B-UL2018_MiniAODv1_NanoAODv2-v1/NANOAOD/07E34CA9-9EDD-6F4C-96E8-6B93D30D4AD8_skimjec_4.root",
      eosdir+"UL2018/SingleMuon/Run2018B-UL2018_MiniAODv1_NanoAODv2-v1/NANOAOD/07E34CA9-9EDD-6F4C-96E8-6B93D30D4AD8_skimjec_5.root",
      eosdir+"UL2018/SingleMuon/Run2018B-UL2018_MiniAODv1_NanoAODv2-v1/NANOAOD/098C2625-AFE2-3B4E-A31A-4A064FFA7AE5_skimjec_0.root",
      eosdir+"UL2018/SingleMuon/Run2018B-UL2018_MiniAODv1_NanoAODv2-v1/NANOAOD/098C2625-AFE2-3B4E-A31A-4A064FFA7AE5_skimjec_1.root",
      eosdir+"UL2018/SingleMuon/Run2018B-UL2018_MiniAODv1_NanoAODv2-v1/NANOAOD/098C2625-AFE2-3B4E-A31A-4A064FFA7AE5_skimjec_2.root",
      eosdir+"UL2018/SingleMuon/Run2018B-UL2018_MiniAODv1_NanoAODv2-v1/NANOAOD/098C2625-AFE2-3B4E-A31A-4A064FFA7AE5_skimjec_3.root",
      eosdir+"UL2018/SingleMuon/Run2018C-UL2018_MiniAODv1_NanoAODv2-v1/NANOAOD/02CCFB9B-65E0-CB46-ACF9-80F3402CA0DB_skimjec_0.root",
      eosdir+"UL2018/SingleMuon/Run2018C-UL2018_MiniAODv1_NanoAODv2-v1/NANOAOD/02CCFB9B-65E0-CB46-ACF9-80F3402CA0DB_skimjec_1.root",
      eosdir+"UL2018/SingleMuon/Run2018C-UL2018_MiniAODv1_NanoAODv2-v1/NANOAOD/02CCFB9B-65E0-CB46-ACF9-80F3402CA0DB_skimjec_2.root",
      eosdir+"UL2018/SingleMuon/Run2018C-UL2018_MiniAODv1_NanoAODv2-v1/NANOAOD/02CCFB9B-65E0-CB46-ACF9-80F3402CA0DB_skimjec_3.root",
      eosdir+"UL2018/SingleMuon/Run2018C-UL2018_MiniAODv1_NanoAODv2-v1/NANOAOD/02CCFB9B-65E0-CB46-ACF9-80F3402CA0DB_skimjec_4.root",
      eosdir+"UL2018/SingleMuon/Run2018C-UL2018_MiniAODv1_NanoAODv2-v1/NANOAOD/02CCFB9B-65E0-CB46-ACF9-80F3402CA0DB_skimjec_5.root",
      eosdir+"UL2018/SingleMuon/Run2018C-UL2018_MiniAODv1_NanoAODv2-v1/NANOAOD/02CCFB9B-65E0-CB46-ACF9-80F3402CA0DB_skimjec_6.root",
      eosdir+"UL2018/SingleMuon/Run2018C-UL2018_MiniAODv1_NanoAODv2-v1/NANOAOD/02CCFB9B-65E0-CB46-ACF9-80F3402CA0DB_skimjec_7.root",
      eosdir+"UL2018/SingleMuon/Run2018C-UL2018_MiniAODv1_NanoAODv2-v1/NANOAOD/02CCFB9B-65E0-CB46-ACF9-80F3402CA0DB_skimjec_8.root",
      eosdir+"UL2018/SingleMuon/Run2018C-UL2018_MiniAODv1_NanoAODv2-v1/NANOAOD/02CCFB9B-65E0-CB46-ACF9-80F3402CA0DB_skimjec_9.root",
      eosdir+"UL2018/SingleMuon/Run2018D-UL2018_MiniAODv1_NanoAODv2-v1/NANOAOD/00305DF9-8122-DF46-B2ED-E80CC491986E_skimjec_0.root",
      eosdir+"UL2018/SingleMuon/Run2018D-UL2018_MiniAODv1_NanoAODv2-v1/NANOAOD/00305DF9-8122-DF46-B2ED-E80CC491986E_skimjec_1.root",
      eosdir+"UL2018/SingleMuon/Run2018D-UL2018_MiniAODv1_NanoAODv2-v1/NANOAOD/00305DF9-8122-DF46-B2ED-E80CC491986E_skimjec_2.root",
      eosdir+"UL2018/SingleMuon/Run2018D-UL2018_MiniAODv1_NanoAODv2-v1/NANOAOD/00305DF9-8122-DF46-B2ED-E80CC491986E_skimjec_3.root",
      eosdir+"UL2018/SingleMuon/Run2018D-UL2018_MiniAODv1_NanoAODv2-v1/NANOAOD/00305DF9-8122-DF46-B2ED-E80CC491986E_skimjec_4.root",
      eosdir+"UL2018/SingleMuon/Run2018D-UL2018_MiniAODv1_NanoAODv2-v1/NANOAOD/00305DF9-8122-DF46-B2ED-E80CC491986E_skimjec_5.root",
      eosdir+"UL2018/SingleMuon/Run2018D-UL2018_MiniAODv1_NanoAODv2-v1/NANOAOD/00305DF9-8122-DF46-B2ED-E80CC491986E_skimjec_6.root",
      eosdir+"UL2018/SingleMuon/Run2018D-UL2018_MiniAODv1_NanoAODv2-v1/NANOAOD/00305DF9-8122-DF46-B2ED-E80CC491986E_skimjec_7.root",
      eosdir+"UL2018/SingleMuon/Run2018D-UL2018_MiniAODv1_NanoAODv2-v1/NANOAOD/0114B8C2-A5FC-ED42-9CE9-7911B79ADCA2_skimjec_0.root",
      eosdir+"UL2018/SingleMuon/Run2018D-UL2018_MiniAODv1_NanoAODv2-v1/NANOAOD/0114B8C2-A5FC-ED42-9CE9-7911B79ADCA2_skimjec_1.root",
    ],nfilemax=nfilemax,data=True,verb=verbosity),
  ]
  
  # DRELL-YAN
  #   head -n 40 ../PicoProducer/samples/files/UL2017/DYJetsToLL_M-50.txt | grep root
  #   dasgoclient -query="/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer*UL16*/NANOAODSIM"
  #   dasgoclient -query="/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer20UL16*/NANOAODSIM"
  #   dasgoclient -query="/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer20UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM file" --limit 6
  #   dasgoclient -query="/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer20UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM file" --limit 6
  samplesets['DYJetsToLL_M-50'] = [
    Sample("DY_16_preVFP_19","Summer19, UL2016 pre-VFP",[
      eosdir+"UL2016_preVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/01DD3EB7-67AC-EA49-ADB8-481277FF50D8_skimjec_0.root",
      eosdir+"UL2016_preVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/01DD3EB7-67AC-EA49-ADB8-481277FF50D8_skimjec_1.root",
      eosdir+"UL2016_preVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/01DD3EB7-67AC-EA49-ADB8-481277FF50D8_skimjec_2.root",
      eosdir+"UL2016_preVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/01DD3EB7-67AC-EA49-ADB8-481277FF50D8_skimjec_3.root",
      eosdir+"UL2016_preVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/01DD3EB7-67AC-EA49-ADB8-481277FF50D8_skimjec_4.root",
      eosdir+"UL2016_preVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/01DD3EB7-67AC-EA49-ADB8-481277FF50D8_skimjec_5.root",
      eosdir+"UL2016_preVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/01DD3EB7-67AC-EA49-ADB8-481277FF50D8_skimjec_6.root",
      eosdir+"UL2016_preVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/071C9BD5-D0EC-7846-A170-E270E02F7966_skimjec_0.root",
      eosdir+"UL2016_preVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/071C9BD5-D0EC-7846-A170-E270E02F7966_skimjec_1.root",
      eosdir+"UL2016_preVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/071C9BD5-D0EC-7846-A170-E270E02F7966_skimjec_2.root",
      eosdir+"UL2016_preVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/071C9BD5-D0EC-7846-A170-E270E02F7966_skimjec_3.root",
      eosdir+"UL2016_preVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/071C9BD5-D0EC-7846-A170-E270E02F7966_skimjec_4.root",
      eosdir+"UL2016_preVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/071C9BD5-D0EC-7846-A170-E270E02F7966_skimjec_5.root",
      eosdir+"UL2016_preVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/071C9BD5-D0EC-7846-A170-E270E02F7966_skimjec_6.root",
      eosdir+"UL2016_preVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/071C9BD5-D0EC-7846-A170-E270E02F7966_skimjec_7.root",
      eosdir+"UL2016_preVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/071C9BD5-D0EC-7846-A170-E270E02F7966_skimjec_8.root",
      eosdir+"UL2016_preVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/0EB134C2-AF97-6445-8BB4-FF44223E20CA_skimjec_0.root",
      eosdir+"UL2016_preVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/0EB134C2-AF97-6445-8BB4-FF44223E20CA_skimjec_1.root",
      eosdir+"UL2016_preVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/0EB134C2-AF97-6445-8BB4-FF44223E20CA_skimjec_2.root",
      eosdir+"UL2016_preVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/0EB134C2-AF97-6445-8BB4-FF44223E20CA_skimjec_3.root",
      eosdir+"UL2016_preVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/0EB134C2-AF97-6445-8BB4-FF44223E20CA_skimjec_4.root",
      eosdir+"UL2016_preVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/0EB134C2-AF97-6445-8BB4-FF44223E20CA_skimjec_5.root",
      eosdir+"UL2016_preVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/0EB134C2-AF97-6445-8BB4-FF44223E20CA_skimjec_6.root",
      eosdir+"UL2016_preVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/11BBBB14-5780-1B48-A6EB-5915E93D1883_skimjec_0.root",
      eosdir+"UL2016_preVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/11BBBB14-5780-1B48-A6EB-5915E93D1883_skimjec_1.root",
      eosdir+"UL2016_preVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/11BBBB14-5780-1B48-A6EB-5915E93D1883_skimjec_2.root",
      eosdir+"UL2016_preVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/11BBBB14-5780-1B48-A6EB-5915E93D1883_skimjec_3.root",
      eosdir+"UL2016_preVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/11BBBB14-5780-1B48-A6EB-5915E93D1883_skimjec_4.root",
      eosdir+"UL2016_preVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/11BBBB14-5780-1B48-A6EB-5915E93D1883_skimjec_5.root",
      eosdir+"UL2016_preVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/11BBBB14-5780-1B48-A6EB-5915E93D1883_skimjec_6.root",
      eosdir+"UL2016_preVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/11BBBB14-5780-1B48-A6EB-5915E93D1883_skimjec_7.root",
      eosdir+"UL2016_preVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/11BBBB14-5780-1B48-A6EB-5915E93D1883_skimjec_8.root",
      eosdir+"UL2016_preVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/162234B0-9CEB-8447-AC36-D2178A261BC2_skimjec_0.root",
      eosdir+"UL2016_preVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/162234B0-9CEB-8447-AC36-D2178A261BC2_skimjec_1.root",
      eosdir+"UL2016_preVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/1BA503A2-2D3E-6045-B817-FF5D0F22A5D8_skimjec_0.root",
      eosdir+"UL2016_preVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/1BA503A2-2D3E-6045-B817-FF5D0F22A5D8_skimjec_1.root",
      eosdir+"UL2016_preVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/1BA503A2-2D3E-6045-B817-FF5D0F22A5D8_skimjec_2.root",
      eosdir+"UL2016_preVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/1BA503A2-2D3E-6045-B817-FF5D0F22A5D8_skimjec_3.root",
      eosdir+"UL2016_preVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/1BA503A2-2D3E-6045-B817-FF5D0F22A5D8_skimjec_4.root",
      eosdir+"UL2016_preVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/1BA503A2-2D3E-6045-B817-FF5D0F22A5D8_skimjec_5.root",
    ],nfilemax=nfilemax,verb=verbosity),
    Sample("DY_16_preVFP_20","Summer20, UL2016 pre-VFP",[
      #dasurl+"/store/mc/RunIISummer20UL16NanoAODAPVv2/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/NANOAODSIM/106X_mcRun2_asymptotic_preVFP_v9-v1/00000/79E1D9D9-4C44-1C4B-AD40-DC5B9B8056EC.root",
      #dasurl+"/store/mc/RunIISummer20UL16NanoAODAPVv2/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/NANOAODSIM/106X_mcRun2_asymptotic_preVFP_v9-v1/00000/1EDAAF46-2981-E240-B24E-55C33C41B0DF.root",
      #dasurl+"/store/mc/RunIISummer20UL16NanoAODAPVv2/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/NANOAODSIM/106X_mcRun2_asymptotic_preVFP_v9-v1/00000/EA0BA9F0-4967-1946-8A9A-B7A1B2376178.root",
      #dasurl+"/store/mc/RunIISummer20UL16NanoAODAPVv2/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/NANOAODSIM/106X_mcRun2_asymptotic_preVFP_v9-v1/00000/C7441CD0-BB23-E140-B0AD-D3316A7FDE57.root",
      #dasurl+"/store/mc/RunIISummer20UL16NanoAODAPVv2/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/NANOAODSIM/106X_mcRun2_asymptotic_preVFP_v9-v1/00000/AD0452CB-BA7A-A246-B721-8B2BF1A4867F.root",
      #dasurl+"/store/mc/RunIISummer20UL16NanoAODAPVv2/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/NANOAODSIM/106X_mcRun2_asymptotic_preVFP_v9-v1/00000/6EA9A456-D466-7049-90EB-8F4E40C637A4.root",
      t3dir+"DYJetsToLL_Summer20UL16NanoAODAPVv2/79E1D9D9-4C44-1C4B-AD40-DC5B9B8056EC.root",
      t3dir+"DYJetsToLL_Summer20UL16NanoAODAPVv2/1EDAAF46-2981-E240-B24E-55C33C41B0DF.root",
      t3dir+"DYJetsToLL_Summer20UL16NanoAODAPVv2/EA0BA9F0-4967-1946-8A9A-B7A1B2376178.root",
      t3dir+"DYJetsToLL_Summer20UL16NanoAODAPVv2/C7441CD0-BB23-E140-B0AD-D3316A7FDE57.root",
      t3dir+"DYJetsToLL_Summer20UL16NanoAODAPVv2/AD0452CB-BA7A-A246-B721-8B2BF1A4867F.root",
      t3dir+"DYJetsToLL_Summer20UL16NanoAODAPVv2/6EA9A456-D466-7049-90EB-8F4E40C637A4.root",
    ],nfilemax=nfilemax,verb=verbosity),
    Sample("DY_16_postVFP_19","Summer19, UL2016 post-VFP",[
      eosdir+"UL2016_postVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/0506D2C0-BBF3-564D-8A20-73007E9E7158_skimjec_0.root",
      eosdir+"UL2016_postVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/0506D2C0-BBF3-564D-8A20-73007E9E7158_skimjec_1.root",
      eosdir+"UL2016_postVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/0506D2C0-BBF3-564D-8A20-73007E9E7158_skimjec_2.root",
      eosdir+"UL2016_postVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/0506D2C0-BBF3-564D-8A20-73007E9E7158_skimjec_3.root",
      eosdir+"UL2016_postVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/0506D2C0-BBF3-564D-8A20-73007E9E7158_skimjec_4.root",
      eosdir+"UL2016_postVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/0E8EA24A-2E7B-E643-8943-A11790FAC73E_skimjec_0.root",
      eosdir+"UL2016_postVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/0E8EA24A-2E7B-E643-8943-A11790FAC73E_skimjec_1.root",
      eosdir+"UL2016_postVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/0E8EA24A-2E7B-E643-8943-A11790FAC73E_skimjec_2.root",
      eosdir+"UL2016_postVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/0E8EA24A-2E7B-E643-8943-A11790FAC73E_skimjec_3.root",
      eosdir+"UL2016_postVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/0E8EA24A-2E7B-E643-8943-A11790FAC73E_skimjec_4.root",
      eosdir+"UL2016_postVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/0E8EA24A-2E7B-E643-8943-A11790FAC73E_skimjec_5.root",
      eosdir+"UL2016_postVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/0E8EA24A-2E7B-E643-8943-A11790FAC73E_skimjec_6.root",
      eosdir+"UL2016_postVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/0E8EA24A-2E7B-E643-8943-A11790FAC73E_skimjec_7.root",
      eosdir+"UL2016_postVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/0E8EA24A-2E7B-E643-8943-A11790FAC73E_skimjec_8.root",
      eosdir+"UL2016_postVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/11C12D83-24F8-9842-9F66-2364D9FD7868_skimjec_0.root",
      eosdir+"UL2016_postVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/11C12D83-24F8-9842-9F66-2364D9FD7868_skimjec_1.root",
      eosdir+"UL2016_postVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/11C12D83-24F8-9842-9F66-2364D9FD7868_skimjec_2.root",
      eosdir+"UL2016_postVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/11C12D83-24F8-9842-9F66-2364D9FD7868_skimjec_3.root",
      eosdir+"UL2016_postVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/11C12D83-24F8-9842-9F66-2364D9FD7868_skimjec_4.root",
      eosdir+"UL2016_postVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/11C12D83-24F8-9842-9F66-2364D9FD7868_skimjec_5.root",
      eosdir+"UL2016_postVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/11C12D83-24F8-9842-9F66-2364D9FD7868_skimjec_6.root",
      eosdir+"UL2016_postVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/11C12D83-24F8-9842-9F66-2364D9FD7868_skimjec_7.root",
      eosdir+"UL2016_postVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/11C12D83-24F8-9842-9F66-2364D9FD7868_skimjec_8.root",
      eosdir+"UL2016_postVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/15341428-8FB1-3347-84FA-947912DC1A73_skimjec_0.root",
      eosdir+"UL2016_postVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/15341428-8FB1-3347-84FA-947912DC1A73_skimjec_1.root",
      eosdir+"UL2016_postVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/15341428-8FB1-3347-84FA-947912DC1A73_skimjec_2.root",
      eosdir+"UL2016_postVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/15341428-8FB1-3347-84FA-947912DC1A73_skimjec_3.root",
      eosdir+"UL2016_postVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/15341428-8FB1-3347-84FA-947912DC1A73_skimjec_4.root",
      eosdir+"UL2016_postVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/15341428-8FB1-3347-84FA-947912DC1A73_skimjec_5.root",
      eosdir+"UL2016_postVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/16FCFD30-DA81-5A49-899D-0797AB6F898C_skimjec_0.root",
      eosdir+"UL2016_postVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/16FCFD30-DA81-5A49-899D-0797AB6F898C_skimjec_1.root",
      eosdir+"UL2016_postVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/16FCFD30-DA81-5A49-899D-0797AB6F898C_skimjec_2.root",
      eosdir+"UL2016_postVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/16FCFD30-DA81-5A49-899D-0797AB6F898C_skimjec_3.root",
      eosdir+"UL2016_postVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/16FCFD30-DA81-5A49-899D-0797AB6F898C_skimjec_4.root",
      eosdir+"UL2016_postVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/16FCFD30-DA81-5A49-899D-0797AB6F898C_skimjec_5.root",
      eosdir+"UL2016_postVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/16FCFD30-DA81-5A49-899D-0797AB6F898C_skimjec_6.root",
      eosdir+"UL2016_postVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/16FCFD30-DA81-5A49-899D-0797AB6F898C_skimjec_7.root",
      eosdir+"UL2016_postVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/16FCFD30-DA81-5A49-899D-0797AB6F898C_skimjec_8.root",
      eosdir+"UL2016_postVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/1CAACDD7-7913-C24C-926F-13FAFD857C6D_skimjec_0.root",
      eosdir+"UL2016_postVFP/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/1CAACDD7-7913-C24C-926F-13FAFD857C6D_skimjec_1.root",
    ],nfilemax=nfilemax,verb=verbosity),
    Sample("DY_16_postVFP_20","Summer20, UL2016 post-VFP",[
      #dasurl+"/store/mc/RunIISummer20UL16NanoAODv2/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/NANOAODSIM/106X_mcRun2_asymptotic_v15-v1/260000/99386FF5-D19F-8B40-915D-53B3DC7FFD23.root",
      #dasurl+"/store/mc/RunIISummer20UL16NanoAODv2/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/NANOAODSIM/106X_mcRun2_asymptotic_v15-v1/260000/EDF20656-7588-C547-A621-AE1247AE3E08.root",
      #dasurl+"/store/mc/RunIISummer20UL16NanoAODv2/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/NANOAODSIM/106X_mcRun2_asymptotic_v15-v1/260000/A4E16BDB-AD76-2D45-AECA-89C0E4135C82.root",
      #dasurl+"/store/mc/RunIISummer20UL16NanoAODv2/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/NANOAODSIM/106X_mcRun2_asymptotic_v15-v1/280000/E6523A98-8A0F-E24E-B8A0-2A6D4FC3BA6E.root",
      #dasurl+"/store/mc/RunIISummer20UL16NanoAODv2/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/NANOAODSIM/106X_mcRun2_asymptotic_v15-v1/280000/0DEE8BE7-06B0-A54B-8EFD-03555761B898.root",
      #dasurl+"/store/mc/RunIISummer20UL16NanoAODv2/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/NANOAODSIM/106X_mcRun2_asymptotic_v15-v1/280000/84C44657-05EB-204C-9507-0D408C291B06.root",
      t3dir+"DYJetsToLL_Summer20UL16NanoAODv2/99386FF5-D19F-8B40-915D-53B3DC7FFD23.root",
      t3dir+"DYJetsToLL_Summer20UL16NanoAODv2/EDF20656-7588-C547-A621-AE1247AE3E08.root",
      t3dir+"DYJetsToLL_Summer20UL16NanoAODv2/A4E16BDB-AD76-2D45-AECA-89C0E4135C82.root",
      t3dir+"DYJetsToLL_Summer20UL16NanoAODv2/E6523A98-8A0F-E24E-B8A0-2A6D4FC3BA6E.root",
      t3dir+"DYJetsToLL_Summer20UL16NanoAODv2/0DEE8BE7-06B0-A54B-8EFD-03555761B898.root",
      t3dir+"DYJetsToLL_Summer20UL16NanoAODv2/84C44657-05EB-204C-9507-0D408C291B06.root",
    ],nfilemax=nfilemax,verb=verbosity),
    Sample("DY_17","Summer19, UL2017",[
      eosdir+"UL2017/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/0132269A-092C-8149-A68F-80415D023182_skimjec_0.root",
      eosdir+"UL2017/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/0132269A-092C-8149-A68F-80415D023182_skimjec_1.root",
      eosdir+"UL2017/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/0132269A-092C-8149-A68F-80415D023182_skimjec_2.root",
      eosdir+"UL2017/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/0132269A-092C-8149-A68F-80415D023182_skimjec_3.root",
      eosdir+"UL2017/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/0132269A-092C-8149-A68F-80415D023182_skimjec_4.root",
      eosdir+"UL2017/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/0551C620-B703-DA48-AD28-747C72C73299_skimjec_0.root",
      eosdir+"UL2017/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/0551C620-B703-DA48-AD28-747C72C73299_skimjec_1.root",
      eosdir+"UL2017/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/0551C620-B703-DA48-AD28-747C72C73299_skimjec_2.root",
      eosdir+"UL2017/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/0551C620-B703-DA48-AD28-747C72C73299_skimjec_3.root",
      eosdir+"UL2017/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/0551C620-B703-DA48-AD28-747C72C73299_skimjec_4.root",
      eosdir+"UL2017/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/0806D81F-68EA-364D-85C6-4EF4E262D63D_skimjec_0.root",
      eosdir+"UL2017/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/0806D81F-68EA-364D-85C6-4EF4E262D63D_skimjec_1.root",
      eosdir+"UL2017/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/0806D81F-68EA-364D-85C6-4EF4E262D63D_skimjec_2.root",
      eosdir+"UL2017/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/0806D81F-68EA-364D-85C6-4EF4E262D63D_skimjec_3.root",
      eosdir+"UL2017/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/0806D81F-68EA-364D-85C6-4EF4E262D63D_skimjec_4.root",
      eosdir+"UL2017/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/0806D81F-68EA-364D-85C6-4EF4E262D63D_skimjec_5.root",
      eosdir+"UL2017/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/0806D81F-68EA-364D-85C6-4EF4E262D63D_skimjec_6.root",
      eosdir+"UL2017/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/0A6CDB21-5CA0-424E-94C1-504243CF1D8D_skimjec_0.root",
      eosdir+"UL2017/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/0A6CDB21-5CA0-424E-94C1-504243CF1D8D_skimjec_1.root",
      eosdir+"UL2017/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/0A6CDB21-5CA0-424E-94C1-504243CF1D8D_skimjec_2.root",
      eosdir+"UL2017/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/0A6CDB21-5CA0-424E-94C1-504243CF1D8D_skimjec_3.root",
      eosdir+"UL2017/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/0A6CDB21-5CA0-424E-94C1-504243CF1D8D_skimjec_4.root",
      eosdir+"UL2017/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/0BBA295F-DEF8-9047-8036-3C621638F9AE_skimjec_0.root",
      eosdir+"UL2017/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/0BBA295F-DEF8-9047-8036-3C621638F9AE_skimjec_1.root",
      eosdir+"UL2017/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/0BBA295F-DEF8-9047-8036-3C621638F9AE_skimjec_2.root",
      eosdir+"UL2017/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/0BBA295F-DEF8-9047-8036-3C621638F9AE_skimjec_3.root",
      eosdir+"UL2017/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/0BBA295F-DEF8-9047-8036-3C621638F9AE_skimjec_4.root",
      eosdir+"UL2017/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/0BBA295F-DEF8-9047-8036-3C621638F9AE_skimjec_5.root",
      eosdir+"UL2017/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/0BBA295F-DEF8-9047-8036-3C621638F9AE_skimjec_6.root",
      eosdir+"UL2017/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/0BBA295F-DEF8-9047-8036-3C621638F9AE_skimjec_7.root",
      eosdir+"UL2017/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/1171AFC4-3019-2846-9D00-CFD076E945C5_skimjec_0.root",
      eosdir+"UL2017/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/1171AFC4-3019-2846-9D00-CFD076E945C5_skimjec_1.root",
      eosdir+"UL2017/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/1171AFC4-3019-2846-9D00-CFD076E945C5_skimjec_2.root",
      eosdir+"UL2017/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/1171AFC4-3019-2846-9D00-CFD076E945C5_skimjec_3.root",
      eosdir+"UL2017/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/1171AFC4-3019-2846-9D00-CFD076E945C5_skimjec_4.root",
      eosdir+"UL2017/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/1171AFC4-3019-2846-9D00-CFD076E945C5_skimjec_5.root",
      eosdir+"UL2017/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/1171AFC4-3019-2846-9D00-CFD076E945C5_skimjec_6.root",
      eosdir+"UL2017/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/1171AFC4-3019-2846-9D00-CFD076E945C5_skimjec_7.root",
      eosdir+"UL2017/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/15977EC5-AE0E-E345-9A6E-401E5F474ED3_skimjec_0.root",
      eosdir+"UL2017/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/15977EC5-AE0E-E345-9A6E-401E5F474ED3_skimjec_1.root",
    ],nfilemax=nfilemax,verb=verbosity),
    Sample("DY_18","Summer19, UL2018",[
      eosdir+"UL2018/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/0024BF3A-8276-5B49-BD3D-62ADE1BB17D0_skimjec_0.root",
      eosdir+"UL2018/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/0024BF3A-8276-5B49-BD3D-62ADE1BB17D0_skimjec_1.root",
      eosdir+"UL2018/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/0024BF3A-8276-5B49-BD3D-62ADE1BB17D0_skimjec_2.root",
      eosdir+"UL2018/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/0024BF3A-8276-5B49-BD3D-62ADE1BB17D0_skimjec_3.root",
      eosdir+"UL2018/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/0024BF3A-8276-5B49-BD3D-62ADE1BB17D0_skimjec_4.root",
      eosdir+"UL2018/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/01A29285-50F4-DB47-8056-6674D91393A2_skimjec_0.root",
      eosdir+"UL2018/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/01A29285-50F4-DB47-8056-6674D91393A2_skimjec_1.root",
      eosdir+"UL2018/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/01A29285-50F4-DB47-8056-6674D91393A2_skimjec_2.root",
      eosdir+"UL2018/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/01A29285-50F4-DB47-8056-6674D91393A2_skimjec_3.root",
      eosdir+"UL2018/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/01A29285-50F4-DB47-8056-6674D91393A2_skimjec_4.root",
      eosdir+"UL2018/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/01A29285-50F4-DB47-8056-6674D91393A2_skimjec_5.root",
      eosdir+"UL2018/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/01A29285-50F4-DB47-8056-6674D91393A2_skimjec_6.root",
      eosdir+"UL2018/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/01A29285-50F4-DB47-8056-6674D91393A2_skimjec_7.root",
      eosdir+"UL2018/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/041D0051-7F32-7941-955A-0E70FD60A244_skimjec_0.root",
      eosdir+"UL2018/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/041D0051-7F32-7941-955A-0E70FD60A244_skimjec_1.root",
      eosdir+"UL2018/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/041D0051-7F32-7941-955A-0E70FD60A244_skimjec_2.root",
      eosdir+"UL2018/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/041D0051-7F32-7941-955A-0E70FD60A244_skimjec_3.root",
      eosdir+"UL2018/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/041D0051-7F32-7941-955A-0E70FD60A244_skimjec_4.root",
      eosdir+"UL2018/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/041D0051-7F32-7941-955A-0E70FD60A244_skimjec_5.root",
      eosdir+"UL2018/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/0A7617D1-1AE6-EE4F-8B0D-BD49DA182445_skimjec_0.root",
      eosdir+"UL2018/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/0A7617D1-1AE6-EE4F-8B0D-BD49DA182445_skimjec_1.root",
      eosdir+"UL2018/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/0A7617D1-1AE6-EE4F-8B0D-BD49DA182445_skimjec_2.root",
      eosdir+"UL2018/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/0A7617D1-1AE6-EE4F-8B0D-BD49DA182445_skimjec_3.root",
      eosdir+"UL2018/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/0A7617D1-1AE6-EE4F-8B0D-BD49DA182445_skimjec_4.root",
      eosdir+"UL2018/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/0CA3FF77-9905-F14C-9444-C7B368865A0C_skimjec_0.root",
      eosdir+"UL2018/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/0CA3FF77-9905-F14C-9444-C7B368865A0C_skimjec_1.root",
      eosdir+"UL2018/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/0CA3FF77-9905-F14C-9444-C7B368865A0C_skimjec_2.root",
      eosdir+"UL2018/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/0CA3FF77-9905-F14C-9444-C7B368865A0C_skimjec_3.root",
      eosdir+"UL2018/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/0CA3FF77-9905-F14C-9444-C7B368865A0C_skimjec_4.root",
      eosdir+"UL2018/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/0CA3FF77-9905-F14C-9444-C7B368865A0C_skimjec_5.root",
      eosdir+"UL2018/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/0CA3FF77-9905-F14C-9444-C7B368865A0C_skimjec_6.root",
      eosdir+"UL2018/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/0CA3FF77-9905-F14C-9444-C7B368865A0C_skimjec_7.root",
      eosdir+"UL2018/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/0CA3FF77-9905-F14C-9444-C7B368865A0C_skimjec_8.root",
      eosdir+"UL2018/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/0DF03192-6F67-654A-A6C6-451F7C1794D5_skimjec_0.root",
      eosdir+"UL2018/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/0DF03192-6F67-654A-A6C6-451F7C1794D5_skimjec_1.root",
      eosdir+"UL2018/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/0DF03192-6F67-654A-A6C6-451F7C1794D5_skimjec_2.root",
      eosdir+"UL2018/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/0DF03192-6F67-654A-A6C6-451F7C1794D5_skimjec_3.root",
      eosdir+"UL2018/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/0DF03192-6F67-654A-A6C6-451F7C1794D5_skimjec_4.root",
      eosdir+"UL2018/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/0DF03192-6F67-654A-A6C6-451F7C1794D5_skimjec_5.root",
      eosdir+"UL2018/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/0DF03192-6F67-654A-A6C6-451F7C1794D5_skimjec_6.root",
    ],nfilemax=nfilemax,verb=verbosity),
  ]
  
  # W2JetsToLNu
  #   head -n 40 ../PicoProducer/samples/files/UL2017/DYJetsToLL_M-50.txt | grep root
  #   dasgoclient -query="/W2JetsToLNu*/RunIISummer20UL16*/NANOAODSIM"
  #   dasgoclient -query="/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer20UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM file" --limit=8
  #   for f in $F; do peval "xrdcp root://xrootd-cms.infn.it/$f /pnfs/psi.ch/cms/trivcat/store/user/ineuteli/samples/tmp/W2JetsToLNu_Summer20UL16NanoAODv2/"; done
  samplesets['W2JetsToLNu'] = [
    Sample("W2J_16_preVFP_19","Summer19, UL2016 pre-VFP",[
      eosdir+"UL2016_preVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/0C6F5334-CFE6-404F-99E0-CC01CA44C7B3_skimjec_0.root",
      eosdir+"UL2016_preVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/0C6F5334-CFE6-404F-99E0-CC01CA44C7B3_skimjec_1.root",
      eosdir+"UL2016_preVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/0C6F5334-CFE6-404F-99E0-CC01CA44C7B3_skimjec_2.root",
      eosdir+"UL2016_preVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/0C6F5334-CFE6-404F-99E0-CC01CA44C7B3_skimjec_3.root",
      eosdir+"UL2016_preVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/0C6F5334-CFE6-404F-99E0-CC01CA44C7B3_skimjec_4.root",
      eosdir+"UL2016_preVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/0C6F5334-CFE6-404F-99E0-CC01CA44C7B3_skimjec_5.root",
      eosdir+"UL2016_preVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/0C6F5334-CFE6-404F-99E0-CC01CA44C7B3_skimjec_6.root",
      eosdir+"UL2016_preVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/0C6F5334-CFE6-404F-99E0-CC01CA44C7B3_skimjec_7.root",
      eosdir+"UL2016_preVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/1365422D-BF30-024C-8FC7-2147A481A76D_skimjec_0.root",
      eosdir+"UL2016_preVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/1365422D-BF30-024C-8FC7-2147A481A76D_skimjec_1.root",
      eosdir+"UL2016_preVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/1365422D-BF30-024C-8FC7-2147A481A76D_skimjec_2.root",
      eosdir+"UL2016_preVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/1365422D-BF30-024C-8FC7-2147A481A76D_skimjec_3.root",
      eosdir+"UL2016_preVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/212ADEC1-2C6F-7145-8C14-EA5025F2D637_skimjec_0.root",
      eosdir+"UL2016_preVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/212ADEC1-2C6F-7145-8C14-EA5025F2D637_skimjec_1.root",
      eosdir+"UL2016_preVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/212ADEC1-2C6F-7145-8C14-EA5025F2D637_skimjec_2.root",
      eosdir+"UL2016_preVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/212ADEC1-2C6F-7145-8C14-EA5025F2D637_skimjec_3.root",
      eosdir+"UL2016_preVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/212ADEC1-2C6F-7145-8C14-EA5025F2D637_skimjec_4.root",
      eosdir+"UL2016_preVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/2E48474E-B7FF-8F49-8403-4863C616ADEA_skimjec_0.root",
      eosdir+"UL2016_preVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/2E48474E-B7FF-8F49-8403-4863C616ADEA_skimjec_1.root",
      eosdir+"UL2016_preVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/2E48474E-B7FF-8F49-8403-4863C616ADEA_skimjec_2.root",
      eosdir+"UL2016_preVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/2E48474E-B7FF-8F49-8403-4863C616ADEA_skimjec_3.root",
      eosdir+"UL2016_preVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/2E48474E-B7FF-8F49-8403-4863C616ADEA_skimjec_4.root",
      eosdir+"UL2016_preVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/31A78F65-D131-6E4D-A167-C1A7187722FE_skimjec.root",
      eosdir+"UL2016_preVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/340219C0-AE9C-354A-9EF4-31710287C207_skimjec_0.root",
      eosdir+"UL2016_preVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/340219C0-AE9C-354A-9EF4-31710287C207_skimjec_1.root",
      eosdir+"UL2016_preVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/340219C0-AE9C-354A-9EF4-31710287C207_skimjec_2.root",
      eosdir+"UL2016_preVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/340219C0-AE9C-354A-9EF4-31710287C207_skimjec_3.root",
      eosdir+"UL2016_preVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/340219C0-AE9C-354A-9EF4-31710287C207_skimjec_4.root",
      eosdir+"UL2016_preVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/340219C0-AE9C-354A-9EF4-31710287C207_skimjec_5.root",
      eosdir+"UL2016_preVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/340219C0-AE9C-354A-9EF4-31710287C207_skimjec_6.root",
      eosdir+"UL2016_preVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/340219C0-AE9C-354A-9EF4-31710287C207_skimjec_7.root",
      eosdir+"UL2016_preVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/4371B1FE-3451-754E-AE36-18DAB2B9600C_skimjec_0.root",
      eosdir+"UL2016_preVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/4371B1FE-3451-754E-AE36-18DAB2B9600C_skimjec_1.root",
      eosdir+"UL2016_preVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/4371B1FE-3451-754E-AE36-18DAB2B9600C_skimjec_2.root",
      eosdir+"UL2016_preVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/4371B1FE-3451-754E-AE36-18DAB2B9600C_skimjec_3.root",
      eosdir+"UL2016_preVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/4371B1FE-3451-754E-AE36-18DAB2B9600C_skimjec_4.root",
      eosdir+"UL2016_preVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/4371B1FE-3451-754E-AE36-18DAB2B9600C_skimjec_5.root",
      eosdir+"UL2016_preVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/4371B1FE-3451-754E-AE36-18DAB2B9600C_skimjec_6.root",
      eosdir+"UL2016_preVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/4371B1FE-3451-754E-AE36-18DAB2B9600C_skimjec_7.root",
      eosdir+"UL2016_preVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM/45B7E9C6-E4FB-1549-8D8E-DF356F7DCD96_skimjec_0.root",
    ],nfilemax=nfilemax,verb=verbosity),
    Sample("W2J_16_postVFP_19","Summer19, UL2016 post-VFP",[
      eosdir+"UL2016_postVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/00A6167D-08DC-BB4F-92F4-D93E04827A82_skimjec_0.root",
      eosdir+"UL2016_postVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/00A6167D-08DC-BB4F-92F4-D93E04827A82_skimjec_1.root",
      eosdir+"UL2016_postVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/00A6167D-08DC-BB4F-92F4-D93E04827A82_skimjec_2.root",
      eosdir+"UL2016_postVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/00A6167D-08DC-BB4F-92F4-D93E04827A82_skimjec_3.root",
      eosdir+"UL2016_postVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/00A6167D-08DC-BB4F-92F4-D93E04827A82_skimjec_4.root",
      eosdir+"UL2016_postVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/00A6167D-08DC-BB4F-92F4-D93E04827A82_skimjec_5.root",
      eosdir+"UL2016_postVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/00A6167D-08DC-BB4F-92F4-D93E04827A82_skimjec_6.root",
      eosdir+"UL2016_postVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/018193F1-E4DF-4B42-9596-EA33BBE84DD0_skimjec_0.root",
      eosdir+"UL2016_postVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/018193F1-E4DF-4B42-9596-EA33BBE84DD0_skimjec_1.root",
      eosdir+"UL2016_postVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/018193F1-E4DF-4B42-9596-EA33BBE84DD0_skimjec_2.root",
      eosdir+"UL2016_postVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/018193F1-E4DF-4B42-9596-EA33BBE84DD0_skimjec_3.root",
      eosdir+"UL2016_postVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/10481335-12B7-EE40-8521-46839D656796_skimjec_0.root",
      eosdir+"UL2016_postVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/10481335-12B7-EE40-8521-46839D656796_skimjec_1.root",
      eosdir+"UL2016_postVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/10481335-12B7-EE40-8521-46839D656796_skimjec_2.root",
      eosdir+"UL2016_postVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/10481335-12B7-EE40-8521-46839D656796_skimjec_3.root",
      eosdir+"UL2016_postVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/10481335-12B7-EE40-8521-46839D656796_skimjec_4.root",
      eosdir+"UL2016_postVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/11218436-B8B1-3E47-8B37-535F5C21A9C0_skimjec_0.root",
      eosdir+"UL2016_postVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/11218436-B8B1-3E47-8B37-535F5C21A9C0_skimjec_1.root",
      eosdir+"UL2016_postVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/11218436-B8B1-3E47-8B37-535F5C21A9C0_skimjec_2.root",
      eosdir+"UL2016_postVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/11218436-B8B1-3E47-8B37-535F5C21A9C0_skimjec_3.root",
      eosdir+"UL2016_postVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/11218436-B8B1-3E47-8B37-535F5C21A9C0_skimjec_4.root",
      eosdir+"UL2016_postVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/145835A6-2DDC-D14E-8C15-C913F1D8AD0F_skimjec_0.root",
      eosdir+"UL2016_postVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/145835A6-2DDC-D14E-8C15-C913F1D8AD0F_skimjec_1.root",
      eosdir+"UL2016_postVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/145835A6-2DDC-D14E-8C15-C913F1D8AD0F_skimjec_2.root",
      eosdir+"UL2016_postVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/145835A6-2DDC-D14E-8C15-C913F1D8AD0F_skimjec_3.root",
      eosdir+"UL2016_postVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/145835A6-2DDC-D14E-8C15-C913F1D8AD0F_skimjec_4.root",
      eosdir+"UL2016_postVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/145835A6-2DDC-D14E-8C15-C913F1D8AD0F_skimjec_5.root",
      eosdir+"UL2016_postVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/145835A6-2DDC-D14E-8C15-C913F1D8AD0F_skimjec_6.root",
      eosdir+"UL2016_postVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/145835A6-2DDC-D14E-8C15-C913F1D8AD0F_skimjec_7.root",
      eosdir+"UL2016_postVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/145835A6-2DDC-D14E-8C15-C913F1D8AD0F_skimjec_8.root",
      eosdir+"UL2016_postVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/193BD7AD-DE6B-B646-AF61-A7BD09E4EF6E_skimjec_0.root",
      eosdir+"UL2016_postVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/193BD7AD-DE6B-B646-AF61-A7BD09E4EF6E_skimjec_1.root",
      eosdir+"UL2016_postVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/193BD7AD-DE6B-B646-AF61-A7BD09E4EF6E_skimjec_2.root",
      eosdir+"UL2016_postVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/193BD7AD-DE6B-B646-AF61-A7BD09E4EF6E_skimjec_3.root",
      eosdir+"UL2016_postVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/193BD7AD-DE6B-B646-AF61-A7BD09E4EF6E_skimjec_4.root",
      eosdir+"UL2016_postVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/193BD7AD-DE6B-B646-AF61-A7BD09E4EF6E_skimjec_5.root",
      eosdir+"UL2016_postVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/28577F67-BC98-EC42-A25A-CDEBFBC8AAF2_skimjec_0.root",
      eosdir+"UL2016_postVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/28577F67-BC98-EC42-A25A-CDEBFBC8AAF2_skimjec_1.root",
      eosdir+"UL2016_postVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/28577F67-BC98-EC42-A25A-CDEBFBC8AAF2_skimjec_2.root",
      eosdir+"UL2016_postVFP/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM/28577F67-BC98-EC42-A25A-CDEBFBC8AAF2_skimjec_3.root",
    ],nfilemax=nfilemax,verb=verbosity),
    Sample("W2J_16_postVFP_20","Summer20, UL2016 post-VFP",[
      t3dir+"W2JetsToLNu_Summer20UL16NanoAODv2/38AE733B-278C-454F-AB21-5A9E63FA032F.root",
      t3dir+"W2JetsToLNu_Summer20UL16NanoAODv2/232F9586-F716-6C4A-945C-75316EC35178.root",
      t3dir+"W2JetsToLNu_Summer20UL16NanoAODv2/60705AE8-592C-E043-B552-A12EEC59CC78.root",
      t3dir+"W2JetsToLNu_Summer20UL16NanoAODv2/1E5654F6-A826-E848-8722-9E094ACE6007.root",
      t3dir+"W2JetsToLNu_Summer20UL16NanoAODv2/11855910-CB02-2446-8DB9-9C955942DA79.root",
      t3dir+"W2JetsToLNu_Summer20UL16NanoAODv2/B9F25DED-3809-594C-9C0C-B9C4011AAB21.root",
      t3dir+"W2JetsToLNu_Summer20UL16NanoAODv2/CC93739C-A64D-0D4A-BFBB-E6901F91EA1C.root",
      t3dir+"W2JetsToLNu_Summer20UL16NanoAODv2/89E72512-E55F-AD44-B138-1EAE20C4741F.root",
    ],nfilemax=nfilemax,verb=verbosity),
    Sample("W2J_17","Summer19, UL2017",[
      eosdir+"UL2017/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/088EFCB6-BF93-0C44-A25F-5998744D4A98_skimjec_0.root",
      eosdir+"UL2017/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/088EFCB6-BF93-0C44-A25F-5998744D4A98_skimjec_1.root",
      eosdir+"UL2017/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/088EFCB6-BF93-0C44-A25F-5998744D4A98_skimjec_2.root",
      eosdir+"UL2017/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/088EFCB6-BF93-0C44-A25F-5998744D4A98_skimjec_3.root",
      eosdir+"UL2017/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/088EFCB6-BF93-0C44-A25F-5998744D4A98_skimjec_4.root",
      eosdir+"UL2017/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/23FD219A-8346-7645-A1A1-467BF8CFA609_skimjec_0.root",
      eosdir+"UL2017/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/23FD219A-8346-7645-A1A1-467BF8CFA609_skimjec_1.root",
      eosdir+"UL2017/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/23FD219A-8346-7645-A1A1-467BF8CFA609_skimjec_2.root",
      eosdir+"UL2017/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/23FD219A-8346-7645-A1A1-467BF8CFA609_skimjec_3.root",
      eosdir+"UL2017/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/3CE99273-8DB2-D146-9DEF-B3E3134ED87C_skimjec_0.root",
      eosdir+"UL2017/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/3CE99273-8DB2-D146-9DEF-B3E3134ED87C_skimjec_1.root",
      eosdir+"UL2017/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/3CE99273-8DB2-D146-9DEF-B3E3134ED87C_skimjec_2.root",
      eosdir+"UL2017/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/3CE99273-8DB2-D146-9DEF-B3E3134ED87C_skimjec_3.root",
      eosdir+"UL2017/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/3CE99273-8DB2-D146-9DEF-B3E3134ED87C_skimjec_4.root",
      eosdir+"UL2017/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/44DA9175-C14B-6441-9B34-5DE70D3770C3_skimjec_0.root",
      eosdir+"UL2017/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/44DA9175-C14B-6441-9B34-5DE70D3770C3_skimjec_1.root",
      eosdir+"UL2017/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/44DA9175-C14B-6441-9B34-5DE70D3770C3_skimjec_2.root",
      eosdir+"UL2017/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/44DA9175-C14B-6441-9B34-5DE70D3770C3_skimjec_3.root",
      eosdir+"UL2017/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/44DA9175-C14B-6441-9B34-5DE70D3770C3_skimjec_4.root",
      eosdir+"UL2017/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/4D2BA697-F093-A44B-ACD5-7C135ABC86CB_skimjec_0.root",
      eosdir+"UL2017/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/4D2BA697-F093-A44B-ACD5-7C135ABC86CB_skimjec_1.root",
      eosdir+"UL2017/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/4D2BA697-F093-A44B-ACD5-7C135ABC86CB_skimjec_2.root",
      eosdir+"UL2017/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/4D2BA697-F093-A44B-ACD5-7C135ABC86CB_skimjec_3.root",
      eosdir+"UL2017/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/4D2BA697-F093-A44B-ACD5-7C135ABC86CB_skimjec_4.root",
      eosdir+"UL2017/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/4D2BA697-F093-A44B-ACD5-7C135ABC86CB_skimjec_5.root",
      eosdir+"UL2017/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/50FE6439-6FAF-1E4F-9BD9-2BE03B3768E5_skimjec_0.root",
      eosdir+"UL2017/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/50FE6439-6FAF-1E4F-9BD9-2BE03B3768E5_skimjec_1.root",
      eosdir+"UL2017/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/50FE6439-6FAF-1E4F-9BD9-2BE03B3768E5_skimjec_2.root",
      eosdir+"UL2017/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/50FE6439-6FAF-1E4F-9BD9-2BE03B3768E5_skimjec_3.root",
      eosdir+"UL2017/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/50FE6439-6FAF-1E4F-9BD9-2BE03B3768E5_skimjec_4.root",
      eosdir+"UL2017/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/50FE6439-6FAF-1E4F-9BD9-2BE03B3768E5_skimjec_5.root",
      eosdir+"UL2017/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/5530F7A0-D588-7647-91C2-CF648525DAA6_skimjec_0.root",
      eosdir+"UL2017/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/5530F7A0-D588-7647-91C2-CF648525DAA6_skimjec_1.root",
      eosdir+"UL2017/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/5530F7A0-D588-7647-91C2-CF648525DAA6_skimjec_2.root",
      eosdir+"UL2017/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/5D853EF5-176A-1849-A3AB-A97C303D2FF5_skimjec_0.root",
      eosdir+"UL2017/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/5D853EF5-176A-1849-A3AB-A97C303D2FF5_skimjec_1.root",
      eosdir+"UL2017/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/5D853EF5-176A-1849-A3AB-A97C303D2FF5_skimjec_2.root",
      eosdir+"UL2017/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/5D853EF5-176A-1849-A3AB-A97C303D2FF5_skimjec_3.root",
      eosdir+"UL2017/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/5D853EF5-176A-1849-A3AB-A97C303D2FF5_skimjec_4.root",
      eosdir+"UL2017/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM/5D853EF5-176A-1849-A3AB-A97C303D2FF5_skimjec_5.root",
    ],nfilemax=nfilemax,verb=verbosity),
    Sample("W2J_18","Summer19, UL2018",[
      eosdir+"UL2018/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/07E64BB3-44FB-AC4C-921C-F3D31CD4A848_skimjec_0.root",
      eosdir+"UL2018/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/07E64BB3-44FB-AC4C-921C-F3D31CD4A848_skimjec_1.root",
      eosdir+"UL2018/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/07E64BB3-44FB-AC4C-921C-F3D31CD4A848_skimjec_2.root",
      eosdir+"UL2018/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/07E64BB3-44FB-AC4C-921C-F3D31CD4A848_skimjec_3.root",
      eosdir+"UL2018/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/07E64BB3-44FB-AC4C-921C-F3D31CD4A848_skimjec_4.root",
      eosdir+"UL2018/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/0AAE1402-C549-2544-ABDD-FCB68EB47F0C_skimjec.root",
      eosdir+"UL2018/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/1A156DE8-1277-5446-9B04-D5B8E2B0210C_skimjec_0.root",
      eosdir+"UL2018/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/1A156DE8-1277-5446-9B04-D5B8E2B0210C_skimjec_1.root",
      eosdir+"UL2018/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/1A156DE8-1277-5446-9B04-D5B8E2B0210C_skimjec_2.root",
      eosdir+"UL2018/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/1A156DE8-1277-5446-9B04-D5B8E2B0210C_skimjec_3.root",
      eosdir+"UL2018/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/1A156DE8-1277-5446-9B04-D5B8E2B0210C_skimjec_4.root",
      eosdir+"UL2018/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/1A156DE8-1277-5446-9B04-D5B8E2B0210C_skimjec_5.root",
      eosdir+"UL2018/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/1BA69C89-A31E-1142-9772-2CCCBB5B7F86_skimjec.root",
      eosdir+"UL2018/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/1CB1C6DD-4553-1545-9308-9E775F264B5B_skimjec_0.root",
      eosdir+"UL2018/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/1CB1C6DD-4553-1545-9308-9E775F264B5B_skimjec_1.root",
      eosdir+"UL2018/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/1CB1C6DD-4553-1545-9308-9E775F264B5B_skimjec_2.root",
      eosdir+"UL2018/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/373A1398-238B-1547-B73A-BEF2C563730D_skimjec.root",
      eosdir+"UL2018/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/388CF9CF-9055-A44A-A280-F11330E31197_skimjec_0.root",
      eosdir+"UL2018/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/388CF9CF-9055-A44A-A280-F11330E31197_skimjec_1.root",
      eosdir+"UL2018/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/3AFA3337-9AB8-EC49-AEDC-757A8365FA89_skimjec.root",
      eosdir+"UL2018/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/4057C551-EEE0-124E-BFBF-08044AF7B98F_skimjec_0.root",
      eosdir+"UL2018/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/4057C551-EEE0-124E-BFBF-08044AF7B98F_skimjec_1.root",
      eosdir+"UL2018/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/4057C551-EEE0-124E-BFBF-08044AF7B98F_skimjec_2.root",
      eosdir+"UL2018/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/4057C551-EEE0-124E-BFBF-08044AF7B98F_skimjec_3.root",
      eosdir+"UL2018/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/4057C551-EEE0-124E-BFBF-08044AF7B98F_skimjec_4.root",
      eosdir+"UL2018/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/4057C551-EEE0-124E-BFBF-08044AF7B98F_skimjec_5.root",
      eosdir+"UL2018/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/4B141D6E-3EE4-D747-A64B-6A99D98F2ED0_skimjec_0.root",
      eosdir+"UL2018/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/4B141D6E-3EE4-D747-A64B-6A99D98F2ED0_skimjec_1.root",
      eosdir+"UL2018/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/4B141D6E-3EE4-D747-A64B-6A99D98F2ED0_skimjec_2.root",
      eosdir+"UL2018/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/4B141D6E-3EE4-D747-A64B-6A99D98F2ED0_skimjec_3.root",
      eosdir+"UL2018/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/4C73E361-3378-5349-B68C-1A50A0E7A11F_skimjec.root",
      eosdir+"UL2018/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/5464D4D6-8DB7-B84C-93BC-C924E06EACB9_skimjec_0.root",
      eosdir+"UL2018/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/5464D4D6-8DB7-B84C-93BC-C924E06EACB9_skimjec_1.root",
      eosdir+"UL2018/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/5464D4D6-8DB7-B84C-93BC-C924E06EACB9_skimjec_2.root",
      eosdir+"UL2018/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/5464D4D6-8DB7-B84C-93BC-C924E06EACB9_skimjec_3.root",
      eosdir+"UL2018/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/5464D4D6-8DB7-B84C-93BC-C924E06EACB9_skimjec_4.root",
      eosdir+"UL2018/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/5A9FFE18-5D1D-4F4E-A93F-2A86F589C88C_skimjec_0.root",
      eosdir+"UL2018/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/5A9FFE18-5D1D-4F4E-A93F-2A86F589C88C_skimjec_1.root",
      eosdir+"UL2018/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/5A9FFE18-5D1D-4F4E-A93F-2A86F589C88C_skimjec_2.root",
      eosdir+"UL2018/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/5A9FFE18-5D1D-4F4E-A93F-2A86F589C88C_skimjec_3.root",
    ],nfilemax=nfilemax,verb=verbosity),
  ]
  
  # FILTER
  for sample in samplesets.keys():
    if filters and not any(f in sample for f in filters):
      samplesets.pop(sample)
    if vetoes and any(f in sample for f in vetoes):
      samplesets.pop(sample)
  
  # COLORS
  colors = _lcolors[:]
  if filters==['W2JetsToLNu']: # for easy comparison to DYJetsPlots
    print colors
    colors.remove(colors[1])
    print colors
  
  # COMPARE
  compare_nano(samplesets,tag=tag,outdir="plots",parallel=parallel,verb=verbosity,colors=colors)


if __name__ == "__main__":
  import sys
  from argparse import ArgumentParser
  argv = sys.argv
  description = """Simple plotting script to compare distributions in nanoAOD tuples"""
  parser = ArgumentParser(prog="plot_compare_nano",description=description,epilog="Good luck!")
  #parser.add_argument('files',           nargs='*', default=[ ], action='store',
  #                                       help="input file(s) (multiple files are added in TChain)" )
  parser.add_argument('-s', '--samples',  nargs='+',action='store',
                                          help="only run these samples" )
  parser.add_argument('-x', '--veto',     nargs='+',dest='vetoes', action='store',
                                          help="do not run these samples" )
  parser.add_argument('-m', '--nfilemax', type=int, default=-1, action='store',
                                          help="maximum number of file" )
  parser.add_argument('-v', '--verbose',  dest='verbosity', type=int, nargs='?', const=1, default=0, action='store',
                                          help="set verbosity" )
  args = parser.parse_args()
  LOG.verbosity = args.verbosity
  PLOG.verbosity = args.verbosity-1
  main(args)
  print "\n>>> Done."
  
