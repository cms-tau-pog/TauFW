#! /usr/bin/env python
# Author: Izaak Neutelings (December 2020)
# Description: Compare variables pf a NANOAOD file
# Instructions:
#   ./utils/compareNano.py nano.root -y 2016 -v3 -t _2016 -V "Jet_pt_nom,Jet_pt_jerUp,Jet_pt_jerDown>>20,0,200"
#   ./utils/compareNano.py nano1.root -O nano2.root -y 2016 -v3 -t _2016 -V "Jet_pt_nom>>20,0,200" "Jet_eta>>20,-4,4" --cut "HLT_IsoMu24 && Muon_pt[0]>25 && Muon_pt[1]>25"
# Sources:
#   https://github.com/CMS-HTT/2017-sync/blob/master/compare.py
from TauFW.common.tools.file import ensuredir
from TauFW.Plotter.plot.Plot import Plot, CMSStyle, Variable
from ROOT import TChain, TH1D
from TauFW.Plotter.plot.utils import LOG


def comparefiles(fnamesets,vars,**kwargs):
  """Compare file(set)s."""
  
  # SETTING
  tname     = kwargs.get('tree',    'Events'  )
  entries   = kwargs.get('entries', [ ]       ) # entries of files
  outdir    = kwargs.get('outdir',  "compare" )
  tag       = kwargs.get('tag',     ""        )
  cut       = kwargs.get('cut',     ""        )
  norm      = kwargs.get('norm',    False     )
  verbosity = kwargs.get('verb',    0         )
  ensuredir(outdir)
  if norm:
    tag += "_norm" # normalize each histogram
  
  # GET FILES & TREES
  trees = [ ]
  for fnames in fnamesets:
    if verbosity>=1:
      print ">>> Creating TChain %r..."%(tname)
    tree = TChain(tname)
    trees.append(tree)
    for fname in fnames:
      if verbosity>=1:
        print ">>>   Adding %s..."%(fname)
      tree.Add(fname)
    if verbosity>=1:
      print ">>>   Total entries: %s"%(tree.GetEntries())
  
  # PLOT
  for xvar in vars:
    fname    = "%s/%s%s.png"%(outdir,xvar.filename,tag)
    rrange   = 0.5
    header   = "Compare"       # legend header
    text     = ""              # corner text
    ratio    = True #and False
    logy     = True and False
    grid     = True #and False
    staterr  = True #and False # add uncertainty band to first histogram
    lstyle   = 1               # solid lines
    LOG.header(fname)
    
    # GET HISOGRAMS
    hists    = [ ]
    for i, tree in enumerate(trees):
      hname  = "%s_%d"%(xvar.filename,i)
      htitle = xvar.name
      #hist   = xvar.gethist(hname,htitle)
      #dcmd   = xvar.drawcmd(hname)
      hist   = xvar.draw(tree,cut,name=hname,title=htitle) # create and fill hist from tree
      evts   = hist.GetEntries()
      hist.SetTitle(htitle) #"%s (%d)"%(htitle,evts)
      hists.append(hist)
      print ">>>   %r: entries=%d, integral=%s, mean=%#.6g, s.d.=%#.6g"%(htitle,evts,hist.Integral(),hist.GetMean(),hist.GetStdDev())
    
    # DRAW PLOT
    plot = Plot(xvar,hists,norm=norm,verb=verbosity-1)
    plot.draw(ratio=True,logy=logy,ratiorange=rrange,lstyle=lstyle,grid=grid,staterr=staterr)
    plot.drawlegend(header=header,latex=False)
    plot.drawtext(text)
    plot.saveas(fname)
    plot.close()
    print
  
  #for tree in trees:
  #  tree.Close()


def comparevars(fnames,varsets,**kwargs):
  """Compare variables for given file(s)."""
  
  # SETTING
  tname    = kwargs.get('tree',    'Events'  )
  entries  = kwargs.get('entries', [ ]       ) # entries of files
  outdir   = kwargs.get('outdir',  "compare" )
  tag      = kwargs.get('tag',     ""        )
  cut      = kwargs.get('cut',     ""        )
  norm     = kwargs.get('norm',    False     )
  verbosity = kwargs.get('verb',    0         )
  ensuredir(outdir)
  if norm:
    tag += "_norm" # normalize each histogram

  if verbosity>=1:
    print ">>> Creating TChain %r..."%(tname)
  tree = TChain(tname)
  
  # GET FILES & TREES
  for fname in fnames:
    if verbosity>=1:
      print ">>>   Adding %s..."%(fname)
    tree.Add(fname)
  if verbosity>=1:
    print ">>>   Total entries: %s"%(tree.GetEntries())
  
  # PLOT
  for varset in varsets:
    fname    = "%s/%s%s.png"%(outdir,'-'.join(v.filename for v in varset),tag)
    rrange   = 0.5
    header   = "Compare"       # legend header
    text     = ""              # corner text
    ratio    = True #and False
    logy     = True and False
    grid     = True #and False
    staterr  = True #and False # add uncertainty band to first histogram
    lstyle   = 1               # solid lines
    xvar     = varset[0]
    LOG.header(fname)
    
    # GET HISOGRAMS
    hists    = [ ]
    for i, variable in enumerate(varset):
      hname  = "%s_%d"%(variable.filename,i)
      htitle = variable.name
      #hist   = variable.gethist(hname,htitle)
      #dcmd   = variable.drawcmd(hname)
      hist   = variable.draw(tree,cut,name=hname,title=htitle) # create and fill hist from tree
      evts   = hist.GetEntries()
      hist.SetTitle(htitle) #"%s (%d)"%(htitle,evts)
      hists.append(hist)
      print ">>>   %r: entries=%d, integral=%s, mean=%#.6g, s.d.=%#.6g"%(htitle,evts,hist.Integral(),hist.GetMean(),hist.GetStdDev())
    
    # DRAW PLOT
    plot = Plot(xvar,hists,norm=norm,verb=verbosity-1)
    plot.draw(ratio=True,logy=logy,ratiorange=rrange,lstyle=lstyle,grid=grid,staterr=staterr)
    plot.drawlegend(header=header,latex=False)
    plot.drawtext(text)
    plot.saveas(fname)
    plot.close()
    print
    

def main(args):
  
  files     = args.files
  other     = args.other
  tree      = args.tree
  era       = args.era
  outdir    = args.outdir
  variables = args.vars or [
    "Jet_pt_nom,Jet_pt_jesTotalUp,Jet_pt_jesTotalDown>>20,0,200",
    "Jet_pt_nom,Jet_pt_jerUp,Jet_pt_jerDown>>20,0,200",
  ]
  cut       = args.cut
  tag       = args.tag
  verbosity = args.verbosity
  
  CMSStyle.setCMSEra(era)
  
  # CREATE VARIABLE SETS
  varsets = [ ]
  for variable in variables:
    subvars = variable.split('>>')[0].split(',')
    binning = variable.split('>>')[1].split(',')
    binning = (int(binning[0]),float(binning[1]),float(binning[2]))
    if other:
      assert len(subvars)==1, "Need exactly one variable per comparison plot! Got %r"%(variable)
      subvar = Variable(subvars[0],*binning,latex=False)
      varsets.append(subvar)
    else:
      assert len(subvars)>=1, "Need at least one variable per comparison plot! Got %r"%(variable)
      subvars = [Variable(v,*binning,latex=False) for v in subvars]
      varsets.append(subvars)
  
  if verbosity>=1:
    print ">>> %-14s = %s"%('files',files)
    print ">>> %-14s = %s"%('other',other)
    print ">>> %-14s = %s"%('tree',tree)
    print ">>> %-14s = %r"%('outdir',outdir)
    print ">>> %-14s = %s"%('variables',variables)
    print ">>> %-14s = %r"%('cut',cut)
    print ">>> %-14s = %r"%('tag',tag)
  
  if other: # compare files
    for norm in [True]: #[True,False]:
      fnamesets = [files,other]
      comparefiles(fnamesets,varsets,outdir=outdir,tag=tag,cut=cut,norm=norm,tree=tree,verb=verbosity)
  else: # compare variables
    for norm in [False]: #[True,False]:
      comparevars(files,varsets,outdir=outdir,tag=tag,cut=cut,norm=norm,tree=tree,verb=verbosity)
  

if __name__ == "__main__":
  import sys
  from argparse import ArgumentParser
  argv = sys.argv
  description = '''This script compares pico files.'''
  parser = ArgumentParser(prog="comparePico",description=description,epilog="Good luck!")
  parser.add_argument('files',               nargs='+', default=[ ], action='store',
                                             help="input file(s) (multiple files are added in TChain)" )
  parser.add_argument('-T', '--tree',        default='Events', action='store',
                                             help="tree name, default=%(default)r" )
  parser.add_argument('-O', '--other',       nargs='+',
                                             help="other input files to compare to" )
  parser.add_argument('-V', '--vars',        nargs='+',
                                             help="variables to compare of format 'var1,var2[,...]>>nbins,xmin,xmax'" )
  parser.add_argument('-y', "--era",         type=str, default="(13 TeV)", action='store',
                                             help="era of file (for plot label)" )
  parser.add_argument('-p', '--pdf',         default=False, action='store_true',
                                             help="create pdf version as well as png" )
  parser.add_argument('-t', '--tag',         type=str, default='', action='store',
                                             help="add tag to plots" )
  parser.add_argument('-c', '--cut',         type=str, default="", action='store',
                                             help="selection cut, e.g. 'HLT_IsoMu24 && Muon_pt[0]>25 && Muon_pt[1]>25'" )
  parser.add_argument('-o', '--out',         dest='outdir',type=str, default="compare", action='store',
                                             help="output directory, default=%(default)r" )
  parser.add_argument('-v', '--verbose',     dest='verbosity', type=int, nargs='?', const=1, default=0, action='store',
                                             help="set verbosity" )
  args = parser.parse_args()
  main(args)
  
