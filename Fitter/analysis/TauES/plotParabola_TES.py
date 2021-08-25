#! /usr/bin/env python
# Author: Izaak Neutelings (January 2018)

import os, sys, re, glob, time
import numpy, copy
from array import array
from argparse import ArgumentParser
import ROOT; ROOT.PyConfig.IgnoreCommandLineOptions = True
from ROOT import gROOT, gPad, gStyle, Double, TFile, TCanvas, TLegend, TLatex, TF1, TGraph, TGraph2D, TPolyMarker3D, TGraphAsymmErrors, TLine,\
                 kBlack, kBlue, kRed, kGreen, kYellow, kOrange, kMagenta, kTeal, kAzure, TMath
import PlotTools.CMS_lumi as CMS_lumi, PlotTools.tdrstyle as tdrstyle
from itertools import combinations
from math import sqrt, log, ceil, floor

gROOT.SetBatch(True)
#gROOT.SetBatch(False)
gStyle.SetOptTitle(0)

# CMS style
CMS_lumi.cmsText      = "CMS"
CMS_lumi.extraText    = "Preliminary"
CMS_lumi.cmsTextSize  = 0.85
CMS_lumi.lumiTextSize = 0.80
CMS_lumi.relPosX      = 0.13
CMS_lumi.outOfFrame   = True
tdrstyle.setTDRStyle()

DM_label    = { 'DM0':      "h^{#pm} decay mode",
                'DM1':      "h^{#pm}#pi^{0} decay mode",
                'DM10':     "h^{#pm}h^{#mp}h^{#pm} decay mode",
                'DM11':     "h^{#pm}h^{#mp}h^{#pm}#pi^{0} decay mode",
                'all':      "all old decay modes",
                'combined': "combined", }
bin_dict    = { 1: 'DM0', 2: 'DM1', 3: 'DM10', 4: 'all', }
varlabel    = { 'm_2':   "m_{#tau}",
                'm_vis': "m_{vis}",
                'DM0':   "h^{#pm}",
                'DM1':   "h^{#pm}#pi^{0}",
                'DM10':  "h^{#pm}h^{#mp}h^{#pm}",
                'DM11':  "h^{#pm}h^{#mp}h^{#pm}#pi^{0}", }
vartitle    = { 'm_2':   "tau mass m_{#tau}",
                'm_vis': "visible mass m_{vis}", }
varshorttitle = { 'm_2':   "m_{#tau}",
                  'm_vis': "m_{vis}", }



def plotParabola(channel,var,DM,year,**kwargs):
    if DM=='DM0' and 'm_2' in var: return
    print green("plot parabola for %s, %s"%(DM, var),pre="\n>>> ")
    
    indir        = kwargs.get('indir',       "output_%d"%year )
    outdir       = kwargs.get('outdir',      "plots_%d"%year  )
    tag          = kwargs.get('tag',         ""               )
    plottag      = kwargs.get('plottag',     ""               )
    MDFslices    = kwargs.get('MDFslices',   None             )
    breakdown    = kwargs.get('breakdown',   { }              )
    asymmetric   = kwargs.get('asymm',       args.asymm       )
    fit          = kwargs.get('fit',         False            ) and not breakdown
    ctext        = kwargs.get('ctext',       [ ]              )
    era          = "%d-13TeV"%year
    results      = [ ]
    results_up   = [ ]
    results_down = [ ]
    if breakdown: plottag = "_breakdown"+plottag
    if MDFslices: plottag = "_MDF"+plottag
    if fit:       plottag = ("_fit_asymm" if asymmetric else "_fit")+plottag
    canvasname = "%s/parabola_tes_%s_%s-%s%s%s"%(outdir,channel,var,DM,tag,plottag)
    ensureDirectory(outdir)
    
    filename     = '%s/higgsCombine.%s_%s-%s%s-%s.MultiDimFit.mH90.root'%(indir,channel,var,'MDF' if MDFslices else DM,tag,era)
    for i, (bdtag,bdtitle) in enumerate(breakdown):
      breakdown[i] = (bdtag, bdtitle,filename.replace("higgsCombine.","higgsCombine.%s-"%bdtag))
    print '>>>   file "%s"'%(filename)
    file = ensureTFile(filename)
    tree = file.Get('limit')
    
    # GET DeltaNLL
    list_nll = [ ]
    list_tes = [ ]
    if MDFslices:
      tes = "tes_%s"%DM
      MDFslices = { t:v for t,v in MDFslices.iteritems() if t!=tes }
      for i, event in enumerate(tree):
        if i==0: continue
        if tree.quantileExpected<0: continue
        if tree.deltaNLL == 0: continue
        if any(abs(getattr(tree,t)-v)>0.000001 for t,v in MDFslices.iteritems()): continue
        list_tes.append(getattr(tree,tes))
        list_nll.append(2*tree.deltaNLL)
      list_nll = [n for _,n in sorted(zip(list_tes,list_nll), key=lambda p: p[0])]
      list_tes.sort()
    else:
      for i, event in enumerate(tree):
        if i==0: continue
        if tree.quantileExpected<0: continue
        if tree.deltaNLL == 0: continue
        #if tree.tes < 0.97: continue
        list_tes.append(tree.tes)
        list_nll.append(2*tree.deltaNLL)
    file.Close()
    nllmin    = min(list_nll)
    list_dnll = map(lambda n: n-nllmin, list_nll) # DeltaNLL
    
    # MINIMUM
    dnllmin         = min(list_dnll) # should be 0.0 by definition
    min_index       = list_dnll.index(dnllmin)
    list_dnll_left  = list_dnll[:min_index]
    list_tes_left   = list_tes[:min_index]
    list_dnll_right = list_dnll[min_index:]
    list_tes_right  = list_tes[min_index:]
    if len(list_dnll_left)==0 or len(list_dnll_right)==0 : 
      print "ERROR! Parabola does not have minimum within given range !!!"
      exit(1)
    tmin_left = -1
    tmin_right = -1
    
    # FIND crossings of 1 sigma line
    # |-----<---min---------|
    for i, val in reversed(list(enumerate(list_dnll_left))):
      if val > (dnllmin+1):
          tmin_left = list_tes_left[i]
          break
    # |---------min--->-----|
    for i, val in enumerate(list_dnll_right):
      if val > (dnllmin+1):
          tmin_right = list_tes_right[i]
          break
    
    tes         = round(list_tes[min_index],4)
    tes_errDown = round((tes-tmin_left)*10000)/10000
    tes_errUp   = round((tmin_right-tes)*10000)/10000
    shift       = (list_tes[min_index]-1)*100
    
    # GRAPHS
    graph       = createParabolaFromLists(list_tes,list_dnll,fit=fit)
    graphs_bd   = [ ]
    colors_bd   = [kRed, kBlue, kGreen]
    tes_bbb, tes_stat = -1., -1.
    for i, (tag_bd, title_bd, filename_bd) in enumerate(breakdown):
      print '>>>   file "%s" (breakdown)'%(filename_bd)
      graph_bd, tes_bd = createParabola(filename_bd)
      graph_bd.SetMarkerColor(colors_bd[i])
      graph_bd.SetLineColor(colors_bd[i])
      graph_bd.SetLineWidth(2)
      graph_bd.SetLineStyle(1)
      graph_bd.SetMarkerStyle(20)
      graph_bd.SetMarkerSize(0.8)
      graph_bd.SetLineWidth(2)
      graph_bd.SetName(tag_bd)
      graph_bd.SetTitle(title_bd)
      breakdown[i] = (graph_bd, tes_bd)
    
    # DRAW
    canvas = TCanvas('canvas','canvas',100,100,700,600)
    canvas.SetFillColor(0)
    canvas.SetBorderMode(0)
    canvas.SetFrameFillStyle(0)
    canvas.SetFrameBorderMode(0)
    canvas.SetTopMargin(  0.07 ); canvas.SetBottomMargin( 0.12 )
    canvas.SetLeftMargin( 0.12 ); canvas.SetRightMargin(  0.04 )
    canvas.cd()
    
    xmin, xmax   = 0.945, 1.08
    ymin, ymax   = 0.0,  10.
    fontsize     = 0.044
    lineheight   = 0.05
    xtext, ytext = 0.90, 0.405
    frame = canvas.DrawFrame(xmin,ymin,xmax,ymax)
    frame.GetYaxis().SetTitleSize(0.055)
    frame.GetXaxis().SetTitleSize(0.055)
    frame.GetXaxis().SetLabelSize(0.050)
    frame.GetYaxis().SetLabelSize(0.050)
    frame.GetXaxis().SetLabelOffset(0.010)
    frame.GetXaxis().SetTitleOffset(1.04)
    frame.GetYaxis().SetTitleOffset(1.02)
    frame.GetXaxis().SetNdivisions(508)
    frame.GetXaxis().SetTitle('tau energy scale')
    frame.GetYaxis().SetTitle('-2#Deltaln(L)')
    
    # GRAPH
    graph.SetMarkerStyle(20)
    graph.SetMarkerSize(0.8 if breakdown else 0.4)
    graph.Draw('PLXSAME')
    
    # FIT
    para, graph_clone, tesf, tesf_errDown, tesf_errUp = None, None, None, None, None
    if fit:
      para = fitParabola(xmin,xmax,tes,list_tes_left,list_dnll_left,list_tes_right,list_dnll_right,asymmetric=asymmetric)
      fit = graph.Fit("fit",'R0')
      para.SetRange(xmin,xmax)
      #print para.GetXmin(),para.GetXmax()
      #fit = graph.Fit("fit",'R0','',para.GetXmin(),para.GetXmax())
      #para = para.Clone("fit_clone")
      para.Draw('SAME')
      gStyle.SetOptFit(0)
      tesf = para.GetParameter(1)
      if asymmetric:
        yline = 1+para.GetParameter(2)
        tesf_errUp   = tesf-para.GetX(yline,tesf-0.02,tesf)
        tesf_errDown = para.GetX(yline,tesf,tesf+0.02)-tesf
      else:
        tesf_errUp   = round( sqrt( 1./(1000.*para.GetParameter(0)) )*10000)/10000 # TODO: propagate fit uncertainties with GetParError(i) !
        tesf_errDown = round( sqrt( 1./(1000.*para.GetParameter(0)) )*10000)/10000        
    
    # RESULTS
    latex = TLatex()
    lines = [ ]
    for i,y in [(1,1),(2,4)]:
      line = TLine(xmin, dnllmin+y, xmax, dnllmin+y)
      #line.SetLineWidth(1)
      line.SetLineStyle(7)
      line.Draw('SAME')
      latex.SetTextSize(0.050)
      latex.SetTextAlign(11)
      latex.SetTextFont(42)
      latex.DrawLatex(xmin+0.04*(xmax-xmin),y+0.02*(ymax-ymin),"%d#sigma"%i)
      lines.append(line)
    
    for tmin in [tmin_left,tmin_right]:
      line = TLine(tmin, dnllmin, tmin, dnllmin+1)
      line.SetLineStyle(2)
      line.Draw('SAME')
      lines.append(line)
    
    # LEGEND
    legend = None
    if breakdown:
      nlines = 1 + len(breakdown) + sum(g[0].GetTitle().count('\n') for g in breakdown)
      height = nlines*fontsize*1.1
      x1, y1 = 0.90, 0.70
      legend = TLegend(x1,y1,x1-0.22,y1-height)
      legend.SetFillStyle(0)
      legend.SetBorderSize(0)
      legend.SetTextSize(fontsize)
      legend.SetTextFont(42)
      for graph_bd, tes_bd in breakdown:
        graph_bd.Draw('PLSAME')
        titles = graph_bd.GetTitle().split('\n')
        legend.AddEntry(graph_bd,titles[0],'lp')
        for line in titles[1:]:
          legend.AddEntry(0,line,'')
      legend.AddEntry(graph,"all syst.",'lp')
      legend.Draw()
    if ctext:
      ctext = writeText(ctext,position='topright',textsize=0.80*fontsize)
    
    print ">>> tes SF %7.3f - %-5.3f + %-5.3f"%(tes,tes_errDown,tes_errUp)
    print ">>> shift  %7.3f - %-5.3f + %-5.3f %%"%(shift,tes_errDown*100,tes_errUp*100)
    if fit:
      print ">>> tes SF %7.3f - %-5.3f + %-5.3f   (parabola)"%(tesf,tesf_errDown,tesf_errUp)
      print ">>> shift  %7.3f - %-5.3f + %-5.3f %% (parabola)"%(tesf-1,tesf_errDown*100,tesf_errUp*100)
    
    text = TLatex()
    text.SetTextSize(fontsize)
    text.SetTextAlign(31)
    text.SetTextFont(42)
    text.SetNDC(True)
    text.DrawLatex(xtext,ytext,                "%s"%(varlabel[var]))
    text.DrawLatex(xtext,ytext-lineheight,     "%s"%(DM_label[DM]))
    text.DrawLatex(xtext,ytext-2.2*lineheight, "%7.3f_{-%5.3f}^{+%5.3f}"%(tes,tes_errDown,tes_errUp))
    if fit:
      text.SetTextColor(kRed)
      text.DrawLatex(xtext,ytext-3.5*lineheight, "%7.3f_{-%5.3f}^{+%5.3f}"%(tesf,tesf_errDown,tesf_errUp))
    for i, (graph_bd, tes_bd) in enumerate(breakdown):
      text.SetTextColor(graph_bd.GetLineColor())
      text.DrawLatex(xtext,ytext-(i+3.5)*lineheight, "%7.3f"%(tes_bd))
    
    CMS_lumi.relPosX = 0.13
    CMS_lumi.CMS_lumi(canvas,13,0)
    #canvas.SetTicks(1,1)
    canvas.Modified()
    canvas.Update()
    canvas.SaveAs(canvasname+".png")
    canvas.SaveAs(canvasname+".pdf")
    canvas.Close()
    
    return tes, tes_errDown, tes_errUp, tesf, tesf_errDown, tesf_errUp
    

    
def plotParabolaMDF(channel,var,year,**kwargs):
    """Plot multidimensional parabola."""
    print green("plot multidimensional parabola for %s"%(var),pre="\n>>> ")
    
    indir      = kwargs.get('indir',      "output_%d"%year )
    outdir     = kwargs.get('outdir',     "plots_%d"%year  )
    tag        = kwargs.get('tag',        ""               )
    nnlmin     = kwargs.get('nnlmin',     0                )
    MDFslices  = kwargs.get('MDFslices', { }               )
    era        = "%d-13TeV"%year
    ensureDirectory(outdir)
    
    canvasname = "%s/parabola_tes_%s_%s-%s%s"%(outdir,channel,var,"MDF",tag)
    filename   = '%s/higgsCombine.%s_%s-%s%s-%s.MultiDimFit.mH90.root'%(indir,channel,var,'MDF',tag,era)
    file       = ensureTFile(filename)
    tree       = file.Get('limit')
    ztitle     = "-2#Deltaln(L)"
    pois       = [b.GetName() for b in tree.GetListOfBranches() if 'tes_DM' in b.GetName()]
    pmin, pmax = 0.97, 1.03
    
    for poi1, poi2 in combinations(pois,2):
      
      if len(pois)>2:
        canvasname = "plots_%s/parabola_tes_%s_%s-%s_%s-%s%s"%(year,channel,var,"MDF",poi1,poi2,tag)
        canvasname = canvasname.replace('tes_DM','DM')
      
      graph = TGraph2D()
      graph.SetTitle(ztitle)
      #tree.Draw("%s:%s:deltaNLL >> graph"%(poi1,poi2),"","COLZ")
      slices = { t:v for t,v in MDFslices.iteritems() if t!=poi1 and t!=poi2 }
      #print nnlmin, slices
      i = 0
      for event in tree:
        if event.quantileExpected<0: continue
        if any(abs(getattr(event,t)-v)>0.000001 for t,v in slices.iteritems()): continue
        nnl  = 2*event.deltaNLL-nnlmin
        xpoi = getattr(event,poi1)
        ypoi = getattr(event,poi2)
        graph.SetPoint(i,xpoi,ypoi,nnl)
        #for t in slices:
        #  print "%9s %14.12f, %9s %14.12f, %9s %14.12f, %16.12f"%(t, getattr(event,t), poi1, xpoi, poi2, ypoi, nnl)
        i += 1
      
      latex = TLatex()
      latex.SetTextSize(0.040)
      latex.SetTextFont(42)
      lines = [ ]
      if poi1 in MDFslices:
        line = TLine(MDFslices[poi1],pmin,MDFslices[poi1],pmax)
        x, y = MDFslices[poi1]+0.001, pmax-0.003
        lines.append((line,"%s = %.3f"%(poi1,MDFslices[poi1]),x,y,13))
      if poi2 in MDFslices:
        line = TLine(pmin,MDFslices[poi2],pmax,MDFslices[poi2])
        x, y = pmin+0.003, MDFslices[poi2]+0.001
        lines.append((line,"%s = %.3f"%(poi2,MDFslices[poi2]),x,y,11))
      
      canvas = TCanvas("canvas","canvas",100,100,800,600)
      canvas.SetFillColor(0)
      canvas.SetBorderMode(0)
      canvas.SetFrameFillStyle(0)
      canvas.SetFrameBorderMode(0)
      canvas.SetTopMargin(  0.07 ); canvas.SetBottomMargin( 0.13 )
      canvas.SetLeftMargin( 0.14 ); canvas.SetRightMargin(  0.18 )
      canvas.cd()
      canvas.SetLogz()
      #canvas.SetTheta(90.); pad.SetPhi(0.001)
      
      frame = canvas.DrawFrame(pmin,pmin,pmax,pmax)
      frame.GetXaxis().SetTitle(re.sub(r"_(DM\d+)",r"_{\1}",poi1))
      frame.GetYaxis().SetTitle(re.sub(r"_(DM\d+)",r"_{\1}",poi2))
      frame.GetZaxis().SetTitle(ztitle)
      frame.GetYaxis().SetTitleSize(0.055)
      frame.GetXaxis().SetTitleSize(0.055)
      frame.GetZaxis().SetTitleSize(0.055)
      frame.GetXaxis().SetLabelSize(0.050)
      frame.GetYaxis().SetLabelSize(0.050)
      frame.GetXaxis().SetLabelOffset(0.010)
      frame.GetXaxis().SetTitleOffset(1.05)
      frame.GetYaxis().SetTitleOffset(1.14)
      graph.GetZaxis().SetTitle(ztitle)
      graph.GetZaxis().SetTitleOffset(0.1)
      frame.GetZaxis().SetTitleOffset(0.1)
      frame.GetZaxis().SetNdivisions(5)
      #if nnlmin:
        #print "here"
        #levels = [0.01,1,10,100,1000]
        #frame.SetContour(len(levels),array('d',levels))
      
      graph.SetMinimum(0.5)
      graph.SetMaximum(100)
      graph.Draw('COLZ SAME')
      
      for line,poi,x,y,align in lines:
        line.SetLineStyle(2)
        line.Draw('SAME')
        latex.SetTextAlign(align)
        latex.DrawLatex(x,y,re.sub(r"_(DM\d+)",r"_{\1}",poi))
      
      latex.SetTextAlign(33)
      latex.SetTextSize(0.055)
      latex.SetTextAngle(90)
      latex.DrawLatex(pmax+0.19*(pmax-pmin),pmax,ztitle)
      
      CMS_lumi.relPosX = 0.14
      CMS_lumi.CMS_lumi(canvas,13,0)
      gPad.Modified()
      gPad.Update()
      gPad.RedrawAxis()
      
      canvas.SaveAs(canvasname+'.png')
      canvas.SaveAs(canvasname+'.pdf')
      canvas.Close()
    


def fitParabola(xmin,xmax,tes,list_tes_left,list_dnll_left,list_tes_right,list_dnll_right,asymmetric=False):
    
    # FIT X RANGE (<ymax)
    xmin_fit = xmin
    xmax_fit = xmax
    ymax_fit = 5
    ymax_left  = min(ymax_fit,max(list_dnll_left))
    ymax_right = min(ymax_fit,max(list_dnll_right))
    # |-->---|----min----|------|
    for i, val in enumerate(list_dnll_left):
      if val <= (ymax_left):
        xmin_fit = round(list_tes_left[i],4)
        print ">>> xmin_fit = %.3f (%2d,%3.1f) is below NLL %.1f"%(xmin_fit,val,i,ymax_left)
        break
    # |------|----min----|---<--|
    for i, val in reversed(list(enumerate(list_dnll_right))):
      if val <= (ymax_right):
        xmax_fit = round(list_tes_right[i],4)
        print ">>> xmax_fit = %.3f (%2d,%3.1f) is below NLL %.1f"%(xmax_fit,val,i,ymax_right)
        break
    
    # FIT MAX WIDTH
    bmid     = (xmax_fit+xmin_fit)/2.
    dtmin    = max(tes-xmin_fit,0.004)
    dtmax    = max(xmax_fit-tes,0.004)
    tmin_fit = tes-abs(dtmin)*0.26
    tmax_fit = tes+abs(dtmax)*0.26
    wmin_fit, wmax_fit = sorted([ymax_left/(1000.*(dtmin**2)),ymax_right/(1000.*(dtmax**2))])
    #print ">>> tes=%.3f, tmin_fit=%.3f, tmin_fit=%.3f, bmid=xmin_fit+(xmax_fit-xmin_fit)/2=%.3f"%(tes,tmin_fit,tmax_fit,bmid)
    #print ">>> wmin_fit=%.3f, wmax_fit=%.3f"%(wmin_fit,wmax_fit)
    
    # FIT Y RANGE (<ymax)
    #ymax_fit = 0.5
    
    # FIT PARAMETERS
    wmin, wval, wmax = wmin_fit*0.99, wmin_fit, wmax_fit*1.50
    bmin, bval, bmax = tmin_fit, tes, tmax_fit
    cmin, cval, cmax = -0.0001, 0.0, 0.5 #max(min(ymax_fit,3),0.001)
    amin, aval, amax = -1000, 0.0, 1000
    
    if bmin<xmin_fit: print ">>> Warning! setting bmin=%.3f -> %.3f=xmin_fit"%(bmin,xmin_fit); bmin = xmin_fit
    if bmax>xmax_fit: print ">>> Warning! setting bmin=%.3f -> %.3f=xmin_fit"%(bmax,xmax_fit); bmax = xmax_fit
    if bval<bmin or bmax<bval: print ">>> Warning! setting bval=%.3f -> %.3f=bmin+(bmin-bmax)/2"%(bval,(bmax+bmin)/2.); bval = (bmax+bmin)/2.
    if cval<cmin or cmax<cval: print ">>> Warning! setting cval=%.3f -> %.3f=cmin+(cmin-cmax)/2"%(cval,(cmax+cmin)/2.); cval = (cmax+cmin)/2.
    print ">>> width   = %5g [%5s, %5s]"%(wval,wmin,wmax)
    print ">>> tes     = %5s [%5s, %5s]"%(bval,bmin,bmax)
    print ">>> yoffset = %5s [%5s, %5s]"%(cval,cmin,cmax)
    if asymmetric:
      print ">>> w_asymm = %5s [%5s, %5s]"%(aval, amin, amax)
    
    # FIT FUNCTION
    if asymmetric:
      #para = TF1("fit","[0]*1000*(x-[1])**2+[3]*10000*(x-[1])**3+[2]",xmin_fit,xmax_fit)
      para = TF1("fit",asymmParabola,xmin_fit,xmax_fit,4)
    else:
      para = TF1("fit","[0]*1000*(x-[1])**2+[2]",xmin_fit,xmax_fit)
    para.SetParName(0,"width")
    para.SetParName(1,"tes")
    para.SetParName(2,"yoffset")
    if asymmetric:
      #para.SetParName(3,"w_asymm")
      para.SetParName(3,"width_left")
    #para.FixParameter(0,0)
    #para.FixParameter(2,0)
    if asymmetric:
      #para.SetParameters(wval,bval,0,0)
      para.SetParameters(wval,bval,0,wval)
    else:
      para.SetParameters(wval,bval,0)
    para.SetParLimits(0,wmin,wmax)
    para.SetParLimits(1,bmin,bmax)
    para.SetParLimits(2,cmin,cmax)
    if asymmetric:
      #para.SetParLimits(3,amin,amax)
      para.SetParLimits(3,wmin,wmax)
    
    return para
    
def asymmParabola(x,par):
    """Asymmetric parabola:
         f(x) = [0]*1000*(x-[1])**2+[2]  if x < [1]
         f(x) = [3]*1000*(x-[1])**2+[2]  if x > [1]
    """
    if x[0]>par[1]:
      return par[0]*1000*(x[0]-par[1])**2+par[2]
    else:
      return par[3]*1000*(x[0]-par[1])**2+par[2]
    

def createParabolaFromLists(list_tes,list_dnll,fit=False):
    """Create TGraph of DeltaNLL parabola vs. tes from lists."""
    npoints = len(list_dnll)
    if not fit: return TGraph(npoints, array('d',list_tes), array('d',list_dnll))
    graph  = TGraphAsymmErrors()
    for i, (tes,dnll) in enumerate(zip(list_tes,list_dnll)):
      error = 1.0
      if dnll<6 and i>0 and i+1<npoints:
        left, right = list_dnll[i-1], list_dnll[i+1]
        error       = max(0.1,(abs(dnll-left)+abs(right-dnll))/2)
      graph.SetPoint(i,tes,dnll)
      graph.SetPointError(i,0.0,0.0,error,error)
    return graph
    
def createParabola(filename):
    """Create TGraph of DeltaNLL parabola vs. tes from MultiDimFit file."""
    file = ensureTFile(filename)
    tree = file.Get('limit')
    tes, nll = [ ], [ ]
    for i, event in enumerate(tree):
      if i==0: continue
      tes.append(tree.tes)
      nll.append(2*tree.deltaNLL)
    file.Close()
    minnll = min(nll)
    mintes = tes[nll.index(minnll)]
    dnll   = map(lambda x: x-minnll, nll) # DeltaNLL
    graph  = TGraph(len(tes), array('d',tes), array('d',dnll))
    return graph, mintes
    
def findMultiDimSlices(channel,var,**kwargs):
    """Find minimum of multidimensional parabola in MultiDimFit file and return
    dictionary of the corresponding values of POI's."""
    tag      = kwargs.get('tag', "" )
    filename = '%s/higgsCombine.%s_%s-%s%s-13TeV.MultiDimFit.mH90.root'%(indir,channel,var,'MDF',tag)
    file     = ensureTFile(filename)
    tree     = file.Get('limit')
    pois     = [b.GetName() for b in tree.GetListOfBranches() if 'tes_DM' in b.GetName()]
    slices   = { }
    nnlmin   = 10e10
    for event in tree:
      nnl = 2*event.deltaNLL
      if nnl<nnlmin:
        nnlmin = nnl
        for poi in pois:
          slices[poi] = getattr(event,poi)
        #print nnlmin, slices
    file.Close()
    #print nnlmin, slices
    return nnlmin, slices
    


def measureTES(filename,unc=False,fit=False,asymmetric=True):
    """Create TGraph of DeltaNLL parabola vs. tes from MultiDimFit file."""
    if fit:
       return measureTES_fit(filename,asymmetric=asymmetric,unc=unc)
    file = ensureTFile(filename)
    tree = file.Get('limit')
    tes, nll = [ ], [ ]
    for event in tree:
      tes.append(tree.tes)
      nll.append(2*tree.deltaNLL)
    file.Close()
    nllmin = min(nll)
    imin   = nll.index(nllmin)
    tesmin = tes[imin]
    
    if unc:
      nll_left  = nll[:imin]
      tes_left  = tes[:imin]
      nll_right = nll[imin:]
      tes_right = tes[imin:]
      if len(nll_left)==0 or len(nll_right)==0 : 
        print "ERROR! measureTES: Parabola does not have a minimum within given range!"
        exit(1)
      tmin_left = -1
      tmin_right = -1
      
      # FIND crossings of 1 sigma line
      # |-----<---min---------|
      for i, val in reversed(list(enumerate(nll_left))):
        if val > (nllmin+1):
          tmin_left = tes_left[i]
          break
      # |---------min--->-----|
      for i, val in enumerate(nll_right):
        if val > (nllmin+1):
          tmin_right = tes_right[i]
          break
      
      tes_errDown = tesmin-tmin_left
      tes_errUp   = tmin_right-tesmin
      return tesmin, tes_errDown, tes_errUp
    
    return tesmin
    


def measureTES_fit(filename,asymmetric=True,unc=False):
    """Create TGraph of DeltaNLL parabola vs. tes from MultiDimFit file."""
    file = ensureTFile(filename)
    tree = file.Get('limit')
    xmin, xmax = 0.945, 1.08
    ymin, ymax = 0.0,  10.
    
    # GET DeltaNLL
    list_nll = [ ]
    list_tes = [ ]
    for i, event in enumerate(tree):
      if i==0: continue
      if tree.quantileExpected<0: continue
      if tree.deltaNLL==0: continue
      list_tes.append(tree.tes)
      list_nll.append(2*tree.deltaNLL)
    file.Close()
    nllmin    = min(list_nll)
    list_dnll = map(lambda n: n-nllmin, list_nll) # DeltaNLL
    
    # MINIMUM
    dnllmin         = min(list_dnll) # should be 0.0 by definition
    min_index       = list_dnll.index(dnllmin)
    list_dnll_left  = list_dnll[:min_index]
    list_tes_left   = list_tes[:min_index]
    list_dnll_right = list_dnll[min_index:]
    list_tes_right  = list_tes[min_index:]
    if len(list_dnll_left)==0 or len(list_dnll_right)==0 : 
      print "ERROR! Parabola does not have minimum within given range !!!"
      exit(1)
    tmin_left = -1
    tmin_right = -1
    
    # FIND crossings of 1 sigma line
    # |-----<---min---------|
    for i, val in reversed(list(enumerate(list_dnll_left))):
      if val > (dnllmin+1):
          tmin_left = list_tes_left[i]
          break
    # |---------min--->-----|
    for i, val in enumerate(list_dnll_right):
      if val > (dnllmin+1):
          tmin_right = list_tes_right[i]
          break
    
    tes   = round(list_tes[min_index],4)
    graph = createParabolaFromLists(list_tes,list_dnll,fit=True)
    para  = fitParabola(xmin,xmax,tes,list_tes_left,list_dnll_left,list_tes_right,list_dnll_right,asymmetric=asymmetric)
    fit   = graph.Fit("fit",'R0')
    tesf  = para.GetParameter(1)
    if unc:
      if asymmetric:
        yline = 1+para.GetParameter(2)
        tesf_errUp   = tesf-para.GetX(yline,tesf-0.02,tesf)
        tesf_errDown = para.GetX(yline,tesf,tesf+0.02)-tesf
      else:
        tesf_errUp   = round( sqrt( 1./(1000.*para.GetParameter(0)) )*10000)/10000 # TODO: propagate fit uncertainties with GetParError(i) !
        tesf_errDown = round( sqrt( 1./(1000.*para.GetParameter(0)) )*10000)/10000  
      return tesf, tesf_errDown, tesf_errUp
    
    return tesf
    

def plotMeasurements(categories,measurements,**kwargs):
    """Plot measurements. in this format:
         cats = [ "cat1",              "cat2"              "cat3"            ]
         meas = [(0.976,0.004,0.004), (0.982,0.006,0.002),(0.992,0.002,0.008)]
       or with pairs of measurements:
         cats = [ "cat1",              "cat2"              "cat3"            ]
         meas = [[(0.996,0.004,0.002),(0.982,0.006,0.002)],
                 [ None,              (0.976,0.004,0.004)],
                 [(1.010,0.010,0.004),(0.992,0.002,0.008)]]
         ents = [ "m_tau", "m_vis" ]
    """
    
    npoints      = len(measurements)
    categories   = categories[::-1]
    measurements = measurements[::-1]
    minB         = 0.13
    colors       = [ kBlack, kBlue, kRed, kOrange, kGreen, kMagenta ]
    title        = kwargs.get('title',       ""                   )
    text         = kwargs.get('text',        ""                   )
    ctext        = kwargs.get('ctext',       ""                   ) # corner text
    entries      = kwargs.get('entries',     [ ]                  )
    emargin      = kwargs.get('emargin',     None                 )
    plottag      = kwargs.get('tag',         ""                   )
    xtitle       = kwargs.get('xtitle',      ""                   )
    xminu        = kwargs.get('xmin',        None                 )
    xmaxu        = kwargs.get('xmax',        None                 )
    rangemargin  = kwargs.get('rangemargin', 0.18                 )
    colors       = kwargs.get('colors',      colors               )
    position     = kwargs.get('position',    ''                   ).lower() # legend
    cposition    = kwargs.get('cposition',   'topright'           ).lower() # cornertext
    ctextsize    = kwargs.get('ctextsize',   0.040                )
    width        = kwargs.get('width',       0.22                 )
    align        = kwargs.get('align',       "center"             ).lower() # category labels
    heigtPerCat  = kwargs.get('h',           55                   )
    canvasH      = kwargs.get('H',           max(400,120+heigtPerCat*npoints) )
    canvasW      = kwargs.get('W',           800                  )
    canvasL      = kwargs.get('L',           0.20                 )
    canvasB      = kwargs.get('B',           minB                 )
    canvasname   = kwargs.get('canvas',      "measurements"       )
    canvasname   = kwargs.get('name',        canvasname           )
    exts         = kwargs.get('ext',         ['png']              )
    exts         = kwargs.get('exts',        exts                 )
    xmin, xmax   = None, None
    maxpoints    = 0
    exts         = ensureList(exts)
    ctext        = ensureList(ctext)
    
    # MAKE GRAPH
    errwidth     = 0.1
    graphs       = [ ]
    for i, points in enumerate(measurements): #(name, points)
      if not isinstance(points,list):
        points = [ points ]
      offset = 1./(len(points)+1)
      while len(points)>maxpoints:
        maxpoints += 1
        graphs.append(TGraphAsymmErrors())
      for j, point in enumerate(points):
        if point==None: continue
        if len(point)==3:
          x, xErrLow, xErrUp = point
        elif len(point)==2:
          x, xErrLow = point
          xErrUp = xErrLow
        else:
          x, xErrLow, xErrUp = point[0], 0, 0
        graph = graphs[j]
        graph.SetPoint(i,x,1+i-(j+1)*offset)
        graph.SetPointError(i,xErrLow,xErrUp,errwidth,errwidth) # -/+ 1 sigma
        if xmin==None or x-xErrLow < xmin: xmin = x-xErrLow
        if xmax==None or x+xErrUp  > xmax: xmax = x+xErrUp
    if xminu or xmaxu:
      if xminu: xmin = xminu
      if xmaxu: xmax = xmaxu
    else:
      range = xmax - xmin
      xmin -= rangemargin*range
      xmax += rangemargin*range
    
    # DRAW
    canvasB  = min(canvasB,minB)
    canvasH  = int(canvasH/(1.-minB+canvasB))
    scale    = 600./canvasH
    canvasT  = 0.07*scale
    canvasB  = minB*(scale-1)+canvasB
    canvasR  = 0.04
    canvas   = TCanvas("canvas","canvas",100,100,canvasW,canvasH)
    canvas.SetTopMargin(  canvasT ); canvas.SetBottomMargin( canvasB )
    canvas.SetLeftMargin( canvasL ); canvas.SetRightMargin(  canvasR )
    canvas.SetGrid(1,0)
    canvas.cd()
    
    # LEGEND
    legend = None
    if entries:
      legtextsize = 0.052*scale
      height      = legtextsize*1.08*len([o for o in [title,text]+zip(graphs,entries) if o])
      if 'out' in position:
        x1 = 0.008; x2 = x1+width
        y1 = 0.018; y2 = y1+height
      else:
        if 'right'  in position:  x1 = 0.95;            x2 = x1-width
        elif 'left' in position:  x1 = canvasL+0.04;    x2 = x1+width
        else:                     x1 = 0.88;            x2 = x1-width 
        if 'bottom' in position:  y1 = 0.04+0.13*scale; y2 = y1+height
        else:                     y1 = 0.96-0.07*scale; y2 = y1-height
      legend = TLegend(x1,y1,x2,y2)
      legend.SetTextSize(legtextsize)
      legend.SetBorderSize(0)
      legend.SetFillStyle(0)
      legend.SetFillColor(0)
      if title:
        legend.SetTextFont(62)
        legend.SetHeader(title)
      legend.SetTextFont(42)
    
    frame  = canvas.DrawFrame(xmin,0.0,xmax,float(npoints))
    frame.GetYaxis().SetLabelSize(0.0)
    frame.GetXaxis().SetLabelSize(0.052*scale)
    frame.GetXaxis().SetTitleSize(0.060*scale)
    frame.GetXaxis().SetTitleOffset(0.98)
    frame.GetYaxis().SetNdivisions(npoints,0,0,False)
    frame.GetXaxis().SetTitle(xtitle)
    
    for i, graph in enumerate(graphs):
      color = colors[i%len(colors)]
      graph.SetLineColor(color)
      graph.SetMarkerColor(color)
      graph.SetLineStyle(1)
      graph.SetMarkerStyle(20)
      graph.SetLineWidth(2)
      graph.SetMarkerSize(1)
      graph.Draw('PSAME')
      if legend and i<len(entries):
        legend.AddEntry(graph,entries[i],'lep')
    if legend:
      if text:
        legend.AddEntry(graph,entries[i],'lep')
      legend.Draw()
    
    # CORNERTEXT
    if ctext:
      ctextsize *= scale
      ctext = writeText(ctext,position=cposition,textsize=ctextsize)
    
    # CATEGORY LABELS
    labelfontsize = 0.050*scale
    latex = TLatex()
    latex.SetTextSize(labelfontsize)
    latex.SetTextFont(62)
    if align=='center':
      latex.SetTextAlign(22)
      margin = emargin #0.02 #+ stringWidth(*categories)*labelfontsize/2. # width strings
      xtext  = marginCenter(canvas,frame.GetXaxis(),margin=margin) # automatic
    else:
      latex.SetTextAlign(32)
      xtext  = xmin-0.02*(xmax-xmin)
    for i, name in enumerate(categories):
      ytext = i+0.5
      latex.DrawLatex(xtext,ytext,name)
    
    CMS_lumi.cmsTextSize  = 0.85
    CMS_lumi.lumiTextSize = 0.80
    CMS_lumi.relPosX      = 0.13*800*0.76/(1.-canvasL-canvasR)/canvasW
    CMS_lumi.CMS_lumi(canvas,13,0)
    
    # SAVE
    if exts:
      for ext in exts:
        if '.' not in ext[0]: ext = '.'+ext
        canvasname1 = re.sub(r"\.?(png|pdf|jpg|gif|eps|tiff?)?$",ext,canvasname,re.IGNORECASE)
        canvas.SaveAs(canvasname1)
    else:
      canvas.SaveAs(canvasname)
    
    canvas.Close()
    
    
def combineMeasurements(measurements):
  """Average measurement (x,errDown,errUp), weighted by their uncertainty."""
  if not isinstance(measurements,list) and isinstance(measurements,ntuple):
    return measurement
  sumxvar2 = sum([ x/em**2 for x,em,ep in measurements])
  sumvar2  = sum([ 1./em**2 for x,em,ep in measurements])
  average  = sumxvar2/sumvar2
  stddev   = sqrt(1./sumvar2)
  return (average,stddev,stddev)

def combineMeasurementsAsymm(measurements):
  """Average measurement (x,errDown,errUp), weighted by their uncertainty."""
  # https://arxiv.org/pdf/physics/0406120v1.pdf (21-25)
  if not isinstance(measurements,list) and isinstance(measurements,ntuple):
    return measurement
  sumxvar2 = sum([ x/em**2 for x,em,ep in measurements])
  sumvar2  = sum([ 1./em**2 for x,em,ep in measurements])
  average  = sumxvar2/sumvar2
  stddev   = sqrt(1./sumvar2)
  return (average,stddev,stddev)

#def weightAsymm(sigmaP,sigmaM):
#  sigmaA = 2*sigmaP*sigmaLow/(sigmaP+sigmaM)
#  sigmaB = (sigmaM-sigmaP)/(sigmaP+sigmaM)
#  weight = sigmaA/(sigmaA+sigmaB)**3
#def sigma(sigmaM,sigmaP):      return 2*sigmaP*sigmaLow/(sigmaP+sigmaM)
#def sigmaPrime(sigmaM,sigmaP): return (sigmaM-sigmaP)/(sigmaP+sigmaM)

def writeMeasurement(filename,categories,measurements,**kwargs):
    """Write measurements to file."""
    if ".txt" not in filename[-4]: filename += ".txt"
    mformat = kwargs.get('format'," %10.4f %10.4f %10.4f") #" %10.6g %10.6g %10.6g"
    sformat = re.sub(r"%(\d*).?\d*[a-z]",r"%\1s",mformat)
    with open(filename,'w+') as file:
      print ">>>   created txt file %s"%(filename)
      startdate = time.strftime("%a %d/%m/%Y %H:%M:%S",time.gmtime())
      file.write("%s\n"%(startdate))
      for category, points in zip(categories,measurements):
        file.write("%-10s"%category)
        for point in points:
          if point:
            file.write(mformat%point)
          else:
            file.write(sformat%("-","-","-"))
        file.write('\n')

def readMeasurement(filename,**kwargs):
    """Read measurements from file."""
    if ".txt" not in filename[-4]: filename += ".txt"
    categories   = [ ]
    measurements = [ ]
    with open(filename,'r') as file:
      print ">>>   reading txt file %s"%(filename)
      startdate = time.strftime("%a %d/%m/%Y %H:%M:%S",time.gmtime())
      file.next()
      for line in file:
        points  = [ ]
        columns = line.split()
        categories.append(columns[0])
        i = 1
        while len(columns[i:])>=3:
          try:
            points.append((float(columns[i]),float(columns[i+1]),float(columns[i+2])))
          except ValueError:
            points.append(None)
          i += 3
        measurements.append(points)
    return measurements
    
def writeText(*text,**kwargs):
    """Write text on plot."""
    
    position = kwargs.get('position',     'topleft'       ).lower()
    textsize = kwargs.get('textsize',     0.040           )
    font     = 62 if kwargs.get('bold',   False           ) else 42
    align    = 13
    if len(text)==1 and isinstance(text[0],list):
      text = text[0]
    else:
      text     = ensureList(text)
    if not text or not any(t!="" for t in text):
      return None
    L, R     = gPad.GetLeftMargin(), gPad.GetRightMargin()
    T, B     = gPad.GetTopMargin(),  gPad.GetBottomMargin()
    
    if 'right' in position:
      x, align = 0.96, 30
    else:
      x, align = 0.04, 10
    if 'bottom' in position:
      y = 0.05; align += 1
    else:
      y = 0.95; align += 3
    x = L + (1-L-R)*x
    y = B + (1-T-B)*y

    latex = TLatex()
    latex.SetTextSize(textsize)
    latex.SetTextAlign(align)
    latex.SetTextFont(font)
    #latex.SetTextColor(kRed)
    latex.SetNDC(True)
    for i, line in enumerate(text):
      latex.DrawLatex(x,y-i*1.2*textsize,line)
    
    return latex
    


def stringWidth(*strings0):
    """Make educated guess on the maximum length of a string."""
    strings = list(strings0)
    for string in strings0:
      matches = re.search(r"#splitline\{(.*?)\}\{(.*?)\}",string) # check splitline
      if matches:
        while string in strings: strings.pop(strings.index(string))
        strings.extend([matches.group(1),matches.group(2)])
      matches = re.search(r"[_^]\{(.*?)\}",string) # check subscript/superscript
      if matches:
        while string in strings: strings.pop(strings.index(string))
        strings.append(matches.group(1))
      string = string.replace('#','')
    return max([len(s) for s in strings])
    
def marginCenter(canvas,axis,side='left',shift=0,margin=None):
    """Calculate the center of the right margin in units of a given axis"""
    range    = axis.GetXmax() - axis.GetXmin()
    rangeNDC = 1 - canvas.GetRightMargin() - canvas.GetLeftMargin()
    if side=='right':
      if margin==None: margin = canvas.GetRightMargin()
      center = axis.GetXmax() + margin*range/rangeNDC/2.
    else:
      if margin==None: margin = canvas.GetLeftMargin()
      center = axis.GetXmin() - margin*range/rangeNDC/2.
    if shift:
        if center>0: center*=(1+shift/100.0)
        else:        center*=(1-shift/100.0)
    return center
    
def tagToSelection(tag):
    """Convert a tag to selections."""
    text = ""
    if "mtlt50" in tag:
      text = "m_{T} < 50 GeV"
      if "_100" in tag:
        text += ", 50 GeV < m_{vis} < 100 GeV"%(106 if "-7" in tag else 100)
      elif "_200" in tag:
        text += ", 50 GeV < m_{vis} < 200 GeV"%(197 if "-7" in tag else 200)
      #else:
      #  text += ", 50 GeV < m_{vis} < 106 GeV"
    elif "ZTTregion2" in tag:
      text = "m_{T} < 50 GeV, 50 GeV < m_{vis} < 100 GeV"
      if "_45" in tag:
        text = text.replace("50 GeV < m_{vis}","45 GeV < m_{vis}")
      if "_85" in tag:
        text = text.replace("m_{vis} < 100 GeV","m_{vis} < 85 GeV")
    elif "ZTTregion" in tag:
      text = "m_{T} < 50 GeV, 50 GeV < m_{vis} < 85 GeV, D_{#zeta} > -25 GeV"
    if "differentCuts" in tag:
      #re.sub(r'\d+ GeV < m_{vis} < \d+ GeV',r'#color[4]{\1}',text)
      text = "m_{T} < 50 GeV, #color[4]{%s GeV < m_{vis} < 100 GeV}"%(45 if "45" in tag else 50)
    lines = text.split(', ')
    return lines
    
def tagToBinning(var,DM,tag):
    """Convert a tag to text."""
    lines = [ ]
    if var=='m_2':
      range = "%.2f GeV < m_{#tau} < %.2f GeV"%((0.85,1.40) if DM=='DM10' else (0.95,1.50) if DM=='DM11' else (0.35,1.20))
      bins  = "%.2f GeV bins"%(0.10 if "0p10" in tag else 0.05 if "0p05" in tag else 0.10)
      lines = tagToSelection(tag) + [range,bins]
    elif var=='m_vis':
      if "mtlt50" in tag:
        lines.append("m_{T} < 50 GeV")
      range = "%d GeV < m_{vis}"%(45 if "_45" in tag else 50)
      if "ZTTregion" in tag:
        lines.append("m_{T} < 50 GeV")
        range += " < %d GeV"%(100 if "ZTTregion2" in tag else 85)
      elif "_100" in tag:
        range += " < %d GeV"%(106 if "-7" in tag else 100)
      elif "_200" in tag:
        range += " < %d GeV"%(197 if "-7" in tag else 200)
      else:
        range += " < 106 GeV"
      bins  = "%d GeV bins"%(5 if any(t in tag for t in ["-5","_5"]) else 7)
      lines += [range,bins]
      if re.search("ZTTregion(?!\d)",tag):
        lines.append("D_{#zeta} > -25 GeV")
    return lines
    
def tagToBinWidth(var,tag):
    if var=='m_2':
      return "%.2f GeV"%(0.10 if "0p10" in tag else 0.05 if "0p05" in tag else 0.04)
    elif var=='m_vis':
      return "%d GeV"%(7 if "-7" in tag else 5)
    return ""


def insertBinning(tag):
  if '_0p' not in tag and '_' in tag and len(tag)>2:
    pieces = tag.split('_')
    pieces.insert(2,'0p10' if '_45' in tag else '0p10')
    tag = '_'.join(pieces)
  return tag

def green(string,**kwargs):
  return kwargs.get('pre',"")+"\x1b[0;32;40m%s\033[0m"%(string)
  
def warning(string,**kwargs):
  print ">>> \x1b[1;33;40m%sWarning!\x1b[0;33;40m %s\033[0m"%(kwargs.get('pre',""),string)
    
def error(string,**kwargs):
  print ">>> \x1b[1;31;40m%sERROR!\x1b[0;31;40m %s\033[0m"%(kwargs.get('pre',""),string)
  exit(1)
  
def ensureDirectory(dirname):
  """Make directory if it does not exist."""
  if not os.path.exists(dirname):
      os.makedirs(dirname)
      print ">>> made directory %s"%dirname
  
def ensureTFile(filename,option='READ',**kwargs):
  """Open TFile and make sure if that it exists."""
  pre  = kwargs.get('pre',  ""   )
  stop = kwargs.get('exit', True )
  if not os.path.isfile(filename):
    error('ensureTFile: File in path "%s" does not exist'%(filename),pre=pre)
  file = TFile(filename,option)
  if not file or file.IsZombie():
    if stop:
      error('ensureTFile: Could not open file by name "%s"'%(filename),pre=pre)
    else:
      warning('ensureTFile: Could not open file by name "%s"'%(filename),pre=pre)
  return file

def ensureFile(filename):
  if not os.path.isfile(filename):
    error('File "%s" does not exist!'%(filename))
  return filename
  
def ensureList(arg):
  return arg if (isinstance(arg,list) or isinstance(arg,tuple)) else [arg]


def finalCalculation(year,**kwargs):
  outdir = kwargs.get('outdir', "plots_%d"%year)
  DMs    = ['DM0','DM1','DM10','DM11']
  if year==2016:
    measurements = [
      [ None,                  (0.9950,0.0063,0.0063)],
      [(1.0021,0.0036,0.0023), (1.0013,0.0033,0.0036)],
      [(0.9985,0.0027,0.0027), (1.0024,0.0045,0.0045)],
      [(1.0199,0.0060,0.0067), (0.9977,0.0099,0.0089)],
    ]
  elif year==2017:
    measurements = [
      [ None,                  (1.0012,0.0090,0.0084)],
      [(0.9933,0.0036,0.0036), (1.0043,0.0036,0.0036)],
      [(1.0017,0.0036,0.0036), (1.0034,0.0054,0.0054)],
      [(1.0229,0.0061,0.0063), (0.9885,0.0105,0.0105)],
    ]
  elif year==2018:
    measurements = [
      [ None,                  (0.9844,0.0086,0.0058)],
      [(0.9961,0.0045,0.0034), (0.9964,0.0036,0.0036)],
      [(0.9963,0.0045,0.0045), (0.9865,0.0053,0.0036)],
      [(1.0014,0.0081,0.0052), (0.9939,0.0109,0.0121)],
    ]
  channel = 'mt'
  ctext = "" #tagToSelection("_mtlt50_0p10_100-7")
  name  = "%s/measurement_tes_%s_final"%(outdir,channel)
  entries = [varlabel[v] for v in ["m_2","m_vis"]]
  
  string = ""
  for i, (DM, points) in enumerate(zip(DMs,measurements)):
    string += "%10s "%(DM)
    for j, point in enumerate(points):
      if point==None:
        string += "& %12s "%('--')
      else:
        tes, eup, elow = point
        err = 100*sqrt(max(eup,elow)**2 + (tes*0.005)**2)
        tes = 100*(tes-1)
        string += "& $%4.1f\\pm%3.1f$ "%(tes,err)
        newpoint = (tes,err,err)
        points[j] = newpoint
    string += "\\\\\n"
  print string
  
  cats = [varlabel[d] for d in DMs]
  plotMeasurements(cats,measurements,xtitle="tau energy scale [%]",xmin=-3,xmax=+4,L=0.20,
                   position="out",entries=entries,emargin=0.14,ctext=ctext,ctextsize=0.035,cposition='topright',canvas=name,exts=['png','pdf'])
  



def main(args):
    
    verbosity     = args.verbose
    year          = args.year
    lumi          = 36.5 if year==2016 else 41.4 if year==2017 else 59.5
    channels      = args.channels
    newDM         = any("newDM" in t or "DeepTau" in t for t in args.tags)
    DMs           = [ 'DM0', 'DM1', 'DM10', 'DM11' ] if newDM else [ 'DM0', 'DM1', 'DM10' ]
    vars          = [ 'm_2', 'm_vis' ]
    indir         = "output_%s"%year
    outdir        = "plots_%d"%year
    tags          = args.tags
    breakdown     = args.breakdown
    multiDimFit   = args.multiDimFit
    summary       = args.summary
    parabola      = args.parabola
    fit           = args.fit
    asymmetric    = args.asymm
    customSummary = args.customSummary
    if args.DMs: DMs = args.DMs
    if args.observables: vars = [o for o in args.observables if '#' not in o]
    ensureDirectory(outdir)
    
    CMS_lumi.lumi_13TeV = "%s, %s fb^{-1}"%(year,lumi)
    
    cats    = [varlabel[d] for d in DMs]
    entries = [varlabel[v] for v in vars]
    fittag  = "_fit_asymm" if asymmetric else "_fit"
    
    finalCalculation(year); exit(0)
    
    # LOOP over tags, channels, variables
    if parabola:
      for tag in tags:
        tag += args.extratag
        for channel in channels:
          points, points_fit = [ ], [ ]
          for var in vars:
            
            # MULTIDIMFIT
            slices = { }
            if multiDimFit:
              nnlmin, slices = findMultiDimSlices(channel,var,year,tag=tag)
              plotParabolaMDF(channel,var,nnlmin=nnlmin,MDFslices=slices,indir=indir,tag=tag)
            
            # LOOP over DMs
            for i, DM in enumerate(DMs):
              if "_0p"  in tag and var=='m_vis':  continue
              if "_100" in tag and var=='m_2':    continue
              if "_200" in tag and var=='m_2':    continue
              if "_85"  in tag and var=='m_2':    continue
              if "_45"  in tag and var=='m_2':    continue
              if "_restr" in tag and var=='m_2':  continue
              if DM=='DM11' and not ("newDM" in tag or "DeepTau" in tag): continue
              if DM=="DM0" and var=='m_2':
                if len(points)<=i:
                  points.append([ ]); points_fit.append([ ])
                points[i].append(None); points_fit[i].append(None)
                continue
              ctext = tagToBinning(var,DM,tag)
              #title = "%s, %s"%(varshorttitle[var],DM_label[DM].replace("decay mode",''))
              
              # PARABOLA
              if breakdown:
                breakdown1 = [ ('stat', "stat. only,\nexcl. b.b.b."), ('sys', "stat. only\nincl. b.b.b.") ]
                breakdown2 = [ ('jtf', "j #rightarrow #tau_{h} fake"), ('ltf', "l #rightarrow #tau_{h} fake"), ('zpt', "Z pT rew.") ]
                breakdown3 = [ ('eff', "#mu, #tau_{h} eff."), ('norm', "xsecs, norms"), ('lumi', "lumi") ]
                tes,tesDown,tesUp,tesf,tesfDown,tesfUp = plotParabola(channel,var,DM,year,indir=indir,breakdown=breakdown1,tag=tag,fit=fit,asymm=asymmetric,ctext=ctext)
                tes,tesDown,tesUp,tesf,tesfDown,tesfUp = plotParabola(channel,var,DM,year,indir=indir,breakdown=breakdown2,tag=tag,plottag='_shapes',fit=fit,asymm=asymmetric,ctext=ctext)
                tes,tesDown,tesUp,tesf,tesfDown,tesfUp = plotParabola(channel,var,DM,year,indir=indir,breakdown=breakdown3,tag=tag,plottag='_norms',fit=fit,asymm=asymmetric,ctext=ctext)
              else:
                tes,tesDown,tesUp,tesf,tesfDown,tesfUp = plotParabola(channel,var,DM,year,indir=indir,tag=tag,fit=fit,asymm=asymmetric,MDFslices=slices,ctext=ctext)
              
              # SAVE points
              if len(points)<=i: points.append([ ]); points_fit.append([ ])
              points[i].append((tes,tesDown,tesUp))
              points_fit[i].append((tesf,tesfDown,tesfUp))
          
          if len(points)>1 and len(DMs)>2 and not breakdown:
            print green("write results to file",pre="\n>>> ")
            #DMs1 = DMs if ("newDM" in tag or "DeepTau" in tag) else DMs[:3]
            filename = "%s/measurement_tes_%s%s"%(outdir,channel,tag)
            writeMeasurement(filename,DMs,points)
            if args.fit:
              writeMeasurement(filename+fittag,DMs,points_fit)
    
    # SUMMARY plot
    if summary:
      for tag in tags:
        tag += args.extratag
        #if 'newDM' in tag: continue
        for channel in channels:
          if len(vars)==2 and len(DMs)>=3:
            print green("make summary plot for %s"%(tag),pre="\n>>> ")
            ftags = [ tag, tag+fittag ] if args.fit else [ tag ]
            for ftag in ftags:
              canvas = "%s/measurement_tes_%s%s"%(outdir,channel,ftag)
              measurements = readMeasurement(canvas)
              ###if "_0p" in tag: # add m_vis from measurement tagged without "_0p05"
              ###  canvas2 = re.sub(r"_0p\d+","",canvas)
              ###  measurements2 = readMeasurement(canvas2)
              ###  for points,points2 in zip(measurements,measurements2):
              ###    points.append(points2[1])
              ###if "_100" in tag: # add m_2 from measurement tagged with "_0p05"
              ###  canvas2 = re.sub(r"_[12]00(?:[_-][5-8])?","",canvas)
              ###  measurements2 = readMeasurement(canvas2)
              ###  for points, points2 in zip(measurements,measurements2):
              ###    points = points.insert(0,points2[0])
              canvas = "%s/measurement_tes_%s%s"%(outdir,channel,insertBinning(ftag)) # rename
              
              ctext = tagToSelection(tag)
              plotMeasurements(cats,measurements,canvas=canvas,xtitle="tau energy scale",xmin=0.97,xmax=1.04,L=0.20,
                               position="out",entries=entries,emargin=0.14,ctext=ctext,ctextsize=0.035,cposition='topright',exts=['png','pdf'])
    
    # CUSTOMARY summary plot
    if customSummary and len(vars)==2 and len(DMs)>=3:
      for ctag in customSummary:
        print green("make customary summary plots for %s"%(ctag),pre="\n>>> ")
        channel = 'mt'
        newDM   = "newDM" in ctag or "DeepTau" in ctag
        DMtag   = "_newDM" if "newDM" in ctag else ""
        DMs     = [ 'DM0', 'DM1', 'DM10', 'DM11' ] if "newDM" in ctag else [ 'DM0', 'DM1', 'DM10',]
        cats    = [varlabel[d] for d in DMs]
        ftags   = [ "", fittag  ] if args.fit else [ "" ]
        mtaubintag = "_0p04" if "0p04" in ctag else "_0p10" if "0p10" in ctag else "_0p05" if "0p05" in ctag else "_0p10"
        mvisbintag = "_45-5" if "45-5" in ctag else "_45-7" if "45-7" in ctag else ""
        for ftag in ftags:
          canvas  = "%s/measurement_tes_%s%s%s%s%s%s"%(outdir,channel,"_differentCuts",DMtag,mtaubintag,mvisbintag,ftag)
          canvas1 = "%s/measurement_tes_%s%s%s%s%s"%(outdir,channel,"_mtlt50",DMtag,mtaubintag,ftag)
          canvas2 = "%s/measurement_tes_%s%s%s%s%s"%(outdir,channel,"_ZTTregion2",DMtag,mvisbintag,ftag)
          ensureFile(canvas1+'.txt')
          ensureFile(canvas2+'.txt')
          measurements1 = readMeasurement(canvas1) # m_2
          measurements2 = readMeasurement(canvas2) # m_vis
          
          # CHECK
          if len(measurements1)<3:
            error('Cannot make measurement summary plot with different cuts: "%s.txt" does not have enough measurements! '%(canvas1))
          if len(measurements2)<3 or any(len(m)<1 for m in measurements2):
            error('Cannot make measurement summary plot with different cuts: "%s.txt" does not have enough measurements !'%(canvas2))
          
          measurements = [ ]
          for points1, points2 in zip(measurements1,measurements2): # loop over DMs
            points = [points1[0],points2[-1]]
            measurements.append(points)
          writeMeasurement(canvas,DMs,measurements)
          ctext = tagToSelection("differentCuts"+mvisbintag)
          plotMeasurements(cats,measurements,xtitle="tau energy scale",xmin=0.97,xmax=1.04,L=0.17,
                               position="out",entries=entries,emargin=0.14,ctext=ctext,ctextsize=0.035,cposition='topright',canvas=canvas,exts=['png','pdf'])
    
#     # CUSTOMARY summary plot to compare selections
#     if len(vars)>0 and len(DMs)>=3:
#       print green("compare selections/binning in customary summary plot",pre="\n>>> ")
#       channel  = "mt"
#       ftags    = [ "", fittag  ] if args.fit else [ "" ]
#       
#       varAndTags = [
#         ( 'm_2',   [ "_mtlt50", "_mtlt50_0p05", "_mtlt50_0p10" ]),
#         ( 'm_vis', [ "_ZTTregion2_45-5", "_ZTTregion2_45-7" ]),
#       ]
#       
#       for var, stags in varAndTags:
#         if var not in vars: continue
#         
#         if var=='m_2':
#           DMs   = [ 'DM1', 'DM10' ]
#           index = 0
#           ctext = tagToSelection(stags[0]) + [varlabel[var]]
#         else:
#           DMs   = [ 'DM0', 'DM1', 'DM10' ]
#           index = -1
#           ctext = tagToSelection(stags[0])
#         
#         canvas  = "%s/measurement_tes_%s_%s%s"%(PLOTS_DIR,channel,var,"_compareSelections")
#         entries = ['NLL profile','parabola fit']
#         cats    = [ "%s %s"%(varlabel[dm],tagToBinWidth(var,t)) for dm in DMs for t in stags ]
#         
#         # LOOP over selection tags
#         points  = { dm: {t:[] for t in stags} for dm in DMs }
#         for stag in stags:
#           
#           # LOOP over fit tags
#           for ftag in ftags:
#             canvas1 = "%s/measurement_tes_%s%s%s"%(PLOTS_DIR,channel,stag,ftag)
#             ensureFile(canvas1+'.txt')
#             measurements1 = readMeasurement(canvas1)
#             
#             # CHECK
#             if len(measurements1)<3:
#               error('Cannot make measurement summary plot with different cuts: "%s.txt" does not have enough measurements! '%(canvas1))
#             
#             if var!='m_2':
#               points['DM0'][stag].append(measurements1[0][index])
#             points['DM1'][stag].append(measurements1[1][index])
#             points['DM10'][stag].append(measurements1[2][index])
#           
#         measurements = [points[dm][t] for dm in DMs for t in stags if len(points[dm][t])>0]
#         plotMeasurements(cats,measurements,xtitle="tau energy scale",xmin=0.97,xmax=1.04,L=0.28,W=900,align='right',colors=[kBlack,kRed],
#                              position="out",entries=entries,ctext=ctext,ctextsize=0.035,cposition='topright',canvas=canvas,exts=['png','pdf'])

    
        


if __name__ == '__main__':
    print 
    
    argv = sys.argv
    description = '''Plot parabolas.'''
    parser = ArgumentParser(prog="plotParabola",description=description,epilog="Succes!")
    parser.add_argument('-y', '--year',        dest='year', choices=[2016,2017,2018], type=int, default=2017, action='store',
                                               help="select year")
    parser.add_argument('-c', '--channel',     dest='channels', choices=['mt','et'], type=str, default=['mt'], action='store',
                                               help="select channel")
    parser.add_argument('-t', '--tag',         dest='tags', type=str, nargs='+', default=[ ], action='store',
                        metavar='TAGS',        help="tags for the input file")
    parser.add_argument('-d', '--decayMode',   dest='DMs', type=str, nargs='+', default=[ ], action='store',
                        metavar='DECAY',       help="decay mode")
    parser.add_argument('-e', '--extra-tag',   dest='extratag', type=str, default="", action='store',
                        metavar='TAG',         help="extra tag for output files")
    parser.add_argument('-o', '--obs',         dest='observables', type=str, nargs='+', default=[ ], action='store',
                        metavar='VARIABLE',    help="name of observable for TES measurement")
    parser.add_argument('-r', '--shift-range', dest='shiftRange', type=str, default="0.940,1.060", action='store',
                        metavar='RANGE',       help="range of TES shifts")
    parser.add_argument('-f', '--fit',         dest='fit',  default=True, action='store_true',
                                               help="fit NLL profile with parametrized parabola")
    parser.add_argument('-a', '--asymm',       dest='asymm',  default=True, action='store_true',
                                               help="fit asymmetric parabola")
    parser.add_argument('-b', '--breakdown',   dest='breakdown',  default=False, action='store_true',
                                               help="plot breakdown of NLL profile")
    parser.add_argument('-M', '--multiDimFit', dest='multiDimFit',  default=False, action='store_true',
                                               help="assume multidimensional fit with a POI for each DM")
    parser.add_argument('-n', '--no-para',     dest='parabola', default=True, action='store_false',
                                               help="make summary of measurements")
    parser.add_argument('-s', '--summary',     dest='summary', default=False, action='store_true',
                                               help="make summary of measurements")
    parser.add_argument(      '--custom',      dest='customSummary', nargs='*', default=False, action='store',
                                               help="make custom summary of measurements")
    parser.add_argument('-v', '--verbose',     dest='verbose',  default=False, action='store_true',
                                               help="set verbose")
    args = parser.parse_args()
    
    if isinstance(args.customSummary,list):
      if args.customSummary==[ ]:
        args.customSummary = [ "_0p10" ]
    
    main(args)
    print ">>>\n>>> done\n"
    

