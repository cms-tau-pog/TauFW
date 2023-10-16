#! /usr/bin/env python
"""
Date : June 2023 
Author : @oponcet 
Description : 
This script get the mean value and the stddev of the pt region using the pt plots produced by plot_v10.py.
"""
import ROOT
import os, sys,yaml
from array import array
from argparse import ArgumentParser
from collections import OrderedDict
from ROOT import gROOT, gPad, gStyle, Double, TFile, TCanvas, TLegend, TLatex, TF1, TGraph, TGraph2D, TPolyMarker3D, TGraphAsymmErrors, TLine,\
                 kBlack, kBlue, kRed, kGreen, kYellow, kOrange, kMagenta, kTeal, kAzure, TMath



def main(args):
    
  print "Using configuration file: %s"%args.config
  with open(args.config, 'r') as file:
      setup = yaml.safe_load(file)

  tag           = setup["tag"] if "tag" in setup else ""
  year          = args.year

  # Regionq defined in config files
  regions = setup["plottingOrder"]
  print(regions)

  # List containing the mean pt of a pt region and the std deviation
  pt_avg_list = []
  pt_error_list = []



  # Loop over the histograms and file names
  for region in regions:
      file_name = "plots/%s/mutau/pt_2_mt-%s-%s%s.root" %(year,region,year,tag)

      # Open the ROOT file
      file = ROOT.TFile(file_name)
      print(file_name)

      # Access the canvas and pad
      canvas = file.Get("canvas")
      pad = canvas.FindObject("pad1")

      # Access the THStack
      stack = pad.FindObject("stack_pt_2")

      # Access the TH1D histogram
      histogram = stack.GetHists().FindObject("pt_2_ZTT")

      # Calculate the mean value
      mean = int(histogram.GetMean())

      # Calculate the standard deviation
      std_dev = int(histogram.GetRMS())

      # Print the mean value and standard deviation
      print("Mean value of %s: %.0f" % (region, mean))
      print("Standard deviation of %s: %d" % (region, std_dev))
      pt_avg_list.append(mean)
      pt_error_list.append(std_dev)

  print("pt_avg_list = %s") %(pt_avg_list)
  print("pt_error_list = %s") %(pt_error_list)



if __name__ == '__main__':

  description = '''This script makes plot of pt-dependants id SF measurments from txt file and config file.'''
  parser = ArgumentParser(prog="get_ptmean",description=description,epilog="Success!")
  parser.add_argument('-y', '--year', dest='year', choices=['2016','2017','2018','UL2016_preVFP','UL2016_postVFP','UL2017','UL2018','UL2018_v10'], type=str, default='UL2018', action='store', help="select year")
  parser.add_argument('-c', '--config', dest='config', type=str, default='./../Fitter/TauES_ID/config/FitSetupTES_mutau_noSF_pt_DM.yml', action='store', help="set config file")

  args = parser.parse_args()
  main(args)
  print ">>>\n>>> done\n"