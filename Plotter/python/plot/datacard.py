# -*- coding: utf-8 -*-
# Author: Izaak Neutelings (August 2020)
# Description: Help function to create and plot input histogram for datacards
import os
from TauFW.common.tools.utils import ensurelist, repkey, lreplace #, rreplace
from TauFW.common.tools.file import ensuredir, ensureTDirectory, ensureTFile, gethist
from TauFW.common.tools.log import color
from TauFW.Plotter.plot.utils import LOG, deletehist, grouphists
from TauFW.Plotter.plot.Stack import Stack
from TauFW.Plotter.plot.Plot import Plot
from TauFW.Plotter.plot.string import joincuts
from ROOT import gStyle, TFile, TH1, TNamed, kBlack


def createinputs(fname,sampleset,observables,bins,**kwargs):
  """Create histogram inputs in ROOT file for datacards.
       fname:       filename pattern of ROOT file
       sampleset:   SampleSet object
       observables: list of Variables objects
       bins:        list of Selection objects
  """
  #LOG.header("createinputs")
  outdir        = kwargs.get('outdir',        ""     )
  tag           = kwargs.get('tag',           ""     ) # file tag
  htag          = kwargs.get('htag',          ""     ) # hist tag for systematic
  filters       = kwargs.get('filter',        None   ) # only create histograms for these processes
  vetoes        = kwargs.get('veto',          None   ) # veto these processes
  parallel      = kwargs.get('parallel',      True   ) # MultiDraw histograms in parallel
  recreate      = kwargs.get('recreate',      False  ) # recreate ROOT file
  replaceweight = kwargs.get('replaceweight', None   ) # replace weight
  extraweight   = kwargs.get('weight',        ""     ) # extraweight
  shiftQCD      = kwargs.get('shiftQCD',      0      ) # e.g 0.30 for 30%
  verbosity     = kwargs.get('verb',          0      )
  option        = 'RECREATE' if recreate else 'UPDATE'
  method        = 'QCD_OSSS' if filters==None or 'QCD' in filters else None
  method        = kwargs.get('method',        method )
  
  # FILE LOGISTICS: prepare file and directories
  files = { }
  ensuredir(outdir)
  fname = os.path.join(outdir,fname)
  for obs in observables:
    obsname = obs.filename
    ftag    = tag+obs.tag
    fname_  = repkey(fname,OBS=obsname,TAG=tag)
    file    = TFile.Open(fname_,option)
    if recreate:
      print ">>> created file %s"%(fname_)
    for selection in bins:
      if not obs.plotfor(selection): continue
      obs.changecontext(selection)
      ensureTDirectory(file,selection.filename,cd=True,verb=verbosity)
      if recreate:
        string = joincuts(selection.selection,obs.cut)
        TNamed("selection",string).Write() # write exact selection string to ROOT file for the record / debugging
        #TNamed("weight",sampleset.weight).Write()
        LOG.verb("%s selection %r: %r"%(obsname,selection.name,string),verbosity,1)
    files[obs] = file
  
  # GET HISTS
  for selection in bins:
    bin = selection.filename # bin name
    print ">>>\n>>> "+color(" %s "%(bin),'magenta',bold=True,ul=True)
    if htag:
      print ">>> systematic uncertainty: %s"%(color(htag.lstrip('_'),'grey'))
    if recreate or verbosity>=1:
      print ">>> %r"%(selection.selection)
    hists = sampleset.gethists(observables,selection,method=method,split=True,
                               parallel=parallel,filter=filters,veto=vetoes)
    
    # SAVE HIST
    ljust = 4+max(11,len(htag)) # extra space
    TAB   = LOG.table("%10.1f %10d  %-18s  %s")
    TAB.printheader('events','entries','variable','process'.ljust(ljust))
    for obs, hist in hists.iterhists():
      name    = lreplace(hist.GetName(),obs.filename).strip('_') # histname = $VAR_$NAME (see Sample.gethist)
      if not name.endswith(htag):
        name += htag # HIST = $PROCESS_$SYSTEMATIC
      name    = repkey(name,BIN=bin)
      drawopt = 'E1' if 'data' in name else 'EHIST'
      lcolor  = kBlack if any(s in name for s in ['data','ST','VV']) else hist.GetFillColor()
      hist.SetOption(drawopt)
      hist.SetLineColor(lcolor)
      hist.SetFillStyle(0) # no fill in ROOT file
      hist.SetName(name)
      hist.GetXaxis().SetTitle(obs.title)
      for i, yval in enumerate(hist):
        if yval<0:
          print ">>> replace bin %d (%.3f<0) of %r"%(i,yval,hist.GetName())
          hist.SetBinContent(i,0)
      files[obs].cd(bin) # $FILE:$BIN/$PROCESS_$SYSTEMATC
      hist.Write(name,TH1.kOverwrite)
      TAB.printrow(hist.GetSumOfWeights(),hist.GetEntries(),obs.printbins(),name)
      deletehist(hist) # clean memory
  
  # CLOSE
  for obs, file in files.iteritems():
    file.Close()
  


def plotinputs(fname,varprocs,observables,bins,**kwargs):
  """Plot histogram inputs from ROOT file for datacards, and write to ROOT file.
       fname:       filename pattern of ROOT file
       varprocs:    dictionary for systematic variation to list of processes,
                    e.g. { 'Nom':   ['ZTT','TTT','W','QCD','data_obs'],
                           'TESUp': ['ZTT','TTT'], 'TESDown': ['ZTT','TTT'] }
       observables: list of Variables objects
       bins:        list of Selection objects
  """
  #LOG.header("plotinputs")
  tag       = kwargs.get('tag',    ""      )
  pname     = kwargs.get('pname',  "$OBS_$BIN$TAG.png" )
  outdir    = kwargs.get('outdir', 'plots' )
  text      = kwargs.get('text',   "$BIN"  )
  groups    = kwargs.get('group',  [ ]     ) # add processes together into one histogram
  verbosity = kwargs.get('verb',   0       )
  ensuredir(outdir)
  print ">>>\n>>> "+color(" plotting... ",'magenta',bold=True,ul=True)
  for obs in observables:
    obsname = obs.filename
    ftag    = tag+obs.tag
    fname_  = repkey(fname,OBS=obsname,TAG=ftag)
    file    = ensureTFile(fname_,'UPDATE')
    for set, procs in varprocs.iteritems(): # loop over processes with variation
      if set=='Nom':
        systag = "" # no systematics tag for nominal
        procs_ = procs[:]
      else:
        systag = '_'+set  # systematics tag for variation, e.g. '_TESUp'
        procs_ = [(p+systag if p in procs else p) for p in varprocs['Nom']] # add tag to varied processes
      for selection in bins:
        if not obs.plotfor(selection): continue
        obs.changecontext(selection)
        bin     = selection.filename
        text_   = repkey(text,BIN=selection.title) # extra text in plot corner
        tdir    = ensureTDirectory(file,bin,cd=True) # directory with histograms
        if set=='Nom':
          gStyle.Write('style',TH1.kOverwrite) # write current TStyle object to reproduce plots
        
        # STACKS
        pname_ = repkey(pname,OBS=obsname,BIN=bin,TAG=ftag+systag) # image file name
        wname  = "stack"+systag # name in ROOT file
        stackinputs(tdir,obs,procs_,group=groups,
                    save=pname_,write=wname,text=text_)
        
        # VARIATIONS
        if 'Down' in set:
          systag_ = systag.replace('Down','') # e.g.'_TES' without 'Up' or 'Down' suffix
          pname_  = repkey(pname,OBS=obsname,BIN=bin,TAG=ftag+"_$PROC"+systag) # image file name
          wname   = "plot_$PROC"+systag # name in ROOT file
          comparevars(tdir,obs,procs,systag_,
                      save=pname_,write=wname,text=text_)
    
    file.Close()
  


def stackinputs(file,variable,processes,**kwargs):
  """Stack histograms from ROOT file.
       file:       TFile or TDirectory object
       variable:  Variables object
       processes: list of strings (name of processes)
     e.g.
       stackinputs(file,variable,['ZTT','TTT','W','QCD','data_obs'])
  """
  text     = kwargs.get('text',  None            )
  tag      = kwargs.get('tag',   ""              )
  groups   = kwargs.get('group', [ ]             ) # e.g. [(['^TT','ST'],'Top')]
  dname    = kwargs.get('dname', None            ) # directory ('bin') name
  pname    = kwargs.get('save',  "stack$TAG.png" ) # save as image file
  wname    = kwargs.get('write', "stack$TAG"     ) # write to file
  style    = kwargs.get('style', False           ) # write style to file
  
  exphists = [ ]
  datahist = None
  tdir     = ensureTDirectory(file,dname,cd=True) if dname else file
  if style:
    gStyle.Write('style',TH1.kOverwrite) # write current TStyle object to reproduce plots
  for process in processes:
    hname = process
    hist  = gethist(tdir,process)
    if not hist: return
    hist.SetDirectory(0)
    hist.SetLineColor(kBlack)
    hist.SetFillStyle(1001) # assume fill color is already correct
    if process=='data_obs':
      datahist = hist
    else:
      exphists.append(hist)
  for group in groups:
    grouphists(exphists,*group,replace=True,regex=True,verb=0)
  stack = Stack(variable,datahist,exphists)
  stack.draw()
  stack.drawlegend(ncols=2,twidth=0.9)
  if text:
    stack.drawtext(text)
  if pname:
    pname = repkey(pname,TAG=tag)
    stack.saveas(pname,ext=['png'])
  if wname:
    wname = repkey(wname,TAG=tag)
    stack.canvas.Write(wname,TH1.kOverwrite)
  stack.close()
  

def comparevars(file,variable,processes,systag,**kwargs):
  """Compare up/down variations of input histograms from ROOT file.
       file:      TFile or TDirectory object
       variable:  Variables object
       processes: list of strings (name of processes)
       systag:    string of systematic (file must contain up/down variation)
     e.g.
       comparevars(file,variable,['ZTT','TTT'],'TES')
  """
  text      = kwargs.get('text',  None        )
  pname     = kwargs.get('pname', "stack.png" )
  tag       = kwargs.get('tag',   ""          )
  groups    = kwargs.get('group', [ ]         ) # e.g. [(['^TT','ST'],'Top')]
  dname     = kwargs.get('dname', None        ) # directory ('bin') name
  pname     = kwargs.get('save',  "plot_$PROC$SYST$TAG.png" ) # save as image file
  wname     = kwargs.get('write', "plot_$PROC$SYST$TAG"     ) # write to file
  processes = ensurelist(processes)
  uptag     = systag+"Up"
  downtag   = systag+"Down"
  tdir      = ensureTDirectory(file,dname,cd=True) if dname else file
  for process in processes:
    hists = [ ]
    skip  = False
    for var in [uptag,"",downtag]:
      hname = process+var
      hist  = gethist(tdir,hname)
      if not hist: skip = True; break
      hists.append(hist)
    if skip:
      LOG.warning("Skipping %r variation for %r..."%(systag,process))
      continue
    plot = Plot(variable,hists)
    plot.draw(ratio=2,lstyle=1)
    plot.drawlegend()
    if text:
      plot.drawtext(text)
    if pname:
      pname_ = repkey(pname,PROC=process,TAG=tag)
      plot.saveas(pname_,ext=['png'])
    if wname:
      wname_ = repkey(wname,PROC=process,TAG=tag)
      plot.canvas.Write(wname_,TH1.kOverwrite)
    plot.close()
  
