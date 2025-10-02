#! /usr/bin/env python
# Author: Izaak Neutelings (July 2020)
# Description: Compare two pico files
# Sources:
#   https://github.com/CMS-HTT/2017-sync/blob/master/compare.py
from TauFW.common.tools.file import ensuredir
from TauFW.Plotter.plot.Plot import Plot, CMSStyle, Variable
from ROOT import TFile, TH1D
from TauFW.Plotter.plot.utils import LOG


def compare(fnames,variables,**kwargs):
  
  # SETTING
  tnames   = kwargs.get('tree',    [ ]       )
  entries  = kwargs.get('entries', [ ]       ) # entries of files
  outdir   = kwargs.get('outdir',  "compare" )
  tag      = kwargs.get('tag',     ""        )
  cut      = kwargs.get('cut',     ""        )
  norm     = kwargs.get('norm',    False     )
  ensuredir(outdir)
  if isinstance(tnames,str):
    tnames = [tnames]*len(fnames)
  else:
    while len(tnames)<len(fnames):
      tnames.append(tnames[-1])
  if norm:
    tag += "_norm" # normalize each histogram
  
  # GET FILES & TREES
  files = [ ]
  trees = [ ]
  for fname, tname in zip(fnames,tnames):
    file = TFile.Open(fname,'READ')
    tree = file.Get(tname)
    files.append(file)
    trees.append(tree)
    for variable in variables[:]:
      if not hasattr(tree,variable.name):
        LOG.warning("compare: tree %s:%s does not contain branch %r! Skipping..."%(fname,tname,variable.name))
        variables.remove(variable)
  while len(entries)<len(trees):
    i     = len(entries)
    entry = "%s %d"%(tnames[i],i+1)
    entries.append(entry)
  
  # PLOT
  for variable in variables:
    fname    = "%s/%s%s.png"%(outdir,variable,tag)
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
    for i, (tree, htitle) in enumerate(zip(trees,entries)):
      hname  = "%s_%d"%(variable.filename,i)
      #hist   = variable.gethist(hname,htitle)
      #dcmd   = variable.drawcmd(hname)
      hist   = variable.draw(tree,cut,name=hname,title=htitle) # create and fill hist from tree
      evts   = hist.GetEntries()
      hist.SetTitle("%s (%d)"%(htitle,evts))
      hists.append(hist)
      print ">>>   %r: entries=%d, integral=%s, mean=%#.6g, s.d.=%#.6g"%(htitle,evts,hist.Integral(),hist.GetMean(),hist.GetStdDev())
    
    # DRAW PLOT
    plot = Plot(variable,hists,norm=norm)
    plot.draw(ratio=True,logy=logy,ratiorange=rrange,lstyle=lstyle,grid=grid,staterr=staterr)
    plot.drawlegend(header=header)
    plot.drawtext(text)
    plot.saveas(fname)
    plot.close()
    print('')
    

def main(args):
  
  CMSStyle.setCMSEra('(13 TeV)')
  
  files     = args.files
  outdir    = args.outdir
  tree      = args.trees
  cut       = args.cut
  tag       = args.tag
  verbosity = args.verbosity
  
  variables = [
    Variable("pt_1",          40, 0,100),
    Variable("pt_2",          40, 0,100),
    Variable("genPartFlav_1", 11,-1, 10),
    Variable("genPartFlav_2", 11,-1, 10),
    Variable("idweight_1",   100,-1,  4),
    Variable("idweight_2",   100,-1,  4),
    Variable("ltfweight_1",  100,-1,  4),
    Variable("ltfweight_2",  100,-1,  4),
    Variable("btagweight",   100,-1,  4),
  ]
  
  if verbosity>=1:
    print ">>> %-14s = %s"%('files',files)
    print ">>> %-14s = %r"%('outdir',outdir)
    print ">>> %-14s = %s"%('tree',tree)
    print ">>> %-14s = %r"%('cut',cut)
    print ">>> %-14s = %r"%('tag',tag)
  
  for norm in [True,False]:
    compare(files,variables,outdir=outdir,tag=tag,cut=cut,tree=tree,norm=norm)
  

if __name__ == "__main__":
  from argparse import ArgumentParser
  description = '''This script compares pico files.'''
  parser = ArgumentParser(prog="comparePico",description=description,epilog="Good luck!")
  parser.add_argument('files',               nargs='+', default=[ ], action='store',
                                             help="files to compare" )
  parser.add_argument('-T', '--tree',        dest="trees", nargs='+', default=['tree'], action='store',
                                             help="tree name, default=%(default)s" )
  parser.add_argument('-p', '--pdf',         default=False, action='store_true',
                                             help="create pdf version as well as png" )
  parser.add_argument('-t', '--tag',         type=str, default='', action='store',
                                             help="add tag to plots" )
  parser.add_argument('-c', '--cut',         type=str, default="", action='store',
                                             help="selection cut" )
  parser.add_argument('-o', '--out',         dest='outdir',type=str, default="compare", action='store',
                                             help="output directory, default=%(default)r" )
  parser.add_argument('-v', '--verbose',     dest='verbosity', type=int, nargs='?', const=1, default=0, action='store',
                                             help="set verbosity" )
  args = parser.parse_args()
  main(args)
  
