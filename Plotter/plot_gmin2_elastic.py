#! /usr/bin/env python3
# Author: Izaak Neutelings (August 2023)
# Description: Measure elastic SF for g-2
# Instructions:
#   ./plot_gmin2_elastic.py -y Run2 -m sf -s 3,7 -p -v
#   ./plot_gmin2_elastic.py -y Run2 -m comp -s 3,7 -p -v
print(">>> Importing...")
import os, json
from array import array
#print(">>> Importing ROOT...")
import ROOT; ROOT.PyConfig.IgnoreCommandLineOptions = True
from ROOT import TF1, kAzure, kRed, kGreen, kOrange #, kMagenta
print(">>> Importing TauFW.sample...")
from config.gmin2.samples import * # for general getsampleset
import TauFW.Plotter.sample.utils as GLOB
from TauFW.Plotter.sample.utils import LOG; SLOG = LOG
from TauFW.Plotter.plot.Plot import LOG as PLOG
from TauFW.Plotter.plot.Stack import Plot, Stack, Ratio, TLegend
from TauFW.Plotter.plot.string import filtervars
from TauFW.common.tools.root import ensureTFile, rootrepr, loadmacro
from TauFW.common.tools.RDataFrame import RDF
from plot_compare_gmin2 import getbaseline, getweight, getsampleset, makemcsample,\
                               loadhist, loadallhists, savehist,\
                               xsec_mm, xsec_tt, xsec_ww
print(">>> Done importing...")
mbins = list(range(50,70,10))+list(range(70,110,5))+list(range(110,200,10))+\
        list(range(200,300,25))+list(range(300,400,50))+[400,500,600,800]
mbins2 = list(range(50,120,10))+list(range(120,160,20))+list(range(160,200,40))+\
         list(range(200,300,50))+[300,400,600,800]
#assert all(e in mbins for e in mbins2) # make sure all edges of mbins2 is in mbins


def getsamples(sampleset,channel,era,loadhists=False,dy=False,verb=0):
  setera(era) # set era for plot style and lumi-xsec normalization
  
  # LOAD WEIGHTS
  ###wgt_dy  = "" #( ntrack_all==0 ? 3.1 : ntrack_all==1 ? 2.3 : 1 )"
  wgt_sig = "" #( ntrack_all==0 ? 3.1 : ntrack_all==1 ? 2.3 : 1 )"
  if loadhists: # skip recreating histograms (fast!)
    print(">>> Skip loading PU track corrections...")
  else: # create histograms from scratch (slow...)
    print(">>> Loading PU track corrections...")
    loadmacro("python/corrections/g-2/corrs_ntracks.C",fast=True,verb=verb+1)
    from ROOT import loadPUTrackWeights
    loadPUTrackWeights(era)
    wgt_sig = "getPUTrackWeight(ntrack_pu,z_mumu,$ERA)" # set $ERA later
    print(">>> Done loading corrections!")
  
  # CREATE SAMPLES
  print(">>> GLOB.lumi=%s"%(GLOB.lumi))
  sample_obs = sampleset.get('Observed',unique=True,verb=verb-1)
  sample_dy  = sampleset.get('DY',unique=True,verb=verb-1) if dy else None
  sample_sig = makemcsample('Signal','GGToMuMu',"#gamma#gamma -> #mu#mu (elastic)",xsec_mm,channel,era,
                            tag="",extraweight=wgt_sig,color=kRed-9,verb=verb)#+3
  sample_ww  = makemcsample('VV','GGToWW',"#gamma#gamma -> WW (elastic)",xsec_ww,channel,era,
                            tag="",extraweight=wgt_sig,color=kOrange-9,verb=verb)#+3
  setera(era) # set era for plot style and lumi-xsec normalization
  print(">>> GLOB.lumi=%s"%(GLOB.lumi))
  
  return sample_obs, sample_dy, sample_sig, sample_ww
  

def integrateZWindow(hist,xmin=75,xmax=105,verb=0):
  binlow   = hist.GetXaxis().FindBin(xmin+0.1)
  binhigh  = hist.GetXaxis().FindBin(xmax-0.1)
  edgelow  = hist.GetXaxis().GetBinLowEdge(binlow)
  edgehigh = hist.GetXaxis().GetBinUpEdge(binhigh)
  if verb>=2:
    print(f">>> integrateInZWindow: xmin={xmin}, binlow={binlow}, edgelow={edgelow}")
    print(f">>> integrateInZWindow: xmax={xmax}, binhigh={binhigh}, edgehigh={edgehigh}")
  assert xmin==edgelow, f"xmin={xmin}, binlow={binlow}, edgelow={edgelow}"
  assert xmax==edgehigh, f"xmax={xmax}, binhigh={binhigh}, edgehigh={edgehigh}"
  integral = hist.Integral(binlow,binhigh)
  if verb>=2:
    print(f">>> integrateInZWindow: integral={integral:.2f}")
  return integral
  

def studyInclBkg(sampleset,channel,tag="",outdir="plots/g-2/elastic/bkg",era="",
         selfilter=None,pdf=True,loadhists=False,verb=0):
  """Study incl. bkg."""
  LOG.header("studyInclBkg")
  
  # SETTINGS
  fraction  = True #and False
  loadhists = loadhists #and False
  hfname    = "%s/elastic_sb_%s.root"%(outdir,era)
  hfile     = ensureTFile(hfname,'READ' if loadhists else 'UPDATE') # back up histograms for reuse
  
  # SELECTIONS
  baseline = getbaseline(channel)
  sel_sb   = f"{baseline} && aco<0.015 && %s<=ntrack_all && ntrack_all<=%s"
  tit_nt   = "N_{#lower[-0.23]{track}}"
  selections = [ # plot these selections
    #Sel(f"A < 0.015, {tit_nt} = 0",  sel_sr_0t, fname="acolt0p015-ntracks0"),
    #Sel(f"A < 0.015, {tit_nt} = 1",  sel_sr_1t, fname="acolt0p015-ntracks1"),
  ]
  for a, b in [
    (3,6),
    (3,7),
    #(3,8),
    (4,7), #(4,8), (4,10),
    (5,8), #(5,8),
    (5,10),
  ]:
    tit  = f"A < 0.015, {a} <= {tit_nt} <= {b}"
    ssel = f"{baseline} && aco<0.015 && {a}<=ntrack_all && ntrack_all<={b}"
    fsel = f"acolt0p015-ntracks{a}to{b}"
    sel  = Sel(tit, ssel, fname=fsel)
    selections.append(sel)
  selections = filtervars(selections,selfilter) # filter variable list with -S/--sel flag
  
  # VARIABLES
  #mbins = list(range(50,140,10))+list(range(140,200,20))+\
  #        list(range(200,300,25))+list(range(300,400,50))+[400,500,600,800]
  variables = [
    #Var('m_ll', "m_mumu", 80, 50, 450, fname="m_mumu_fine", logy=True, ymargin=1.18, logyrange=6.5 ),
    Var('m_ll', "m_mumu", mbins2, fname="m_mumu", logy=True, ymargin=1.18, logyrange=7 ),
  ]
  
  # SAMPLES
  sample_obs, sample_dy, sample_sig, sample_ww = getsamples(sampleset,channel,era,dy=True,verb=verb)
  samples = [sample_obs,sample_dy,sample_ww,sample_sig]
  
  # LOOP over SELECTIONS
  outdir = ensuredir(repkey(outdir,CHANNEL=channel,ERA=era))
  exts   = ['png','pdf'] if pdf else ['png'] # extensions
  hists_bkg = { v: [ ] for v in variables } # for comparing incl. bkg later
  hists_dy  = { v: [ ] for v in variables } # for comparing DY later
  for selection in selections:
    LOG.header("Selection %r: %r"%(selection.filename,selection.selection))
    #print(">>> Selection %r: %r"%(selection.title,selection.selection))
    htitle = selection.title.split(', ')[-1]
    
    # STEP 1: Create observed data & signal in signal region
    LOG.color("Step 1: Creating hists...",b=True)
    bkgname = "bkg_incl"
    hists = { s: { } for s in samples } # side band
    for sample in samples:
      if loadhists: # skip recreating histograms (fast!)
        hists[sample] = loadallhists(hfile,variables,variables,sample,subdir=selection,verb=verb)
      else: # create histograms from scratch (slow...)
        hists[sample] = sample.gethist(variables,selection,verb=verb)
    
    # STEP 2: Create inclusive background
    LOG.color("Step 2: Create inclusive background...",b=True)
    hists[bkgname] = { } # overwrite previous
    for var in variables:
      hist_bkg = hists[sample_obs][var].Clone(f"{var.filename}_{selection.filename}_{bkgname}")
      hist_bkg.Add(hists[sample_ww][var], -1) # subtract WW signal
      hist_bkg.Add(hists[sample_sig][var],-1) # subtract mumu signal
      hist_bkg.SetFillColor(kAzure-9)
      hist_bkg.SetTitle("Incl. bkg.")
      hist_bkg2 = hist_bkg.Clone(hist_bkg.GetName()+'_clone') # store for later comparison
      hist_bkg2.SetTitle(htitle)
      hists[bkgname][var] = hist_bkg
      hists_bkg[var].append(hist_bkg2)
      hist_dy = hists[sample_dy][var]
      hist_dy.SetTitle(htitle)
      hists_dy[var].append(hist_dy)
      
      # STORE for later reuse
      if not loadhists: # store for later reuse
        for sample in hists.keys():
          savehist(hists[sample][var],hfile,var,var,sample,subdir=selection,verb=verb+2) # store for later use
    
    # STEP 3: Plot
    LOG.color("Step 3: Plot...",b=True)
    fname = "%s/$VAR_%s-%s-%s$TAG"%(outdir,channel.replace('mu','m').replace('tau','t'),selection.filename,era)
    text  = selection.title
    for var in variables:
      hist_obs  = hists[sample_obs][var] # observed
      hists_exp = [hists[s][var] for s in [bkgname,sample_sig,sample_ww]] # expected bkg + sig
      stack = Stack(var,hist_obs,hists_exp,clone=True,verb=verb)
      stack.draw(fraction=fraction,rmin=0,rmax=1.25)
      stack.drawlegend(twidth=1)
      stack.drawtext(text)
      stack.saveas(fname,ext=exts,tag=tag)
      stack.close()
  
  # PLOT COMPARISON of Incl. Bkg.
  texts = [f"A < 0.015","Incl. bkg."]
  fname  = "%s/compareInclBkg_$VAR_%s-acolt0p015-%s$TAG"%(outdir,channel.replace('mu','m').replace('tau','t'),era)
  for var in variables:
    #for h in hists_bkg[var]:
    #  print(rootrepr(h),h.Integral())
    plot = Plot(var,hists_bkg[var],norm=True)
    plot.draw(lstyle=1,rrange=0.2,staterr=True,enderrorsize=4,msize=0.5,#colors=lcols,mstyles=mstyles
              ratio=1,logy=True,ymargin=1.29,logyrange=5.1,verb=verb+1)
    plot.drawlegend(pos='TR',tsize=0.052)
    plot.drawtext(texts,size=0.052)
    plot.saveas(fname,ext=exts)
    plot.close(keep=False)
  
  # PLOT COMPARISON of Drell-Yan
  texts = [f"A < 0.015","Drell-Yan MC"]
  fname  = "%s/compareDY_$VAR_%s-acolt0p015-%s$TAG"%(outdir,channel.replace('mu','m').replace('tau','t'),era)
  sel_0t = f"{baseline} && aco<0.015 && ntrack_all==0"
  sel_1t = f"{baseline} && aco<0.015 && ntrack_all==1"
  selections = [ # plot these selections
    Sel(f"{tit_nt} = 0",  sel_0t, fname="acolt0p015-ntracks0"),
    Sel(f"{tit_nt} = 1",  sel_1t, fname="acolt0p015-ntracks1"),
  ]
  for var in variables:
    hists = [ ]
    for selection in selections:
      htitle = selection.title.split(', ')[-1]
      if loadhists or True: # always create histogram from scratch
        hist = sample_dy.gethist(var,selection,verb=verb)
        hist.SetTitle(htitle)
        savehist(hist,hfile,var,var,sample_dy,subdir=selection,verb=verb) # store for later reuse
      else:
        hist = loadhist(hfile,var,var,sample_dy,subdir=selection,verb=verb)
      hist.SetTitle(htitle)
      hists.append(hist)
    hists += hists_dy[var]
    ##for hist in hists:
    ##  hist.SetTitle(f"Drell-Yan MC, {selection.title}")
    plot = Plot(var,hists,norm=True)
    plot.draw(lstyle=1,rrange=0.2,staterr=True,enderrorsize=4,msize=0.5,#colors=lcols,mstyles=mstyles
              ratio=1,ncols=2,logy=True,ymargin=1.29,logyrange=5.1,verb=verb+1)
    plot.drawlegend(pos='TR',tsize=0.052)
    plot.drawtext(texts,size=0.052)
    plot.saveas(fname,ext=exts)
    plot.close(keep=False)
    

def measureElasicSF(sampleset,channel,tag="",outdir="plots/g-2/elastic",era="",
         selfilter=None,pdf=True,loadhists=False,sideband=None,verb=0):
  """Test plotting of SampleSet class for data/MC comparison."""
  LOG.header("measureElasicSF")
  
  # SETTINGS
  fraction  = True #and False
  loadhists = loadhists #and False
  foption   = 'UPDATE' #'READ' if loadhists else 'UPDATE'
  outdir    = ensuredir(repkey(outdir,CHANNEL=channel,ERA=era))
  jfname    = "%s/elastic.json"%(outdir)
  hfname    = "%s/elastic_%s.root"%(outdir,era)
  hfile     = ensureTFile(hfname,'UPDATE') # back up histograms for reuse
  fcols     = [ kRed, kGreen, kOrange ] # line colors for fit functions
  ftits     = [ "Flat", "Lin.", "Quadr." ] # titles for fit functions
  rtitle    = "#frac{Obs. #minus Bkg.}{#gamma#gamma #rightarrow #mu#mu, WW}  "
  chstr     = channel.replace('mu','m').replace('tau','t') 
  redoes    = [0,1,2]
  bkgname   = "bkg_incl"
  exts      = ['png','pdf'] if pdf else ['png'] # extensions
  if sideband==None:
  #   ntmin, ntmax = 3, 6 # ntrack range in side band
    ntmin, ntmax = 3, 7 # ntrack range in side band
  #   ###ntmin, ntmax = 3, 8 # ntrack range in side band
  #   ntmin, ntmax = 4, 7 # ntrack range in side band
  #   ntmin, ntmax = 5, 8 # ntrack range in side band
  #   ntmin, ntmax = 5, 10 # ntrack range in side band
  else:
    ntmin, ntmax = (int(t.strip(',')) for t in sideband.split(','))
  print(f">>> loadhists = {loadhists!r}")
  print(f">>> jfname    = {jfname!r}")
  print(f">>> hfname    = {hfname!r}")
  print(f">>> sideband  = {ntmin!r} <= ntrack <= {ntmax!r}")
  
  # SELECTIONS
  baseline = getbaseline(channel)
  sel_0t   = f"{baseline} && ntrack_all==0"
  sel_1t   = f"{baseline} && ntrack_all==1"
  sel_sr   = f"{baseline} && aco<0.015 && ntrack_all<=1"
  tit_nt   = "N_{#lower[-0.23]{track}}"
  selections = [ # plot these selections
    #Sel(f"{tit_nt} <= 1",            sel_sr,    fname="ntracksleq1"),
    #Sel(f"{tit_nt} = 0",             sel_0t,    fname="ntracks0"),
    #Sel(f"{tit_nt} = 1",             sel_1t,    fname="ntracks1"),
    #Sel(f"A < 0.015, {tit_nt} <= 1", sel_sr,    fname="acolt0p015-ntracksleq1"),
    Sel(f"A < 0.015, {tit_nt} = 0",  f"{baseline} && aco<0.015 && ntrack_all==0", fname="acolt0p015-ntracks0"),
    Sel(f"A < 0.015, {tit_nt} = 1",  f"{baseline} && aco<0.015 && ntrack_all==1", fname="acolt0p015-ntracks1"),
  ]
  if ntmin in [3,4] and ntmax in [7]:
    selections += [ # study
      Sel(f"A < 0.015, {tit_nt} = 2",  f"{baseline} && aco<0.015 && ntrack_all==2", fname="acolt0p015-ntracks2"),
      Sel(f"A < 0.015, {tit_nt} = 3",  f"{baseline} && aco<0.015 && ntrack_all==3", fname="acolt0p015-ntracks3"),
  ]
  selections = filtervars(selections,selfilter) # filter variable list with -S/--sel flag
  
  # SELECTIONS for ntrack SIDEBAND to estimate incl. background
  allselections = selections[:] # SR + SB selections
  sel_sb_dict   = { } # to avoid duplicate objects
  for selection in selections:
    fname_sb = re.sub(r"ntracks(?:leq)?\d",f"ntracks{ntmin}to{ntmax}",selection.filename)
    tit_sb   = re.sub(f"{re.escape(tit_nt)}\s*(?:#leq|<|<?=)\s*\d+",f"{ntmin} <= {tit_nt} <= {ntmax}",selection.title) #tit_nt
    repl     = ('ntrack_all[<=]=?[0123]',f"{ntmin}<=ntrack_all && ntrack_all<={ntmax}")
    sel_sb   = selection.clone(title=tit_sb,replace=repl,regex=True,fname=fname_sb,verb=verb)
    if sel_sb.selection in sel_sb_dict: # duplicate !
      assert sel_sb.filename==fname_sb, f"sel_sb.filename={sel_sb.filename!r}, fname_sb={fname_sb!r}"
      #assert sel_sb.title==tit_sb, f"sel_sb.title={sel_sb.title!r}, tit_sb={tit_sb!r}"
      sel_sb = sel_sb_dict[sel_sb.selection]
    else: # new side band
      sel_sb_dict[sel_sb.selection] = sel_sb
      allselections.append(sel_sb)
    selection.sideband = sel_sb
    selection.issr = any("ntracks_all=="+n in selection.selection for n in '01')
  
  # VARIABLES
  variables = [
    #Var('m_ll', "m_mumu", 80, 50, 450, fname="m_mumu_fine", logy=True, ymargin=1.18, logyrange=6.5 ),
    Var('m_ll', "m_mumu", mbins, fname="m_mumu", logy=True, ymargin=1.18, logyrange=7 ),
  ]
  
  # JSON file for storing SFs
  sfs = { }
  if os.path.isfile(jfname):
    with open(jfname,'r') as infile:
      sfs = json.load(infile)
  for era_ in ['UL2016_preVFP','UL2016_postVFP','UL2017','UL2018','Run2']:
    sfs.setdefault(era_,{ })
    for sel in selections:
      sname = sel.filename
      sfs[era_].setdefault(sname,{ }) # era -> selection
      key_sb = sel.sideband.filename
      for tit in ['ZWindow']+ftits:
        sfs[era_][sname].setdefault(key_sb,{ }).setdefault(tit,{ }) # era -> selection -> sideband -> fit title -> fit
  
  # SAMPLES
  sample_obs, sample_dy, sample_sig, sample_ww = getsamples(sampleset,channel,era,dy=True,verb=verb)
  samples = [sample_obs, sample_dy, sample_ww, sample_sig]
  
  # STEP 0: Create observed data & signal in signal region
  LOG.color("Step 0: Creating hists...",b=True)
  allhists = { } # { sample: { selection: { variable: hist } } }
  for sample in samples:
    LOG.color("Sample %s (%r) for %s variables, and %s selections"%(
      sample.name,sample.title,len(variables),len(allselections)),c='grey',b=True)
    if loadhists: # skip recreating histograms (fast!)
      allhists[sample] = loadallhists(hfile,variables,variables,sample,subdir=allselections,verb=verb)
    elif hasattr(sample,'gethist'): # create histograms from scratch (slow...)
      print(f">>>   Creating hist for {sample.name}...")
      #allhists[sample] = sample.gethist(variables,allselections,verb=verb+2)
      allhists[sample] = sample.gethist(variables,allselections,preselect=baseline,verb=verb+1)
  
  # LOOP over SELECTIONS
  ratios_dy = { s: { } for s in allselections } # to compute DY extrapolation SF
  for selection in selections:
    LOG.header("Selection %r: %r"%(selection.filename,selection.selection.replace(baseline+" && ",'')))
    #print(">>> Selection %r: %r"%(selection.title,selection.selection))
    sel_sb = selection.sideband
    
    # STEP 1: Retrieve observed data & signal histograms
    LOG.color("Step 1: Retrieve histograms for this selection...",b=True)
    #hists_obs, hists_bkg, hists_ww, hists_sig = [ ], [ ], [ ], [ ]
    hists_sr = { } # signal region (ntrack==0, 1)
    hists_sb = { } # side band (high track)
    for sample in samples: # { sample: { variable: hist } }
      hists_sr[sample] = allhists[sample][selection]
      hists_sb[sample] = allhists[sample][sel_sb]
    
    # STORE for later reuse
    if not loadhists: # store for later reuse
      for var in variables:
        for sample in hists_sr: # SIGNAL REGION
          if not isinstance(sample,str): # store everything, except incl. bkg.
            savehist(hists_sr[sample][var],hfile,var,var,sample,subdir=selection,verb=verb+2) # store for later reuse
    
    # GET ANSATZ SF for JSON
    #sf_el = 2.6 if 'ntrack_all==0' in selection.selection else 2.8 # ansatz SF for this selection (old, 11/2024)
    sf_el = 2.7 if 'ntrack_all==0' in selection.selection else 2.7 # ansatz SF for this selection (new, 11/2024)
    sfs_  = sfs[era][selection.filename][sel_sb.filename].get('Flat',{ })
    if len(sfs_)>=1:
      lastkey = list(sorted(sfs_.keys()))[-1]
      sf_el   = float(sfs_[lastkey]['0'].split(' ')[0]) # reuse
    
    # STEP 2: Create inclusive background from side band with inverted track selections
    LOG.color("Step 2: Create inclusive background...",b=True)
    
    # STEP 2a: Create background histogram from side band for first and last time
    if bkgname not in hists_sb: # create background histogram from side band for first and last time
      LOG.color("Step 2a: Create inclusive background in side band...",b=True)
      hists_sb[bkgname] = { } # { variable: hist }
      allhists[bkgname] = { sel_sb: { } } # { selection: { variable: hist } }
      for var in variables:
        hist_sb_bkg = hists_sb[sample_obs][var].Clone(f"{var.filename}_{fname_sb}_{bkgname}")
        hist_sb_bkg.Add(hists_sb[sample_ww][var], -1) # subtract WW signal (note: no rescaling)
        hist_sb_bkg.Add(hists_sb[sample_sig][var],-1) # subtract mumu signal (note: no rescaling)
        hist_sb_bkg.SetFillColor(kAzure-9)
        hist_sb_bkg.SetTitle("Incl. bkg.")
        hists_sb[bkgname][var] = hist_sb_bkg # for plotting
        allhists[bkgname][sel_sb][var] = hist_sb_bkg # save for next selection in iteration
      
      # STORE for later reuse
      if not loadhists: # store for later reuse
        for var in variables:
          for sample in hists_sb: # store everything
            savehist(hists_sb[sample][var],hfile,var,var,sample,subdir=sel_sb,verb=verb) # store for later reuse
      
      # STEP 2b: Plot side band region
      LOG.color("Step 2b: Plot sideband...",b=True)
      fname = f"{outdir}/$VAR_{chstr}-{sel_sb.filename}-{era}$TAG"
      text  = sel_sb.title
      for var in variables:
        hist_obs  = hists_sb[sample_obs][var] # observed
        hists_exp = [hists_sb[s][var] for s in [bkgname,sample_sig,sample_ww]] # expected bkg + sig
        stack = Stack(var,hist_obs,hists_exp,clone=True,verb=verb)
        stack.draw(fraction=fraction,rmin=0,rmax=1.25,lowerpanels=2)
        stack.drawlegend(twidth=1)
        stack.drawtext(text)
        stack.canvas.cd(3)
        fstack = stack.ratio.fraction
        frame3 = fstack.GetStack().Last()
        frame3.Draw()
        fstack.Draw('HISTSAME')
        stack.setaxes(frame3,ymin=1e-3,ymax=1,logy=True,xtitle=var.title,ytitle="Fractions",
                      nydiv=506,center=True,latex=False,drawx=True,verb=verb)
        stack.saveas(fname,ext=exts,tag=tag)
        stack.close()
    
    # PERFORM FIT several times to let flat SF converge
    for redo in redoes: # perform fit twice
      fitkey = f"fit{redo+1}"+tag # for JSON dictionary of SFs
      if redo>=1:
        print(f">>>\n>>> FIT AGAIN! redo={redo} with sf={sf_el}...")
      
      # STEP 2c: Create inclusive background in signal region
      LOG.color("Step 2c: Create incl. bkg. in signal region...",b=True)
      hists_sr[bkgname] = { } # overwrite previous
      for var in variables:
        hist_bkg = hists_sb[bkgname][var].Clone(f"{var.filename}_{selection.filename}_{bkgname}")
        hists_sr[bkgname][var] = hist_bkg
      
      # STEP 2d: Apply extrapolation SF from DY MC
      if 'extraSF' in tag:
        LOG.color("Step 2d: Apply extrapolation SF from DY MC...",b=True)
        for var in variables:
          hist_sr_bkg = hists_sr[bkgname][var]   # signal region (low ntracks)
          hist_sr_dy  = hists_sr[sample_dy][var] # signal region (low ntracks)
          hist_sb_dy  = hists_sb[sample_dy][var] # sideband (high ntracks)
          if redo==0: # only do this the first time
            ntrack     = int(selection.title[-1])
            n_dy_sr    = integrateZWindow(hist_sr_dy,75,105)
            n_dy_sb    = integrateZWindow(hist_sb_dy,75,105)
            norm_dy    = n_dy_sb/n_dy_sr # normalize to Z peak
            print(f">>>   n_dy_sr={n_dy_sr:.2f}, n_dy_sb={n_dy_sb:.2f} => norm_dy={norm_dy} to Z peak")
            ratio_dy   = hist_sr_dy.Rebin(len(mbins2)-1,f"sf_dy_ntrack{ntrack}_{ntmin}to{ntmax}",array('d',mbins2))
            hist_sb_dy = hist_sb_dy.Rebin(len(mbins2)-1,f"sf_dy_ntrack{ntrack}_{ntmin}to{ntmax}",array('d',mbins2))
            ratio_dy.SetTitle(f"{tit_nt} = {ntrack} #rightarrow {ntmin}-{ntmax} extrapolation SF")
            ratio_dy.Divide(hist_sb_dy)
            ratio_dy.Scale(norm_dy) # normalize to Z peak
            savehist(ratio_dy,hfile,var,var,ratio_dy.GetName(),subdir=sel_sb,verb=verb) # store for later reuse
            ratios_dy[selection][var] = ratio_dy # store for later reuse
        ratio_dy = ratios_dy[selection][var]
        #hist_sr_bkg.Multiply(ratio_dy) # multiply bin-by-bin
        for i in range(1,hist_sr_bkg.GetXaxis().GetNbins()+1):
          n_bkg = hist_sr_bkg.GetBinContent(i)
          xval  = hist_sr_bkg.GetXaxis().GetBinCenter(i)
          i2    = ratio_dy.GetXaxis().FindBin(xval)
          xval2 = hist_sr_bkg.GetXaxis().GetBinCenter(i2)
          sf_ep = ratio_dy.GetBinContent(i2) # SB -> SR extrapolation factor
          hist_sr_bkg.SetBinContent(i,n_bkg*sf_ep)
          print(f">>>   n_bkg={n_bkg:7.2f} in bin={i:2d} ({xval:5.1f}) => sf_ep={sf_ep:5.2f} in bin={i2:2d} ({xval2:4.1f})")
      
      # STEP 2e: Normalize inclusive background to |M-90| < 15 GeV
      LOG.color("Step 2e: Normalize incl. bkg. to Z peak...",b=True)
      for var in variables:
        hist_bkg = hists_sr[bkgname][var]    # expected incl bkg from sideband (before scaling)
        hist_obs = hists_sr[sample_obs][var] # observed
        hist_ww  = hists_sr[sample_ww][var]  # expected WW signal
        hist_sig = hists_sr[sample_sig][var] # expected mumu signal
        n_obs    = integrateZWindow(hist_obs,verb=verb)
        n_bkg    = integrateZWindow(hist_bkg,verb=verb) # before scaling
        n_ww     = integrateZWindow(hist_ww, verb=verb)
        n_sig    = integrateZWindow(hist_sig,verb=verb)
        assert n_bkg>0
        #sf_el = 2.52 if 'ntrack_all==0' in selection.selection else 2.85
        sf_bkg = (n_obs-sf_el*(n_sig+n_ww))/n_bkg
        print(f">>>   n_obs={n_obs:.2f}, n_ww={n_ww:.2f}, n_sig={n_sig:.2f}, sf_el={sf_el:.3f}, n_bkg={n_bkg:.2f} => sf_bkg={sf_bkg}")
        sfs[era][selection.filename][sel_sb.filename]['ZWindow'].update({ # store to JSON
          'obs': round(n_obs,6), 'bkg_sb': round(n_bkg,6), 'ww': round(n_ww,7), 'sig': round(n_sig,6)
        })
        sfs[era][selection.filename][sel_sb.filename]['ZWindow'][fitkey] = { # SF-dependent bkg estimation
          'bkg_sr': round(sf_bkg*n_bkg,6), 'sf_el': round(sf_el,6), 'sf_bkg': round(sf_bkg,6)
        }
        hist_bkg.Scale(sf_bkg)
        hist_bkg.SetTitle(f"Incl. bkg. ({ntmin} <= N_{{#lower[-0.2]{{track}}}} <= {ntmax})")
      
      # STORE for later reuse
      #if not loadhists and redo==redoes[-1]: # store for later reuse
      if redo==redoes[-1]: # store for later reuse
        for var in variables:
          for sample in hists_sr: # SIGNAL REGION
            if isinstance(sample,str): # store only background (after scaling)
              sample_ = sample+f"_ntracks{ntmin}to{ntmax}"+tag
              savehist(hists_sr[sample][var],hfile,var,var,sample_,subdir=selection,verb=verb+3) # store for later reuse
      
      # STEP 3: Plot signal region
      LOG.color("Step 3: Plot signal region...",b=True)
      fname = f"{outdir}/$VAR_{chstr}-{selection.filename}-{era}_bkg{ntmin}to{ntmax}_fit{redo+1}$TAG"
      #text  = "%s: %s"%(channel.replace('mu',"#mu").replace('tau',"#tau_{h}"),selection.title)
      text  = selection.title
      rmax  = 3 if selection.issr else 1.6
      rmax2 = 6.7 if selection.issr else 6.7
      for var in variables:
        
        # GET HIST
        hist_obs  = hists_sr[sample_obs][var] # observed
        hists_exp = [hists_sr[s][var] for s in [bkgname,sample_sig,sample_ww]] # expected bkg + sig
        
        # PLOT STACK
        stack = Stack(var,hist_obs,hists_exp,clone=True,verb=verb)
        stack.draw(ymin=1e-3,fraction=fraction,rmin=0,rmax=rmax,lowerpanels=2)
        stack.drawlegend(y=0.94,twidth=0.85)
        stack.drawtext(text)
        
        # STEP 4: Fit ratio
        LOG.color("Step 4: Fit...",b=True)
        hnum = hist_obs.Clone("num")
        hnum.Add(hists_sr[bkgname][var],-1)
        hnum.SetOption('E0 E1')
        hden = hists_sr[sample_sig][var].Clone("den")
        hden.Add(hists_sr[sample_ww][var],+1)
        funcs = { } # fit functions
        stack.canvas.cd(3)
        ratio2 = Ratio(hnum,hden,errband=True,verb=verb)
        ratio2.draw(data=True)
        hrat = ratio2.ratios[0]
        fres  = [ ]
        for i, (ftit, fcol) in enumerate(zip(ftits,fcols)):
          func = TF1(f"f{i}",f"pol{i}",var.xmin,var.xmax)
          func.SetParameter(0,sf_el) # ansatz
          func.SetTitle(ftit)
          func.SetLineColor(fcol)
          func.SetLineWidth(2)
          hrat.Fit(func)
          func.Draw('SAME')
          funcs[i] = func
          sgn  = lambda s: '#minus' if s<0 else '+'
          mtit = "m_{#mu#mu}"
          sfs_ = sfs[era][selection.filename][sel_sb.filename][ftit][fitkey] = { } # for storing to JSON
          for ip in range(0,i+1): # store fit results
            sfs_[ip] = f"{func.GetParameter(ip):.4g} +- {func.GetParError(ip):.4g}"
          if i==0:
            sf_el = func.GetParameter(0) # save for redo
            text = f"Flat SF = {sf_el:.3f} #pm {func.GetParError(0):.3f}"
          elif i==1:
            sf = func.GetParameter(1)
            text = f"Lin. SF = {func.GetParameter(0):.3f}"
            text += f" {sf:+.3g} #times #frac{{{mtit}}}{{GeV}}"
            #text += f" {sgn(sf)} ({sf:.2f} #pm {func.GetParError(1):.2f} )x"
          elif i==2:
            continue
            #sf1 = func.GetParameter(1)
            #sf2 = func.GetParameter(2)
            #text = f"Lin. SF = {func.GetParameter(0):.3f}"
            ##text += f" {sgn(sf1)} ({sf1:.2f} #pm {func.GetParError(1):.2f} )x"
            ##text += f" {sgn(sf2)} ({sf2:.2f} #pm {func.GetParError(2):.2f} )x^{2}"
            #text += f" {abs(sf1):+.3g} #times {mtit}"
            #text += f" {abs(sf2):+.3g} #times {mtit}^{{2}}"
          text = text.replace('+','+ ').replace('-','#minus ')
          print(text)
          fres.append(text)
        hrat.Draw('E0 E1 SAME') # draw on top (DOES NOT WORK?)
        stack.drawtext(fres,x=0.50,y=0.57,size=0.044,theight=1.16)
        stack.canvas.cd(3)
        stack.setaxes(ratio2,ymin=0,ymax=rmax2,xtitle=var.title,ytitle=rtitle,nydiv=506,
                      ytitlesize=0.054,ytitleoffset=0.92,center=True,latex=False)
        
        # RATIO LEGEND
        x1 = 0.17; x2 = x1 + 0.32
        y1 = 0.96; y2 = y1 - 0.15
        legend = TLegend(x1,y1,x2,y2)
        legend.SetFillStyle(0)
        legend.SetBorderSize(0)
        legend.SetTextSize(0.075)
        legend.SetMargin(0.3)
        legend.SetTextFont(42)
        legend.SetNColumns(len(funcs))
        legend.SetColumnSeparation(0.011)
        for i, func in sorted(funcs.items()):
          legend.AddEntry(func,func.GetTitle(),'l')
        legend.Draw()
        
        # SAVE & CLOSE STACK
        stack.saveas(fname,ext=exts,tag=tag)
        stack.close()
      
      # STEP 5: Plot again
      if redo==redoes[-1]: # only last time
        LOG.color("Step 5: Plot again after applying SF...",b=True)
        for var in variables:
          
          # GET HISTS
          hist_obs  = hists_sr[sample_obs][var] # observed
          hists_exp = [hists_sr[s][var] for s in [bkgname,sample_sig,sample_ww]] # expected bkg + sig
          hists_sr[sample_sig][var].Scale(sf_el) # scale with SF
          hists_sr[sample_ww][var].Scale(sf_el)  # scale with SF
          
          # PLOT STACK
          stack = Stack(var,hist_obs,hists_exp,clone=True,verb=verb)
          stack.draw(ymin=1e-3,fraction=fraction,rmin=0,rmax=1.6,lowerpanels=2)
          stack.drawlegend(y=0.94,twidth=0.85)
          stack.drawtext(selection.title)
          stack.drawtext(f"SF = {sf_el:.3f} applied",x=0.55,y=0.53,size=0.044)
          
          # PLOT BOTTOM RATIO
          hnum = hist_obs.Clone("num")
          hnum.Add(hists_sr[bkgname][var],-1)
          hnum.SetOption('E0 E1')
          hden = hists_sr[sample_sig][var].Clone("den")
          hden.Add(hists_sr[sample_ww][var],+1)
          stack.canvas.cd(3)
          ratio2 = Ratio(hnum,hden,errband=True,verb=verb)
          ratio2.draw(data=True)
          hrat = ratio2.ratios[0]
          hrat.Draw('E0 E1 SAME') # draw on top (DOES NOT WORK?)
          stack.canvas.cd(3)
          stack.setaxes(ratio2,ymin=0,ymax=2.5,xtitle=var.title,ytitle=rtitle,nydiv=506,
                        ytitlesize=0.054,ytitleoffset=0.92,center=True,latex=False)
          
          # SAVE & CLOSE STACK
          stack.saveas(fname,ext=exts,tag=tag+"_applied")
          stack.close()
  
  # STEP 6: Compare Incl. Bkg. to DY MC
  #if redo==redoes[-1]: # only last time
  #LOG.header("Comparing DY & Incl. Bkg.")
  LOG.color("Step 6: Compare DY MC & Incl. Bkg. data...",b=True)
  hists    = { v: [ ] for v in variables } # for reuse
  sel_sb   = selections[0].sideband
  #ratio_dy = { v: { } for v in variables } # to compute DY extrapolation SF
  for selection in selections:
    #ntrack = int(selection.title[-1])
    for var in variables:
      hist = loadhist(hfile,var,var,sample_dy,subdir=selection,verb=verb)
      hist.SetTitle(f"Drell-Yan MC, {selection.title}")
      hists[var].append(hist)
      #ratio_dy[var][selection] = hist.Clone("sf_dy_ntrack%s_%sto%s"%(ntmin,ntmax,ntrack))
  #tit_sb = f"{ntmin} <= {tit_nt} <= {ntmax}"
  for var in variables:
    #if loadhists: # skip recreating histograms (fast!)
    #hist_dy = sample_dy.gethist(var,sel_sb,verb=verb)
    hist_dy = loadhist(hfile,var,var,sample_dy,subdir=sel_sb,verb=verb)
    hist_sb = loadhist(hfile,var,var,bkgname,subdir=sel_sb,verb=verb)
    hist_dy.SetTitle(f"Drell-Yan MC, {sel_sb.title}")
    hist_sb.SetTitle(f"Incl. bkg. data, {sel_sb.title}")
    hists[var].append(hist_dy)
    hists[var].append(hist_sb)
    #ratio_dy[var][selection].Divide(hist_dy)
    #savehist(hist_dy,hfile,var,var,sample_dy,subdir=sel_sb,verb=verb) # store for later reuse
    #savehist(ratio_dy[var][selection],hfile,var,var,sample_dy,subdir=sel_sb,verb=verb) # store for later reuse
  for var in variables:
    for i, oldhist in enumerate(hists[var][:]): # rebin all histogram for plotting
      newhist = oldhist.Rebin(len(mbins2)-1,oldhist.GetName()+"_rebin",array('d',mbins2))
      hists[var][i] = newhist # overwrite
    texts = [f"A < 0.015"]
    fname  = f"{outdir}/bkg/compareInclBkg-DY_$VAR_{chstr}-acolt0p015-ntracks{ntmin}to{ntmax}-{era}$TAG"
    plot = Plot(var,hists[var],norm=True)
    plot.draw(lstyle=1,rmin=0.34,rmax=1.3,staterr=True,enderrorsize=4,msize=0.5,#colors=lcols,mstyles=mstyles
              ratio=-1,logy=True,ymargin=1.29,logyrange=5.1,verb=verb+1)
    plot.drawlegend(pos='Ty=0.43',tsize=0.052)
    plot.drawtext(texts,size=0.052)
    plot.saveas(fname,ext=exts)
    plot.close(keep=False)
  
  # JSON file
  LOG.color("Step 7: Writing fit results to JSON...",b=True)
  ###for era in sfs:
  ###  for sel in sfs[era]:
  ###    if not sel.issr:
  ###      print(f">>> Ignore era={era!r}, sel={sel.selection!r}")
  ###      sfs[era].pop(sel)
  with open(jfname,'w') as outfile:
    outfile.write(json.dumps(sfs,sort_keys=False,indent=2)+'\n')
  
  # CLOSE FILE
  hfile.Close()
  

def printResults(era,outdir,all=False):
  """Print fit results."""
  jfname = "%s/elastic.json"%(outdir)
  fits = [
    "Flat",
    "Lin.", 
    "Quadr.",
  ]
  def printFit(fit):
    res = [ ]
    for par, sf in fit['fit3'].items():
      if par!='0':
        sf = f"({sf}) \\times " #m_{{\\PGm\\PGm}}"
        if int(par)==1:
          sf += "\\frac{\\mmumu}{\\GeVns}"
        elif int(par)==2:
          sf += "\\frac{\\mmumu^2}{\\GeVns^2}"
        if int(par)==2 and sf.count('e-06')==2:
          sf = sf.replace('e-06','').replace(')',") \\times 10^{-6}")
      else:
        sf = ' +- '.join(f"{float(x):.3f}" for x in sf.split(' +- '))
      res.append(sf.replace('+-','\\pm'))
      #return ', '.join(f"{p}: {s}" for p,s in fit['fit3'].items() )
      #', '.join(f"{s} \\times { if p else }" for p,s in fit['fit3'].items() )
    return (' + '.join(res)).replace('+ (-','- (')
  print(f">>> Opening {jfname!r}...")
  if os.path.isfile(jfname):
    with open(jfname,'r') as infile:
      sfs = json.load(infile)
    print(">>> "+'-'*100)
    sfs_final = [ ] 
    for sel_sr in sfs[era]:
      for sel_sb, sfs_ in sfs[era][sel_sr].items():
        if any('ntracks'+n in sel_sr for n in '01') and '3to7' in sel_sb:
          sfs_final.append((sel_sr,sel_sb,sfs_))
        print(f">>> {sel_sr} with sideband {sel_sb}:")
        for fit in ["Flat"]: # only linear
          print(f">>>   {(fit+':').ljust(10)} {printFit(sfs_[fit])}")
    print(">>> "+'-'*100)
    for fit in fits:
      print(f">>> {fit}:")
      for sel_sr, sel_sb, sfs_ in sfs_final:
        print(f">>>   {sel_sr} with sideband {sel_sb}:")
        print(f">>>     {printFit(sfs_[fit])}")
    print(">>> "+'-'*100)
    

# def testFit():
#   """Test if TH1::Fit takes into account errors in bin content."""
#   # https://root.cern.ch/doc/master/classTH1.html
#   # https://root.cern.ch/doc/master/classTF1.html
#   from ROOT import TF1, TH1D, gRandom, kBlack, kBlue, kAzure, kGreen
#   from math import ceil
#   nbins = 10
#   xmin, xmax = 0., 100.
#   pars = (1,0.1) # parameters of f1 = pol1 = 1 + 0.1*x
#   f = { }
#   for i, col in [(1,kRed),(2,kOrange)]:
#     f[i] = TF1('f1',"pol1",xmin,xmax)
#     f[i].SetParameters(*pars)
#     f[i].SetLineColor(col)
#     f[i].SetLineWidth(2)
#   h1 = TH1D('h1','h1',nbins,xmin,xmax)
#   h2 = TH1D('h2','h2',nbins,xmin,xmax)
#   #f1.GetRandom()
#   #h1.FillRandom('f1',10000)
#   gRandom.SetSeed(137137)
#   ymax = 0
#   for i in range(1,nbins+1):
#     x = h1.GetXaxis().GetBinCenter(i)
#     e = 0.03*x #+ gRandom.Gaus(0,0.0001*x) # uncertainty increasing with x
#     m = pars[0]+pars[1]*x # expected y value at x
#     y = gRandom.Gaus(m,0.5*e) # fluctuate around mean
#     print(f">>> testFit: i={i}, x={x}, y={y}, m={m}, e={e}")
#     h1.SetBinContent(i,y)
#     h1.SetBinError(i,e)
#     h2.SetBinContent(i,y)
#     h2.SetBinError(nbins-i-1,e) # invert uncertainties (decreasing with x)
#     if y+e>ymax:
#       ymax = y+e
#   #ymax = ceil(1.1*ymax)
#   ymin, ymax = -2, 16
#   h1.Fit(f[1])
#   h2.Fit(f[2])
#   plot = Plot('x',h1,h2)
#   plot.draw(ymin=ymin,ymax=ymax,option='E1',enderrorsize=6.0,
#             colors=[kOrange+4,kAzure+1],lwidth=[3,2],mstyle='data')
#   f[1].Draw('SAME')
#   f[2].Draw('SAME')
#   plot.saveas("testFit.png")
#   plot.close()
  

def main(args):
  verbosity  = args.verbosity
  channels   = args.channels
  eras       = args.eras
  varfilter  = args.varfilter
  selfilter  = args.selfilter
  loadhists  = args.loadhists
  methods    = args.methods
  sidebands  = args.sidebands
  tag        = args.tag
  nthreads   = args.nthreads
  outdir     = "plots/g-2/elastic"
  outdir_bkg = "plots/g-2/elastic/bkg"
  #testFit(); exit(0)
  RDF.SetNumberOfThreads(nthreads,verb=verbosity+1) # set nthreads globally
  
  # LOOP over channels
  for channel in channels:
    for era in eras:
      if 'res' in methods:
        printResults(era,outdir=outdir)
        exit(0)
      setera(era) # set era for plot style and lumi-xsec normalization
      sampleset = getsampleset(channel,era,loadcorrs=True)
      #plotStack(sampleset,channel,tag=tag,outdir=outdir,era=era)
      if 'sf' in methods:
        for sideband in sidebands:
          measureElasicSF(sampleset,channel,tag=tag,outdir=outdir,era=era,
                          loadhists=loadhists,sideband=sideband)
      if 'comp' in methods:
        studyInclBkg(sampleset,channel,tag=tag,outdir=outdir_bkg,era=era,loadhists=loadhists)
  

if __name__ == "__main__":
  from argparse import ArgumentParser
  description = """Simple plotting script to compare distributions in pico analysis tuples"""
  parser = ArgumentParser(prog="plot_compare",description=description,epilog="Good luck!")
  #parser.add_argument('-m', '--method',    dest='methods', choices=['pu','hs','sam','var'], nargs='+', default=['pu'],
  #                                         help="routine" )
  parser.add_argument('-y', '--era',       dest='eras', nargs='*', default=['UL2018'],
                                           help="set era" )
  parser.add_argument('-c', '--channel',   dest='channels', type=str, nargs='+', default=['mumu'],
                                           help="channels, default=%(default)r" )
  parser.add_argument('-V', '--var',       dest='varfilter', nargs='+',
                                           help="only plot the variables passing this filter (glob patterns allowed)" )
  parser.add_argument('-S', '--sel',       dest='selfilter', nargs='+',
                                           help="only plot the selection passing this filter (glob patterns allowed)" )
  #parser.add_argument('-s', '--serial',    dest='parallel', action='store_false',
  #                                         help="run Tree::MultiDraw serial instead of in parallel" )
  #parser.add_argument('-p', '--parallel',  action='store_true',
  #                                         help="run Tree::MultiDraw in parallel instead of in serial" )
  parser.add_argument('-n', '--nthreads',  type=int, nargs='?', const=10, default=10, action='store',
                                           help="run RDF in parallel instead of in serial, nthreads=%(default)r" )
  #parser.add_argument('-p', '--pdf',       dest='pdf', action='store_true',
  #                                         help="create pdf version of each plot" )
  parser.add_argument('-m', '--method',    dest='methods', choices=['sf','comp','res'], nargs='+', default=['sf'],
                                           help="routine" )
  parser.add_argument('-s', '--sb',        dest='sidebands', nargs='+', default=[None],
                                           help="sidebands ntrack limits, comma-separated integers, e.g. '-s 3,7 3,8'" )
  parser.add_argument('-L', '--loadhists', action='store_true',
                                           help="load histograms from ROOT file" )
  parser.add_argument('-t', '--tag',       default="", help="extra tag for output" )
  parser.add_argument('-v', '--verbose',   dest='verbosity', type=int, nargs='?', const=1, default=0, action='store',
                                           help="set verbosity" )
  args = parser.parse_args()
  LOG.verbosity = args.verbosity
  PLOG.verbosity = args.verbosity-1
  SLOG.verbosity = args.verbosity
  main(args)
  print("\n>>> Done.")
  
