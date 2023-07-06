#! /usr/bin/env python
# Author: Izaak Neutelings (January 2019)
#   ./getBTagEfficiencies.py -c mutau - y 2016 -w loose -t DeepJet

import os, sys
from collections import OrderedDict
from argparse import ArgumentParser
import ROOT; ROOT.PyConfig.IgnoreCommandLineOptions = True
from ROOT import gROOT, gStyle, gPad, gDirectory, TFile, TTree, TH2F, TCanvas, TLegend, TLatex, kBlue, kRed, kOrange
gStyle.SetOptStat(False)
gROOT.SetBatch(True)

argv = sys.argv
description = '''Extract histograms from the analysis framework output run on MC samples to create b tag efficiencies.'''
parser = ArgumentParser(prog="pileup",description=description,epilog="Succes!")
parser.add_argument('-i', '--inputdir', dest='indir', help="eras to run" )
parser.add_argument('-y', '--era',      dest='eras', nargs='+', default=[],
                                        help="eras to run" )
parser.add_argument('-c', '--channel',  dest='channels', choices=['eletau','mutau','tautau','elemu','mumu','eleele'], type=str, nargs='+', default=['mutau'],
                                        help="channels to run" )
parser.add_argument('-t', '--tagger',   dest='taggers', choices=['DeepCSV','DeepJet'], type=str, nargs='+', default=['DeepJet'],
                                        help="tagger to run" )
parser.add_argument('-w', '--wp',       dest='wps', choices=['loose','medium','tight'], type=str, nargs='+', default=['medium'],
                                        help="working point to run" )
parser.add_argument('-d', '--chdir',    help="name of target directory in output file" )
parser.add_argument('-t', '--tag',      default="", help="extra tag for histograms" )
parser.add_argument('-C', '--campaign', default="", help="MC campaign name for output file" )
parser.add_argument('-p', '--plot',     action='store_true',  help="plot efficiencies" )
parser.add_argument('-v', '--verbose',  action='store_true',  help="print verbose" )
args = parser.parse_args()


def getBTagEfficiencies(tagger,wp,outfname,samples,era,channel,tag="",effdir=None,plot=False):
  """Get pileup profile in MC by adding Pileup_nTrueInt histograms from a given list of samples."""
  print '>>> getBTagEfficiencies("%s","%s","%s")'%(outfname,wp,era)
  
  # PREPARE numerator and denominator histograms per flavor
  nhists  = { }
  hists   = OrderedDict()
  histdir = 'btag'
  if effdir==None:
    effdir = channel+tag
  elif '$CHANNEL' in effdir:
    effdir = effdir.replace('$CHANNEL',channel)
  for flavor in ['b','c','udsg']:
    hname = "%s_%s_%s%s"%(tagger,flavor,wp,tag)
    hists[hname] = None        # numerator
    hists[hname+'_all'] = None # denominator
  
  # ADD numerator and denominator histograms
  for fname in samples:
    print ">>>   %s"%(fname)
    file = TFile(fname,'READ')
    if not file or file.IsZombie():
      print ">>>   Warning! getBTagEfficiencies: Could not open %s. Ignoring..."%(fname)
      continue
    for hname in hists:
      histpath = "%s/%s"%(histdir,hname)
      hist = file.Get(histpath)
      if not hist:
        print ">>>   Warning! getBTagEfficiencies: Could not open histogram '%s' in %s. Ignoring..."%(histpath,fname)        
        dir = file.Get(histdir)
        if dir: dir.ls()
        continue
      if hists[hname]==None:
        hists[hname] = hist.Clone(hname)
        hists[hname].SetDirectory(0)
        nhists[hname] = 1
      else:
        hists[hname].Add(hist)
        nhists[hname] += 1
    file.Close()
  
  # CHECK
  if len(nhists)>0:
    print ">>>   added %d MC hists:"%(sum(nhists[n] for n in nhists))
    for hname, nhist in sorted(nhists.items()):
      info = "%4.3e jets"%(hists[hname].GetEntries())
      if '_all' not in hname:
        info += " (%4.1f%%)"%(100.0*hists[hname].GetEntries()/hists[hname+"_all"].GetEntries())
      print ">>>     %-26s%4d histograms, %s"%(hname+':',nhist,info)
  else:
    print ">>>   no histograms added !"
    return
  
  # DIVIDE and SAVE histograms
  print ">>>   writing to %s..."%(outfname)
  file = TFile(outfname,'UPDATE') #RECREATE
  ensureTDirectory(file,channel)
  for hname, hist in hists.items():
    if 'all' in hname:
      continue
    hname_all = hname+'_all'
    hname_eff = 'eff_'+hname
    print ">>>     writing %s..."%(hname)
    print ">>>     writing %s..."%(hname_all)
    print ">>>     writing %s..."%(hname_eff)
    hist_all = hists[hname_all]
    hist_eff = hist.Clone(hname_eff)
    hist_eff.SetTitle(makeTitle(tagger,wp,hname_eff,channel,era))
    hist_eff.Divide(hist_all)
    hist.Write(hname,TH2F.kOverwrite)
    hist_all.Write(hname_all,TH2F.kOverwrite)
    hist_eff.Write(hname_eff,TH2F.kOverwrite)
    if plot:
      plot1D(hname_eff+"_vs_pt",hist,hist_all,era,channel,title=hist_eff.GetTitle(),log=True,write=True)
      plot2D(hname_eff,hist_eff,era,channel,log=True)
      plot2D(hname_eff,hist_eff,era,channel,log=False)
  file.Close()
  print ">>> "
  

def plot2D(hname,hist,era,channel,log=False):
  """Plot 2D efficiency."""
  dir    = ensureDirectory('plots/%d'%era)
  name   = "%s/%s_%s"%(dir,hname,channel)
  if log:
    name += "_log"
  xtitle = "Jet p_{T} [GeV]"
  ytitle = "Jet #eta"
  ztitle = 'B tag efficiencies' if '_b_' in hname else 'B mistag rate'
  xmin, xmax = 20, hist.GetXaxis().GetXmax()
  zmin, zmax = 5e-3 if log else 0.0, 1.0
  angle  = 22 if log else 77
  
  canvas = TCanvas('canvas','canvas',100,100,800,700)
  canvas.SetFillColor(0)
  canvas.SetBorderMode(0)
  canvas.SetFrameFillStyle(0)
  canvas.SetFrameBorderMode(0)
  canvas.SetTopMargin(  0.07 ); canvas.SetBottomMargin( 0.13 )
  canvas.SetLeftMargin( 0.12 ); canvas.SetRightMargin(  0.17 )
  canvas.SetTickx(0); canvas.SetTicky(0)
  canvas.SetGrid()
  gStyle.SetOptTitle(0) #FontSize(0.04)
  if log:
    canvas.SetLogx()
    canvas.SetLogz()
  canvas.cd()
  
  hist.GetXaxis().SetTitle(xtitle)
  hist.GetYaxis().SetTitle(ytitle)
  hist.GetZaxis().SetTitle(ztitle)
  hist.GetXaxis().SetLabelSize(0.048)
  hist.GetYaxis().SetLabelSize(0.048)
  hist.GetZaxis().SetLabelSize(0.048)
  hist.GetXaxis().SetTitleSize(0.058)
  hist.GetYaxis().SetTitleSize(0.058)
  hist.GetZaxis().SetTitleSize(0.056)
  hist.GetXaxis().SetTitleOffset(1.03)
  hist.GetYaxis().SetTitleOffset(1.04)
  hist.GetZaxis().SetTitleOffset(1.03)
  hist.GetXaxis().SetLabelOffset(-0.004 if log else 0.005)
  hist.GetZaxis().SetLabelOffset(-0.005 if log else 0.005)
  hist.GetXaxis().SetRangeUser(xmin,xmax)
  hist.SetMinimum(zmin)
  hist.SetMaximum(zmax)
  hist.Draw('COLZTEXT%d'%angle)
  
  gStyle.SetPaintTextFormat('.2f')
  hist.SetMarkerColor(kRed)
  hist.SetMarkerSize(1.8 if log else 1)
  #gPad.Update()
  #gPad.RedrawAxis()
  
  latex = TLatex()
  latex.SetTextSize(0.048)
  latex.SetTextAlign(23)
  latex.SetTextFont(42)
  latex.SetNDC(True)
  latex.DrawLatex(0.475,0.99,hist.GetTitle()) # to prevent typesetting issues
  
  canvas.SaveAs(name+'.pdf')
  canvas.SaveAs(name+'.png')
  canvas.Close()
  

def plot1D(hname,histnum2D,histden2D,era,channel,title="",log=False,write=True):
  """Plot efficiency."""
  dir      = ensureDirectory('plots/%d'%era)
  name     = "%s/%s_%s"%(dir,hname,channel)
  if log:
    name  += "_log"
  header   = ""
  xtitle   = 'Jet p_{T} [GeV]'
  ytitle   = 'B tag efficiencies' if '_b_' in hname else 'B mistag rate'
  xmin, xmax = 20 if log else 10, histnum2D.GetXaxis().GetXmax()
  ymin, ymax = 5e-3 if log else 0.0, 2.0
  colors   = [kBlue, kRed, kOrange]
  x1, y1   = (0.27, 0.44) if '_b_' in hname else (0.55, 0.80)
  width, height = 0.3, 0.16
  x2, y2   = x1 + width, y1 - height
  hists    = createEff1D(histnum2D,histden2D)
  
  canvas = TCanvas('canvas','canvas',100,100,800,700)
  canvas.SetFillColor(0)
  canvas.SetBorderMode(0)
  canvas.SetFrameFillStyle(0)
  canvas.SetFrameBorderMode(0)
  canvas.SetTopMargin(  0.04 ); canvas.SetBottomMargin( 0.13 )
  canvas.SetLeftMargin( 0.12 ); canvas.SetRightMargin(  0.05 )
  canvas.SetTickx(0); canvas.SetTicky(0)
  canvas.SetGrid()
  gStyle.SetOptTitle(0)
  if log:
    canvas.SetLogx()
    canvas.SetLogy()
  canvas.cd()
  
  frame = hists[0]
  for i, hist in enumerate(hists):
    hist.SetLineColor(colors[i%len(colors)])
    hist.SetMarkerColor(colors[i%len(colors)])
    hist.SetLineWidth(2)
    hist.SetMarkerSize(2)
    hist.SetMarkerStyle(1)
    hist.Draw('PE0SAME')
  frame.GetXaxis().SetTitle(xtitle)
  frame.GetYaxis().SetTitle(ytitle)
  frame.GetXaxis().SetLabelSize(0.048)
  frame.GetYaxis().SetLabelSize(0.048)
  frame.GetXaxis().SetTitleSize(0.058)
  frame.GetYaxis().SetTitleSize(0.058)
  frame.GetXaxis().SetTitleOffset(1.03)
  frame.GetYaxis().SetTitleOffset(1.04)
  frame.GetXaxis().SetLabelOffset(-0.004 if log else 0.005)
  frame.GetXaxis().SetRangeUser(xmin,xmax)
  frame.SetMinimum(ymin)
  frame.SetMaximum(ymax)
  
  if title:    
    latex = TLatex()
    latex.SetTextSize(0.04)
    latex.SetTextAlign(13)
    latex.SetTextFont(62)
    latex.SetNDC(True)
    latex.DrawLatex(0.15,0.94,title)
  
  legend = TLegend(x1,y1,x2,y2)
  legend.SetTextSize(0.04)
  legend.SetBorderSize(0)
  legend.SetFillStyle(0)
  legend.SetFillColor(0)
  if header:
    legend.SetTextFont(62)
    legend.SetHeader(header)
  legend.SetTextFont(42)
  for hist in hists:
    legend.AddEntry(hist,hist.GetTitle(),'lep')
  legend.Draw()
  
  if write:
    canvas.Write(os.path.basename(name))
  canvas.SaveAs(name+'.pdf')
  canvas.SaveAs(name+'.png')
  canvas.Close()
  

def createEff1D(histnum2D,histden2D):
  """Create 1D histogram of efficiency vs. pT for central and forward eta bins."""
  etabins = {
    "|#eta| < 2.5":       [(0,5)],
    "|#eta| < 1.5":       [(2,3)],
    "1.5 < |#eta| < 2.5": [(1,1),(4,4)],
  }
  hists = [ ]
  for etatitle, bins in etabins.items():
    histnum  = None
    histden  = None
    for bin1, bin2 in bins:
      if histnum==None or histden==None:
        histnum  = histnum2D.ProjectionX("%s_%d"%(histnum2D.GetName(),bin1),bin1,bin2)
        histden  = histden2D.ProjectionX("%s_%d"%(histden2D.GetName(),bin1),bin1,bin2)
      else:
        histnum.Add(histnum2D.ProjectionX("%s_%d"%(histnum2D.GetName(),bin1),bin1,bin2))
        histden.Add(histden2D.ProjectionX("%s_%d"%(histden2D.GetName(),bin1),bin1,bin2))
    histnum.Sumw2()
    histnum.Divide(histden)
    histnum.SetTitle(etatitle)
    hists.append(histnum)
    gDirectory.Delete(histden.GetName())
    #for i in range(0,histnum.GetXaxis().GetNbins()+1):
    #  print i, histnum.GetBinContent(i)
  return hists
  

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
    print ">>>   created directory %s in %s" % (dirname,file.GetName())
  dir.cd()
  return dir
  

def ensureDirectory(dirname):
  """Make directory if it does not exist."""
  if not os.path.exists(dirname):
    os.makedirs(dirname)
    print '>>> made directory "%s"'%(dirname)
    if not os.path.exists(dirname):
      print '>>> failed to make directory "%s"'%(dirname)
  return dirname
  

def main():
  
  indir    = args.indir
  eras     = args.era
  channels = args.channels
  chdir    = args.chdir
  outdir   = 'effs'
  
  for era in eras:
    
    # SAMPLES: list of analysis framework output run on MC samples
    #          that is used to add together and compute the efficiency
    if '2016' in era:
      samples = [
        ( "TT/TT"                    ),
        ( "DY/DYJetsToLL_M-10to50"   ),
        ( "DY/DYJetsToLL_M-50_reg"   ),
        ( "DY/DY1JetsToLL_M-50"      ),
        ( "DY/DY2JetsToLL_M-50"      ),
        ( "DY/DY3JetsToLL_M-50"      ),
        ( "WJ/WJetsToLNu"            ),
        ( "WJ/W1JetsToLNu"           ),
        ( "WJ/W2JetsToLNu"           ),
        ( "WJ/W3JetsToLNu"           ),
        ( "WJ/W4JetsToLNu"           ),
        ( "ST/ST_tW_top"             ),
        ( "ST/ST_tW_antitop"         ),
        ( "ST/ST_t-channel_top"      ),
        ( "ST/ST_t-channel_antitop"  ),
        #( "ST/ST_s-channel"          ),
        ( "VV/WW"                    ),
        ( "VV/WZ"                    ),
        ( "VV/ZZ"                    ),
      ]
    elif '2017' in era:
      samples = [ 
        ( "TT/TTTo2L2Nu"             ),
        ( "TT/TTToHadronic"          ),
        ( "TT/TTToSemiLeptonic"      ),
        ( "DY/DYJetsToLL_M-10to50"   ),
        ( "DY/DYJetsToLL_M-50"       ),
        ( "DY/DY1JetsToLL_M-50"      ),
        ( "DY/DY2JetsToLL_M-50"      ),
        ( "DY/DY3JetsToLL_M-50"      ),
        ( "DY/DY4JetsToLL_M-50"      ),
        ( "WJ/WJetsToLNu"            ),
        ( "WJ/W1JetsToLNu"           ),
        ( "WJ/W2JetsToLNu"           ),
        ( "WJ/W3JetsToLNu"           ),
        ( "WJ/W4JetsToLNu"           ),
        ( "ST/ST_tW_top"             ),
        ( "ST/ST_tW_antitop"         ),
        ( "ST/ST_t-channel_top"      ),
        ( "ST/ST_t-channel_antitop"  ),
        #( "ST/ST_s-channel"          ),
        ( "VV/WW"                    ),
        ( "VV/WZ"                    ),
        ( "VV/ZZ"                    ),
      ]
    elif '2018' in era:
      samples = [
        ( "TT/TTTo2L2Nu"             ),
        ( "TT/TTToHadronic"          ),
        ( "TT/TTToSemiLeptonic"      ),
        ( "DY/DYJetsToLL_M-10to50"   ),
        ( "DY/DYJetsToLL_M-50"       ),
        ( "DY/DY1JetsToLL_M-50"      ),
        ( "DY/DY2JetsToLL_M-50"      ),
        ( "DY/DY3JetsToLL_M-50"      ),
        ( "DY/DY4JetsToLL_M-50"      ),
        #( "WJ/WJetsToLNu"            ),
        ( "WJ/W1JetsToLNu"           ),
        ( "WJ/W2JetsToLNu"           ),
        ( "WJ/W3JetsToLNu"           ),
        ( "WJ/W4JetsToLNu"           ),
        ( "ST/ST_tW_top"             ),
        ( "ST/ST_tW_antitop"         ),
        ( "ST/ST_t-channel_top"      ),
        ( "ST/ST_t-channel_antitop"  ),
        #( "ST/ST_s-channel"          ),
        ( "VV/WW"                    ),
        ( "VV/WZ"                    ),
        ( "VV/ZZ"                    ),
      ]
    else:
      print "Warning! Did not recognize era %r"%(era)
      continue
    
    # MC CAMPAIGN NAMES of each era 
    campaigns = { 
       '2016': "2016Legacy",  'UL2016_preVFP': "Summer20UL16APV",
                              'UL2016_postVFP': "Summer20UL16",
       '2017': "12Apr2017",   'UL2017': "Summer20UL17",
       '2018': "Autumn18",    'UL2018': "Summer20UL18",
    }
    
    # LOOP over channels
    for channel in args.channels:
      
      # SAMPLE FILE NAMES
      samplefiles = ["%s/%s_%s.root"%(indir,s,channel) for s in samples]
      for fname in samplefiles[:]:
        if '*' in fname:
          fnames = glob.glob(fname)
          index = samplefiles.index(fname)
          samplefiles = samplefiles[:index] + fnames + samplefiles[index+1:]
      
      # COMPUTE and SAVE b tag efficiencies
      for tagger in args.taggers:
        for wp in args.wps:
          campaign = args.campaign or campaigns[era]
          outfname = "%s/%s_%d_%s_eff.root"%(outdir,tagger,era,campaigns[era])
          getBTagEfficiencies(tagger,wp,outfname,samplefiles,era,channel,tag=args.tag,effdir=chdir,plot=args.plot)
  

if __name__ == '__main__':
  print('')
  main()
  print ">>> done\n"
  
