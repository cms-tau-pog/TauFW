  
#! /usr/bin/env python
# Author: OPoncet (February 2023)
'''This script makes plot of pt-dependants id SF measurments from txt file and config file.'''
import ROOT
import os, sys,yaml
from array import array
from argparse import ArgumentParser
from collections import OrderedDict
from ROOT import gROOT, gPad, gStyle, Double, TFile, TCanvas, TLegend, TLatex, TF1, TGraph, TGraph2D, TPolyMarker3D, TGraphAsymmErrors, TLine,\
                 kBlack, kBlue, kRed, kGreen, kYellow, kOrange, kMagenta, kTeal, kAzure, TMath
from TauFW.Plotter.sample.utils import CMSStyle



def load_pt_values(setup,**kwargs):
    pt_avg_list = []
    pt_error_list  = []
    bins_order = setup["plottingOrder"]
    for ibin, ptregion in enumerate(bins_order):
        # print("region = %s" %(ptregion))
        title = setup["tid_SFRegions"][ptregion]["title"]
        str_pt_lo = title.split("<")[0].split(" ")[-1]
        str_pt_hi = title.split("<")[-1].split(" ")[0]
        pt_hi = float(str_pt_hi)
        pt_lo = float(str_pt_lo)
        pt_avg = (pt_hi + pt_lo) / 2.0
        pt_error = pt_avg - pt_lo
        pt_avg_list.append(pt_avg)
        pt_error_list.append(pt_error)
        # print("pt average = %f and pt error = %s" %(pt_avg, pt_error))

    return pt_avg_list, pt_error_list

# Load the id SF measurement from measurement_poi_.txt file produced with plotParabola_POI_region.py
def load_sf_measurements(setup,year,**kwargs):

  indir   = kwargs.get('indir',       "plots_%s"%year )
  tag     = kwargs.get('tag',         ""              )

  region = []
  id_SFs = []
  id_SFs_errhi = []
  id_SFs_errlo = []
  inputfilename = "%s/measurement_poi_mt%s_DeepTau.txt" %(indir,tag)
  with open(inputfilename, 'r') as file:
      next(file)
      for line in file:
          cols = line.strip().split()
          region.append(str(cols[0]))
          id_SFs.append(float(cols[1]))
          id_SFs_errhi.append(float(cols[2]))
          id_SFs_errlo.append(float(cols[3]))
  #Print the lists
  # print(region)
  # print(id_SFs)
  # print(id_SFs_errhi)
  # print(id_SFs_errlo)
  return region, id_SFs, id_SFs_errhi, id_SFs_errlo


def plot_dm_graph(setup,year,**kwargs):

  indir   = kwargs.get('indir',       "plots_%s"%year )
  outdir  = kwargs.get('outdir',      "plots_%s"%year )
  tag     = kwargs.get('tag',         ""              )
  dm_bins = kwargs.get('dm_bins',     False              )

  pt_avg_list, pt_error_list = load_pt_values(setup)
  region, id_SFs, id_SFs_errhi, id_SFs_errlo = load_sf_measurements(setup, year, tag=tag, indir=indir)
  
  print(dm_bins)
  if bool(dm_bins)==False:
    print(">>> DM inclusive ")
    graph = ROOT.TGraphAsymmErrors(len(pt_avg_list),
                                    array("d", pt_avg_list),
                                    array("d", id_SFs),
                                    array("d", pt_error_list),
                                    array("d", pt_error_list),
                                    array("d", id_SFs_errlo),
                                    array("d", id_SFs_errhi))

    # set the title and axis labels for the graph
    graph.SetTitle("ID Scale Factors vs. pT")
    graph.GetXaxis().SetTitle("pT [GeV]")
    graph.GetYaxis().SetTitle("ID Scale Factors")
    graph.GetYaxis().SetRangeUser(0.65, 1.1)

    # disable the canvas drawing
    ROOT.gROOT.SetBatch(True)

    # draw the graph
    canvasname = "%s/id_SF_ptplot_%s" %(outdir,tag)
    canvas = ROOT.TCanvas(canvasname, canvasname, 800, 600)
    graph.Draw("AP")
    canvas.Draw()
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
      dm_id_SFs = [id_SFs[region.index(elem)] for elem in dm_list]
      print("id_SFs for : %s" %(dm_id_SFs))
      dm_id_SFs_errhi = [id_SFs_errhi[region.index(elem)] for elem in dm_list]
      print("id_SFs_errhi :  %s" %(dm_id_SFs_errhi))
      dm_id_SFs_errlo = [id_SFs_errlo[region.index(elem)] for elem in dm_list]
      print("id_SFs_errlo :  %s" %(dm_id_SFs_errlo))
      dm_pt_avg_list = [pt_avg_list[region.index(elem)] for elem in dm_list]
      print("pt_avg_list : %s" %(dm_pt_avg_list))
      dm_pt_error_list = [pt_error_list[region.index(elem)] for elem in dm_list]
      print("pt_error_list : %s" %(dm_pt_error_list))
      
      # create a TGraphAsymmErrors object for the current DM
      graph = ROOT.TGraphAsymmErrors(len(dm_pt_avg_list),
                                      array("d", dm_pt_avg_list),
                                      array("d", dm_id_SFs),
                                      array("d", dm_pt_error_list),
                                      array("d", dm_pt_error_list),
                                      array("d", dm_id_SFs_errlo),
                                      array("d", dm_id_SFs_errhi))
      
      # set the title and axis labels for the graph
      graph.SetTitle("ID Scale Factors vs. pT for %s" % dm)
      graph.GetXaxis().SetTitle("pT [GeV]")
      graph.GetYaxis().SetTitle("ID Scale Factors")
      #graph.GetYaxis().SetRangeUser(0.65, 1.1)
      
      # add the graph to the dictionary
      graphs_dict[dm] = graph
      
      # disable the canvas drawing
      ROOT.gROOT.SetBatch(True)
      
      # draw the graph
      canvasname = "%s/id_SF_ptplot%s_%s" %(outdir,tag,dm)
      canvas = ROOT.TCanvas(canvasname, canvasname, 800, 600)
      graph.Draw("AP")
      canvas.Draw()
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
  indir         = "plots_%s"%year
  outdir        = "plots_%s"%year
  ensureDirectory(outdir)
  CMSStyle.setCMSEra(year)
  print(dm_bins)

  plot_dm_graph(setup,year,dm_bins=dm_bins,indir=indir,outdir=outdir,tag=tag)





if __name__ == '__main__':

  description = '''This script makes plot of pt-dependants id SF measurments from txt file and config file.'''
  parser = ArgumentParser(prog="plot_it_SF",description=description,epilog="Success!")
  parser.add_argument('-y', '--year', dest='year', choices=['2016','2017','2018','UL2016_preVFP','UL2016_postVFP','UL2017','UL2018'], type=str, default='UL2018', action='store', help="select year")
  parser.add_argument('-c', '--config', dest='config', type=str, default='TauES_ID/config/FitSetupTES_mutau_noSF_pt_DM.yml', action='store', help="set config file")
  parser.add_argument('--dm-bins', dest='dm_bins', default=False, action='store_true', help="if true then the mutau channel fits are also split by tau decay-mode")
  args = parser.parse_args()
  main(args)
  print ">>>\n>>> done\n"
