#! /usr/bin/env python3
# Author: Izaak Neutelings (June 2023)
#   cd PicoProducer/data/beamspot/
#   ./getBeamSpotProfiles.py SingleMuon_Run2018*.root -o beamspot_UL2018.root --tree
#   ./getBeamSpotProfiles.py SingleMuon_Run2018*.root -o beamspot_UL2018.root --histdir beamspot
import os
#import numpy as np
#from collections import OrderedDict
import ROOT; ROOT.PyConfig.IgnoreCommandLineOptions = True
from ROOT import gROOT, gStyle, gPad, gDirectory, TFile, TChain, TH1D, TH2D,\
                 TCanvas, TLegend, TLatex, kBlue, kRed, kOrange
gStyle.SetOptStat(False)
gROOT.SetBatch(True)

# HISTOGRAM TITLES
tit_z      = "Beamspot z [cm]"
tit_sig    = "Beamspot width [cm]"
tit_sigErr = "Beamspot width error [cm]"
tit_sigUp  = "Beamspot width (up) [cm]"
tit_sigDn  = "Beamspot width (down) [cm]"


def getBeamspotProfilesFromTree(infnames,outfname,tname='tree',cut="",verb=0):
  """Get beamspot profiles from trees (after pre-selections via nanoaAOD-tools)."""
  print(">>> getBeamspotProfilesFromTree")
  #print(">>> getBeamspotProfilesFromTree(%r,%r)"%(infnames,outfname))
  
  # PREPARE INPUT TREE
  chain = TChain(tname)
  for fname in infnames:
    print(">>>   Adding %s..."%(fname))
    chain.Add(fname)
  
  # PREPARE HISTOGRAMS
  ###zedges    = np.concatenate((np.arange(-6,-2,0.2),np.arange(-2,0,0.05),np.arange(0,2,0.05),np.arange(2,6,0.2)))
  ###if verb>=4:
  ###  print(">>>   Edges: %r"%(zedges))
  zbins = (300,-6,6) # equidistant binning
  ###zbins = (len(zedges)-1,zedges) # variable binning
  sigbins = (200, 0,8)
  errbins   = (100, 0,0.5) # sigma error
  if verb>=2:
    print(">>>   Binning for z: %r"%(zbins,))
    print(">>>   Binning for sigma: %r"%(sigbins,))
  hists = [
    TH1D('bs_z',           '%s;%s;Events'%(tit_z,tit_z),          *zbins),
    TH1D('bs_sigma',       '%s;%s;Events'%(tit_sig,tit_sig),      *sigbins),
    TH1D('bs_sigmaErr',    '%s;%s;Events'%(tit_sigErr,tit_sigErr),*errbins),
    TH1D('bs_sigmaUp',     '%s;%s;Events'%(tit_sigUp,tit_sigUp),  *sigbins),
    TH1D('bs_sigmaDown',   '%s;%s;Events'%(tit_sigDn,tit_sigDn),  *sigbins),
    TH2D('bs_z_vs_sigma',  ';%s;%s;Events'%(tit_sig,tit_z),       *(zbins+sigbins)),
    TH2D('bs_err_vs_sigma',';%s;%s;Events'%(tit_sig,tit_sigErr),  *(sigbins+errbins)),
  ]
  
  # DRAW
  #cut  = ""
  for hist in hists:
    hname = hist.GetName()
    var = hname
    if '_vs_' in hname:
      yvar, xvar = hname.replace('_err','_sigmaErr').split('_vs_')
      var = "bs_%s:%s"%(xvar,yvar)
    elif var.endswith('Up'):
      var = var[:-2]
      var = "%s+%sErr"%(var,var)
    elif var.endswith('Down'):
      var = var[:-4]
      var = "%s-%sErr"%(var,var)
    dcmd = "%s >> %s"%(var,hname)
    if isinstance(hist,TH2D):
      dopt = 'gOff COLZ'
      assert ':' in dcmd, "Draw command %r wrong format for 2D histogram!"%(dcmd)
    else:
      dopt = 'gOff'
    print(">>>   Drawing %r..."%(dcmd))
    nevts = chain.Draw(dcmd,cut,dopt)
    print(">>>     => %s events"%(nevts))
  
  # DIVIDE and SAVE histograms
  print(">>>   Writing to file %s..."%(outfname))
  file = TFile(outfname,'UPDATE') #RECREATE
  for hist in hists:
    hname = hist.GetName()
    print(">>>     Histogram %s..."%(hname))
    if hist.InheritsFrom('TH2'):
      hist.SetOption('COLZ') # for display in TBrowser
    hist.Write(hname,hist.kOverwrite)
  file.Close()
  print(">>> ")
  

def getBeamspotProfilesFromHist(infnames,outfname,hdname='beamspot',verb=0):
  """Get beamspot profiles from histograms."""
  print(">>> getBeamspotProfilesFromHist")
  #print(">>> getBeamspotProfilesFromHist(%r,%r)"%(infnames,outfname))
  
  # PREPARE HISTOGRAMS
  hnames = [
    'bs_z',
    'bs_sigma', 'bs_sigmaErr',
    'bs_sigmaUp', 'bs_sigmaDown',
    'bs_sigma_vs_z', 'bs_err_vs_sig',
  ]
  hists = { }
  
  # ADD HISTOGRAMS
  for fname in infnames:
    print(">>>   Opening %s..."%(fname))
    file = TFile.Open(fname,'READ')
    if verb>=2:
      tdir = file.Get(hdname)
      print(">>> Contents of %s"%(tdir.GetPath()))
      tdir.ls()
    for hname in hnames:
      hname_ = "%s/%s"%(hdname,hname)
      hist = file.Get(hname_)
      print(">>>     Adding %s:%s..."%(fname,hname_))
      if not hist:
        print(">>> WARNING! Could not find %s:%s"%(fname,hname_))
        continue
      if hname in hists:
        #print(hists[hname].GetEntries(),hist.GetEntries())
        hists[hname].Add(hist)
      else:
        hists[hname] = hist
        hist.SetDirectory(0)
    file.Close()
  
  # DIVIDE and SAVE histograms
  print(">>>   Writing to file %s..."%(outfname))
  file = TFile(outfname,'UPDATE') #RECREATE
  for hname, hist in hists.items():
    print(">>>     Histogram %s..."%(hname))
    if hist.InheritsFrom('TH2'):
      hist.SetOption('COLZ') # for display in TBrowser
    hist.Write(hname,hist.kOverwrite)
  file.Close()
  print(">>> ")
  

# def plot2D(hname,hist,era,channel,log=False):
#   """Plot 2D efficiency."""
#   dir    = ensureDirectory('plots/%d'%era)
#   name   = "%s/%s_%s"%(dir,hname,channel)
#   if log:
#     name += "_log"
#   xtitle = "Jet p_{T} [GeV]"
#   ytitle = "Jet #eta"
#   ztitle = 'B tag efficiencies' if '_b_' in hname else 'B mistag rate'
#   xmin, xmax = 20, hist.GetXaxis().GetXmax()
#   zmin, zmax = 5e-3 if log else 0.0, 1.0
#   angle  = 22 if log else 77
#   
#   canvas = TCanvas('canvas','canvas',100,100,800,700)
#   canvas.SetFillColor(0)
#   canvas.SetBorderMode(0)
#   canvas.SetFrameFillStyle(0)
#   canvas.SetFrameBorderMode(0)
#   canvas.SetTopMargin(  0.07 ); canvas.SetBottomMargin( 0.13 )
#   canvas.SetLeftMargin( 0.12 ); canvas.SetRightMargin(  0.17 )
#   canvas.SetTickx(0); canvas.SetTicky(0)
#   canvas.SetGrid()
#   gStyle.SetOptTitle(0) #FontSize(0.04)
#   if log:
#     canvas.SetLogx()
#     canvas.SetLogz()
#   canvas.cd()
#   
#   hist.GetXaxis().SetTitle(xtitle)
#   hist.GetYaxis().SetTitle(ytitle)
#   hist.GetZaxis().SetTitle(ztitle)
#   hist.GetXaxis().SetLabelSize(0.048)
#   hist.GetYaxis().SetLabelSize(0.048)
#   hist.GetZaxis().SetLabelSize(0.048)
#   hist.GetXaxis().SetTitleSize(0.058)
#   hist.GetYaxis().SetTitleSize(0.058)
#   hist.GetZaxis().SetTitleSize(0.056)
#   hist.GetXaxis().SetTitleOffset(1.03)
#   hist.GetYaxis().SetTitleOffset(1.04)
#   hist.GetZaxis().SetTitleOffset(1.03)
#   hist.GetXaxis().SetLabelOffset(-0.004 if log else 0.005)
#   hist.GetZaxis().SetLabelOffset(-0.005 if log else 0.005)
#   hist.GetXaxis().SetRangeUser(xmin,xmax)
#   hist.SetMinimum(zmin)
#   hist.SetMaximum(zmax)
#   hist.Draw('COLZTEXT%d'%angle)
#   
#   gStyle.SetPaintTextFormat('.2f')
#   hist.SetMarkerColor(kRed)
#   hist.SetMarkerSize(1.8 if log else 1)
#   #gPad.Update()
#   #gPad.RedrawAxis()
#   
#   latex = TLatex()
#   latex.SetTextSize(0.048)
#   latex.SetTextAlign(23)
#   latex.SetTextFont(42)
#   latex.SetNDC(True)
#   latex.DrawLatex(0.475,0.99,hist.GetTitle()) # to prevent typesetting issues
#   
#   canvas.SaveAs(name+'.pdf')
#   canvas.SaveAs(name+'.png')
#   canvas.Close()
#   
# 
# def compareDataMCProfiles(datahists,mchist,era="",minbiases=0.0,tag="",rmin=0.6,rmax=1.4,xmax=100,delete=False):
#   """Compare data/MC profiles."""
#   print ">>> compareDataMCProfiles()"
#   mctitle = "MC average"
#   outdir  = ensuredir("plots")
#   if islist(datahists): # multiple datahists
#     if all(islist(x) for x in datahists): # datahists = [(minbias1,datahist1),...]
#       minbiases = [m for m,h in datahists]
#       datahists = [h for m,h in datahists]
#   else: # is single datahist histogram
#     minbiases = [minbiases]
#     datahists = [datahists]
#   hists  = datahists+[mchist]
#   styles = [kSolid]*len(datahists)+[kDashed]
#   colors = [kBlack]+linecolors if len(datahists)==1 else linecolors[:len(datahists)]+[kBlack]
#   if 'pmx' in tag:
#     width  = 0.35
#     position = 'TCR'
#   else:
#     width  = 0.35
#     position = 'TR'
#   if era and isinstance(era,str) and any(s in era for s in ["Run","VFP"]):
#     width =  max(width,0.26+(len(era)-5)*0.018)
#     position = 'TCR'
#   if tag and tag[0]!='_':
#     tag = '_'+tag
#   if 'pmx' in tag:
#     mctitle += " (%s pre-mixing)"%("old" if "old" in tag else "new")
#   if len(minbiases)==1 and minbiases[0]>0:
#     tag = "_"+str(minbiases[0]).replace('.','p')
#   
#   for datahist, minbias in zip(datahists,minbiases):
#     title = "Data"
#     if era:
#       title += " %s"%(era)
#     if minbias>0:
#       title += ", %.1f pb"%(minbias)
#     if 'VFP' in era:
#       title = title.replace("_"," ").replace("VFP","-VFP")
#     datahist.SetTitle(title)
#     datahist.Scale(1./datahist.Integral())
#   mchist.SetTitle(mctitle)
#   mchist.Scale(1./mchist.Integral())
#   
#   xtitle = "Mean number of pileup interactions" # 'true' pileup, i.e. Poisson mean
#   pname  = "%s/pileup_Data-MC_%s%s"%(outdir,era,tag)
#   plot   = Plot(hists,ratio=True,rmin=rmin,rmax=rmax,xmax=xmax)
#   plot.draw(xtitle=xtitle,ytitle="A.U.",rtitle="Data / MC",grid=False,
#             textsize=0.045,denom=-1,colors=colors,styles=styles)
#   plot.drawlegend(position,width=width)
#   plot.saveas(pname+".png")
#   plot.saveas(pname+".pdf")
#   plot.close(keep=True)
#   if delete:
#     deletehist(datahists) # clean memory  
# 

def makeTitle(tagger,wp,flavor,channel,era):
  flavor = flavor.replace('_',' ')
  if ' b ' in flavor:
    flavor = 'b quark'
  elif ' c ' in flavor:
    flavor = 'c quark'
  else:
    flavor = 'Light-flavor'
  channel = channel.replace('_',' ').replace('tau',"#tau_{h}").replace('mu',"#mu").replace('ele',"e")
  string = "%s, %s %s WP (%s, %d)"%(flavor,tagger,wp,channel,era)
  return string
  

def ensureTDirectory(file,dirname):
  dir = file.GetDirectory(dirname)
  if not dir:
    dir = file.mkdir(dirname)
    print(">>>   created directory %s in %s" % (dirname,file.GetName()))
  dir.cd()
  return dir
  

def ensureDirectory(dirname):
  """Make directory if it does not exist."""
  if not os.path.exists(dirname):
    os.makedirs(dirname)
    print('>>> made directory "%s"'%(dirname))
    if not os.path.exists(dirname):
      print('>>> failed to make directory "%s"'%(dirname))
  return dirname
  

def main(args):
  infnames  = args.infiles
  outfname  = args.outfile
  tname     = args.tname
  cut       = args.cut
  hdname    = args.hdname
  verb      = args.verbosity
  
  if tname: # use tree (with preselections)
    getBeamspotProfilesFromTree(infnames,outfname,tname=tname,cut=cut,verb=verb)
  else: # use histograms (without preselection)
    getBeamspotProfilesFromHist(infnames,outfname,hdname=hdname,verb=verb)
  

if __name__ == '__main__':
  from argparse import ArgumentParser
  description = '''Extract histograms from the analysis framework output to obtain total beam spot profiles.'''
  parser = ArgumentParser(prog="pileup",description=description,epilog="Succes!")
  parser.add_argument('infiles',          nargs='+', help="input files" )
  parser.add_argument('-T', '--tree',     dest='tname',  nargs='?', const='tree', default=None,
                      metavar='TREE',     help="get histograms from tree; tree name optional, default=%(const)r" )
  parser.add_argument('-c', '--cut',      default="", help="extra cut for drawing histograms" )
  parser.add_argument('-D', '--histdir',  dest='hdname', default='beamspot',
                      metavar='DIR',      help="name of directory in file with histograms, default=%(default)r" )
  parser.add_argument('-o', '--outfile',  default='beamspot.root', help="output file" )
  parser.add_argument('-t', '--tag',      default="", help="extra tag for histograms" )
  parser.add_argument('-p', '--plot',     action='store_true',  help="plot efficiencies" )
  parser.add_argument('-v', '--verbose',  dest='verbosity', type=int, nargs='?', const=1, default=0, action='store',
                                          help="set verbosity level" )
  args = parser.parse_args()
  print('')
  main(args)
  print(">>> Done\n")
  
