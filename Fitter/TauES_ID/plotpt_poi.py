#! /usr/bin/env python
"""
Date : February 2023 
Author : @oponcet 
Description : 
This script makes plot of pt-dependants summary plots of the results of the POI (tes or tid_SF) with DM inclusif 
bins or not (with --dm-bins option). This script use the txt output file of plotParabola_POI_region.py to produce the plots.
The valuesof the mean of the pt bin and its std dev need to be change in the fit. This values can be obtained using
./Plotter/get_ptmean.py (need pt plots of the distribution).
"""
import ROOT
import os, sys,yaml
from array import array
from argparse import ArgumentParser
from collections import OrderedDict
from ROOT import gROOT, gPad, gStyle, Double, TFile, TCanvas, TLegend, TLatex, TF1, TGraph, TGraph2D, TPolyMarker3D, TGraphAsymmErrors, TLine,\
                 kBlack, kBlue, kRed, kGreen, kYellow, kOrange, kMagenta, kTeal, kAzure, TMath
from TauFW.Plotter.sample.utils import CMSStyle



def load_pt_values(setup,**kwargs):
    poi          = kwargs.get('poi',       ""              )
    pt_avg_list = []
    pt_error_list  = []
    bins_order = setup["plottingOrder"]
    for ibin, ptregion in enumerate(bins_order):
        # print("region = %s" %(ptregion))
        if poi == 'tes': 
          print(poi)
          title = setup["tesRegions"][ptregion]["title"]
        else:
          title = setup["tid_SFRegions"][ptregion]["title"]
        
        str_pt_lo = title.split("<")[0].split(" ")[-1]
        str_pt_hi = title.split("<")[-1].split(" ")[0]
        pt_hi = float(str_pt_hi)
        pt_lo = float(str_pt_lo)
        #pt_avg = (pt_hi + pt_lo) / 2.0
        #pt_error = pt_avg - pt_lo
        # pt_avg_list.append(pt_avg)
        #pt_avg_list = [28,54,28,53,30,52,31,53] 
        #pt_error_list.append(pt_error)
        # print("pt average = %f and pt error = %s" %(pt_avg, pt_error))

        # Obtained with get_ptmean.py 2 pt region
        # pt_avg_list = [28, 54, 28, 53, 30, 52, 31, 53]
        # pt_error_list = [5, 21, 5, 19, 5, 18, 5, 20]

        # # 9 pt regions
        # pt_avg_list = [22, 27, 32, 37, 43, 54, 68, 88, 130, 22, 27, 32, 37, 43, 54, 67, 88, 128, 22, 27, 32, 37, 43, 53, 68, 88, 127, 22, 27, 32, 37, 44, 53, 68, 88, 128]
        # pt_error_list = [1, 1, 1, 1, 2, 2, 5, 5, 24, 1, 1, 1, 1, 2, 2, 5, 5, 24, 1, 1, 1, 1, 2, 2, 5, 5, 22, 1, 1, 1, 1, 2, 2, 5, 5, 23]

        # # 3 pt regions
        pt_avg_list = [26, 39, 64, 27, 39, 61, 28, 39, 61, 28, 39, 61]
        pt_error_list = [4, 2, 25, 4, 2, 22, 4, 2, 21, 3, 2, 23]

    return pt_avg_list, pt_error_list

# Load the id SF measurement from measurement_poi_.txt file produced with plotParabola_POI_region.py
def load_measurements(setup,year,**kwargs):

  indir   = kwargs.get('indir',       "plots_%s"%year )
  tag     = kwargs.get('tag',         ""              )
  poi     = kwargs.get('poi',       ""              )


  region = []
  poi_val = []
  poi_errhi = []
  poi_errlo = []

  if poi == 'tes': 
    inputfilename = "%s/measurement_tes_mt%s_DeepTau_fit_asymm.txt" %(indir,tag)
  elif poi == 'tid_SF': 
    inputfilename = "%s/measurement_tid_SF_mt%s_DeepTau_fit_asymm.txt" %(indir,tag)
  else:
    inputfilename = "%s/measurement_poi_mt%s_DeepTau_fit_asymm.txt" %(indir,tag)


  with open(inputfilename, 'r') as file:
      next(file)
      for line in file:
          cols = line.strip().split()
          region.append(str(cols[0]))
          poi_val.append(float(cols[1]))
          poi_errhi.append(float(cols[3]))
          poi_errlo.append(float(cols[2]))
  #Print the lists
  # print(region)
  # print(id_SFs)
  # print(id_SFs_errhi)
  # print(id_SFs_errlo)
  return region, poi_val, poi_errhi, poi_errlo


def plot_dm_graph(setup,year,**kwargs):

  indir   = kwargs.get('indir',       "plots_%s"%year )
  outdir  = kwargs.get('outdir',      "plots_%s"%year )
  tag     = kwargs.get('tag',         ""              )
  dm_bins = kwargs.get('dm_bins',     False           )
  poi     = kwargs.get('poi',       ""              )


  pt_avg_list, pt_error_list = load_pt_values(setup)
  region, poi_val, poi_errhi, poi_errlo = load_measurements(setup, year, tag=tag, indir=indir, poi=poi)
  
  print(dm_bins)
  if bool(dm_bins)==False:
    print(">>> DM inclusive ")
    graph = ROOT.TGraphAsymmErrors(len(pt_avg_list),
                                    array("d", pt_avg_list),
                                    array("d", poi_val),
                                    array("d", pt_error_list),
                                    array("d", pt_error_list),
                                    array("d", poi_errlo),
                                    array("d", poi_errhi))

    # set the title and axis labels for the graph

    if poi == 'tes':
      graph.SetTitle("TES vs. pT")
      graph.GetYaxis().SetTitle("Energy scale")
    elif poi == 'tid_SF':
      graph.SetTitle("ID Scale Factors vs. pT")
      graph.GetYaxis().SetTitle("ID Scale Factors")
    else:
      graph.SetTitle("poi vs. pT")
      graph.GetYaxis().SetTitle("poi")

    graph.GetXaxis().SetTitle("pT [GeV]")  
    graph.GetYaxis().SetRangeUser(0.65, 1.0)

    # disable the canvas drawing
    ROOT.gROOT.SetBatch(True)

    # draw the graph
    canvasname = "%s/%s_ptplot_%s" %(outdir,poi,tag)
    canvas = ROOT.TCanvas(canvasname, canvasname, 800, 600)
    graph.Draw("AP")
    canvas.Draw()
    canvas.SaveAs(canvasname+".png")
    canvas.SaveAs(canvasname+".root")
    canvas.Close()

  # loop over DMs
  else:
    print(">>> DM exclusive ")
    # define the DM order
    dm_order = ["DM0_", "DM1_", "DM10_", "DM11_"]

    # create a dictionary to store the TGraphAsymmErrors objects
    graphs_dict = {}
    # loop over DMs
    for dm in dm_order:
      print(">>>>>>>>>>>> %s:" %(dm))
      # filter elements with current DM
      dm_list = [elem for elem in region if dm in elem]
      print("Elements with %s:" %(dm_list))
      # get values for current DM
      dm_poi_val = [poi_val[region.index(elem)] for elem in dm_list]
      print("poi for : %s" %(dm_poi_val))
      dm_poi_errhi = [poi_errhi[region.index(elem)] for elem in dm_list]
      print("poi errhi :  %s" %(dm_poi_errhi))
      dm_poi_errlo = [poi_errlo[region.index(elem)] for elem in dm_list]
      print("poi errlo :  %s" %(dm_poi_errlo))
      dm_pt_avg_list = [pt_avg_list[region.index(elem)] for elem in dm_list]
      print("pt_avg_list : %s" %(dm_pt_avg_list))
      dm_pt_error_list = [pt_error_list[region.index(elem)] for elem in dm_list]
      print("pt_error_list : %s" %(dm_pt_error_list))
      
      # create a TGraphAsymmErrors object for the current DM
      graph = ROOT.TGraphAsymmErrors(len(dm_pt_avg_list),
                                      array("d", dm_pt_avg_list),
                                      array("d", dm_poi_val),
                                      array("d", dm_pt_error_list),
                                      array("d", dm_pt_error_list),
                                      array("d", dm_poi_errlo),
                                      array("d", dm_poi_errhi))
      
      # set the title and axis labels for the graph
      if poi == 'tes':
        graph.SetTitle("TES vs. pT")
        graph.GetYaxis().SetTitle("Energy scale")
      elif poi == 'tid_SF':
        graph.SetTitle("ID Scale Factors vs. pT")
        graph.GetYaxis().SetTitle("ID Scale Factors")
      else:
        graph.SetTitle("poi vs. pT")
        graph.GetYaxis().SetTitle("poi")

      graph.GetXaxis().SetTitle("pT [GeV]")  
      #graph.GetYaxis().SetRangeUser(0.65, 1.0)
      
      # add the graph to the dictionary
      graphs_dict[dm] = graph
      
      # disable the canvas drawing
      ROOT.gROOT.SetBatch(True)
      
      # draw the graph
      canvasname = "%s/%s_ptplot%s_%s" %(outdir,poi,tag,dm)
      canvas = ROOT.TCanvas(canvasname, canvasname, 800, 600)
      graph.Draw("AP")
      canvas.Draw()
      canvas.SaveAs(canvasname+".png")
      canvas.SaveAs(canvasname+".root")
      canvas.Close()

def ensureDirectory(dirname):
  """Make directory if it does not exist."""
  if not os.path.exists(dirname):
      os.makedirs(dirname)
      print ">>> made directory %s"%dirname


def main(args):
    
  print "Using configuration file: %s"%args.config
  with open(args.config, 'r') as file:
      setup = yaml.safe_load(file)

  tag           = setup["tag"] if "tag" in setup else ""
  year          = args.year
  dm_bins       = args.dm_bins
  poi           = args.poi
  indir         = "plots_%s"%year
  outdir        = "plots_%s"%year
  ensureDirectory(outdir)
  CMSStyle.setCMSEra(year)
  print(dm_bins)

  plot_dm_graph(setup,year,dm_bins=dm_bins,indir=indir,outdir=outdir,tag=tag, poi=poi)



if __name__ == '__main__':

  description = '''This script makes plot of pt-dependants id SF measurments from txt file and config file.'''
  parser = ArgumentParser(prog="plot_it_SF",description=description,epilog="Success!")
  parser.add_argument('-y', '--year', dest='year', choices=['2016','2017','2018','UL2016_preVFP','UL2016_postVFP','UL2017','UL2018','UL2018_v10'], type=str, default='UL2018', action='store', help="select year")
  parser.add_argument('-c', '--config', dest='config', type=str, default='TauES_ID/config/FitSetupTES_mutau_noSF_pt_DM.yml', action='store', help="set config file")
  parser.add_argument('--dm-bins', dest='dm_bins', default=False, action='store_true', help="if true then the mutau channel fits are also split by tau decay-mode")
  parser.add_argument('-p', '--poi',         dest='poi', default='tid_SF', type=str, action='store', help='use this parameter of interest')

  args = parser.parse_args()
  main(args)
  print ">>>\n>>> done\n"
