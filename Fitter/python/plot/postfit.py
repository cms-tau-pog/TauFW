#! /usr/bin/env python
# Author: Izaak Neutelings (Februari 2021)
import os, sys, re
#sys.path.append('../plots')
from TauFW.common.tools.file import ensuredir
from TauFW.common.tools.root import ensureTFile #, gethist
from TauFW.common.tools.utils import repkey
from TauFW.Plotter.plot.utils import LOG, grouphists
from TauFW.Plotter.plot.Stack import Stack # Var
from TauFW.Plotter.sample.utils import setera
import TauFW.Plotter.sample.SampleStyle as STYLE


def drawpostfit(fname,bin,procs,**kwargs):
  """Plot pre- and post-fit plots PostFitShapesFromWorkspace."""
  print(">>>\n>>> drawpostfit(%r,%r)"%(fname,bin))
  outdir    = kwargs.get('outdir',  ""         )
  pname     = kwargs.get('pname',   "$FIT.png" ) # replace $FIT = 'prefit', 'postfit'
  ratio     = kwargs.get('ratio',   True       )
  tag       = kwargs.get('tag',     ""         )
  xtitle    = kwargs.get('xtitle',  None       )
  title     = kwargs.get('title',   None       )
  text      = kwargs.get('text',    ""         )
  tsize     = kwargs.get('tsize',   0.050      )
  xmin      = kwargs.get('xmin',    None       )
  xmax      = kwargs.get('xmax',    None       )
  ymargin   = kwargs.get('ymargin', 1.22       )
  groups    = kwargs.get('group',   [ ]        )
  position  = kwargs.get('pos',     None       ) # legend position
  ncol      = kwargs.get('ncol',    None       ) # legend columns
  square    = kwargs.get('square',  False      )
  era       = kwargs.get('era',     ""         )
  exts      = kwargs.get('exts', ['pdf','png'] ) # figure extension
  fits      = kwargs.get('fits', ['prefit', 'postfit'] )
  ymax      = None
  file      = ensureTFile(fname,'READ')
  if outdir:
    ensuredir(outdir)
  if era:
    setera(era)
  
  # DRAW PRE-/POST-FIT
  for fit in fits:
    fitdirname = "%s_%s"%(bin,fit)
    dir = file.Get(fitdirname)
    if not dir:
      LOG.warning('drawpostfit: Did not find dir "%s"'%(fitdirname),pre="   ")
      return
    obshist = None
    exphists = [ ]
    
    # GET HIST
    for proc in procs: #reversed(samples):
      hname = "%s/%s"%(fitdirname,proc)
      hist  = file.Get(hname)
      if not hist:
        LOG.warning('drawpostfit: Could not find "%s" template in directory "%s_%s"'%(proc,bin,fit),pre="   ")
        continue
      if 'data_obs' in proc:
        obshist = hist
        hist.SetLineColor(1)
        ymax = hist.GetMaximum()*ymargin
      else:
        exphists.append(hist)
      if proc in STYLE.sample_titles:
        hist.SetTitle(STYLE.sample_titles[proc])
      if proc in STYLE.sample_colors:
        hist.SetFillStyle(1001)
        hist.SetFillColor(STYLE.sample_colors[proc])
    if len(exphists)==0:
      LOG.warning('drawpostfit: Could not find any templates in directory "%s"'%(bin),pre="   ")
      continue
    if not obshist:
      LOG.warning('drawpostfit: Could not find a data template in directory "%s"'%(bin),pre="   ")
      continue
    for groupargs in groups:
      grouphists(exphists,*groupargs,replace=True)
    
    # PLOT
    xtitle     = (xtitle or exphists[0].GetXaxis().GetTitle()) #.replace('[GeV]','(GeV)')
    xmax       = xmax or exphists[0].GetXaxis().GetXmax()
    xmin       = xmin or exphists[0].GetXaxis().GetXmin()
    errtitle   = "Pre-fit stat. + syst. unc." if fit=='prefit' else "Post-fit unc."
    pname_     = repkey(pname,FIT=fit,ERA=era)
    rmin, rmax = (0.28,1.52)
    plot = Stack(xtitle,obshist,exphists)
    plot.draw(xmin=xmin,xmax=xmax,ymax=ymax,square=square,ratio=ratio,rmin=rmin,rmax=rmax,
              staterror=True,errtitle=errtitle)
    plot.drawlegend(position,tsize=tsize,text=text,ncol=ncol)
    if title:
      plot.drawtext(title,bold=False)
    plot.saveas(pname_,outdir=outdir,ext=exts)
    plot.close()
  
  file.Close()
  
