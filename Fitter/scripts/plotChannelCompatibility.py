#! /usr/bin/env python
# Author: Izaak Neutelings (May 2022)
# Adapted from
#   https://github.com/cms-analysis/HiggsAnalysis-CombinedLimit/blob/master/test/plotting/cccPlot.cxx
#   https://cms-analysis.github.io/HiggsAnalysis-CombinedLimit/part3/commonstatsmethods/#channel-compatibility
# Instructions:
#   combine -M ChannelCompatibilityCheck workspace.root -m 160 -n .HWW --saveFitResult
#   ./plotChannelCompatibility.py -n. HWW -m 160
#   ./plotChannelCompatibility.py higgsCombine.HWW.ChannelCompatibilityCheck.mH160.root
import json
from collections import OrderedDict
import ROOT; ROOT.PyConfig.IgnoreCommandLineOptions = True
from ROOT import ROOT, gROOT, gStyle, TFile, TH2F, TCanvas, TGraphAsymmErrors, TBox, TLine, TLatex, kRed
gROOT.SetBatch(True)
gStyle.SetOptStat(0) # no stat. box
gStyle.SetEndErrorSize(6) # size of bars at the end of error bars


def getPOIs(fname,poi='r',chandict={ }):
  """Get POI from ChannelCompatibilityCheck file."""
  
  # GET FITS
  file = TFile.Open(fname,'READ')
  fit_nom = file.Get('fit_nominal')
  fit_alt = file.Get('fit_alternate')
  if not fit_nom or not fit_alt:
    print("Input file %s does not contain 'fit_nominal' or 'fit_alternate'..."%(file.GetName())+
          "Make sure you use --saveFitResult with -M ChannelCompatibilityCheck.")
    return
  
  # GET MAIN POI
  poi = fit_nom.floatParsFinal().find(poiname)
  if not poi:
    print "Nominal fit does not contain parameter of interest %s"%(poiname)
    return
  if rmin==None:
    rmin = poi.getMin() #min(poi.getMin(),rmin)
  if rmax==None:
    rmax = poi.getMax() #max(poi.getMax(),rmax)
  
  # GET CHANNEL POIs
  pois_chan = [ ]
  prefix = "_ChannelCompatibilityCheck_%s_"%(poiname)
  iter = fit_alt.floatParsFinal().createIterator()
  var = iter.Next()
  vname = lambda v: v.GetName().replace(prefix,'') # help function
  while var:
    if prefix in var.GetName():
      channel = vname(var)
      if channel in chandict:
        channel = chandict[channel]
      var.SetTitle(channel)
      print ">>> Found channel POI %r -> %r"%(var.GetName(),channel)
      pois_chan.append(var)
    var = iter.Next()
  
  file.Close()
  return poi, pois_chan


def plotChannelCompatibility(fname,outname,poi='r',rmin=None,rmax=None,**kwargs):
  # Adapted from
  #   https://github.com/cms-analysis/HiggsAnalysis-CombinedLimit/blob/master/test/plotting/cccPlot.cxx
  poiname  = poi
  xtitle   = kwargs.get('xtitle',  "r"     ) #" #sigma/#sigma_{SM}"
  chandict = kwargs.get('chandict',{ }     ) # dictionary for channel POIs
  others   = kwargs.get('others',  [ ]     )
  texts    = kwargs.get('text',    [ ]     ) or [ ]
  exts     = kwargs.get('ext',     ['png'] )
  verb     = kwargs.get('verb',    0       )
  if not isinstance(exts,list):
    exts = list(exts)
  if isinstance(texts,str):
    texts = texts.split('\\n') if '\\n' in texts else texts.split('\n')
  
  # GET POIs
  poi, pois_chan = getPOIs(fname,poi=poiname,chandict=chandict)
  if others:
    for ofname in others:
      pois_chan1 = pois_chan[:] # so list does not increase during iteration
      poi2, pois_chan2 = getPOIs(ofname,poi=poiname,chandict=chandict)
      if (poi.getVal()!=poi2.getVal() or poi.getAsymErrorLo()!=poi2.getAsymErrorLo() or poi.getAsymErrorHi()!=poi2.getAsymErrorHi()):
        print ">>> WARNING! POI results for other file %s (%s = %7.2f %+4.2f %+4.2f) does not match main file %s (%s = %7.2f %+4.2f %+4.2f)"%(
          ofname,poi2.GetTitle(),poi2.getVal(),poi2.getAsymErrorLo(),poi2.getAsymErrorHi(),
          fname, poi.GetTitle(), poi.getVal(), poi.getAsymErrorLo(), poi.getAsymErrorHi())
      for poi_chan in pois_chan2:
        if not any(poi_chan.GetName()==p.GetName() for p in pois_chan1):
          print ">>> Adding %r from %s"%(poi_chan.GetTitle(),ofname)
          pois_chan.append(poi_chan)
  
  # SORT
  if chandict: # reorder according to ordered channel dictionary
    keys = chandict.keys()
    pois_chan.sort(key=lambda v: keys.index(vname(v)) if vname(v) in keys else len(keys))
  
  # CREATE POINTS
  if verb>=1:
    print ">>> xtitle=%s"%(xtitle)
    print ">>> rmin=%s, rmax=%s"%(rmin,rmax)
  print ">>> %7.2f %+4.2f %+4.2f %s"%(poi.getVal(),poi.getAsymErrorLo(),poi.getAsymErrorHi(),poi.GetTitle())
  nchans = len(pois_chan)
  frame = TH2F('frame',";Best fit %s;"%(xtitle),1,rmin,rmax,nchans,0,nchans)
  graph = TGraphAsymmErrors(nchans)
  for i, poi_chan in enumerate(pois_chan):
    channel = poi_chan.GetTitle()
    yval = nchans-i-0.5
    xval = poi_chan.getVal()
    errup, errdn = poi_chan.getAsymErrorLo(), poi_chan.getAsymErrorHi()
    print ">>> %7.2f %+4.2f %+4.2f %s"%(xval,errup,errdn,channel) #poi_chan.GetName()
    graph.SetPoint(i,xval,yval)
    graph.SetPointError(i,-errup,errdn,0,0)
    frame.GetYaxis().SetBinLabel(nchans-i,channel)
  
  # PREPARE CANVAS
  tsize = 0.045
  canvas = TCanvas('canvas')
  canvas.SetMargin(0.2,0.02,0.15,0.02) # LRBT
  canvas.SetGridx(1)
  graph.SetLineColor(kRed)
  graph.SetLineWidth(3)
  graph.SetMarkerStyle(21)
  #frame.GetXaxis().SetNdivisions(505)
  frame.GetXaxis().SetTitleSize(0.055)
  frame.GetXaxis().SetLabelSize(tsize)
  frame.GetYaxis().SetLabelSize(1.5*tsize)
  frame.Draw()
  
  # DRAW
  band = TBox(poi.getVal()+poi.getAsymErrorLo(),0,poi.getVal()+poi.getAsymErrorHi(),nchans)
  #band.SetFillStyle(3013)
  band.SetFillColor(65)
  band.SetLineStyle(0)
  band.Draw('SAME') #DrawClone
  line = TLine(poi.getVal(),0,poi.getVal(),nchans) # global line
  line.SetLineWidth(4)
  line.SetLineColor(214)
  line.Draw('SAME') #DrawClone
  graph.Draw('P SAME')
  
  # EXTRA TEXT
  latex = None
  if texts:
    latex = TLatex()
    latex.SetTextSize(tsize)
    latex.SetTextAlign(33)
    latex.SetTextFont(42)
    #latex.SetTextColor(kRed)
    latex.SetNDC(True)
    x, y = 0.96, 0.96
    for i, line in enumerate(texts):
      y -= 1.15*i*tsize
      if verb>=1:
        print ">>> Extra text: x=%s y=%s, line=%s"%(x,y,line)
      latex.DrawLatex(x,y,line)
  
  # STORE
  canvas.RedrawAxis()
  for ext in exts:
    canvas.SaveAs(outname+'.'+ext)
  canvas.Close()
  

def main(args):
  filenames  = args.filenames
  outname    = args.outname
  masses     = args.masses
  names      = args.names
  others     = args.others
  tag        = args.tag
  poi        = args.poi
  text       = args.text
  xtitle     = args.title
  dictfname  = args.translate
  chantitles = args.chantitles
  rmin, rmax = args.rMin, args.rMax
  verbosity  = args.verbosity
  chandict   = OrderedDict()
  if dictfname:
    if verbosity>=2:
      print ">>> Opening JSON file %r"%(dictfname)
    with open(translate,'r') as dfile:
      chandict = json.load(dfile,object_pairs_hook=OrderedDict)
  for channel in chantitles:
    if verbosity>=2:
      print ">>> Parsing channel title %r"%(channel)
    channel, chantitle = channel.split('=',1) if '=' in channel else (channel,channel)
    chandict[channel] = chantitle or channel
    print ">>> %r -> %r"%(channel,chandict[channel])
  for fname in filenames:
    for mass in masses:
      for name in names:
        fname_   = fname.replace('$NAME',name).replace('$MASS',mass)
        others_  = [f.replace('$NAME',name).replace('$MASS',mass) for f in others]
        outname_ = outname.replace('$NAME',name).replace('$TAG',tag).replace('$MASS',mass)
        plotChannelCompatibility(fname_,outname_,poi=poi,rmin=rmin,rmax=rmax,xtitle=xtitle,
                                 text=text,chandict=chandict,others=others_,verb=verbosity)
  

if __name__ == "__main__":
  from argparse import ArgumentParser
  parser = ArgumentParser(prog="pulls",description="Plotting script for pulls",epilog="Good luck!")
  parser.add_argument("filenames",        nargs='+', default=["higgsCombineTest$NAME.ChannelCompatibilityCheck.mH$MASS.root"],
                                          help="input ROOT files from ChannelCompatibilityCheck, default=%(default)s")
  parser.add_argument('-O',"--other",     dest='others', nargs='+', default=[ ], help="extra input file(s) to add in plot")
  parser.add_argument('-o',"--outname",   default='plot_channelCompatibility$NAME$TAG.mH$MASS',
                                          help="name of output image files, default=%(default)s")
  parser.add_argument('-e',"--exts",      nargs='+', default=['png','pdf'],help="output file extensions")
  parser.add_argument('-m',"--masses",    nargs='+', default=['120'],help="Mass for input files")
  parser.add_argument('-n',"--names",     nargs='+', default=[''],help="Names for input files")
  parser.add_argument(     "--rMin",      type=float, help="Minimum of POI range for x axis")
  parser.add_argument(     "--rMax",      type=float, help="Maximum of POI range for x axis")
  parser.add_argument('-E',"--text",      help="extra text")
  parser.add_argument('-p',"--title",     default='r', help="Title of POI for title of x axis")
  parser.add_argument('-P',"--poi",       default='r',help="Parameter of interest")
  parser.add_argument('-t',"--tag",       default='t',help="Tag for output file")
  parser.add_argument('-c',"--chantitles",nargs='+',default=[],help="titles for channels")
  parser.add_argument('-T',"--translate", help="json file with dictionary for channel titles")
  parser.add_argument('-v',"--verbose",   dest='verbosity', type=int, nargs='?', const=1, default=0,
                                          help="set verbosity level" )
  args = parser.parse_args()
  main(args)
  
