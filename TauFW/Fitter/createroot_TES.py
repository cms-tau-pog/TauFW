  
#! /usr/bin/env python
# Author: P.Mastrapasqua, O. Poncet (May 2023)
# Usage: python TauES_ID/createJSON_TES.py -y UL2018 -c ./TauES_ID/config/FitSetup_mutau_9pt_40-200.yml
'''This script makes pt-dependants TES json/root files from config file.'''
import ROOT
import os, sys,yaml
from array import array
from argparse import ArgumentParser
from collections import OrderedDict
from ROOT import gROOT, gPad, gStyle, TFile, TCanvas, TLegend, TLatex, TF1, TMultiGraph, TGraph, TGraph2D, TPolyMarker3D, TGraphAsymmErrors, TLine,kBlack, kBlue, kRed, kGreen, kYellow, kOrange, kMagenta, kTeal, kAzure, TMath, TH1F
from fit_tools import FitSF
#from TauFW.Plotter.sample.utils import CMSStyle
# import correctionlib.schemav2 as cs
# import rich

def load_pt_values(setup,**kwargs):
    pt_avg_list = []
    pt_error_list = []
    bins_order = setup["plottingOrder"]
    for region in setup['regions']:
        # print("region = %s" %(ptregion))
        title = setup['regions'][region]["title"]
        if 'pt' not in title: continue
        str_pt_lo = title.split("pt:")[-1].split('-')[0].strip()
        str_pt_hi = title.split("pt:")[-1].split('-')[1].strip()
        pt_hi = float(str_pt_hi)
        pt_lo = float(str_pt_lo)
        pt_avg = (pt_hi + pt_lo) / 2.0
        pt_error = pt_avg - pt_lo
        pt_avg_list.append(pt_avg)
        pt_error_list.append(pt_error)
        # print("pt average = %f and pt error = %s" %(pt_avg, pt_error))
    #pt_avg_list = sorted(list(set(pt_avg_list)), key=lambda k: k[0])
    #print(pt_avg_list)
    return pt_avg_list, pt_error_list

def load_edges(setup,**kwargs):
    edg  = []
    bins_order = setup["plottingOrder"]
    for region in setup['regions']:
        # print("region = %s" %(ptregion))
        title = setup["regions"][region]["title"]
        if 'pt' not in title: continue
        str_pt_lo = title.split("pt:")[-1].split('-')[0].strip()
        str_pt_hi = title.split("pt:")[-1].split('-')[1].strip()
        #print("ibin")
        #print(str_pt_lo)
        #print(str_pt_hi)
        pt_hi = float(str_pt_hi)
        pt_lo = float(str_pt_lo)
        edg.append(pt_lo)
    print(edg)
    edg.append(pt_hi)
    #edg = sorted(list(set(edg)))
    print(edg)
    return edg

# Load the id SF measurement from measurement_poi_.txt file produced with plotParabola_POI_region.py
def load_sf_measurements(setup,year,**kwargs):

  tag     = kwargs.get('tag',         ""              )
  jet_wp  = kwargs.get('jet_wp',      "Tight"         )
  ele_wp  = kwargs.get('ele_wp',      "Tight"         )
  sf      = kwargs.get('sf',          "tes"         )
  region = []
  tes = []
  tes_errhi = []
  tes_errlo = []
  inputfilename = f"plots_pt_less_region/againstjet_{jet_wp}/againstelectron_{ele_wp}/{year}/measurement_{sf}_mt_mutau_mt65_DM_pt_Dt2p5_puppimet_DeepTau_fit_asymm.txt"
  with open(inputfilename, 'r') as file:
      next(file)
      for line in file:
        cols = line.strip().split()
        region.append(str(cols[0]))
        tes.append(float(cols[1]))
        tes_errhi.append(float(cols[3]))
        tes_errlo.append(float(cols[2]))
  #Print the lists
  # print(region)
  # print(tes)
  # print(tes_errhi)
  # print(tes_errlo)
  return region, tes, tes_errhi, tes_errlo


def plot_dm_graph(setup,form,ele_wp,**kwargs):

  tag     = kwargs.get('tag',         ""              )
  jet_wps = ['Loose', 'Medium', 'Tight', 'VTight']
  sfs     = ['tes', 'tid_SF']
  pt_avg_list, pt_error_list = load_pt_values(setup)
  pt_edges = load_edges(setup)
  
  # loop over DMs
  print(">>> DM exclusive ")
  # define the DM order
  dm_order = ["DM0_", "DM1_", "DM10_", "DM11_"]

  # create a dictionary to store sf data
  sf_dict = {}
  # loop over DMs
  for sf in sfs:
   sf_dict[sf] = {}
   for era in ['2023C', '2023D']:
       sf_dict[sf][era] = {}
       for dm in dm_order:
           print(">>>>>>>>>>>> %s:" %(dm))
           #loop over jet_wps
           for jet_wp in jet_wps:
               print('jet_wp: ', jet_wp)
               region, tes, tes_errhi, tes_errlo = load_sf_measurements(setup, era, tag=tag, jet_wp=jet_wp, ele_wp=ele_wp, sf=sf)
               # filter elements with current DM
               dm_list = [elem for elem in region if dm in elem]
               print("Elements with %s:" %(dm_list))
               # get values for current DM
               print(">>>>>> INPUT FOR JSON")
               dm_tes = [tes[region.index(elem)] for elem in dm_list]
               print("tes for : %s" %(dm_tes))
               dm_pt_edges = [pt_edges[region.index(elem)] for elem in dm_list]
               dm_pt_edges.append(pt_edges[-1])
               print("pt_edges for : %s" %(dm_pt_edges))

               dm_tes_errhi = [tes_errhi[region.index(elem)] for elem in dm_list]
               print("tes_errhi :  %s" %(dm_tes_errhi))
               dm_tes_errlo = [tes_errlo[region.index(elem)] for elem in dm_list]
               print("tes_errlo :  %s" %(dm_tes_errlo))
   
               dm_tes_up = [sum(x) for x in zip(dm_tes,dm_tes_errhi)] 
               print("tes_up for : %s" %(dm_tes_up))
               dm_tes_errlo_neg = [-x for x in dm_tes_errlo]
               dm_tes_down = [sum(x) for x in zip(dm_tes,dm_tes_errlo_neg)]
               print("tes_down for : %s" %(dm_tes_down))

               sf_dict[sf][era][dm.replace("_","")+ f'_{jet_wp}'] = {"edges": dm_pt_edges, "content":dm_tes, "up": dm_tes_up, "down": dm_tes_down}
  print("SF dictionary")
  print(sf_dict)
  colors = [kBlack, kBlue, kRed, kMagenta, kYellow, kOrange, kGreen, kTeal, kAzure]
  for sf in sfs:
    if form=='root':
       #loop on DMs
       for idx, jet_wp in enumerate(jet_wps):
          if sf == 'tes':
             name = 'TauES'
          else:
             name = 'TauID'
          sfile = TFile(f"tau_sf/{name}_SF_dm_DeepTau2018v2p5_2023_VSjet{jet_wp}_VSele{ele_wp}_Run3_May24.root", 'recreate')
          for era in ['2023C', '2023D']:
            for dm in dm_order:
               funcstr = '(x<=20)*0'
               funcstr_up = '(x<=20)*0'
               funcstr_down = '(x<=20)*0'

               key = dm+f'{jet_wp}'

               for ip in range(0, len(sf_dict[sf][era][key]["content"])):
                 pt_avg = (sf_dict[sf][era][key]["edges"][ip]+sf_dict[sf][era][key]["edges"][ip+1])/2
                 pt_err = pt_avg - sf_dict[sf][era][key]["edges"][ip]
                 print('ip: ', ip)
                 funcstr += '+ ( x > ' + str(sf_dict[sf][era][key]["edges"][ip]) + ' && x <=' + str(sf_dict[sf][era][key]["edges"][ip+1]) + ')*' + str(sf_dict[sf][era][key]["content"][ip])
                 funcstr_up += '+ ( x > ' + str(sf_dict[sf][era][key]["edges"][ip]) + ' && x <=' + str(sf_dict[sf][era][key]["edges"][ip+1]) + ')*' + str(sf_dict[sf][era][key]["up"][ip])
                 funcstr_down += '+ ( x > ' + str(sf_dict[sf][era][key]["edges"][ip]) + ' && x <=' + str(sf_dict[sf][era][key]["edges"][ip+1]) + ')*' + str(sf_dict[sf][era][key]["down"][ip])
               #fit_func='pol1'
               #fit_up, h_uncert_up, h_up, uncerts_up = FitSF(graph_cent,func=fit_func)
               funcstr +='+ ( x > 200)*1.0'
               funcstr_up +='+ ( x > 200)*1.0'
               funcstr_down +='+ ( x > 200)*1.0'
               print(key)
               print(funcstr, '\t', dm, '\t', era)
               func_SF      = TF1(dm+era, funcstr,     0,200)
               func_SF.Write()
               func_SF_up   = TF1(dm+era+'_up', funcstr_up,     0,200)
               func_SF_up.Write()
               func_SF_down = TF1(dm+era+'_down', funcstr_down,     0,200)
               func_SF_down.Write()
          sfile.Write()
          sfile.Close()

#   if form=='json': 
#       ###############################################################
#       ## create JSON file with SFs (following correctionlib rules)
#       corr = cs.Correction(
#          name="TauIdSF",
#          version=1,
#          description="Tau Id SF, pT binned divided by DM",
#          inputs= [
#                  cs.Variable(name="genmatch", type="int", description="Tau genmatch, sf only on real taus (genmatch 5) "),
#                  cs.Variable(name="DM", type="int", description="Tau decay mode (0,1,10,11)"),
#                  cs.Variable(name="pT", type="real", description="Tau transverse momentum"),
#                  ], 
#          output={'name': "sf", 'type': "real", 'description': "Tau Id scale factor"},
#          data=cs.Category(
#               nodetype="category",
#               input="genmatch",
#               content=[
#                       cs.CategoryItem(key=1,value=1.0),
#                       cs.CategoryItem(key=2,value=1.0),
#                       cs.CategoryItem(key=3,value=1.0),
#                       cs.CategoryItem(key=4,value=1.0),
#                       cs.CategoryItem(key=5,
#                                       value=cs.Category(
#                                             nodetype="category",
#                                             input="DM",
#                                             content=[
#                                                     cs.CategoryItem(key=0,
#                                                     value=cs.Binning(
#                                                           nodetype="binning",
#                                                           input="pT",
#                                                           edges=sf_dict["0"]["edges"],
#                                                           content=sf_dict["0"]["content"] ,
#                                                           flow="clamp"
#                                                           )), 
#                                                     cs.CategoryItem(key=1,
#                                                     value=cs.Binning(
#                                                           nodetype="binning",
#                                                           input="pT",
#                                                           edges=sf_dict["1"]["edges"],
#                                                           content=sf_dict["1"]["content"] ,
#                                                           flow="clamp"
#                                                           )),
#                                                     cs.CategoryItem(key=10,
#                                                     value=cs.Binning(
#                                                           nodetype="binning",
#                                                           input="pT",
#                                                           edges=sf_dict["10"]["edges"],
#                                                           content=sf_dict["10"]["content"] ,
#                                                           flow="clamp"
#                                                           )),
#                                                     cs.CategoryItem(key=11,
#                                                     value=cs.Binning(
#                                                           nodetype="binning",
#                                                           input="pT",
#                                                           edges=sf_dict["11"]["edges"],
#                                                           content=sf_dict["11"]["content"] ,
#                                                           flow="clamp"
#                                                           )),
#                                                     ]
#                                                     )),
#                       cs.CategoryItem(key=6,value=1.0),
#                       cs.CategoryItem(key=0,value=1.0)
#                       ]
#                       )
#              )

    #   print("Evaluate a point: ")
    #   print(corr.to_evaluator().evaluate(5,11,300.))
    #   rich.print(corr)
    #   cset = cs.CorrectionSet(
    #          schema_version=2,
    #          description="Tau SFs",
    #          corrections=[
    #                       corr
    #                      ],
    #          )
    #   with open("tes_DeepTau2018v2p5VSjet_%s.json"%year, "w") as fout:
    #        print(">>>Writing JSON!")
    #        fout.write(cset.json())


def ensureDirectory(dirname):
  """Make directory if it does not exist."""
  if not os.path.exists(dirname):
      os.makedirs(dirname)
      print(">>> made directory %s"%dirname)


def main(args):
    
  print("Using configuration file: %s"%args.config)
  with open(args.config, 'r') as file:
      setup = yaml.safe_load(file)

  tag           = setup["tag"] if "tag" in setup else ""
  form          = args.form
  ele_wp        = args.ele_wp
  #CMSStyle.setCMSEra(year)

  plot_dm_graph(setup,form,ele_wp,tag=tag)





if __name__ == '__main__':

  description = '''This script makes plot of pt-dependants id SF measurments from txt file and config file.'''
  parser = ArgumentParser(prog="plot_it_SF",description=description,epilog="Success!")
  parser.add_argument('-c', '--config', dest='config', type=str, default='TauES_ID/config/Default_FitSetupTES_mutau_DM_mt65pt_lessptregion.yml', action='store', help="set config file")
  parser.add_argument('-f', '--form', dest='form', choices=['json', 'root'], type=str, default='root', action='store', help="select format")
  parser.add_argument('-e', '--electron_wp', dest='ele_wp', type=str, default='VVLoose', help="electron wp")
  args = parser.parse_args()
  main(args)
  print(">>>\n>>> done\n")
