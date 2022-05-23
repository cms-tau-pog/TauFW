#! /usr/bin/env python
# Author: Izaak Neutelings (January 2019)
import os, sys, re
import json
import array
from math import ceil
from argparse import ArgumentParser
import ROOT; ROOT.PyConfig.IgnoreCommandLineOptions = True
from ROOT import gROOT, gStyle, gPad, TFile, TChain, TCanvas, TH1F, TGraph, TGraphErrors, TLegend, TLatex, TLine,\
                 kBlack, kBlue, kRed, kGreen, kGray, kOrange
gROOT.SetBatch(True)
gStyle.SetOptTitle(False)
gStyle.SetEndErrorSize(4)
gStyle.SetErrorX(0)

argv = sys.argv
description = '''Plots bias tests and comparisons.'''
parser = ArgumentParser(prog="plotBias",description=description,epilog="Good luck!")
parser.add_argument("filenames",          type=str, nargs='+',
                                          help="file from fitDiagnostics" ),
parser.add_argument('-r', "--rinj",       dest="rinj", type=float, default=0,
                                          help="injected signal strength" )
parser.add_argument('-R', "--rtitle",     dest="rtitle",
                                          help="title for injected signal strength" )
parser.add_argument('-t', "--text",       dest="text", type=str, default="",
                                          help="extra text" )
parser.add_argument('-m', "--nmax",       type=long, default=-1,
                                          help="maximum number of toys to process" )
parser.add_argument('-o', "--outfile",    dest="outfile", type=str, default="biastest",
                    metavar="FILENAME",   help="name of output figure" )
parser.add_argument('-S', "--skipchecks", action='store_true',
                                          help="skip checking errors" )
parser.add_argument('-v', "--verbose",    dest="verbose", action='store_true',
                                          help="set verbose" )
args = parser.parse_args()


def warning(string,**kwargs):
  return ">>> \033[1m\033[93m%sWarning!\033[0m\033[93m %s\033[0m"%(kwargs.get('pre',""),string)
  
def lowerstr(string):
  """Help function to add #lower to ROOT string."""
  string = re.sub(r"_(\{[^#}]+\})",r"_{#lower[-0.1]\1}",string)
  string = re.sub(r"\^(\{[^#}]+\})",r"^{#lower[0.25]\1}",string)
  return string

def columnize(oldlist,ncol=2):
  """Transpose lists into n columns, useful for TLegend,
  e.g. [1,2,3,4,5,6,7] -> [1,5,2,6,3,7,4] for ncol=2."""
  if ncol<2:
    return oldlist
  parts   = partition(oldlist,ncol)
  collist = [ ]
  row     = 0
  assert len(parts)>0, "len(parts)==0"
  while len(collist)<len(oldlist):
    for part in parts:
      if row<len(part):
        collist.append(part[row])
    row += 1
  return collist
  

def partition(list,nparts):
  """Partion list into n chunks, as evenly sized as possible."""
  nleft    = len(list)
  divider  = float(nparts)
  parts    = [ ]
  findex   = 0
  for i in range(0,nparts): # partition recursively
    nnew   = int(ceil(nleft/divider))
    lindex = findex + nnew
    parts.append(list[findex:lindex])
    nleft   -= nnew
    divider -= 1
    findex   = lindex
    #print nnew
  return parts
  

def checkErrors(tree,nmax=-1):
  """Help function to check for asymmetric errors, and detect possible 'Error: closed range without finding crossing'."""
  nmax = long(nmax if nmax>0 else 1e15)
  varexps = [
    ('low',  "rLoErr/rErr"),
    ('up',   "rHiErr/rErr"),
    ('asym', "abs(rLoErr-rHiErr)/min(rLoErr,rHiErr)"),
    #('low',  "abs(rLoErr-r)"),
    #('low',  "abs(rHiErr-r)"),
  ]
  marks = [ 2, 10, 100, 1000 ]
  cutexp = "fit_status==0 && rErr>0" #|| fit_status==300"
  for name, varexp in varexps:
    nevts = tree.Draw(varexp,cutexp,'gOff',nmax)
    if nevts<=0:
      print warning("Out of %d events none found with %r"%(tree.GetEntries(),cutexp))
    vector = tree.GetV1()
    #result = sorted([float(vector[i]) for i in xrange(nevts)])
    #results.append((name,result))
    #print result
    counts = { m: 0 for m in marks }
    for i in xrange(nevts):
      x = float(vector[i])
      for mark in reversed(marks):
        if x>mark:
          counts[mark] += 1
          break
    for mark in marks:
      if counts[mark]>0:
        frac = 100.0*counts[mark]/nevts
        print warning("Found %s > %2s: %4s/%3s (%.1f%%)"%(varexp,mark,counts[mark],nevts,frac))
    

def drawBiasTest(filenames,outfilename,rinj=0,text=None,rtitle=None,nmax=-1,
                 skipchecks=False,write=False,verbose=False):
  """Draw bias test."""
  print '>>> drawBiasTest(%r,%r,rinj=%s)'%(filenames[0],outfilename,rinj)
  gStyle.SetOptStat(1111)
  gStyle.SetOptFit(1111)
  
  # SETTINGS
  tname  = 'tree_fit_sb'
  hname  = 'Toys'
  rtitle = str(rinj) if rtitle==None else rtitle.replace("rexp","r_{95%}^{exp}") #lowerstr ##lower[0.7]{exp}
  htitle = "#mu_{#lower[-0.3]{inj.}} = %s"%rtitle
  title  = "#mu_{#lower[-0.3]{inj.}} = %s"%rtitle
  ytitle = "Toys"
  xtitle = "(#mu_{#lower[-0.3]{meas.}} - #mu_{#lower[-0.3]{inj.}}) / #sigma_{#lower[-0.1]{#mu}}}"
  varexp = "(r-%s)/rErr >> %s"%(rinj,hname)
  cutexp = "fit_status==0 || fit_status==300" #fit_status==0" # http://cms-analysis.github.io/HiggsAnalysis-CombinedLimit/part3/nonstandard/?#fitting-diagnostics
  nmax   = long(nmax if nmax>0 else 1e15)
  xmin   = -4
  xmax   = 5
  nbins  = 30
  tsize  = 0.050
  lmargin, rmargin = 0.10, 0.03
  bmargin, tmargin = 0.12, 0.03
  
  # HIST
  file = None
  if len(filenames)==1:
    print ">>> Creating TFile for %r..."%(filenames[0])
    file     = TFile(filenames[0],'READ')
    tree     = file.Get(tname)
  else:
    print ">>> Creating TChain with %d files..."%(len(filenames))
    tree     = TChain(tname)
    for filename in filenames:
      tree.Add(filename)
  hist     = TH1F(hname,htitle,nbins,xmin,xmax)
  #hist.SetDirectory(0)
  print ">>> Draw bias..."
  tree.Draw(varexp,cutexp,'gOff',nmax)
  print ">>> Fitting Gaussian..."
  hist.Fit('gaus',"0")
  func = hist.GetFunction('gaus')
  if not skipchecks:
    print ">>> Checking errors..."
    checkErrors(tree,nmax)
    print ">>> Checking number of entries with fit_status==300..."
    nevts    = tree.GetEntries()
    nevts300 = tree.GetEntries("fit_status==300")
    if nevts300>0:
      print warning("Found %d/%d (%.1f%%) events with 'fit_status==300'"%(nevts300,nevts,100.0*nevts300/nevts))
  
  # WRITE to JSON
  bias  = func.GetParameter(1)
  sigma = func.GetParameter(2)
  berr  = func.GetParError(1) # statistical error in bias
  if write:
    print ">>> Writing to JSON..."
    try:
      with open('bias.json','r') as jsonfile:
        data = json.load(jsonfile)
    except:
      data = { }
    with open('bias.json','w') as jsonfile:
      data[outfilename] = (round(100000*bias)/100000.,round(100000*berr)/100000.,round(100000*sigma)/100000.,hist.GetEntries())
      json.dump(data,jsonfile,sort_keys=True,indent=2)
  
  # DRAW
  print ">>> Drawing bias test..."
  ymin, ymax = 0., 1.55*hist.GetMaximum()
  canvas = TCanvas('canvas','canvas',100,100,900,800)
  canvas.SetMargin(lmargin,rmargin,bmargin,tmargin) # LRBT
  #frame = canvas.DrawFrame(xmin,ymin,xmax,ymax)
  frame = hist
  frame.GetXaxis().SetTitle(xtitle)
  frame.GetYaxis().SetTitle(ytitle)
  frame.GetXaxis().SetTitleSize(tsize)
  frame.GetYaxis().SetTitleSize(tsize)
  frame.GetXaxis().SetLabelSize(0.9*tsize)
  frame.GetYaxis().SetLabelSize(0.9*tsize)
  frame.GetXaxis().SetTitleOffset(1.04)
  hist.SetMaximum(ymax)
  hist.SetLineColor(kBlue+1)
  hist.SetLineWidth(2)
  hist.SetMarkerSize(0.8)
  hist.SetMarkerColor(kBlack)
  hist.SetMarkerStyle(8)
  func.SetLineColor(kRed)
  func.SetLineWidth(2)
  hist.Draw('E1 SAMES')
  func.Draw('SAME')
  
  # TEXT
  x = lmargin + (1-lmargin-rmargin)*0.05
  y = bmargin + (1-tmargin-bmargin)*0.97
  latex = TLatex()
  latex.SetTextSize(0.95*tsize)
  latex.SetTextAlign(13)
  latex.SetTextFont(62)
  latex.SetNDC(True)
  latex.DrawLatex(x,y,title)
  if text:
    for i, line in enumerate(text.replace('\\n','\n').split('\n'),1):
      #print i, line
      latex.SetTextFont(42)
      latex.DrawLatex(x,y-(1.3+1.2*i)*tsize,line)
  
  # SAVE
  canvas.SaveAs(outfilename+".png")
  canvas.SaveAs(outfilename+".pdf")
  canvas.Close()
  if file:
    file.Close()
  

def plotBiasSummary(jsonname,signal,masses,labels,keyexp,rinj,header=None):
  """Plot summary of bias test."""
  gStyle.SetOptStat(False)
  gStyle.SetOptFit(False)
  
  #regexp = re.compile(r"(merge\d+).*([SV]LQ).*M(\d+).*S(\d?)R")
  biasset = { }
  with open(jsonname,'r') as jsonfile:
    data = json.load(jsonfile)
  for label, _ in labels:
    biasset.setdefault(label,[ ])
    for mass in masses:
      key  = keyexp.replace("$SIGNAL",signal).replace("$LABEL",label).replace("$MASS",str(mass)).replace("$EXPSIG",str(rinj))
      print ">>> Fetching key %r..."%(key) #data[key]
      biasset[label].append((data[key][0],data[key][1]))
    #print ">>>   bias: %s"%(biasset[label])
  
  lcolors = [ kBlack, kRed, kBlue, kGreen+1, kOrange+1 ]
  xwidth  = min(0.5,0.07*len(labels)) # total width of all points combined
  #biasset = biassets[signal]
  print ">>> Signal %r"%(signal)
  graphs = [ ]
  for il, (label,title) in enumerate(labels,0):
    print ">>>   label %r"%(label)
    color = lcolors[il%len(lcolors)]
    graph = TGraphErrors()
    graph.SetTitle(title)
    graph.SetMarkerColor(color)
    graph.SetLineColor(color)
    graphs.append(graph)
    for im, (bias, sigma) in enumerate(biasset[label]):
      x = 0.5+im + (xwidth*(il-(len(labels)-1)/2.)/(len(labels)-1))
      print ">>>    x = %4.1f, bias = %.2f +- %.2f"%(x,bias,sigma)
      graph.SetPoint(im,x,bias)
      graph.SetPointError(im,0,sigma)
  
  title   = "#mu_{inj.} = %s"%rinj
  text    = 'Vector LQ' if 'VLQ' in signal else 'Scalar LQ' if 'SLQ' in signal else None
  nbins   = len(masses)
  pname   = ("bias_summary_%s_S%dR"%(signal,rinj)).replace('S1R','SR')
  ###ymin, ymax = -1.35, 1.97 # +- 1.0
  ymin, ymax = -0.60, 0.35 # +- 0.5
  lmargin, rmargin = 0.128, 0.02
  bmargin, tmargin = 0.150, 0.02
  tsize  = 0.045
  x1, y1 = 0.96-rmargin, 0.98-tmargin
  canvas  = TCanvas('canvas','canvas',100,100,800,600)
  canvas.SetMargin(lmargin,rmargin,bmargin,tmargin) # LRBT
  canvas.SetGrid(1,1)
  canvas.SetTicks(1,1)
  #canvas.SetGridx(1)
  gStyle.SetGridStyle(0)
  ###frame  = canvas.DrawFrame(0.5,-2,nbins+0.5,+2)
  frame  = TH1F('frame','frame',3,0,3)
  frame.GetYaxis().SetRangeUser(ymin,ymax)
  ###frame.SetMinimum(-2); frame.SetMaximum(2)
  frame.Draw('AXIS')
  
  # MAKE AXIS
  frame.GetXaxis().SetTitleSize(0.07)
  frame.GetYaxis().SetTitleSize(0.07)
  frame.GetXaxis().SetLabelSize(0.08)
  frame.GetYaxis().SetLabelSize(0.05)
  frame.GetYaxis().SetTitleOffset(0.88)
  frame.GetYaxis().SetLabelOffset(0.01)
  #frame.GetYaxis().CenterTitle(False)
  frame.GetXaxis().SetTitle("m_{LQ} [GeV]")
  frame.GetYaxis().SetTitle("Fitted bias #pm #sigma_{bias}")
  frame.GetXaxis().SetNdivisions(304)
  frame.GetYaxis().SetNdivisions(508)
  for i, mass in enumerate(masses):
    index = frame.GetXaxis().FindBin(i)
    frame.GetXaxis().SetBinLabel(index,str(mass))
  ###frame.GetXaxis().ChangeLabel(2,-1,-1,-1,-1,-1,"600")
  ###frame.GetXaxis().ChangeLabel(-2,-1,-1,-1,-1,-1,"1300")
  ###frame.GetXaxis().LabelsOption("h")
  canvas.Modified()
  canvas.Update()
  
  # TLINE
  lines  = [ ]
  ylines = [-0.4,-0.2,0] #[-1,0,1]
  for y in ylines:
    line = TLine(0,y,3,y)
    line.SetLineStyle(2 if y==0 else 3)
    line.SetLineColor(kGray+(3 if y==0 else 1))
    line.Draw()
    lines.append(line)
  
  # LEGEND
  nlines = len(graphs)+(1 if header else 0)
  lsplit = nlines>=4 #and False
  nrows  = (1 if header else 0) + ceil(nlines/2.) if lsplit else nlines
  width  = (0.40 if lsplit else 0.27)
  height = 1.20*tsize*nrows
  margin = (0.10 if lsplit else 0.05)/width
  legend = TLegend(x1,y1,x1-width,y1-height)
  legend.SetMargin(margin)
  legend.SetFillStyle(0)
  legend.SetBorderSize(0)
  legend.SetTextSize(tsize)
  if header:
    legend.SetTextFont(62)
    legend.SetHeader(header)
  legend.SetTextFont(42)
  if lsplit:
    legend.SetNColumns(2)
    legend.SetColumnSeparation(0.02)
  legend.Draw()
  
  # TEXT
  x = lmargin + (1-lmargin-rmargin)*0.06
  y = bmargin + (1-tmargin-bmargin)*0.96
  latex = TLatex()
  latex.SetTextSize(1.1*tsize)
  latex.SetTextAlign(13)
  latex.SetTextFont(62)
  latex.SetNDC(True)
  latex.DrawLatex(x,y,title)
  if text:
    latex.SetTextFont(42)
    latex.DrawLatex(x,y-2*tsize,text)
  
  # DRAW
  for graph in graphs:
    graph.SetMarkerStyle(8)
    graph.SetMarkerSize(1.2)
    graph.SetLineWidth(2)
    graph.Draw("PLSAME")
  for graph in columnize(graphs,2):
    legend.AddEntry(graph,graph.GetTitle(),'LEP')
  #frame.Draw('SAMEAXIS')
  legend.Draw()
  
  # SAVE & CLOSE
  canvas.SaveAs(pname+'.png')
  canvas.SaveAs(pname+'.pdf')
  canvas.Close()
  gROOT.Delete(frame.GetName())
  


def main():
    
    # PLOT BIAS TEST
    filenames   = args.filenames
    outfilename = args.outfile
    nmax        = args.nmax
    rinj        = args.rinj
    rtitle      = args.rtitle or str(args.rinj)
    text        = args.text.replace("GeV, #","GeV,\n#")
    skipchecks  = args.skipchecks
    verbose     = args.verbose
    
    if filenames[0].endswith('.json'):
      # PLOT BIAS SUMMARY
      jsonname = 'bias/bias.json'
      signals = ['SLQ','VLQ']
      expsigs = [0,1,2,3,]
      masses  = { 'SLQ': [600,1000,1400], 'VLQ': [500,1100,1400], }
      header  = "Bin merge threshold" # (max. unc.)
      for signal in signals:
        for rinj in expsigs:
          key    = "../plots/biastest_combined_Run2_$LABEL_$SIGNAL_noBBBToys-M$MASS-S$EXPSIGR"
          thres  = [10,15,20,25,30] # [10,15,20,25] if rinj<=1 else [10,15,20,25,30]
          labels = [("merge%s"%x, "%d%%"%x) for x in thres]
          if rinj==1:
            key = key.replace('$EXPSIG','')
          plotBiasSummary(jsonname,signal,masses[signal],labels,key,rinj,header=header)
    else:
      drawBiasTest(filenames,outfilename,rinj,text,rtitle=rtitle,nmax=nmax,skipchecks=skipchecks,write=True,verbose=verbose)
    


if __name__ == '__main__':
    main()
    

