#! /usr/bin/env python
# Author: Izaak Neutelings (January 2018)
# Modification: Oceane Poncet (June 2022)
# Add Plotting regions in config file to specify it
# Add POI parameter (ex: tes, tid_SF) 

import os, sys, re, glob, time
from unittest import result
import numpy, copy
import math
from array import array
from argparse import ArgumentParser
import ROOT; ROOT.PyConfig.IgnoreCommandLineOptions = True
from ROOT import gROOT, gPad, gStyle, TFile, TCanvas, TLegend, TLatex, TF1, TGraph, TGraph2D, TPolyMarker3D, TGraphAsymmErrors, TLine,\
                 kBlack, kBlue, kRed, kGreen, kYellow, kOrange, kMagenta, kTeal, kAzure, TMath
from TauFW.Plotter.sample.utils import CMSStyle
from itertools import combinations
from math import sqrt, log, ceil, floor

import yaml

gROOT.SetBatch(True)
#gROOT.SetBatch(False)
gStyle.SetOptTitle(0)

# CMS style
CMSStyle.setTDRStyle()


def plotParabola(setup,var,region,year,**kwargs):
    print green("plot parabola for %s, %s"%(region, var),pre="\n>>> ")
    
    indir        = kwargs.get('indir',       "output_%s"%year )
    outdir       = indir.replace('output', 'plots') #kwargs.get('outdir',      "plots_%s"%year  )
    tag          = kwargs.get('tag',         ""               )
    plottag      = kwargs.get('plottag',     ""               )
    MDFslices    = kwargs.get('MDFslices',   None             )
    breakdown    = kwargs.get('breakdown',   { }              )
    asymmetric   = kwargs.get('asymm',       args.asymm       )
    fit          = kwargs.get('fit',         False            ) and not breakdown
    ctext        = kwargs.get('ctext',       [ ]              )
    poi          = kwargs.get('poi',       ""              )
    era          = "%s-13TeV"%year
    channel      = setup["channel"].replace("mu","m").replace("tau","t")
    title = setup["regions"][region]["title"]
    results      = [ ]
    results_up   = [ ]
    results_down = [ ]
    if breakdown: plottag = "_breakdown"+plottag
    if MDFslices: plottag = "_MDF"+plottag
    if fit:       plottag = ("_fit_asymm" if asymmetric else "_fit")+plottag
    canvasname = "%s/parabola_%s_%s_%s-%s%s%s"%(outdir,poi,channel,var,region,tag,plottag)
    ensureDirectory(outdir)


    filename     = '%s/higgsCombine.%s_%s-%s%s-%s.MultiDimFit.mH90.root'%(indir,channel,var,'MDF' if MDFslices else region,tag,era)
    for i, (bdtag,bdtitle) in enumerate(breakdown):
      breakdown[i] = (bdtag, bdtitle,filename.replace("higgsCombine.","higgsCombine.%s-"%bdtag))
    print '>>>   file "%s"'%(filename)
    file = ensureTFile(filename)
    tree = file.Get('limit')
    # GET DeltaNLL
    list_nll = [ ]
    list_poi = [ ]
    if MDFslices:
      poi_name = "%s_%s"%(poi,region)
      MDFslices = { t:v for t,v in MDFslices.iteritems() if t!=poi_name }
      for i, event in enumerate(tree):
        if i==0: continue
        if tree.quantileExpected<0: continue
        if tree.deltaNLL == 0: continue
        if any(abs(getattr(tree,t)-v)>0.000001 for t,v in MDFslices.iteritems()): continue
        list_poi.append(getattr(tree,poi_name))
        list_nll.append(2*tree.deltaNLL)
        #print "NLL = %d" %(2*tree.deltaNLL)#
      list_nll = [n for _,n in sorted(zip(list_poi,list_nll), key=lambda p: p[0])]
      list_poi.sort()
    else:
      for i, event in enumerate(tree):
        if i==0: continue
        if tree.quantileExpected<0: continue
        if tree.deltaNLL == 0: continue
        #if tree.poi < 0.97: continue
        poi_name = "%s_%s"%(poi,region) #combine DM
        #list_poi.append(tree.poi)
        list_poi.append(getattr(tree,poi_name)) #combine DM
        list_nll.append(2*tree.deltaNLL)
        
    file.Close()
    nllmin    = min(list_nll)
    print "nlmin: ", nllmin
    list_dnll = map(lambda n: n-nllmin, list_nll) # DeltaNLL 
    # MINIMUM
    dnllmin         = min(list_dnll) # should be 0.0 by definition
    min_index       = list_dnll.index(dnllmin)
    list_dnll_left  = list_dnll[:min_index]
    list_poi_left   = list_poi[:min_index]
    list_dnll_right = list_dnll[min_index:]
    list_poi_right  = list_poi[min_index:]
    #print ">>> min   = %d , min_index = %d"%(dnllmin, min_index)
    if len(list_dnll_left)==0 or len(list_dnll_right)==0 : 
      print "ERROR! Parabola does not have minimum within given range !!!"
      return 0, 0, 0, 0, 0, 0
      #exit(1)
    tmin_left = -1
    tmin_right = -1
    
    # FIND crossings of 1 sigma line
    # |-----<---min---------|
    for i, val in reversed(list(enumerate(list_dnll_left))):
      if val > (dnllmin+1):
          tmin_left = list_poi_left[i]
          break
    # |---------min--->-----|
    for i, val in enumerate(list_dnll_right):
      if val > (dnllmin+1):
          tmin_right = list_poi_right[i]
          break
    
    poi_val         = round(list_poi[min_index],4)
    poi_errDown = round((poi_val-tmin_left)*10000)/10000 if tmin_left != -1 else float('nan')
    poi_errUp   = round((tmin_right-poi_val)*10000)/10000 if tmin_right != -1 else float('nan')
    shift       = (list_poi[min_index]-1)*100
    
    # GRAPHS
    graph       = createParabolaFromLists(list_poi,list_dnll,fit=fit)
    graphs_bd   = [ ]
    colors_bd   = [kRed, kBlue, kGreen]
    poi_bbb, poi_stat = -1., -1.
    for i, (tag_bd, title_bd, filename_bd) in enumerate(breakdown):
      print '>>>   file "%s" (breakdown)'%(filename_bd)
      graph_bd, poi_bd = createParabola(filename_bd, poi, region)
      graph_bd.SetMarkerColor(colors_bd[i])
      graph_bd.SetLineColor(colors_bd[i])
      graph_bd.SetLineWidth(2)
      graph_bd.SetLineStyle(1)
      graph_bd.SetMarkerStyle(20)
      graph_bd.SetMarkerSize(0.8)
      graph_bd.SetLineWidth(2)
      graph_bd.SetName(tag_bd)
      graph_bd.SetTitle(title_bd)
      breakdown[i] = (graph_bd, poi_bd)
    
    # DRAW
    canvas = TCanvas('canvas','canvas',100,100,700,600)
    canvas.SetFillColor(0)
    canvas.SetBorderMode(0)
    canvas.SetFrameFillStyle(0)
    canvas.SetFrameBorderMode(0)
    canvas.SetTopMargin(  0.07 ); canvas.SetBottomMargin( 0.12 )
    canvas.SetLeftMargin( 0.12 ); canvas.SetRightMargin(  0.04 )
    canvas.cd()
    
    if poi == 'tid_SF' or poi == 'trackedParam_tid_SF':
          xmin, xmax = 0.55, 1.5
    if poi == 'tes' :
          xmin, xmax = min(setup["TESvariations"]["values"])-0.05, max(setup["TESvariations"]["values"])+0.05
    ymin, ymax   = 0.0,  10.
    fontsize     = 0.044
    lineheight   = 0.05
    xtext, ytext = 0.90, 0.405
    if poi == 'tid_SF' or poi == 'trackedParam_tid_SF':
      title = "tau id scale factor"
    elif poi == 'tes':
      title = "tau energy scale"
    else:
      title = "parameter of interest"
    frame = canvas.DrawFrame(xmin,ymin,xmax,ymax)
    frame.GetYaxis().SetTitleSize(0.055)
    frame.GetXaxis().SetTitleSize(0.055)
    frame.GetXaxis().SetLabelSize(0.050)
    frame.GetYaxis().SetLabelSize(0.050)
    frame.GetXaxis().SetLabelOffset(0.010)
    frame.GetXaxis().SetTitleOffset(1.04)
    frame.GetYaxis().SetTitleOffset(1.02)
    frame.GetXaxis().SetNdivisions(508)
    frame.GetXaxis().SetTitle(title)
    frame.GetYaxis().SetTitle('-2#Deltaln(L)')
    
    # GRAPH
    graph.SetMarkerStyle(20)
    graph.SetMarkerSize(0.8 if breakdown else 0.4)
    graph.Draw('PLXSAME')
    
    # FIT
    para, graph_clone, poif, poif_errDown, poif_errUp = None, None, None, None, None
    if fit:
      para = fitParabola(xmin,xmax,poi_val,list_poi_left,list_dnll_left,list_poi_right,list_dnll_right,asymmetric=asymmetric)
      fit = graph.Fit("fit",'R0')
      para.SetRange(xmin,xmax)
      para.SetLineColor(2)
      para.Draw('SAME')
      gStyle.SetOptFit(0)
      poif = para.GetParameter(1)
      if asymmetric:
        yline = 1+para.GetParameter(2)
        print("yline = " ,yline)
        print("para.GetParameter(1) = " ,para.GetParameter(1))
        poif_errDown = poif-para.GetX(yline,poif-0.05,poif)
        poif_errUp   = para.GetX(yline,poif,poif+0.05)-poif
        if math.isnan(poif_errDown) or math.isnan(poif_errUp):
           delta_poif = 0.05+0.05
           while 1:
             poif_errDown = poif-para.GetX(yline,poif-delta_poif,poif) if math.isnan(poif_errDown) else poif_errDown
             poif_errUp   = para.GetX(yline,poif,poif+delta_poif)-poif if math.isnan(poif_errUp) else poif_errUp
             if math.isnan(poif_errDown) or math.isnan(poif_errUp):
                 delta_poif += 0.05
             else:
                 break
      else:
        poif_errUp   = round( sqrt( 1./(1000.*para.GetParameter(0)) )*10000)/10000 # TODO: propagate fit uncertainties with GetParError(i) !
        poif_errDown = round( sqrt( 1./(1000.*para.GetParameter(0)) )*10000)/10000        

    # print("poi_val = ", poi_val)
    # print("poif = ", poif)
    # print("poi_errDown = ", poi_errDown)
    # print("poi_errUp = ", poi_errUp)
    # print("poif_errDown = ", poif_errDown)
    # print("poif_errUp = ", poif_errUp)

    # print("tmin_right = ", tmin_right)
    # print("tmin_left = ", tmin_left)

    print("shift = ", shift)
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
      for graph_bd, poi_bd in breakdown:
        graph_bd.Draw('PLSAME')
        titles = graph_bd.GetTitle().split('\n')
        legend.AddEntry(graph_bd,titles[0],'lp')
        for line in titles[1:]:
          legend.AddEntry(0,line,'')
      legend.AddEntry(graph,"all syst.",'lp')
      legend.Draw()
    if ctext:
      ctext = writeText(ctext,position='topright',textsize=0.80*fontsize)
    
    print ">>> poi %7.3f - %-5.3f + %-5.3f"%(poi_val,poi_errDown,poi_errUp)
    print ">>> shift  %7.3f - %-5.3f + %-5.3f %%"%(shift,poi_errDown*100,poi_errUp*100)
    if fit:
      print ">>> poi %7.3f - %-5.3f + %-5.3f   (parabola)"%(poif,poif_errDown,poif_errUp)
      print ">>> shift  %7.3f - %-5.3f + %-5.3f %% (parabola)"%(poif-1,poif_errDown*100,poif_errUp*100)
    
    text = TLatex()
    text.SetTextSize(fontsize)
    text.SetTextAlign(31)
    text.SetTextFont(42)
    text.SetNDC(True)
    if "title" in setup["observables"][var]:
        text.DrawLatex(xtext,ytext, "%s"%(setup["observables"][var]["title"]))
    else:
        text.DrawLatex(xtext,ytext, "%s"%(var))
    text.DrawLatex(xtext,ytext-lineheight,     "%s:" %region)
    text.DrawLatex(xtext,ytext-2.2*lineheight,     "%s"%(setup["regions"][region]["title"]))
    text.DrawLatex(xtext,ytext-4.4*lineheight, "%7.3f_{-%5.3f}^{+%5.3f}"%(poi_val,poi_errDown,poi_errUp))
    if fit:
      text.SetTextColor(kRed)
      text.DrawLatex(xtext,ytext-3.5*lineheight, "%7.3f_{-%5.3f}^{+%5.3f}"%(poif,poif_errDown,poif_errUp))
    for i, (graph_bd, poi_bd) in enumerate(breakdown):
      text.SetTextColor(graph_bd.GetLineColor())
      text.DrawLatex(xtext,ytext-(i+3.5)*lineheight, "%7.3f"%(poi_bd))
    
    CMSStyle.setCMSLumiStyle(canvas,0)
    #canvas.SetTicks(1,1)
    canvas.SetGrid()
    canvas.Modified()
    canvas.Update()
    canvas.SaveAs(canvasname+".png")
    canvas.SaveAs(canvasname+".pdf")
    canvas.Close()

    return poi_val, poi_errDown, poi_errUp, poif, poif_errDown, poif_errUp
    

    
def plotParabolaMDF(setup,var,year,**kwargs):
    """Plot multidimensional parabola."""
    print green("plot multidimensional parabola for %s"%(var),pre="\n>>> ")
    
    indir      = kwargs.get('indir',      "output_%s"%year )
    outdir     = kwargs.get('outdir',     "plots_%s"%year  )
    poi          = kwargs.get('poi',       ""              )
    tag        = kwargs.get('tag',        ""               )
    nnlmin     = kwargs.get('nnlmin',     0                )
    MDFslices  = kwargs.get('MDFslices', { }               )
    era        = "%s-13TeV"%year
    ensureDirectory(outdir)
    
    channel    = setup["channel"].replace("mu","m").replace("tau","t")

    canvasname = "%s/parabola_poi_%s_%s-%s%s"%(outdir,channel,var,"MDF",tag)
    filename   = '%s/higgsCombine.%s_%s-%s%s-%s.MultiDimFit.mH90.root'%(indir,channel,var,'MDF',tag,era)
    file       = ensureTFile(filename)
    tree       = file.Get('limit')
    ztitle     = "-2#Deltaln(L)"
    pois       = [b.GetName() for b in tree.GetListOfBranches() if 'poi_DM' in b.GetName()]
    # pmin, pmax = 0.97, 1.03
    pmin, pmax = 0.7, 1.1

    for poi1, poi2 in combinations(pois,2):
      
      if len(pois)>2:
        canvasname = "plots_%s/parabola_poi_%s_%s-%s_%s-%s%s"%(year,channel,var,"MDF",poi1,poi2,tag)
        canvasname = canvasname.replace('poi_DM','DM')
      
      graph = TGraph2D()
      graph.SetTitle(ztitle)
      #tree.Draw("%s:%s:deltaNLL >> graph"%(poi1,poi2),"","COLZ")
      slices = { t:v for t,v in MDFslices.iteritems() if t!=poi1 and t!=poi2 }
      #\print nnlmin, slices
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
      graph.SetMaximum(1)
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
      
      CMSStyle.setCMSLumiStyle(canvas,0)
      gPad.Modified()
      gPad.Update()
      gPad.RedrawAxis()
      
      canvas.SaveAs(canvasname+'.png')
      canvas.SaveAs(canvasname+'.pdf')
      canvas.Close()
    


def fitParabola(xmin,xmax,poi,list_poi_left,list_dnll_left,list_poi_right,list_dnll_right,asymmetric=False):
    
    # FIT X RANGE (<ymax)
    xmin_fit = xmin
    xmax_fit = xmax
    ymax_fit = 5
    ymax_left  = min(ymax_fit,max(list_dnll_left))
    ymax_right = min(ymax_fit,max(list_dnll_right))
    # |-->---|----min----|------|
    for i, val in enumerate(list_dnll_left):
      if val <= (ymax_left):
        xmin_fit = round(list_poi_left[i],4)
        print ">>> xmin_fit = %.3f (%2d,%3.1f) is below NLL %.1f"%(xmin_fit,val,i,ymax_left)
        break
    # |------|----min----|---<--|
    for i, val in reversed(list(enumerate(list_dnll_right))):
      if val <= (ymax_right):
        xmax_fit = round(list_poi_right[i],4)
        print ">>> xmax_fit = %.3f (%2d,%3.1f) is below NLL %.1f"%(xmax_fit,val,i,ymax_right)
        break
    # FIT MAX WIDTH
    bmid     = (xmax_fit+xmin_fit)/2.
    dtmin    = max(poi-xmin_fit,0.004)
    dtmax    = max(xmax_fit-poi,0.004)
    tmin_fit = poi-abs(dtmin)*0.26
    tmax_fit = poi+abs(dtmax)*0.26
    wmin_fit, wmax_fit = sorted([ymax_left/(1000.*(dtmin**2)),ymax_right/(1000.*(dtmax**2))])
    #print ">>> poi=%.3f, tmin_fit=%.3f, tmin_fit=%.3f, bmid=xmin_fit+(xmax_fit-xmin_fit)/2=%.3f"%(poi,tmin_fit,tmax_fit,bmid)
    #print ">>> wmin_fit=%.3f, wmax_fit=%.3f"%(wmin_fit,wmax_fit)
    # print("wmin_fit = ", wmin_fit)
    # print("wmax_fit = ", wmax_fit)

    # FIT Y RANGE (<ymax)
    #ymax_fit = 0.5
    
    # FIT PARAMETERS
    wmin, wval, wmax = wmin_fit*0.20, wmin_fit, wmax_fit*1.80
    wmin_fit = 0
    wmax_fit = 50
    print("wmin_fit = ", wmin_fit)
    print("wmax_fit = ", wmax_fit)
    bmin, bval, bmax = tmin_fit, poi, tmax_fit
    cmin, cval, cmax = -0.0001, 0.0, 0.5 #max(min(ymax_fit,3),0.001)
    amin, aval, amax = -1000, 0.0, 1000
    
    if bmin<xmin_fit: print ">>> Warning! setting bmin=%.3f -> %.3f=xmin_fit"%(bmin,xmin_fit); bmin = xmin_fit
    if bmax>xmax_fit: print ">>> Warning! setting bmin=%.3f -> %.3f=xmin_fit"%(bmax,xmax_fit); bmax = xmax_fit
    if bval<bmin or bmax<bval: print ">>> Warning! setting bval=%.3f -> %.3f=bmin+(bmin-bmax)/2"%(bval,(bmax+bmin)/2.); bval = (bmax+bmin)/2.
    if cval<cmin or cmax<cval: print ">>> Warning! setting cval=%.3f -> %.3f=cmin+(cmin-cmax)/2"%(cval,(cmax+cmin)/2.); cval = (cmax+cmin)/2.
    print ">>> width   = %5g [%5s, %5s]"%(wval,wmin,wmax)
    print ">>> poi     = %5s [%5s, %5s]"%(bval,bmin,bmax)
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
    para.SetParName(1,"poi")
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
    

def createParabolaFromLists(list_poi,list_dnll,fit=False):
    """Create TGraph of DeltaNLL parabola vs. poi from lists."""
    npoints = len(list_dnll)
    if not fit: return TGraph(npoints, array('d',list_poi), array('d',list_dnll))
    graph  = TGraphAsymmErrors()
    for i, (poi,dnll) in enumerate(zip(list_poi,list_dnll)):
      error = 1.0
      if dnll<6 and i>0 and i+1<npoints:
        left, right = list_dnll[i-1], list_dnll[i+1]
        error       = max(0.1,(abs(dnll-left)+abs(right-dnll))/2)
      graph.SetPoint(i,poi,dnll)
      graph.SetPointError(i,0.0,0.0,error,error)
    return graph
    
def createParabola(filename, poi, region):
    """Create TGraph of DeltaNLL parabola vs. poi from MultiDimFit file."""
    file = ensureTFile(filename)
    tree = file.Get('limit')
    poi, nll = [ ], [ ]
    for i, event in enumerate(tree):
      if i==0: continue
      #poi.append(tree.poi)
      poi_name = "%s_%s"%(poi,region) #combine DM 
      poi.append(getattr(tree,poi_name)) #combine DM
      nll.append(2*tree.deltaNLL)
    file.Close()
    minnll = min(nll)
    minpoi = poi[nll.index(minnll)]
    dnll   = map(lambda x: x-minnll, nll) # DeltaNLL
    graph  = TGraph(len(poi), array('d',poi), array('d',dnll))
    return graph, minpoi
    
def findMultiDimSlices(channel,var,**kwargs):
    """Find minimum of multidimensional parabola in MultiDimFit file and return
    dictionary of the corresponding values of POI's."""
    year     = kwargs.get('year', "")
    tag      = kwargs.get('tag', "" )
    indir    = kwargs.get('indir',       "output_%s"%year )
    filename = '%s/higgsCombine.%s_%s-%s%s-%s-13TeV.MultiDimFit.mH90.root'%(indir,channel,var,'MDF',tag,year)
    file     = ensureTFile(filename)
    tree     = file.Get('limit')
    pois     = [b.GetName() for b in tree.GetListOfBranches() if 'poi_DM' in b.GetName()]
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
    


def measurepoi(filename,poi,region,unc=False,fit=False,asymmetric=True,**kwargs):
    #region = kwargs.get('scanRegions', "")

    """Create TGraph of DeltaNLL parabola vs. poi from MultiDimFit file."""
    if fit:
       return measurepoi_fit(filename,poi=poi,region=region,asymmetric=asymmetric,unc=unc)
    file = ensureTFile(filename)
    tree = file.Get('limit')
    poi_list, nll = [ ], [ ]
    for event in tree:
      poiname = "%s_%s"%(poi,region) #combine DM
      poi_list.append(getattr(tree,poiname)) #combine DM
      #poi.append(tree.poi)
      nll.append(2*tree.deltaNLL)
    file.Close()
    nllmin = min(nll)
    imin   = nll.index(nllmin)
    poimin = poi_list[imin]
    if unc:
      nll_left  = nll[:imin]
      poi_left  = poi_list[:imin]
      nll_right = nll[imin:]
      poi_right = poi_list[imin:]
      if len(nll_left)==0 or len(nll_right)==0 : 
        print "ERROR! measurepoi: Parabola does not have a minimum within given range!"
        exit(1)
      tmin_left = -1
      tmin_right = -1
      
      # FIND crossings of 1 sigma line
      # |-----<---min---------|
      for i, val in reversed(list(enumerate(nll_left))):
        if val > (nllmin+1):
          tmin_left = poi_left[i]
          break
      # |---------min--->-----|
      for i, val in enumerate(nll_right):
        if val > (nllmin+1):
          tmin_right = poi_right[i]
          break
      
      poi_errDown = poimin-tmin_left
      poi_errUp   = tmin_right-poimin
      return poimin, poi_errDown, poi_errUp
    
    return poimin
    


def measurepoi_fit(filename,poi,region,asymmetric=True,unc=False):
    """Create TGraph of DeltaNLL parabola vs. poi from MultiDimFit file."""
    file = ensureTFile(filename)
    tree = file.Get('limit')
    xmin, xmax = 0.945, 1.08
    ymin, ymax = 0.0,  10.
    
    # GET DeltaNLL
    list_nll = [ ]
    list_poi = [ ]
    for i, event in enumerate(tree):
      if i==0: continue
      if tree.quantileExpected<0: continue
      if tree.deltaNLL==0: continue
      #list_poi.append(tree.poi)
      poi_name = "%s_%s"%(poi,region) #combine DM
      list_poi.append(getattr(tree,poi_name)) #combine DM
      list_nll.append(2*tree.deltaNLL)
    file.Close()
    nllmin    = min(list_nll)
    list_dnll = map(lambda n: n-nllmin, list_nll) # DeltaNLL
    
    # MINIMUM
    dnllmin         = min(list_dnll) # should be 0.0 by definition
    min_index       = list_dnll.index(dnllmin)
    list_dnll_left  = list_dnll[:min_index]
    list_poi_left   = list_poi[:min_index]
    list_dnll_right = list_dnll[min_index:]
    list_poi_right  = list_poi[min_index:]
    if len(list_dnll_left)==0 or len(list_dnll_right)==0 : 
      print "ERROR! Parabola does not have minimum within given range !!!"
      exit(1)
    tmin_left = -1
    tmin_right = -1
    
    # FIND crossings of 1 sigma line
    # |-----<---min---------|
    for i, val in reversed(list(enumerate(list_dnll_left))):
      if val > (dnllmin+1):
          tmin_left = list_poi_left[i]
          break
    # |---------min--->-----|
    for i, val in enumerate(list_dnll_right):
      if val > (dnllmin+1):
          tmin_right = list_poi_right[i]
          break
    
    poi   = round(list_poi[min_index],4)
    graph = createParabolaFromLists(list_poi,list_dnll,fit=True)
    para  = fitParabola(xmin,xmax,poi,list_poi_left,list_dnll_left,list_poi_right,list_dnll_right,asymmetric=asymmetric)
    fit   = graph.Fit("fit",'R0')
    poif  = para.GetParameter(1)
    if unc:
      if asymmetric:
        yline = 1+para.GetParameter(2)
        poif_errDown = poif-para.GetX(yline,poif-0.02,poif)
        poif_errUp   = para.GetX(yline,poif,poif+0.02)-poif
      else:
        poif_errUp   = round( sqrt( 1./(1000.*para.GetParameter(0)) )*10000)/10000 # TODO: propagate fit uncertainties with GetParError(i) !
        poif_errDown = round( sqrt( 1./(1000.*para.GetParameter(0)) )*10000)/10000  
      return poif, poif_errDown, poif_errUp
    
    return poif
    

def plotMeasurements(setup, measurements,binsOrder,**kwargs):
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
    minB         = 0.13
    colors       = [ kBlack, kBlue, kRed, kOrange, kGreen, kMagenta ]
    poi          = kwargs.get('poi',          ""                  )
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
    for i,name in enumerate(binsOrder):
      points = measurements[name]
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
    for i, name in enumerate(binsOrder):
      ytext = i+0.5

      if poi == 'tes':
        text = setup["tesRegions"][name]["title"] if "title" in setup["tesRegions"][name] else name
      elif poi == 'tid_SF' or poi == 'trackedParam_tid_SF':
        text = setup["tid_SFRegions"][name]["title"] if "title" in setup["tid_SFRegions"][name] else name
      else:
        text = setup["regions"][name]["title"] if "title" in setup["regions"][name] else name     
      latex.DrawLatex(xtext,ytext,text)
    
    CMSStyle.setCMSLumiStyle(canvas,0)
    CMSStyle.cmsTextSize  = 0.85
    CMSStyle.lumiTextSize = 0.80
    CMSStyle.relPosX      = 0.13*800*0.76/(1.-canvasL-canvasR)/canvasW
    
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

def writeMeasurement_Json(setup,filename,categories,measurements,**kwargs):
    """Write measurements to file."""
    if ".json" not in filename[-4]: filename += ".json"
    mformat = kwargs.get('format',"fit_value: %10.4f down_variation: %10.4f up variation:%10.4f") #" %10.6g %10.6g %10.6g"
    sformat = re.sub(r"%(\d*).?\d*[a-z]",r"%\1s",mformat)
    with open(filename,'w+') as file:
      print ">>>   created txt file %s"%(filename)
      baselineCuts = setup["baselineCuts"]
      #startdate = time.strftime("%a %d/%m/%Y %H:%M:%S",time.gmtime())
      file.write("\"baselineCuts = %s\"\n"%(baselineCuts))
      for category, points in zip(categories,measurements):
        for region in setup["regions"]:
          if category == region:
            print("category = ", category)
            print("region = ", region)
            region_def = setup["regions"][region]["definition"]
            file.write("\"%s: %-10s\""%(category,region_def))
            for point in points:
              if point:
                file.write(mformat%point)
              else:
                file.write(sformat%("-","-","-"))
            file.write('\n')

def readMeasurement(filename,**kwargs):
    """Read measurements from file."""
    if ".txt" not in filename[-4]: filename += ".txt"
    measurements = dict()
    with open(filename,'r') as file:
      print ">>>   reading txt file %s"%(filename)
      startdate = time.strftime("%a %d/%m/%Y %H:%M:%S",time.gmtime())
      file.next()
      for line in file:
        points  = [ ]
        columns = line.split()
        i = 1
        while len(columns[i:])>=3:
          try:
            points.append((float(columns[i]),float(columns[i+1]),float(columns[i+2])))
          except ValueError:
            points.append(None)
          i += 3
        measurements[columns[0]] = points
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



def main(args):
    
    print "Using configuration file: %s"%args.config
    with open(args.config, 'r') as file:
        setup = yaml.safe_load(file)

    channel       = setup["channel"].replace("mu","m").replace("tau","t")
    tag           = setup["tag"] if "tag" in setup else ""

    verbosity     = args.verbose
    poi           = args.poi
    year          = args.year
    lumi          = 36.5 if year=='2016' else 41.4 if (year=='2017' or year=='UL2017') else 59.5 if (year=='2018' or year=='UL2018') else 19.5 if year=='UL2016_preVFP' else 16.8
    indir         = args.indir
    outdir        = indir.replace('output', 'plots')
    breakdown     = args.breakdown
    multiDimFit   = args.multiDimFit
    summary       = args.summary
    parabola      = args.parabola
    fit           = args.fit
    asymmetric    = args.asymm
    customSummary = args.customSummary
    ensureDirectory(outdir)

    CMSStyle.setCMSEra(year)
    
    fittag  = "_fit_asymm" if asymmetric else "_fit"
    tag += args.extratag
    
    # LOOP over tags, channels, variables
    print "parabola %i"%parabola
    if parabola:
        points, points_fit = [ ], [ ]

        allObs = []
        allObsTitles = []
        allRegions = []
        for v in setup["observables"]:
            print v
            var = setup["observables"][v]
            if not v in allObs:
                allObs.append(v)
                if "title" in var:
                    allObsTitles.append(var["title"])
                else:
                    allObsTitles.append(v)
        for r in setup["plottingOrder"]:
            print r
            isUsedInFit = False #change to true
            for v in setup["observables"]:
                if r in setup["observables"][v]["scanRegions"]:
                    isUsedInFit = True
                    break
            if isUsedInFit and not r in allRegions:
                allRegions.append(r)
        for var in setup["observables"]:
            variable = setup["observables"][var]
            
            # MULTIDIMFIT
            slices = { }
            if multiDimFit:
                nnlmin, slices = findMultiDimSlices(channel,var,year=year,tag=tag)
                plotParabolaMDF(setup,var,year,nnlmin=nnlmin,MDFslices=slices,indir=indir,tag=tag,poi=poi)
            
            print allRegions
            # LOOP over regions
            for i, region in enumerate(allRegions):
                if not region in variable["scanRegions"]:
                    if len(points)<=i: points.append([ ]); points_fit.append([ ])
                    points[i].append(None); points_fit[i].append(None)
                    continue
      
                # PARABOLA
                if breakdown:
                    breakdown1 = [ ('stat', "stat. only,\nexcl. b.b.b."), ('sys', "stat. only\nincl. b.b.b.") ]
                    breakdown2 = [ ('jtf', "j #rightarrow #tau_{h} fake"), ('ltf', "l #rightarrow #tau_{h} fake"), ('zpt', "Z pT rew.") ]
                    breakdown3 = [ ('eff', "#mu, #tau_{h} eff."), ('norm', "xsecs, norms"), ('lumi', "lumi") ]
                    poi_val,poiDown,poiUp,poif,poifDown,poifUp = plotParabola(setup,var,region,year,indir=indir,breakdown=breakdown1,tag=tag,fit=fit,asymm=asymmetric, poi=poi)
                    poi_val,poiDown,poiUp,poif,poifDown,poifUp = plotParabola(setup,var,region,year,indir=indir,breakdown=breakdown2,tag=tag,plottag='_shapes',fit=fit,asymm=asymmetric,poi=poi)
                    poi_val,poiDown,poiUp,poif,poifDown,poifUp = plotParabola(setup,var,region,year,indir=indir,breakdown=breakdown3,tag=tag,plottag='_norms',fit=fit,asymm=asymmetric,poi=poi)
                else:
                    poi_val,poiDown,poiUp,poif,poifDown,poifUp = plotParabola(setup,var,region,year,indir=indir,tag=tag,fit=fit,asymm=asymmetric,MDFslices=slices,poi=poi)
                #if poi_val == poiDown == poiUp == poif == poifDown == poifUp == 0: continue
                # SAVE points
                if len(points)<=i: points.append([ ]); points_fit.append([ ])
                points[i].append((poi_val,poiDown,poiUp))
                points_fit[i].append((poif,poifDown,poifUp))
          
            if len(points)>1 and not breakdown:
                print green("write results to file",pre="\n>>> ")
                filename = "%s/measurement_%s_%s%s"%(outdir,poi,channel,tag)
                writeMeasurement(filename,allRegions,points)
                writeMeasurement_Json(setup,filename,allRegions,points)
            if args.fit:
                filename = "%s/measurement_%s_%s%s"%(outdir,poi,channel,tag)
                writeMeasurement(filename+fittag,allRegions,points_fit)
                writeMeasurement_Json(setup,filename+fittag,allRegions,points_fit)
    
    # SUMMARY plot
    if summary:
        print green("make summary plot for %s"%(tag),pre="\n>>> ")
        ftags = [ tag, tag+fittag ] if args.fit else [ tag ]
        for ftag in ftags:
            canvas = "%s/measurement_%s_%s%s"%(outdir,poi,channel,ftag)
            measurements = readMeasurement(canvas)

            if poi == 'tid_SF' or poi == 'trackedParam_tid_SF':
              plotMeasurements(setup, measurements, (setup["plottingOrder"] if "plottingOrder" in setup else allRegions) ,canvas=canvas,xtitle="tau id scale factor",xmin=0.55,xmax=1.05,L=0.20, position="out",entries=allObsTitles,emargin=0.14,cposition='topright',exts=['png','pdf'], poi=poi)
            #defaut case = tes 
            elif poi == 'tes':
              plotMeasurements(setup, measurements, (setup["plottingOrder"] if "plottingOrder" in setup else allRegions) ,canvas=canvas,xtitle="tau energy scale",xmin=min(setup["TESvariations"]["values"]),xmax=max(setup["TESvariations"]["values"]),L=0.20, position="out",entries=allObsTitles,emargin=0.14,cposition='topright',exts=['png','pdf'], poi=poi)
            else:
              plotMeasurements(setup, measurements, (setup["plottingOrder"] if "plottingOrder" in setup else allRegions) ,canvas=canvas,xtitle="tau energy scale",xmin=min(setup["TESvariations"]["values"]),xmax=max(setup["TESvariations"]["values"]),L=0.20, position="out",entries=allObsTitles,emargin=0.14,cposition='topright',exts=['png','pdf'], poi=poi)

            #plotidSF_pt(setup, measurements, (setup["plottingOrder"] if "plottingOrder" in setup else allRegions),xtitle="tau id scale factor",xmin=0.7,xmax=1.05,L=0.20, position="out",entries=allObsTitles,emargin=0.14,cposition='topright',exts=['png','pdf'], poi=poi)

       


if __name__ == '__main__':
    print 
    
    argv = sys.argv
    description = '''Plot parabolas.'''
    parser = ArgumentParser(prog="plotParabola",description=description,epilog="Succes!")
    parser.add_argument('-y', '--year',        dest='year', choices=['2016','2017','2018','UL2016_preVFP','UL2016_postVFP','UL2017','UL2018', 'UL2018_v10','2022_postEE','2022_preEE', '2023C', '2023D'], type=str, default='2017', action='store', help="select year")
    parser.add_argument('-c', '--config', dest='config', type=str, default='TauES/config/defaultFitSetuppoi_mutau.yml', action='store', help="set config file containing sample & fit setup" )
    parser.add_argument('-e', '--extra-tag',   dest='extratag', type=str, default="", action='store', metavar='TAG', help="extra tag for output files")
    parser.add_argument('-r', '--shift-range', dest='shiftRange', type=str, default="0.940,1.060", action='store', metavar='RANGE',       help="range of poi shifts")
    parser.add_argument('-f', '--fit',         dest='fit',  default=True, action='store_true', help="fit NLL profile with parametrized parabola")
    parser.add_argument('-a', '--asymm',       dest='asymm',  default=True, action='store_true', help="fit asymmetric parabola")
    parser.add_argument('-b', '--breakdown',   dest='breakdown',  default=False, action='store_true', help="plot breakdown of NLL profile")
    parser.add_argument('-M', '--multiDimFit', dest='multiDimFit',  default=False, action='store_true', help="assume multidimensional fit with a POI for each DM")
    parser.add_argument('-n', '--no-para',     dest='parabola', default=True, action='store_false', help="make summary of measurements")
    parser.add_argument('-s', '--summary',     dest='summary', default=False, action='store_true', help="make summary of measurements")
    parser.add_argument(      '--custom',      dest='customSummary', nargs='*', default=False, action='store',help="make custom summary of measurements")
    parser.add_argument('-v', '--verbose',     dest='verbose',  default=False, action='store_true', help="set verbose")
    parser.add_argument('-p', '--poi',         dest='poi', default='poi', type=str, action='store', help='use this parameter of interest')
    parser.add_argument('-i', '--indir',         dest='indir', type=str, help='indir')

    args = parser.parse_args()
    
    main(args)
    print ">>>\n>>> done\n"
    

