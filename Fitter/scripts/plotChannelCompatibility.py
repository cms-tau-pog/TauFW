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
gStyle.SetEndErrorSize(7) # size of bars at the end of error bars


def rmprefix(var,poiname='r'):
  """Help function to remove the ChannelCompatibilityCheck prefix."""
  #vname = lambda v: v.GetName().replace(prefix,'') # help function
  prefix = "_ChannelCompatibilityCheck_%s_"%(poiname)
  return var.GetName().replace(prefix,'')


def channelkey(var,keys,poiname='r'):
  """Sort key to sort according to the order in the dictionary."""
  #lambda v: keys.index(rmprefix(v)) if rmprefix(v) in keys else len(keys))
  vname = rmprefix(var,poiname)
  return keys.index(vname) if vname in keys else len(keys)
  

def getPOIs(fname,**kwargs):
  """Get POI from ChannelCompatibilityCheck file."""
  poiname  = kwargs.get('poi',      None ) # string
  chandict = kwargs.get('chandict', { }  ) # dictionary for channel POIs
  verb     = kwargs.get('verb',     0    )
  if verb>=1:
    print ">>> getPOIs(%r)"%(fname)
  
  # GET FITS
  file = TFile.Open(fname,'READ')
  fit_nom = file.Get('fit_nominal')
  fit_alt = file.Get('fit_alternate')
  if not fit_nom or not fit_alt:
    print("Input file %s does not contain 'fit_nominal' or 'fit_alternate'..."%(file.GetName())+
          "Make sure you use --saveFitResult with -M ChannelCompatibilityCheck.")
    return
  
  # GET MAIN POI
  prefix = "_ChannelCompatibilityCheck_%s_"%(poiname)
  poi = fit_nom.floatParsFinal().find(poiname) # RooRealVar object
  if not poi:
    print "Nominal fit does not contain parameter of interest %s"%(poiname)
    return
  
  # GET CHANNEL POIs
  pois_chan = [ ]
  iter = fit_alt.floatParsFinal().createIterator()
  var = iter.Next()
  while var:
    if prefix in var.GetName():
      varname = var.GetName()
      channel = rmprefix(var,poiname)
      var.SetName(channel)
      if channel in chandict:
        channel = chandict[channel]
      var.SetTitle(channel)
      print ">>> Found channel POI %r -> %r"%(varname,channel)
      pois_chan.append(var)
    var = iter.Next()
  
  file.Close()
  return poi, pois_chan # RooRealVar, [RooRealVar,...]
  

def plotChannelCompatibility(fname,outname,**kwargs):
  # Adapted from
  #   https://github.com/cms-analysis/HiggsAnalysis-CombinedLimit/blob/master/test/plotting/cccPlot.cxx
  poiname   = kwargs.get('poi',       None    ) # string
  xtitle    = kwargs.get('xtitle',    None    ) #" #sigma/#sigma_{SM}"
  chandict  = kwargs.get('chandict',  { }     ) # dictionary for channel POIs
  others    = kwargs.get('others',    [ ]     )
  texts     = kwargs.get('text',      [ ]     ) or [ ]
  exts      = kwargs.get('ext',       ['png'] )
  rmin      = kwargs.get('rmin',      None    )
  rmax      = kwargs.get('rmax',      None    )
  autorange = kwargs.get('autorange', False   )
  verb      = kwargs.get('verb',      0       )
  if not isinstance(exts,list):
    exts = list(exts)
  if isinstance(texts,str):
    texts = texts.split('\\n') if '\\n' in texts else texts.split('\n')
  
  # GET POIs
  poi, pois_chan = getPOIs(fname,**kwargs) # RooRealVar, [RooRealVar,...]
  if others:
    for ofname in others:
      pois_chan1 = pois_chan[:] # so list does not increase during iteration
      poi2, pois_chan2 = getPOIs(ofname,**kwargs)
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
    keys = chandict.keys() # ordered keys
    pois_chan.sort(key=lambda v: channelkey(v,keys,poiname))
  poi.SetTitle('Combined')
  pois_chan.append(poi) # add main POI
  
  # CREATE POINTS
  rmin_ = poi.getMin()
  rmax_ = poi.getMax()
  if autorange:
    rmin_ = rmin_ if rmin==None else rmin
    rmax_ = rmax_ if rmax==None else rmax
  print ">>> %7.2f %+4.2f %+4.2f %s (%r)"%(poi.getVal(),poi.getAsymErrorHi(),poi.getAsymErrorLo(),poi.GetName(),poi.GetTitle())
  nchans = len(pois_chan)
  graph = TGraphAsymmErrors(nchans)
  for i, poi_chan in enumerate(pois_chan):
    varname = poi_chan.GetName() #rmprefix(poi_chan,poiname)
    channel = poi_chan.GetTitle()
    yval = nchans-i-0.5
    xval = poi_chan.getVal()
    errdn, errup = -poi_chan.getAsymErrorLo(), poi_chan.getAsymErrorHi()
    print ">>> %7.2f %+4.2f %+4.2f %s (%r)"%(xval,errup,-errdn,varname,channel) #poi_chan.GetName()
    graph.SetPoint(i,xval,yval)
    graph.SetPointError(i,errdn,errup,0,0)
    if rmin_>xval-errdn:
      rmin_ = xval-errdn
    if rmax_<xval+errup:
      rmax_ = xval+errup
  
  # CREATE FRAME
  if rmin==None or autorange:
    rmin = 1.05*rmin_-0.05*rmax_ # add ~5% margin
  if rmax==None or autorange:
    rmax = 1.05*rmax_-0.05*rmin_ # add ~5% margin
  if xtitle==None:
    xtitle = chandict.get(poiname,poiname)
  if verb>=1:
    print ">>> xtitle=%r, rmin=%.6g, rmax=%.6g"%(xtitle,rmin,rmax)
  frame = TH2F('frame',";Best fit %s;"%(xtitle),1,rmin,rmax,nchans,0,nchans)
  for i, poi_chan in enumerate(pois_chan):
    channel = poi_chan.GetTitle()
    frame.GetYaxis().SetBinLabel(nchans-i,channel)
  
  # PREPARE CANVAS
  tsize  = 0.050
  bmarg  = 0.15
  canvas = TCanvas("canvas","Pulls",900,140+nchans*60)
  canvas.SetMargin(0.2,0.02,bmarg,0.02) # LRBT
  canvas.SetGridx(1)
  canvas.SetTicks(1,1)
  graph.SetLineColor(kRed)
  graph.SetLineWidth(3)
  graph.SetMarkerStyle(8)
  graph.SetMarkerSize(1)
  #graph.SetMarkerStyle(21)
  #frame.GetXaxis().SetNdivisions(505)
  frame.GetXaxis().SetTitleSize(0.055)
  frame.GetXaxis().SetLabelSize(tsize)
  frame.GetYaxis().SetLabelSize(1.5*tsize)
  frame.Draw()
  
  # DRAW
  band = None
  poi_up = poi.getVal()+poi.getAsymErrorHi()
  poi_dn = poi.getVal()+poi.getAsymErrorLo()
  if poi_up>=rmin and poi_dn<=rmax: # make sure entire band within range
    band = TBox(max(rmin,poi_dn),0,min(rmax,poi_up),nchans)
    #band.SetFillStyle(3013)
    band.SetFillColor(65)
    band.SetLineStyle(0)
    band.Draw('SAME') #DrawClone
    line = TLine(poi.getVal(),0,poi.getVal(),nchans) # global line
    line.SetLineWidth(4)
    line.SetLineColor(214)
    line.Draw('SAME') #DrawClone
    graph.Draw('P0 SAME')
  
  # EXTRA TEXT
  latex = None
  if texts:
    lsize = 0.050
    latex = TLatex()
    latex.SetTextSize(lsize)
    latex.SetTextAlign(30)
    latex.SetTextFont(42)
    #latex.SetTextColor(kRed)
    latex.SetNDC(True)
    x, y = 0.96, bmarg+0.04
    for i, line in enumerate(texts):
      y -= 1.15*i*lsize
      if verb>=1:
        print ">>> Extra text: x=%.6g y=%.6g, line=%r"%(x,y,line)
      latex.DrawLatex(x,y,line)
  
  # STORE
  canvas.RedrawAxis()
  for ext in exts:
    canvas.SaveAs(outname+'.'+ext)
  canvas.Close()
  

def main(args):
  filenames  = args.filenames
  outname    = args.outname
  exts       = args.exts
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
  autorange  = args.autoRange
  verbosity  = args.verbosity
  chandict   = OrderedDict()
  if dictfname:
    if verbosity>=2:
      print ">>> Opening JSON file %r"%(dictfname)
    with open(translate,'r') as dfile:
      chandict = json.load(dfile,object_pairs_hook=OrderedDict)
  for channel in chantitles:
    channel, chantitle = channel.split('=',1) if '=' in channel else (channel,channel)
    chandict[channel] = chantitle or channel
    if verbosity>=2:
      print ">>> Parsed channel title %r -> %r"%(channel,chandict[channel])
  for fname in filenames:
    for mass in masses:
      for name in names:
        fname_   = fname.replace('$NAME',name).replace('$MASS',mass)
        others_  = [f.replace('$NAME',name).replace('$MASS',mass) for f in others]
        outname_ = outname.replace('$NAME',name).replace('$TAG',tag).replace('$MASS',mass)
        plotChannelCompatibility(fname_,outname_,poi=poi,rmin=rmin,rmax=rmax,autorange=autorange,xtitle=xtitle,
                                 text=text,chandict=chandict,others=others_,ext=exts,verb=verbosity)
  

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
  parser.add_argument('-a',"--autoRange", action='store_true',help="Allow automatic setting of POI range")
  parser.add_argument('-E',"--text",      help="extra text")
  parser.add_argument('-p',"--title",     help="Title of POI for title of x axis")
  parser.add_argument('-P',"--poi",       default='r',help="Parameter of interest")
  parser.add_argument('-t',"--tag",       default='t',help="Tag for output file")
  parser.add_argument('-c',"--chantitles",nargs='+',default=[],help="titles for channels")
  parser.add_argument('-T',"--translate", help="json file with dictionary for channel titles")
  parser.add_argument('-v',"--verbose",   dest='verbosity', type=int, nargs='?', const=1, default=0,
                                          help="set verbosity level" )
  args = parser.parse_args()
  main(args)
  
