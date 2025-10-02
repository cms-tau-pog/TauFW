# -*- coding: utf-8 -*-
# Author: Izaak Neutelings (August 2020)
# Description: Help function to create and plot input histogram for datacards
import os, re
from collections import OrderedDict
from TauFW.common.tools.utils import ensurelist, repkey, lreplace #, rreplace
from TauFW.common.tools.file import ensuredir
from TauFW.common.tools.root import ensureTDirectory, ensureTFile, gethist
from TauFW.common.tools.log import color
from TauFW.Plotter.plot.utils import LOG, deletehist, grouphists
from TauFW.Plotter.plot.Stack import Stack
from TauFW.Plotter.plot.Plot import Plot
from TauFW.Plotter.plot.string import joincuts
from ROOT import gStyle, TFile, TH1, TNamed, kBlack



class Systematic(object):
  """Container class for systematics."""
  
  def __init__(self, systag, procs, replaceweight=('','',''), **kwargs):
    regexp     = kwargs.pop('regex',False)
    self.procs = procs # list of processes
    self.tag   = repkey(systag,**kwargs)
    self.dn    = self.tag +'Down'
    self.up    = self.tag +'Up'
    #weightnom  = replaceweight[0] if regexp else re.escape(replaceweight[0]) # escape non regexp
    self.wgtup = (replaceweight[0],replaceweight[1],regexp) # (oldweight,newweightUp)
    self.wgtdn = (replaceweight[0],replaceweight[2],regexp) # (oldweight,newweightDown)
    

def preparesysts(*args,**kwargs):
  """Help function to prepare tags for systematic variation."""
  systs = OrderedDict()
  for sysargs in args:
    systs[sysargs[0]] = Systematic(*sysargs[1:],**kwargs)
  return systs
  

def createinputs(fname,sampleset,obsset,bins,syst="",**kwargs):
  """Create histogram inputs in ROOT file for datacards.
       fname:     filename pattern of ROOT file
       sampleset: SampleSet object
       obsset:    list of Variables objects
       bins:      list of Selection objects
       syst:      tag for histogram name for this systematic
  """
  #LOG.header("createinputs")
  htag          = syst
  outdir        = kwargs.get('outdir',        ""     )
  era           = kwargs.get('era',           ""     ) # era to replace in htag
  tag           = kwargs.get('tag',           ""     ) # file tag
  filters       = kwargs.get('filter',        None   ) # only create histograms for these processes
  vetoes        = kwargs.get('veto',          None   ) # veto these processes
  nthreads      = kwargs.get('parallel',      None   ) # set multithreading for filling histograms with RDF in parallel
  nthreads      = kwargs.get('nthreads',      nthreads ) # alias
  recreate      = kwargs.get('recreate',      False  ) # recreate ROOT file
  replaceweight = kwargs.get('replaceweight', None   ) # replace weight (e.g. for syst. variations)
  replacenames  = kwargs.get('replacename',   [ ]    ) # replace name (regular expressions)
  extraweight   = kwargs.get('weight',        ""     ) # extraweight
  shift         = kwargs.get('shift',         ""     ) # shift variable (e.g. for syst. variations)
  shiftjme      = kwargs.get('shiftjme',      ""     ) # shift jet/MET variable (e.g. 'jer', 'jec')
  shiftQCD      = kwargs.get('shiftQCD',      0      ) # e.g 0.30 for 30%
  noneg         = kwargs.get('noneg',         True   ) # suppress negative bin values (for fit stability)
  dots          = kwargs.get('dots',          False  ) # replace 'p' with '.' in histogram names with floats
  verbosity     = kwargs.get('verb',          0      ) # verbosity level
  option        = 'RECREATE' if recreate else 'UPDATE'
  method        = 'QCD_OSSS' if filters==None or 'QCD' in filters else None
  method        = kwargs.get('method',        method )
  replacenames  = ensurelist(replacenames)
  
  # FILE LOGISTICS: prepare file and directories
  files = { }
  ensuredir(outdir)
  fname = os.path.join(outdir,fname)
  if shift: # shift observable name
    if isinstance(shift,str): # shift only variable by adding tag, e.g. shift='_ResUp'
      obsset = [o.shift(shift,keepfile=True) for o in obsset]
    else: # shift specified variables, e.g. shift=('_ResUp','m_vis')
      obsset = [o.shift(*shift,keepfile=True) for o in obsset]
      bins = [s.shift(*shift,keepfile=True) for s in bins]
  if shiftjme: # shift jet/MET variables, e.g. shiftjme='jec', 'jer', 'unclen'
    obsset = [o.shiftjme(shiftjme,keepfile=True) for o in obsset]
    bins = [s.shiftjme(shiftjme,keepfile=True) for s in bins]
  for obs in obsset:
    obsname = obs.filename
    ftag    = tag+obs.tag
    fname_  = repkey(fname,OBS=obsname,TAG=tag) # replace keys
    file    = TFile.Open(fname_,option)
    if recreate:
      print(">>> created file %s"%(fname_))
    for selection in bins:
      if not obs.plotfor(selection): continue
      obs.changecontext(selection) # update contextual cuts, binning, name, title, ...
      ensureTDirectory(file,selection.filename,cd=True,verb=verbosity)
      if recreate:
        string = joincuts(selection.selection,obs.cut)
        TNamed("selection",string).Write() # write exact selection string to ROOT file for the record / debugging
        #TNamed("weight",sampleset.weight).Write()
        LOG.verb("%s selection %r: %r"%(obsname,selection.name,string),verbosity,1)
    files[obs] = file
  
  # GET HISTS
  # TODO: We can now run bins/selections in parallel, using RDF
  for selection in bins:
    bin = selection.filename # bin name
    print(">>>\n>>> "+color(" %s "%(bin),'magenta',bold=True,ul=True))
    if htag: # hist tag for systematic
      print(">>> systematic uncertainty: %s"%(color(htag.lstrip('_'),'grey')))
    if recreate or verbosity>=1:
      print(">>> %r"%(selection.selection))
    for obs in obsset: # update contextual cuts, binning, name, title, ...
      obs.changecontext(selection)
    hists = sampleset.gethists(obsset,selection,method=method,split=True,nthreads=nthreads,
                               filter=filters,veto=vetoes,replaceweight=replaceweight)
    
    # SAVE HIST
    wobs  = max([10]+[len(o.printbins(filename=True)) for o in hists]) # extra space
    wproc = 4+max(11,len(htag)) # extra space
    TAB   = LOG.table(f"%11.1f %10d  %-{wobs}s  %s")
    TAB.printheader('Events','Entries','Observable','Process'.ljust(wproc))
    for obs, histset in hists.items():
      for hist in histset:
        hname = hist.GetName() # = $VAR_$BIN_$NAME (created by makehistname in Sample.getrdframe)
        hname = lreplace(hname,obs.filename).strip('_') # remove variable prefix
        hname = lreplace(hname,selection.filename).strip('_') # remove selection prefix
        hname = hname.replace('.', 'p')
        if not hname.endswith(htag):
          hname += htag # HIST = $PROCESS_$SYSTEMATIC
        hname = repkey(hname,BIN=bin)
        if dots and 'p' in hname: # replace 'p' with '.' in float
          hname = re.sub(r"(\d+)p(\d+)",r"\1.\2",hname)
        for exp, sub in replacenames: # replace regular expressions
          hname = re.sub(exp,sub,hname)
        drawopt = 'E1' if 'data' in hname else 'EHIST'
        lcolor  = kBlack if any(s in hname for s in ['data','ST','VV']) else hist.GetFillColor()
        hist.SetOption(drawopt)
        hist.SetLineColor(lcolor)
        hist.SetFillStyle(0) # no fill in ROOT file
        hist.SetName(hname)
        hist.GetXaxis().SetTitle(obs.title)
        if noneg:
          for i, yval in enumerate(hist):
            if yval<0: # manually delete negative bin values
              print(f">>> Set negative value of {hname!r} bin {i} ({yval:.3f}<0) to 0") #hist.GetName()
              hist.SetBinContent(i,0)
        if files[obs].cd(bin): # $FILE:$BIN/$PROCESS_$SYSTEMATC
          hist.Write(hname,TH1.kOverwrite)
        TAB.printrow(hist.GetSumOfWeights(),hist.GetEntries(),obs.printbins(filename=True),hname)
        #if not parallel: # avoid segmentation faults for parallel
        #  deletehist(hist) # clean histogram from memory
  
  # CLOSE
  for obs, file in files.items():
    file.Close()
  


def plotinputs(fname,varprocs,obsset,bins,**kwargs):
  """Plot histogram inputs from ROOT file for datacards, and write to ROOT file.
       fname:    filename pattern of ROOT file
       varprocs: dictionary for systematic variation to list of processes,
                 e.g. { 'Nom':   ['ZTT','TTT','W','QCD','data_obs'],
                        'TESUp': ['ZTT','TTT'], 'TESDown': ['ZTT','TTT'] }
       obsset:   list of Variables objects
       bins:     list of Selection objects
  """
  #LOG.header("plotinputs")
  tag       = kwargs.pop('tag',    ""                  )
  pname     = kwargs.pop('pname',  "$OBS_$BIN$TAG.png" )
  outdir    = kwargs.pop('outdir', 'plots'             )
  text      = kwargs.pop('text',   "$BIN"              )
  verbosity = kwargs.get('verb',   0                   )
  ensuredir(outdir)
  print(">>>\n>>> "+color(" plotting... ",'magenta',bold=True,ul=True))
  if 'Nom' not in varprocs:
    LOG.warning("plotinputs: Cannot make plots because did not find nominal process templates 'Nom'.")
    return
  if isinstance(varprocs['Nom'],Systematic): # convert Systematic objects back to simple string
    systs    = varprocs # OrderedDict of Systematic objects
    varprocs = OrderedDict()
    for syskey, syst in systs.items():
      if syskey.lower()=='nom':
        varprocs['Nom'] = syst.procs
      else:
        varprocs[syst.up.lstrip('_')] = syst.procs
        varprocs[syst.dn.lstrip('_')] = syst.procs
  for obs in obsset:
    obsname = obs.filename
    ftag    = tag+obs.tag
    fname_  = repkey(fname,OBS=obsname,TAG=ftag)
    file    = ensureTFile(fname_,'UPDATE')
    for set, procs in varprocs.items(): # loop over processes with variation
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
        stackinputs(tdir,obs,procs_,save=pname_,write=wname,
                    text=text_,printmean=printmean,**kwargs)
        
        # VARIATIONS
        if 'Down' in set:
          systag_ = systag.replace('Down','') # e.g.'_TES' without 'Up' or 'Down' suffix
          pname_  = repkey(pname,OBS=obsname,BIN=bin,TAG=ftag+"_$PROC"+systag_) # image file name
          wname   = "plot_$PROC"+systag_ # name in ROOT file
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
  text      = kwargs.get('text',  None            )
  tag       = kwargs.get('tag',   ""              )
  logy      = kwargs.get('logy',  variable.logy   ) # plot in logarithmic y scale
  groups    = kwargs.get('group', [ ]             ) # e.g. [(['^TT','ST'],'Top'),(['QCD','W'],'j -> tau_h fakes')]
  dname     = kwargs.get('dname', None            ) # directory ('bin') name
  pname     = kwargs.get('save',  "stack$TAG.png" ) # save as image file
  wname     = kwargs.get('write', "stack$TAG"     ) # write to file
  style     = kwargs.get('style', False           ) # write style to file
  printmean = kwargs.get('printmean', False       ) # print mean in legend
  verbosity = kwargs.pop('verb',  0               )
  
  exphists = [ ]
  datahist = None
  tdir     = ensureTDirectory(file,dname,cd=True) if dname else file
  if style:
    gStyle.Write('style',TH1.kOverwrite) # write current TStyle object to reproduce plots
  for process in processes:
    hname = process
    hist  = gethist(tdir,process,fatal=False,warn=False)
    if not hist:
      LOG.warning("stackinputs: Could not find %r in %s. Skipping stacked plot..."%(process,tdir.GetPath()))
      return
    hist.SetDirectory(0)
    hist.SetLineColor(kBlack)
    hist.SetFillStyle(1001) # assume fill color is already correct
    if 'data_obs' in process:
      datahist = hist
    else:
      exphists.append(hist)
  for group in groups:
    grouphists(exphists,*group,replace=True,regex=True,verb=0)
  stack = Stack(variable,datahist,exphists,clone=True,verb=verbosity)
  stack.draw(logy=logy)
  stack.drawlegend(ncols=2,twidth=0.9,printmean=printmean)
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
      hist  = gethist(tdir,hname,fatal=False,warn=False)
      if not hist: skip = True; break
      hists.append(hist)
    if skip:
      LOG.warning("comparevars: Could not find %r in %s. Skipping shape comparison..."%(hname,tdir.GetPath()))
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
  
