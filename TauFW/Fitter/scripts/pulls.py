#! /usr/bin/env python
import os, re, json
import multiprocessing
import copy
import math
from array import array
import ROOT; ROOT.PyConfig.IgnoreCommandLineOptions = True
from ROOT import ROOT, gROOT, gStyle, gRandom, TSystemDirectory
from ROOT import TFile, TChain, TTree, TCut, TH1F, TH2F, TF1, THStack, TGraph, TGraphAsymmErrors,\
                 TStyle, TCanvas, TPad, TBox, TLegend, TLatex, TText, TLine,\
                 TPaveText, kBlack, kRed, kBlue, kOrange, kGreen
#from utils import *

# Format:
#0 : sys name
#1 : b-only DX
#2 : b-only dDX
#3 : s+b DX
#4 : s+b dDX
#5 : rho

gStyle.SetOptStat(0)
gStyle.SetErrorX(0)
var_dict = { 'geq': "#geq", 'leq': "#leq", 'pfmt_1': "m_{T}", 'm_vis': "m_{vis}", 'm_2': "m_{#tau}", }
cat_dict = { 'DM0': "h^{#pm}", 'DM1': "h^{#pm}#pi^{0}", 'DM10': "h^{#pm}h^{#mp}h^{#pm}", }
paramdict = { }


def pullsDistribution(filename,outname,text="",rhomin=None,verb=0):
    if verb>=1:
      print ">>>> pullsDistribution(%r)"%(filename)
    nbins, xmin, xmax = 35, -3., 4.
    pulllist = filterPullFile(filename,rhomin=rhomin,verb=verb)
    b_pulls = TH1F("b_pulls","",nbins,xmin,xmax)
    s_pulls = TH1F("s_pulls","",nbins,xmin,xmax)
    frame = b_pulls
    
    for i, pull in enumerate(pulllist):
      if verb>=2:
        print pull
      _, pb, _, ps, _, _ = pull
      b_pulls.Fill(pb)
      s_pulls.Fill(ps)
    bmu, bsigma = b_pulls.GetMean(), b_pulls.GetStdDev()
    smu, ssigma = s_pulls.GetMean(), s_pulls.GetStdDev()
    #norm = b_pulls.GetMaximum()
    bwidth = (xmax-xmin)/nbins
    norm = b_pulls.GetEntries()*bwidth/math.sqrt(2*math.pi) # 1/sqrt(2*pi) = 0.3989422804
    if verb>=1:
      print ">>>> pullsDistribution: norm=%.4g, b_pulls.GetEntries()=%d, math.sqrt(2*math.pi)=%.5g, bwidth=%.5g"%(
        norm,b_pulls.GetEntries(),math.sqrt(2*math.pi),bwidth)
    gaus = TF1('g',"gaus",xmin,xmax)
    gaus.SetParameters(norm,0,1)
    
    canvas = TCanvas("canvas", "Pulls", 800, 600)
    #canvas.cd()
    #canvas.SetGrid(0,1)
    canvas.SetMargin(0.09,0.02,0.11,0.02) # LRBT
    canvas.SetTicks(1,1)
    
    b_pulls.SetLineColor(kBlue)
    s_pulls.SetLineColor(kRed)
    b_pulls.SetLineWidth(2)
    s_pulls.SetLineWidth(2)
    s_pulls.SetLineStyle(2)
    gaus.SetLineColor(kBlack)
    #gaus.SetLineWidth(2)
    #gaus.SetLineStyle(2)
    
    ymax = 1.15*max(s_pulls.GetMaximum(),b_pulls.GetMaximum())
    frame.SetMaximum(ymax)
    #b_pulls.GetYaxis().SetRangeUser(0, 2.5)
    frame.GetXaxis().SetTitle("Pull (#hat{#theta} - #theta_{0}) / #Delta#theta")
    frame.GetYaxis().SetTitle("Number of nuisance parameters")
    frame.GetXaxis().SetLabelSize(0.042)
    frame.GetYaxis().SetLabelSize(0.042)
    frame.GetXaxis().SetTitleSize(0.049)
    frame.GetYaxis().SetTitleSize(0.049)
    frame.GetXaxis().SetLabelOffset(0.01)
    frame.GetXaxis().SetTitleOffset(0.95)
    frame.GetYaxis().SetTitleOffset(0.90)
    #frame.GetYaxis().SetNdivisions(nbins, 0, 0)
    
    frame.Draw('')
    gaus.Draw('LSAME')
    b_pulls.Draw('HISTSAME')
    s_pulls.Draw('HISTSAME')
    
    leg = TLegend(0.60,0.77,0.95,0.92)
    leg.SetTextSize(0.044)
    leg.SetBorderSize(0)
    leg.SetFillStyle(0)
    leg.SetFillColor(0)
    leg.SetMargin(0.10)
    leg.AddEntry(b_pulls,"B-only fit: %.2f #pm %.2f"%(bmu,bsigma),'lp')
    leg.AddEntry(s_pulls,"S+B fit: %.2f #pm %.2f"%(smu,ssigma),'lp')
    leg.AddEntry(gaus,"Gausian: 0.0 #pm 1.0",'lp')
    #if text: leg.AddEntry(0, text, "")
    leg.Draw()
    
    latex = None
    if text:
      latex = TLatex()
      latex.SetTextSize(0.044)
      latex.SetTextAlign(13)
      latex.SetTextFont(42)
      latex.SetNDC(True)
      latex.DrawLatex(0.13,0.95,text)
    
    canvas.RedrawAxis()
    canvas.Print(outname+".png")
    canvas.Print(outname+".pdf")
    canvas.Close()
    if not gROOT.IsBatch(): raw_input("Press Enter to continue...")



def pullErrorsDistribution(filename,outname,text="",xmax=1.5,rhomin=None,verb=0):
    if verb>=1:
      print ">>>> pullErrorsDistribution(%r)"%(filename)
    nbins, xmin = 30, 0.
    pulllist = filterPullFile(filename,rhomin=rhomin)
    b_pulls = TH1F("b_pulls","",nbins,xmin,xmax)
    s_pulls = TH1F("s_pulls","",nbins,xmin,xmax)
    frame = b_pulls
    
    for i, pull in enumerate(pulllist):
      name, pb, eb, ps, es, rho = pull
      b_pulls.Fill(eb)
      s_pulls.Fill(es)
      if eb>xmax or es>xmax:
        print "pullErrorsDistribution: WARNING! Overflow (>%s) pull uncertainty for %r with %.3f+-%.3f (B-only), %.3f+-%.3f (S+B), rho=%.3f"%(
          xmax,name,pb,eb,ps,es,rho)
      if eb<0 or es<0:
        print "pullErrorsDistribution: WARNING! Negative pull uncertainty for %r with %.3f+-%.3f (B-only), %.3f+-%.3f (S+B), rho=%.3f"%(
          name,pb,eb,ps,es,rho)
    
    canvas = TCanvas("canvas", "Pulls", 800, 600)
    canvas.SetMargin(0.09,0.02,0.11,0.02) # LRBT
    canvas.SetTicks(1,1)
    
    b_pulls.SetLineColor(kBlue)
    s_pulls.SetLineColor(kRed)
    b_pulls.SetLineWidth(2)
    s_pulls.SetLineWidth(2)
    s_pulls.SetLineStyle(2)
    
    ymax = 1.15*max(s_pulls.GetMaximum(),b_pulls.GetMaximum())
    frame.SetMaximum(ymax)
    frame.GetXaxis().SetTitle("Post-fit uncertainty #Delta#hat{#theta}")
    frame.GetYaxis().SetTitle("Number of nuisance parameters")
    frame.GetXaxis().SetLabelSize(0.042)
    frame.GetYaxis().SetLabelSize(0.042)
    frame.GetXaxis().SetTitleSize(0.049)
    frame.GetYaxis().SetTitleSize(0.049)
    frame.GetXaxis().SetLabelOffset(0.01)
    frame.GetXaxis().SetTitleOffset(0.95)
    frame.GetYaxis().SetTitleOffset(0.90)
    #frame.GetYaxis().SetNdivisions(nbins, 0, 0)
    
    frame.Draw('')
    b_pulls.Draw('HISTSAME')
    s_pulls.Draw('HISTSAME')
    
    leg = TLegend(0.18,0.73,0.45,0.85)
    leg.SetTextSize(0.044)
    leg.SetBorderSize(0)
    leg.SetFillStyle(0)
    leg.SetFillColor(0)
    leg.SetMargin(0.10)
    leg.AddEntry(b_pulls,"B-only fit",'lp')
    leg.AddEntry(s_pulls,"S+B fit",'lp')
    #if text: leg.AddEntry(0, text, "")
    leg.Draw()
    
    latex = None
    if text:
      latex = TLatex()
      latex.SetTextSize(0.044)
      latex.SetTextAlign(13)
      latex.SetTextFont(42)
      latex.SetNDC(True)
      latex.DrawLatex(0.13,0.95,text)
    
    canvas.RedrawAxis()
    canvas.Print(outname+".png")
    canvas.Print(outname+".pdf")
    canvas.Close()
    if not gROOT.IsBatch(): raw_input("Press Enter to continue...")


###def pulls(filename,outname,text=""):
###    
###    pulllist = filterPullFile(filename)
###    nbins, off = len(pulllist), 0.10
###    
###    b_pulls = TH1F("b_pulls", ";;Pulls", nbins, 0.-off, nbins-off)
###    s_pulls = TH1F("s_pulls", ";;Pulls", nbins, 0.+off, nbins+off) #
###
###    for i, pull in enumerate(pulllist):
###        name, pb, eb, ps, es, rho = pull
###        b_pulls.GetXaxis().SetBinLabel(i+1,name)
###        s_pulls.GetXaxis().SetBinLabel(i+1,name)
###        b_pulls.SetBinContent(i+1,pb)
###        b_pulls.SetBinError(i+1,eb)
###        s_pulls.SetBinContent(i+1,ps)
###        s_pulls.SetBinError(i+1,es)
###
###    b_pulls.SetFillStyle(3005)
###    b_pulls.SetFillColor(923)
###    b_pulls.SetLineColor(923)
###    b_pulls.SetLineWidth(2)
###    b_pulls.SetMarkerStyle(20)
###    b_pulls.SetMarkerSize(1.25)
###    
###    s_pulls.SetLineColor(602)
###    s_pulls.SetMarkerColor(602)
###    s_pulls.SetMarkerStyle(24) #24
###    s_pulls.SetLineWidth(2)
###    
###    b_pulls.GetYaxis().SetRangeUser(-2.5, 2.5)
###    
###    canvas = TCanvas("canvas", "Pulls", 1600, 800)
###    canvas.cd()
###    canvas.SetTopMargin(0.06)
###    canvas.SetRightMargin(0.05)
###    canvas.SetBottomMargin(0.15)
###    canvas.SetTicks(1, 1)
###
###    # Draw
###    b_pulls.Draw("PE1")
###    #b_pulls.Draw("B")
###    s_pulls.Draw("SAME, PE1")
###
###    leg = TLegend(0.25, 0.95, 0.75, 0.995)
###    leg.SetBorderSize(0)
###    leg.SetFillStyle(0)
###    leg.SetFillColor(0)
###    leg.SetNColumns(2)
###    leg.AddEntry(b_pulls,  "background-only fit", "flp")
###    leg.AddEntry(s_pulls,  "signal+background fit", 'lp')
###    if text: leg.AddEntry(0, text, "")
###    
###    line = TLine()
###    line.DrawLine(0., 0., nbins, 0.)
###    line.SetLineStyle(7)
###    line.SetLineWidth(2)
###    line.SetLineColor(417)
###    line.DrawLine(0., 1., nbins, 1.)
###    line.DrawLine(0., -1., nbins, -1.)
###    line.SetLineColor(800)
###    line.DrawLine(0., 2., nbins, 2.)
###    line.DrawLine(0., -2., nbins, -2.)
###    
###    leg.Draw()
###    canvas.Print(outname+".png")
###    canvas.Print(outname+".pdf")
###    canvas.Close()
###
###    if not gROOT.IsBatch(): raw_input("Press Enter to continue...")



def pullsVertical(filename,outname,titles=None,text="",**kwargs):
    nmax     = kwargs.get('nmax',      -1     )
    sort     = kwargs.get('sort',      None   )
    rhomin   = kwargs.get('rhomin',    None   )
    showrho  = kwargs.get('showrho',   False  )
    rhotitle = kwargs.get('rhotitle',  "#rho" )
    Bonly    = kwargs.get('Bonly',     True   )
    SplusB   = kwargs.get('SplusB',    True   )
    showr    = kwargs.get('showr',     None   )
    verb     = kwargs.get('verb',      0      )
    rhomin0  = rhomin # original value
    if verb>=1:
      print ">>> pullsVertical(%r,nmax=%d)"%(filename,nmax)
    pulllist = None
    while not pulllist:
      if isinstance(filename,str):
        pulllist = filterPullFile(filename,nmax=nmax,rhomin=rhomin,sort=sort)
      else: # assume filename is actually a list of pulls, [(name,pb,eb,ps,es,rho), ... ]
        pulllist = filename
      npulls, off = len(pulllist), 0.10
      if not pulllist:
        print ">>> pullsVertical: WARNING! Could not find any pulls for %r with nmax=%s, rhomin=%s"%(filename,nmax,rhomin)
      if rhomin!=None:
        if rhomin/rhomin0<0.10:
          return
        rhomin *= 0.5 # try again with smaller rho
        print ">>> pullsVertical: Trying again with rhomin=%s..."%(rhomin)
    if not titles:
      sigstr = "S+B fit"
      if showr:
        rhat, rup, rlow = getSignalStrength(showr)
        sigstr += " (#hat{r} = %.2f^{#lower[0.35]{+%.2f}}_{#lower[-0.25]{-%.2f}})"%(rhat,rup,rlow)
      titles = ["B-only fit",sigstr]
    
    # Graphs
    xmin, xmax = -3, 3.
    h_pulls = TH2F("pulls","",6,xmin,xmax,npulls,0,npulls)
    B_pulls = TGraphAsymmErrors(npulls)
    S_pulls = TGraphAsymmErrors(npulls)
    
    boxes = [ ]
    rhos  = [ ]
    
    width   = 900
    height  = 170+npulls*20
    canvas  = TCanvas("canvas","Pulls",width,height)#npulls*20)
    scale   = 500./min(canvas.GetWh()*canvas.GetHNDC(),canvas.GetWw()*canvas.GetWNDC())
    yscale  = 500./height
    tmarg, bmarg = 0.01*yscale, 0.15*yscale
    lmarg, rmarg = 0.50, (0.06 if showrho else 0.01)
    tsize   = 0.055*scale
    #xlaboff = -3e-6*max(500,height)
    #xlaboff = 4e-3-4.1e-6*max([canvas.GetWh()*canvas.GetHNDC(),canvas.GetWw()*canvas.GetWNDC()]) #*max(500,height)
    #xlaboff = -2e-6*max(1000.,height)
    xlaboff = min(0.0,2.362e-3-5.051e-6*height+3.071e-10*height**2)
    xtitoff = 800./max(1000.,height)
    if verb>=2:
      print ">>> npulls=%s, height=%s, scale=%.4f, yscale=%.3f tmarg=%.5f, bmarg=%.5f, tsize=%.5f"%(npulls,height,scale,yscale,tmarg,bmarg,tsize)
      print ">>> tmarg+bmarg=%.3f, 1-tmarg-bmarg=%.4f"%(tmarg+bmarg,1-tmarg-bmarg)
      print ">>> pad.GetWh()*pad.GetHNDC()=%.3f*%.3f=%.3f"%(canvas.GetWh(),canvas.GetHNDC(),canvas.GetWh()*canvas.GetHNDC())
      print ">>> pad.GetWw()*pad.GetWNDC()=%.3f*%.3f=%.3f"%(canvas.GetWw(),canvas.GetWNDC(),canvas.GetWw()*canvas.GetWNDC())
      print ">>> xlaboff=%.3f, xtitoff=%.3f"%(xlaboff,xtitoff)
    canvas.SetGrid(0,1)
    canvas.SetMargin(lmarg,rmarg,bmarg,tmarg) # LRBT
    canvas.SetTicks(1, 1)
    
    offset = 0.2
    for i, pull in enumerate(pulllist):
      if len(pull)==5:
        name, pb, eb, ps, es = pull
        rho = 0.0
      else:
        name, pb, eb, ps, es, rho = pull
      yval = npulls-i-0.5
      ybin = npulls-i
      h_pulls.GetYaxis().SetBinLabel(ybin,name)
      B_pulls.SetPoint(i,pb,yval+offset)
      B_pulls.SetPointError(i,eb,eb,0.,0.)
      S_pulls.SetPoint(i,ps,yval-offset)
      S_pulls.SetPointError(i,es,es,0.,0.)
      if showrho:
        rhos.append(rho)
    
    h_pulls.GetXaxis().SetTitle("(#hat{#theta} - #theta_{0}) / #Delta#theta")
    h_pulls.GetXaxis().SetLabelOffset(xlaboff)
    h_pulls.GetXaxis().SetTitleOffset(xtitoff)
    h_pulls.GetXaxis().SetLabelSize(0.8*tsize)
    h_pulls.GetYaxis().SetLabelSize(1.1*tsize)
    h_pulls.GetXaxis().SetTitleSize(tsize)
    #h_pulls.GetYaxis().SetTitleSize(tsize)
    h_pulls.GetYaxis().SetNdivisions(npulls,0,0)
    
    B_pulls.SetFillColor(1)
    B_pulls.SetLineColor(1)
    B_pulls.SetLineStyle(1)
    B_pulls.SetLineWidth(2)
    B_pulls.SetMarkerColor(1)
    B_pulls.SetMarkerStyle(20)
    B_pulls.SetMarkerSize(1)#(0.75)
    
    S_pulls.SetFillColor(629)
    S_pulls.SetLineColor(629)
    S_pulls.SetMarkerColor(629)
    S_pulls.SetLineWidth(2)
    S_pulls.SetMarkerStyle(20)
    S_pulls.SetMarkerSize(1)
    
    box1 = TBox(-1.,0.,1.,npulls)
    #box1.SetFillStyle(3001) # 3001 checkered
    #box1.SetFillStyle(0)
    box1.SetFillColor(kGreen+1) # 417
    box1.SetLineWidth(2)
    box1.SetLineStyle(2)
    box1.SetLineColor(kGreen+1) # 417
    
    box2 = TBox(-2.,0.,2.,npulls)
    #box2.SetFillStyle(3001) # 3001 checkered
    #box2.SetFillStyle(0)
    box2.SetFillColor(kOrange) # 800
    box2.SetLineWidth(2)
    box2.SetLineStyle(2)
    box2.SetLineColor(kOrange) # 800
    
    x1 = 0.10 if showr else 0.16
    x2 = 0.35
    y1 = 0.000003/yscale #(1-tmarg-bmarg)*height
    y2 = y1+0.8*bmarg
    if verb>=1:
      print ">>> y1=%.5f, y2=%.5f"%(y1,y2)
    leg = TLegend(x1,y1,x2,y2)
    leg.SetBorderSize(0)
    leg.SetFillStyle(0)
    leg.SetFillColor(0)
    leg.SetNColumns(2)
    leg.SetTextSize(0.9*tsize)
    leg.SetTextFont(42)
    leg.AddEntry(B_pulls,titles[0],'lp')
    leg.AddEntry(S_pulls,titles[1],'lp')
    if text:
      leg.AddEntry(0,text,"")
    
    h_pulls.Draw('')
    box2.Draw()
    box1.Draw()
    B_pulls.Draw('P6SAME')
    S_pulls.Draw('P6SAME')
    leg.Draw()
    
    latex = None
    if showrho:
      latex = TLatex()
      latex.SetTextSize(0.5*tsize)
      latex.SetTextAlign(32)
      latex.SetTextFont(42)
      latex.SetNDC(False)
      x = xmin+(xmax-xmin)*(1-lmarg)/(1.01-lmarg-rmarg)
      gradient = [(-0.30,kRed),(-0.20,kRed+2),(-0.10,kRed+4),(0.15,kBlack),
                  (0.10,kBlue+4),(0.20,kBlue+2),(1e10,kBlue)] # gradient
      for i, rho in enumerate(rhos):
        for rmin, color in gradient:
          if rho<rmin:
            tcolor = color; break
        else:
          tcolor = kBlue
        latex.SetTextColor(tcolor) # highlight large values
        y = npulls-i-0.5
        latex.DrawLatex(x,y,"%+.2f"%(rho))
      latex.SetTextColor(kBlack)
      latex.DrawLatex(x,-0.3,rhotitle)
      #if rhomin>0:
      #  latex.DrawLatex(x+0.08,-0.5,"|#rho|>%d%%"%(100.0*rhomin))
        
    
    canvas.RedrawAxis()
    canvas.Print(outname+".png")
    canvas.Print(outname+".pdf")
    #canvas.Print(outname+".root")
    canvas.Close()

    if not gROOT.IsBatch(): raw_input("Press Enter to continue...")
  

def comparePulls(filenames,outname,titles=None,text="",nmax=-1,rhomin=None,deltamin=None,showdelta=False,sort=None,verb=0):
    if verb>=1:
      print ">>> comparePulls(%r,nmax=%d)"%(filenames,nmax)
    #assert len(filenames)>=2, "Can compare only two files!"
    pulldict  = { }
    pullnames = [ ] # common pull names
    pulllist  = [ ]
    titles    = [ ]
    npulls    = [ ]
    ipull     = 2 # 0: B-only, 2: S+B
    for i, filename in enumerate(filenames):
      if '=' in filename:
        parts = filename.split('=')
        title, filename = parts[0], '='.join(parts[1:])
      else:
        title = "File %d"%(i)
      titles.append(title)
      sublist = filterPullFile(filename,sort=sort)
      npulls.append(len(sublist))
      for pull in sublist:
        pullname = pull[0]
        if i==0 and pullname not in pullnames:
          pullnames.append(pullname)
          pulldict[pullname] = [pull[1:]]
        elif pullname in pullnames:
          pulldict[pullname].append(pull[1:])
    for pullname in pullnames: # find common pull names
       if len(pulldict[pullname])!=len(filenames): continue
       pull1 = pulldict[pullname][0]
       pull2 = pulldict[pullname][1]
       if pull1[ipull]==pull2[ipull]:
         diff = 0.0
       else:
         #denom = abs(max([1e-6,pull1[ipull],pull2[ipull]]))
         diff = (pull2[ipull]-pull1[ipull]) #/denom # relative difference
       if verb>=2:
         print ">>>   common pull name: %r (Delta=%.2f%%)"%(pullname,100.0*diff)
       if rhomin and abs(pull1[-1])<rhomin and abs(pull2[-1])<rhomin: continue
       if deltamin and abs(diff)<deltamin: continue
       pulllist.append((pullname,pull1[ipull],pull1[ipull+1],pull2[ipull],pull2[ipull+1],diff))
    if verb>=1:
      print ">>>   compare %s: %s/%s vs. %s/%s"%(filenames,len(pulllist),npulls[0],len(pulllist),npulls[1])
    if verb>=3:
      print ">>>   %s"%(pulllist)
    if sort and sort.lower()=='rho': # sort by correlation factor rho
      pulllist.sort(key=lambda x: x[-1])
    pullsVertical(pulllist,outname,titles=titles,text=text,showrho=showdelta,rhotitle="#Delta",verb=verb)
    

def translate(x):
  return paramdict.get(x,x) if paramdict else x
  

def parsePull(line):
  parts = line.split()
  try:
    pull = translate(parts[0])
    p_b, e_b = float(parts[1]), float(parts[2])
    p_s, e_s = (float(parts[3]), float(parts[4])) if len(parts)>=4 else (0.0,0.0)
    rho = float(parts[5]) if len(parts)>=6 else 0
  except Exception as err:
    print "ERROR! parsePull: Could not convert pull %r -> %r -> name, S+B, B-only, rho"%(pull,parts)
    raise err
  return pull, p_b, e_b, p_s, e_s, rho
  

def filterPullFile(fname,nmax=-1,rhomin=None,sort=None,verb=0):
  """Filter and parse pulls from txt file created by FitDiagnostics and
  $CMSSW_BASE/src/HiggsAnalysis/CombinedLimit/test/diffNuisances.py"""
  with open(fname) as file:
    content = file.readlines()
  pulls = [ ]
  for line in content:
    if not any(c.isdigit() for c in line):
      continue #'bin_' not in x and 'prop_bin' not in x and
    if '!' in line:
      continue #'bin_' not in x and 'prop_bin' not in x and
    line = line.replace('*','')
    pull = parsePull(line) 
    if rhomin!=None and abs(pull[-1])<rhomin:
      continue
    pulls.append(pull)
  if nmax>0:
    pulls = pulls[:nmax]
  if sort and sort.lower()=='rho': # sort by correlation factor rho
    pulls.sort(key=lambda x: x[-1])
  else: # sort by pull name
    pulls.sort()
  return pulls
  

def getSignalStrength(fname,**kwargs):
  """Get signal strength r from fitDiagnostics file."""
  tname = kwargs.get('tree', "fit_s" ) #"tree_fit_sb"
  file  = TFile.Open(fname,'READ')
  if not file or file.IsZombie():
    print '>>> getSignalStrength: did not find file "%s"'%(fname)
  #tree     = file.Get(treename)
  #if not tree:
  #  print warning('getSignalStrength: did not find tree "%s" in file "%s"'%(tname,fname),pre="   ")
  #tree.GetEntry(0)
  #signalr   = tree.r
  #signalr = (tree.r,tree.rHiErr,tree.rLoErr)
  fit_s = file.Get(tname)
  param = fit_s.floatParsFinal().find('r')
  signalr = (param.getVal(),param.getAsymErrorHi(),abs(param.getAsymErrorLo()))
  file.Close()
  return signalr
  

def formatParameter(param):
  """Helpfunction to format nuisance parameter."""
  string = param.replace("CMS_","").replace("ttbar_","").replace("ztt_","").replace("_13TeV","")
  if "DM" in string:
    string = re.sub(r"mt_DM\d+_","",string)
  return string
  

def makeLatex(string):
  for var in var_dict:
    string = string.replace(var,var_dict[var])
  for wp,Wp in [("vvlo","VVLo"),("vlo","VLo"),("lo","Lo"),("me","Me"),
                ("vvti","VVTi"),("vti","VTi"),("ti","Ti")]:
    if wp in string:
      string = string.replace(wp,Wp)
  #if '_' in string:
  #  string = re.sub(r"\b([^_]*)_([^_]*)\b",r"\1_{\2}",string,flags=re.IGNORECASE)
  return string
  

def main(args):
  filename  = args.filename
  compare   = args.compare  # list of files to compare
  outname   = args.outname
  text      = makeLatex(args.text)
  dictfname = args.translate
  distr     = args.distr
  rhomin    = args.rhomin
  deltamin  = args.deltamin
  showrho   = args.showrho
  showr     = args.showr
  batch     = args.batch
  verbosity = args.verbosity
  sort      = 'rho' if args.sortrho else None
  if args.batch:
    gROOT.SetBatch(True)
  if dictfname:
    global paramdict
    with open(dictfname,'r') as dfile:
      paramdict = json.load(dfile)
  if distr:
    pullsDistribution(filename,outname,text=text,rhomin=rhomin,verb=verbosity)
    pullErrorsDistribution(filename,outname+"_err",text=text,rhomin=rhomin,verb=verbosity)
  elif compare:
    comparePulls(compare,outname,text=text,rhomin=rhomin,deltamin=deltamin,showdelta=showrho,sort=sort,verb=verbosity)
  else:
    #pullsVertical_noBonly(fileName)
    pullsVertical(filename,outname,text=text,rhomin=rhomin,showrho=showrho,showr=showr,sort=sort,verb=verbosity)
  

if __name__ == "__main__":
  from argparse import ArgumentParser
  parser = ArgumentParser(prog="pulls",description="Plotting script for pulls",epilog="Good luck!")
  parser.add_argument('-b', "--batch",     action="store_true"       )
  parser.add_argument('-c', "--compare",   nargs=2, default=None,
                                           help="compare two files"  )
  parser.add_argument('-f', "--filename",  default=None              )
  parser.add_argument('-o', "--outname",   default="pulls"           )
  parser.add_argument('-T', "--translate", default=None              )
  parser.add_argument('-t', "--text",      default=""                )
  parser.add_argument('-d', "--distr",     action="store_true"       )
  parser.add_argument('-r', "--rhomin",    type=float, default=None,
                                           help="minimum rho"        )
  parser.add_argument('-D', "--deltamin",  type=float, default=None,
                                           help="minimum difference" )
  parser.add_argument(      "--showr",     default=None,
                                           help="show signal strength r from given FitDiagnostics file" )
  parser.add_argument(      "--showrho",   action="store_true",
                                           help="show rho in margin" )
  parser.add_argument(      "--sortrho",   action="store_true",
                                           help="sort by rho"        )
  parser.add_argument('-v', "--verbose",   dest='verbosity', type=int, nargs='?', const=1, default=0,
                                           help="set verbosity"      )
  args = parser.parse_args()
  main(args)
  
