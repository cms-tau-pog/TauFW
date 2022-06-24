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
from ROOT import ROOT, gROOT, gStyle, TFile, TH2F, TCanvas, TGraphAsymmErrors, TLatex, TLegend, TBox, TLine,\
                 kDashed, kBlack, kRed, kBlue
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
  

def scalePOI(xvar,scale,verb=0):
  """Scale POI (RooRealVar)."""
  if not scale or scale==1:
    return xvar
  if isinstance(xvar,list):
    return [scalePOI(v,scale,verb=verb) for v in xvar]
  if verb>=2:
    print '-'*80
    print "scalePOI: Scale %s by %s"%(xvar.GetName(),scale)
    xvar.Print()
  xmin, xmax = xvar.getMin(), xvar.getMax()
  xvar.setRange(scale*xmin,scale*xmax)
  xval, xhi, xlo = xvar.getVal(), xvar.getAsymErrorHi(), xvar.getAsymErrorLo()
  xvar.setVal(scale*xval)
  #xvar.setError(abs(scale*xlo))
  xvar.setAsymError(scale*xlo,scale*xhi)
  if verb>=2:
    xvar.Print()
    print '-'*80
  return xvar
  

def getPOIs(fname,**kwargs):
  """Get POI from ChannelCompatibilityCheck file."""
  poiname  = kwargs.get('poi',      None ) # string
  chandict = kwargs.get('chandict', { }  ) # dictionary for channel POIs
  scale    = kwargs.get('scale',    1    ) # scale by number (e.g. to convert to cross section)
  verb     = kwargs.get('verb',     0    )
  if verb>=1:
    print ">>> getPOIs(%r,scale=%r)"%(fname,scale)
  
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
  xvar = iter.Next()
  while xvar:
    if prefix in xvar.GetName():
      varname = xvar.GetName()
      channel = rmprefix(xvar,poiname)
      xvar.SetName(channel)
      if channel in chandict:
        channel = chandict[channel]
      xvar.SetTitle(channel)
      print ">>>   Found channel POI %r -> %r"%(varname,channel)
      pois_chan.append(xvar)
    xvar = iter.Next()
  
  # SCALE
  if scale and scale!=0 and scale>0:
    scalePOI(pois_chan+[poi],scale,verb=verb)
  
  file.Close()
  return poi, pois_chan # RooRealVar, [RooRealVar,...]
  

def plotChannelCompatibility(fname,outname,**kwargs):
  # Adapted from
  #   https://github.com/cms-analysis/HiggsAnalysis-CombinedLimit/blob/master/test/plotting/cccPlot.cxx
  poiname   = kwargs.get('poi',       None    ) # string
  xtitle    = kwargs.get('xtitle',    None    ) #" #sigma/#sigma_{SM}"
  chandict  = kwargs.get('chandict',  { }     ) # dictionary for channel POIs
  others    = kwargs.get('others',    [ ]     ) # list of file names
  bonly     = kwargs.get('bonly',     [ ]     ) # list of file names for B-only (from Asimov)
  texts     = kwargs.get('text',      [ ]     ) or [ ]
  exts      = kwargs.get('ext',       ['png'] )
  rmin      = kwargs.get('rmin',      None    )
  rmax      = kwargs.get('rmax',      None    )
  autorange = kwargs.get('autorange', False   )
  logx      = kwargs.get('logx',      False   )
  lumi      = kwargs.get('lumi',      None    ) # integrated luminosity
  xsec      = kwargs.get('xsec',      None    ) # cross section (in units of pb) to scale graph
  scale     = kwargs.get('scale',     1       ) or 1
  verb      = kwargs.get('verb',      0       )
  if xsec:
    kwargs['scale'] = xsec*scale # for getPOIs
  if not isinstance(exts,list):
    exts = list(exts)
  if isinstance(texts,str):
    texts = texts.split('\\n') if '\\n' in texts else texts.split('\n')
  assert (not bonly or len(bonly)==len(others)+1), (
    "plotChannelCompatibility: Number of B-only files (%s) does not match number of S+B files (%s)!"%(len(bonly),len(others)+1))
  
  # GET POIs
  print ">>> Getting POIs from %s"%(fname)
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
          print ">>>   Adding %r from %s"%(poi_chan.GetTitle(),ofname)
          pois_chan.append(poi_chan)
  
  # GET B-only
  poi_bo = None
  if bonly:
    for i, fname_bo in enumerate(bonly):
      print ">>> Getting B-only from %s"%(fname_bo)
      poi_bo, pois_chan_bo_ = getPOIs(fname_bo,**kwargs) # RooRealVar, [RooRealVar,...]
      if i==0:
        if verb>=1:
          print ">>>   Matched POI for B-only %s (%6.4f %+6.4f %+6.4f)"%(poi_bo.GetName(),poi_bo.getVal(),poi_bo.getAsymErrorHi(),poi_bo.getAsymErrorLo())
        poi.bonly = (-poi_bo.getAsymErrorLo(),poi_bo.getAsymErrorHi()) # store for later use
      for poi_chan_bo in pois_chan_bo_:
        for poi_chan in pois_chan: # look for corresponding
          if poi_chan.GetName()==poi_chan_bo.GetName():
            if verb>=1:
              print ">>>   Matched channel POI for B-only %s (%6.4f %+6.4f %+6.4f)"%(poi_chan_bo.GetName(),poi_chan_bo.getVal(),poi_chan_bo.getAsymErrorHi(),poi_chan_bo.getAsymErrorLo())
            poi_chan.bonly = (-poi_chan_bo.getAsymErrorLo(),poi_chan_bo.getAsymErrorHi())
            break
        else:
          print ">>> WARNING! Did not find corresponding channel POI for B-only %s"%(poi_chan_bo.GetName())
  
  # SORT
  if chandict: # reorder according to ordered channel dictionary
    keys = chandict.keys() # ordered keys
    pois_chan.sort(key=lambda v: channelkey(v,keys,poiname))
  poi.SetTitle('Combined')
  pois_chan.append(poi) # add main POI
  
  # CREATE POINTS
  nchans = len(pois_chan)
  rmin_ = poi.getMin()
  rmax_ = poi.getMax()
  if autorange:
    rmin_ = rmin_ if rmin==None else rmin
    rmax_ = rmax_ if rmax==None else rmax
  print ">>> Creating graphs with %s channels..."%(nchans)
  print ">>> %7.2f %+4.2f %+4.2f %s (%s)"%(poi.getVal(),poi.getAsymErrorHi(),poi.getAsymErrorLo(),poi.GetName(),poi.GetTitle())
  graph  = TGraphAsymmErrors(nchans)
  bandbo = TGraphAsymmErrors(nchans) if bonly else None
  graph.SetTitle("Observed")
  bandbo.SetTitle("Bkg. unc.")
  for i, poi_chan in enumerate(pois_chan):
    varname = poi_chan.GetName() #rmprefix(poi_chan,poiname)
    channel = poi_chan.GetTitle()
    yval = nchans-i-0.5
    xval = poi_chan.getVal()
    errdn, errup = -poi_chan.getAsymErrorLo(), poi_chan.getAsymErrorHi()
    xdn, xup = xval-errdn, xval+errup
    print ">>> %7.2f %+4.2f %+4.2f %s (%s)"%(xval,errup,-errdn,varname,channel) #poi_chan.GetName()
    graph.SetPoint(i,xval,yval)
    graph.SetPointError(i,errdn,errup,0,0)
    if rmin_>xdn:
      rmin_ = xdn
    if i==0 and autorange and lumi and lumi>0:
      xup = 1.15*xup-0.15*rmin_ # add 10% to avoid CMS logo in top right corner
    if rmax_<xup:
      rmax_ = xup
    if bonly:
      try:
        yval_bo = nchans-i if i==0 else nchans-i-1 # align first error at top, rest at bottom
        yerr_bo = (1.0,0.0) if i==0 else (0.0,1.0)
        errdn_bo, errup_bo = poi_chan.bonly
        bandbo.SetPoint(i,0,yval_bo)
        bandbo.SetPointError(i,errdn_bo,errup_bo,*yerr_bo)
        print ">>> %7.2f %+4.2f %+4.2f %s (%s, B-only)"%(0.0,errup_bo,-errdn_bo,varname,channel) #poi_chan.GetName()
        if rmin_>-errdn_bo:
          rmin_ = -errdn_bo
      except AttributeError as err:
        print("WARNING! AttributeError: channel POI %s does not have B-only! Ignoring...")
  ###if xsec and xsec>0:
  ###  graph.Scale(xsec,'xy')
  ###  bandbo.Scale(xsec,'xy')
  
  # CREATE FRAME
  if rmin==None or autorange:
    rmin = 1.05*rmin_-0.05*rmax_ # add ~5% margin
  if rmax==None or autorange:
    rmax = 1.05*rmax_-0.05*rmin_ # add ~5% margin
  if xtitle==None:
    if xsec and xsec>0:
      xtitle = "Measured cross section #sigma [pb]"
    else: #if xtitle==None
      xtitle = "Best fit %s"%(chandict.get(poiname,poiname))
  if verb>=1:
    print ">>> xtitle=%r, rmin=%.6g, rmax=%.6g"%(xtitle,rmin,rmax)
  frame = TH2F('frame',";%s;"%(xtitle),1,rmin,rmax,nchans,0,nchans)
  for i, poi_chan in enumerate(pois_chan):
    channel = poi_chan.GetTitle()
    frame.GetYaxis().SetBinLabel(nchans-i,channel)
  
  # PREPARE CANVAS
  tsize  = 0.050
  lmarg, rmarg = 0.2, 0.02
  bmarg, tmarg  = 0.15, 0.065
  canvas = TCanvas("canvas","Pulls",900,150+nchans*60)
  canvas.SetMargin(lmarg,rmarg,bmarg,tmarg) # LRBT
  canvas.SetGridx(1)
  canvas.SetTicks(1,1)
  if logx:
    canvas.SetLogx(True)
  graph.SetLineColor(kRed+1)
  graph.SetLineWidth(3)
  graph.SetMarkerStyle(8)
  graph.SetMarkerSize(1)
  #graph.SetMarkerStyle(21)
  #frame.GetXaxis().SetNdivisions(505)
  frame.GetXaxis().SetTitleSize(0.055)
  frame.GetXaxis().SetLabelSize(tsize)
  frame.GetYaxis().SetLabelSize(1.5*tsize)
  frame.Draw()
  
  # LEGEND
  lsize  = 0.055
  x1, y1 = 1.0-rmarg, bmarg+0.06
  height = 1.1*lsize*(2+1*bool(bandbo))
  legend = TLegend(x1,y1,x1-0.25,y1+height)
  legend.SetMargin(0.15)
  legend.SetFillStyle(0)
  legend.SetBorderSize(0)
  legend.SetTextSize(lsize)
  legend.AddEntry(graph,graph.GetTitle(),'ep')
  
  # DRAW
  band, line = None, None # global/combined band
  poi_up = poi.getAsymErrorHi() #poi.getVal()+poi.getAsymErrorHi()
  poi_dn = -poi.getAsymErrorLo() #poi.getVal()+poi.getAsymErrorLo()
  if poi_up>=rmin and poi_dn<=rmax: # make sure entire band within range
    ###band = TGraphAsymmErrors(1)
    ###band.SetTitle("Combined")
    ###band.SetPoint(0,poi.getVal(),0) # start at bottom
    ###band.SetPoint(1,poi.getVal(),nchans) # end at top
    ###band.SetPointError(0,max(rmin,poi_dn),min(rmax,poi_up),0,nchans/2.)
    ###band.SetPointError(1,max(rmin,poi_dn),min(rmax,poi_up),nchans/2.,0)
    ####band.SetFillStyle(3013)
    ###band.SetFillColor(65)
    ###band.SetLineStyle(0)
    ###band.SetLineWidth(2)
    ###band.SetLineColor(214)
    ######band.Draw('ZL SAME') # draw line only
    ####band.Draw('ZLE2 SAME') # draw with band
    ###legend.AddEntry(band,band.GetTitle(),'fl')
    ###band = TBox(max(rmin,poi_dn),0,min(rmax,poi_up),nchans)
    ####band.SetFillStyle(3013)
    ###band.SetFillColor(65)
    ###band.SetLineStyle(0)
    ###band.Draw('SAME') #DrawClone
    line = TLine(poi.getVal(),0,poi.getVal(),nchans) # global line
    line.SetLineWidth(2)
    line.SetLineColor(214)
    line.Draw('SAME')
    legend.AddEntry(line,"Combined",'l')
  graph.Draw('PE1 SAME') #PE0
  
  # ERROR BAND
  if bandbo:
    bandbo.SetLineWidth(2)
    bandbo.SetLineStyle(kDashed)
    bandbo.SetLineColor(kBlack)
    bandbo.SetFillStyle(3004) #3013
    bandbo.SetFillColor(kBlue+3) #kBlack
    bandbo.SetMarkerSize(0)
    bandbo.Draw('ZLE2 SAME')
    legend.AddEntry(bandbo,bandbo.GetTitle(),'fl')
  legend.Draw()
  
  # EXTRA TEXT
  latex = None
  if texts:
    lsize = 0.050
    latex = TLatex()
    latex.SetNDC(True)
    latex.SetTextFont(42)
    latex.SetTextColor(kBlack)
    if len(texts)==1 or lumi: # outside frame
      x, y = lmarg+0.01, 1.015-tmarg
      latex.SetTextSize(0.82*tmarg)
      latex.SetTextAlign(11) # 10*horizontal + 1*vertical
    else: # inside frame
      x, y = 0.96, bmarg+0.04
      latex.SetTextSize(lsize)
      latex.SetTextAlign(31) # 10*horizontal + 1*vertical
    for i, tline in enumerate(texts):
      y -= 1.15*i*lsize
      if verb>=1:
        print ">>> Extra text: x=%.6g y=%.6g, line=%r"%(x,y,tline)
      latex.DrawLatex(x,y,tline)
  
  # CMS LUMI
  if lumi and lumi>0:
    latex.SetTextAlign(31) # 10*horizontal + 1*vertical
    latex.SetTextFont(42)
    latex.SetTextSize(0.82*tmarg)
    latex.DrawLatex(1-rmarg,1.015-tmarg,"%s fb^{#minus1} (13 TeV)"%(lumi))
    latex.SetTextAlign(33) # 10*horizontal + 1*vertical
    latex.SetTextFont(62)
    latex.SetTextSize(1.4*lsize)
    latex.DrawLatex(0.98-rmarg,0.97-tmarg,"CMS")
  
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
  bonly      = args.bonly
  tag        = args.tag or ""
  poi        = args.poi
  text       = args.text
  lumi       = args.lumi
  xsec       = args.xsec
  xtitle     = args.title
  dictfname  = args.translate
  chantitles = args.chantitles
  rmin, rmax = args.rMin, args.rMax
  autorange  = args.autoRange
  logx       = args.log
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
        bonly_   = [f.replace('$NAME',name).replace('$MASS',mass) for f in bonly]
        outname_ = outname.replace('$NAME',name).replace('$TAG',tag).replace('$MASS',mass)
        plotChannelCompatibility(fname_,outname_,poi=poi,rmin=rmin,rmax=rmax,autorange=autorange,xtitle=xtitle,text=text,logx=logx,
                                 chandict=chandict,others=others_,bonly=bonly_,lumi=lumi,xsec=xsec,ext=exts,verb=verbosity)
  

if __name__ == "__main__":
  from argparse import ArgumentParser
  parser = ArgumentParser(prog="pulls",description="Plotting script for pulls",epilog="Good luck!")
  parser.add_argument("filenames",        nargs='+', default=["higgsCombineTest$NAME.ChannelCompatibilityCheck.mH$MASS.root"],
                                          help="Input ROOT files from ChannelCompatibilityCheck, default=%(default)s")
  parser.add_argument('-O',"--other",     dest='others', nargs='+', default=[ ], help="Extra input file(s) to add in plot")
  parser.add_argument('-b',"--bonly",     dest='bonly', nargs='+', default=[ ], help="Extra input file(s) to add B-only uncertainty band (from Asimov) at r=0")
  parser.add_argument('-o',"--outname",   default='plot_channelCompatibility$NAME$TAG.mH$MASS',
                                          help="name of output image files, default=%(default)s")
  parser.add_argument('-e',"--exts",      nargs='+', default=['png','pdf'],help="Output file extensions")
  parser.add_argument('-m',"--masses",    nargs='+', default=['120'],help="Mass for input files")
  parser.add_argument('-n',"--names",     nargs='+', default=[''],help="Names for input files")
  parser.add_argument(     "--rMin",      type=float, help="Minimum of POI range for x axis")
  parser.add_argument(     "--rMax",      type=float, help="Maximum of POI range for x axis")
  parser.add_argument('-a',"--autoRange", action='store_true',help="Allow automatic setting of POI range")
  parser.add_argument('-l',"--log",       action='store_true',help="Make x axis logarithmic")
  parser.add_argument('-E',"--text",      help="Extra text")
  parser.add_argument('-L',"--lumi",      type=float, help="Add integrated luminosity and CMS logo")
  parser.add_argument('-p',"--title",     help="Title of POI for title of x axis")
  parser.add_argument('-P',"--poi",       default='r',help="Parameter of interest")
  parser.add_argument('-t',"--tag",       help="Tag for output file")
  parser.add_argument('-x',"--xsec",      type=float,help="Convert signal strength to cross section in pb")
  parser.add_argument('-c',"--chantitles",nargs='+',default=[],help="Titles for channels")
  parser.add_argument('-T',"--translate", help="JSON file with dictionary for channel titles")
  parser.add_argument('-v',"--verbose",   dest='verbosity', type=int, nargs='?', const=1, default=0,
                                          help="Set verbosity level" )
  args = parser.parse_args()
  main(args)
  
