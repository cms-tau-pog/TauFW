#!/usr/bin/env python
"""
Date : January 2024
Author : @oponcet
Description :
This script makes plot of pt-dependants summary plots of the results of the POI (tes or tid_SF) with DM inclusif
bins or not (with --dm-bins option). This script use the txt output file of plotParabola_POI_region.py to produce the plots.
The valuesof the mean of the pt bin and its std dev need to be change in the fit. This values can be obtained usin pt distribution.
Example of usage : 
python3 TauES_ID/saveSFs_root.py -y 2022_postEE --dmpt-bins --poi tes -c ./TauES_ID/config/Default_FitSetupTES_mutau_DM_4pt.yml 
python3 TauES_ID/saveSFs_root.py -y 2022_preEE --poi tes -c ./TauES_ID/config/Default_FitSetupTES_mutau_DM_mt40_JetM_muVT.yml --dm-bins

"""
import ROOT
import os
import sys
import yaml
import json
from array import array
from argparse import ArgumentParser
from collections import OrderedDict
from ROOT import (
    gROOT,
    gPad,
    gStyle,
    TFile,
    TCanvas,
    TLegend,
    TLatex,
    TF1,
    TGraph,
    TGraph2D,
    TPolyMarker3D,
    TGraphAsymmErrors,
    TLine,
    kBlack,
    kBlue,
    kRed,
    kGreen,
    kYellow,
    kOrange,
    kMagenta,
    kTeal,
    kAzure,
    TMath,
)
from TauFW.Plotter.sample.utils import CMSStyle


def load_pt_values(setup, **kwargs):
    """
    Load average pt values and corresponding errors for different pt bins.

    Parameters:
    - setup (dict): Configuration setup containing information about pt bins.
    - poi (str): Parameter of interest, either "tes" or "tid_SF".

    Returns:
    - pt_avg_list (list): List of average pt values for each bin.
    - pt_errorup_list (list): List of upper errors corresponding to each pt bin.
    - pt_errordown_list (list): List of lower errors corresponding to each pt bin.
    """

    # Get the value of the parameter of interest (tes or tid_SF)
    poi = kwargs.get("poi", "")

    # Initialize lists to store average pt values and corresponding errors
    pt_avg_list = []
    pt_error_list = []

    # Get the order in which bins should be plotted
    bins_order = setup["plottingOrder"]

    for ibin, ptregion in enumerate(bins_order):
        if poi == "tes":
            print(poi)
            title = setup["tesRegions"][ptregion]["title"]
        else:
            title = setup["tid_SFRegions"][ptregion]["title"]

            # Extract the lower and upper bounds of the pt range from the title
        str_pt_lo = title.split("<")[0].split(" ")[-1]
        str_pt_hi = title.split("<")[-1].split(" ")[0]
        pt_hi = float(str_pt_hi)
        pt_lo = float(str_pt_lo)

        # Example values for pt_avg_list, pt_errorup_list, pt_errordown_list # 4 pt bins [20,30,40,50,200] 
        pt_avg_list = [25, 35, 44, 70, 25, 35, 44, 73, 25, 35, 44, 72, 26, 35, 44, 72] # [DM0, DM1, DM10, DM11]
        # pt_errorup_list = [3, 3, 3, 25, 3, 3, 3, 26, 3, 3, 3, 24, 3, 3, 3, 26] # [DM0, DM1, DM10, DM11] stdd
        # pt_errordown_list = [3, 3, 3, 20, 3, 3, 3, 23, 3, 3, 3, 22, 3, 3, 3, 22] # [DM0, DM1, DM10, DM11]stdd
        pt_errorup_list = [5, 5, 6, 130, 5, 5, 6, 127, 5, 5, 6, 128, 4, 5, 6, 128] # [DM0, DM1, DM10, DM11] bin width
        pt_errordown_list = [5, 5, 4, 20, 5, 5, 4, 23, 5, 5, 4, 22, 6, 5, 4, 22] # [DM0, DM1, DM10, DM11] bin width

    # Return the lists containing average pt values and errors
    return pt_avg_list, pt_errorup_list, pt_errordown_list


def load_measurements(setup, year, **kwargs):
    """
    Load ID SF measurements from a file produced with plotParabola_POI_region.py.

    Parameters:
    - setup (dict): Configuration setup containing information about the measurement file structure.
    - year (str): The year for which the measurements are loaded.
    - indir (str): Input directory where measurement files are located.
    - tag (str): Additional tag to identify the measurement file.
    - poi (str): Parameter of interest, either "tes" or "tid_SF".

    Returns:
    - region (list): List of regions corresponding to the measurements.
    - poi_val (list): List of measured values for the parameter of interest.
    - poi_errhi (list): List of upper errors corresponding to each measurement.
    - poi_errlo (list): List of lower errors corresponding to each measurement.
    """

    indir = kwargs.get("indir", "plots_%s" % year)
    tag = kwargs.get("tag", "")
    poi = kwargs.get("poi", "")

    region = []
    poi_val = []
    poi_errhi = []
    poi_errlo = []

    if poi == "tes":
        inputfilename = "%s/measurement_tes_mt%s_DeepTau_fit_asymm.txt" % (indir, tag)
    elif poi == "tid_SF":
        inputfilename = "%s/measurement_tid_SF_mt%s_DeepTau.txt" % (indir, tag)
    else:
        inputfilename = "%s/measurement_poi_mt%s_DeepTau_fit_asymm.txt" % (indir, tag)

    with open(inputfilename, "r") as file:
        next(file)
        for line in file:
            cols = line.strip().split()
            region.append(str(cols[0]))
            poi_val.append(float(cols[1]))
            poi_errhi.append(float(cols[3]))
            poi_errlo.append(float(cols[2]))

    return region, poi_val, poi_errhi, poi_errlo

def save_tes_json(setup, year, dm_bins, dmpt_bins, **kwargs):
    """
    Save DM or DM-pT dependent tau energy scale data to a JSON file.

    Parameters:
    - setup (dict): Configuration setup containing information about the measurement file structure.
    - year (str): The year for which the measurements are saved.
    - dm_bins (bool): Flag indicating whether DM bins are used.
    - dmpt_bins (bool): Flag indicating whether DM-pt bins are used.
    - indir (str): Input directory where measurement files are located.
    - outdir (str): Output directory where the JSON file will be saved.
    - tag (str): Additional tag to identify the measurement file.
    - poi (str): Parameter of interest, either "tes" or "tid_SF".

    Returns:
    - None: The function saves the data to a JSON file.
    """
    indir = kwargs.get("indir", "plots_%s" % year)
    outdir = kwargs.get("outdir", "plots_%s" % year)
    tag = kwargs.get("tag", "")
    poi = kwargs.get("poi", "")

    # Initialize a dictionary to store the JSON data
    data = {}

    # Set default working points : adjust this according to your needs
    wp = "Medium"  
    wp_VSe = "VVLoose" 


    if dmpt_bins:
        print("DM-pt dependence")
        pt_avg_list, pt_errorup_list, pt_errordown_list = load_pt_values(setup)
        region, tes_val_list, tes_errup_list, tes_errdown_list = load_measurements(setup, year, tag=tag, indir=indir, poi=poi)

        dm_order = ["DM11_", "DM10_", "DM1_", "DM0_"]
        dm_str_list = ["DM11", "DM10", "DM1", "DM0"]
        dm_values = [11, 10, 1 , 0]
        
        data = {dm_str: {} for dm_str in dm_str_list}

        edges = [20.0, 30.0 ,40.0 ,50.0 ,200.0] #pt binning 

        # loop over DMs
        for dm,dm_str in zip(dm_order,dm_str_list):
            print(">>>>>>>>>>>> %s:" % (dm))
            # filter elements with current DM
            dm_list = [elem for elem in region if dm in elem]
            print("Elements with %s:" % (dm_list))
            # get values for current DM
            tes_val_list_dm = [tes_val_list[region.index(elem)] for elem in dm_list]
            print("poi nom : %s" % (tes_val_list_dm))
            tes_errup_list_dm= [tes_errup_list[region.index(elem)] for elem in dm_list]
            print("poi errhi :  %s" % (tes_errup_list_dm))
            tes_errdown_list_dm = [tes_errdown_list[region.index(elem)] for elem in dm_list]
            print("poi errlo :  %s" % (tes_errdown_list_dm))
            dm_pt_avg_list = [pt_avg_list[region.index(elem)] for elem in dm_list]
            print("pt_avg_list : %s" % (dm_pt_avg_list))
            dm_pt_errordown_list = [pt_errordown_list[region.index(elem)] for elem in dm_list]
            print("dm_pt_errordown_list : %s" % (dm_pt_errordown_list))
            dm_pt_errorup_list = [pt_errorup_list[region.index(elem)] for elem in dm_list]
            print("dm_pt_errorup_list : %s" % (dm_pt_errorup_list))


            data[dm_str] = []

            print(dm_str)

            data[dm_str] =  [
                { "key": "nom", 
                         "value": {
                            "nodetype": "binning",
                            "input": "pt",
                            "edges": edges,
                            "content": tes_val_list_dm,
                            "flow": "clamp"
                        }
                },  
                { "key": "up", 
                         "value": {
                            "nodetype": "binning",
                            "input": "pt",
                            "edges": edges ,
                            "content": [tes_val + tes_errup for tes_val,tes_errup in zip (tes_val_list_dm,tes_errup_list_dm)],
                            "flow": "clamp"
                        }
                }, 
                { "key": "down", 
                         "value": {
                            "nodetype": "binning",
                            "input": "pt",
                            "edges": edges ,
                            "content": [tes_val - tes_errdown for tes_val,tes_errdown in zip (tes_val_list_dm,tes_errdown_list_dm)],
                            "flow": "clamp"
                        }
                }  
            ]
                 
           

        

    elif dm_bins:
        dm_values = [11, 10, 1, 0]
        dm_str_list = ["DM11", "DM10", "DM1", "DM0"]
        data = {dm_str: {} for dm_str in dm_str_list}
        #data[dm_str] = []
        
        region, tes_val_list, tes_errup_list, tes_errdown_list = load_measurements(setup, year, tag=tag, indir=indir, poi=poi)
        
        for dm, dm_str, tes_val, tes_errup, tes_errdown in zip(dm_values, dm_str_list,tes_val_list, tes_errup_list, tes_errdown_list):
            data[dm_str]= [
                { 'key': 'nom',  'value': tes_val },
                { 'key': 'up',   'value': tes_val + tes_errup },
                { 'key': 'down', 'value': tes_val - tes_errdown },
                ]
   
   
    for dm,dm_str in zip(dm_values,dm_str_list):       
        print(dm,dm_str)
    print(data)

    tesdata_dmbins = {
        "nodetype": "category",
        "input": "id",
        "content": [
        { "key": "DeepTau2018v2p5",
            "value": {
            "nodetype": "transform",
            "input": "genmatch",
            "content": [
                { "key": 1, "value": 1.0 },
                { "key": 2, "value": 1.0 },
                { "key": 3, "value": 1.0 },
                { "key": 4, "value": 1.0 },
                { "key": 5,
                  "value": {
                    "nodetype": "category",
                    "input": "wp",
                    "content": [
                        { "key": wp,
                            "value": {
                                "nodetype": "category",
                                "input": "wp_VSe",
                                "content": [
                                { "key": wp_VSe,
                                    "value": {
                                    "nodetype": "category",
                                    "input": "dm",
                                    "content": [ # key:dm
                                    { 'key': dm,
                                        'value': {
                                        'nodetype': 'category', # syst
                                        'input': "syst",
                                        'content': data[dm_str]
                                        }
                                    } for dm,dm_str in zip(dm_values,dm_str_list)
                                    ] # key:dm
                                    }
                                }
                                ] # key: wp_VSe
                            }
                        }
                    ] # key: wp
                  }
                }
            ] # key: genmatch
            }
        }   
        ] # key :  DeepTau2018v2p5  
    } # category:dm



    # Save the data to a JSON file
    output_filename = "%s/TauES_DeepTau2018v2p5_%s.json" % (outdir, year)

    with open(output_filename, "w") as json_file:
            json.dump({
                "name": "tau_es_dm_%s" % year,
                "description": "DM-dependent tau energy scale in %s, to be applied to reconstructed tau_h Lorentz vector (pT, mass and energy) in simulated data" % year,
                "version": 0,
                "inputs": [
                    {"name": "wp", "type": "string", "description": "DeepTau2018v2p5VSjet working point: Medium"},
                    {"name": "wp_VSe", "type": "string", "description": "DeepTau2018v2p5VSe working point: VVLoose"},
                    {"name": "pt", "type": "real", "description": "Reconstructed tau pT"},
                    {"name": "dm", "type": "int", "description": "Reconstructed tau decay mode: 0, 1, 10, 11"},
                    {"name": "syst", "type": "string", "description": "Systematic variation: 'nom', 'up', 'down'"},
                    { "name": "genmatch", "type": "int", "description": "genmatch: 0 or 6 = unmatched or jet, 1 or 3 = electron, 2 or 4 = muon, 5 = real tau"},
                    { "name": "id", "type": "string","description": "Tau ID: DeepTau2018v2p5"}
                ],
                "output": {
                    "name": "tes",
                    "type": "real",
                    "description": "tau energy scale"
                },
                "data":tesdata_dmbins
                }, json_file, indent=2)


def plot_dm_graph(setup, year, **kwargs):
    """
    Save TGraphAsymmErrors to a ROOT file containing DM-specific values.

    """

    indir = kwargs.get("indir", "plots_%s" % year)
    outdir = kwargs.get("outdir", "plots_%s" % year)
    tag = kwargs.get("tag", "")
    poi = kwargs.get("poi", "")

    region, poi_val, poi_errhi, poi_errlo = load_measurements(setup, year, tag=tag, indir=indir, poi=poi)
    dm_values= [11,10,1,0]

    graph = ROOT.TGraphAsymmErrors(
        len(dm_values),
        array("d", dm_values),
        array("d", poi_val),
        array("d", [0.50] * len(dm_values)),  # x errors (not used)
        array("d", [0.50] * len(dm_values)),  # x errors (not used)
        array("d", poi_errlo),
        array("d", poi_errhi),
    )


    # set the title and axis labels for the graph
    if poi == "tes":
        graph.SetTitle("TES vs. pT")
        graph.GetYaxis().SetTitle("Energy scale")
    elif poi == "tid_SF":
        graph.SetTitle("ID Scale Factors vs. pT")
        graph.GetYaxis().SetTitle("ID Scale Factors")
    else:
        graph.SetTitle("poi vs. pT")
        graph.GetYaxis().SetTitle("poi")

    graph.GetXaxis().SetTitle("Decay Modes")

    # disable the canvas drawing
    ROOT.gROOT.SetBatch(True)

    # Save the TGraphAsymmErrors to a ROOT file
    wp = "Medium" #VSjetMedium
    wp_VSe = "VVLoose" #VSele
    output_file = ROOT.TFile("%s/TauES_dm_DeepTau2018v2p5VSjet_%s_VSjetMedium_VSeleVVLoose_Run3_Jan11.root" % (outdir,year), "RECREATE")
    #output_file = ROOT.TFile(output_filename, "RECREATE")
    graph.Write(poi)
    output_file.Close()


def plot_dmpt_graph(setup, year, **kwargs):

    indir = kwargs.get("indir", "plots_%s" % year)
    outdir = kwargs.get("outdir", "plots_%s" % year)
    tag = kwargs.get("tag", "")
    dmpt_bins = kwargs.get("dmpt_bins", False)
    poi = kwargs.get("poi", "")

    pt_avg_list, pt_errorup_list, pt_errordown_list = load_pt_values(setup)
    region, poi_val, poi_errhi, poi_errlo = load_measurements(setup, year, tag=tag, indir=indir, poi=poi)

    print(dmpt_bins)
    if not dmpt_bins:
        print(">>> DM inclusive and pt regions")
        graph = ROOT.TGraphAsymmErrors(
            len(pt_avg_list),
            array("d", pt_avg_list),
            array("d", poi_val),
            array("d", pt_errordown_list),
            array("d", pt_errorup_list),
            array("d", poi_errlo),
            array("d", poi_errhi),
        )

        # set the title and axis labels for the graph
        if poi == "tes":
            graph.SetTitle("TES vs. pT")
            graph.GetYaxis().SetTitle("Energy scale")
        elif poi == "tid_SF":
            graph.SetTitle("ID Scale Factors vs. pT")
            graph.GetYaxis().SetTitle("ID Scale Factors")
        else:
            graph.SetTitle("poi vs. pT")
            graph.GetYaxis().SetTitle("poi")

        graph.GetXaxis().SetTitle("pT [GeV]")
        graph.GetYaxis().SetRangeUser(0.65, 1.0)

        # disable the canvas drawing
        ROOT.gROOT.SetBatch(True)

        # Save the TGraphAsymmErrors to a root file
        # idDeepTau2018v2p5VSjet_2>=5 = Medium WP
        # idDeepTau2018v2p5VSe_2>=2 = VVLoose WP
      # idDeepTau2018v2p5VSmu_2>=4 = Tight WP
        output_file = ROOT.TFile("%s/TauES_dm_DeepTau2018v2p5VSjet_2022_postEE_VSjetMedium_VSeleVVLoose_Run3_Jan11.root" % (outdir), "RECREATE")
        #output_file = ROOT.TFile("%s/%s_histograms_%s.root" % (outdir, poi, tag), "RECREATE")
        graph.Write(poi)
        output_file.Close()

    else:
        print(">>> DM exclusive ")
        # define the DM order
        dm_order = ["DM0_", "DM1_", "DM10_", "DM11_"]

        # create a dictionary to store the TGraphAsymmErrors objects
        graphs_dict = {}
        # loop over DMs
        for dm in dm_order:
            #print(">>>>>>>>>>>> %s:" % (dm))
            # filter elements with current DM
            dm_list = [elem for elem in region if dm in elem]
            #print("Elements with %s:" % (dm_list))
            # get values for current DM
            dm_poi_val = [poi_val[region.index(elem)] for elem in dm_list]
            #print("poi for : %s" % (dm_poi_val))
            dm_poi_errhi = [poi_errhi[region.index(elem)] for elem in dm_list]
            #print("poi errhi :  %s" % (dm_poi_errhi))
            dm_poi_errlo = [poi_errlo[region.index(elem)] for elem in dm_list]
            #print("poi errlo :  %s" % (dm_poi_errlo))
            dm_pt_avg_list = [pt_avg_list[region.index(elem)] for elem in dm_list]
            #print("pt_avg_list : %s" % (dm_pt_avg_list))
            dm_pt_errordown_list = [pt_errordown_list[region.index(elem)] for elem in dm_list]
            #print("dm_pt_errordown_list : %s" % (dm_pt_errordown_list))
            dm_pt_errorup_list = [pt_errorup_list[region.index(elem)] for elem in dm_list]
            #print("dm_pt_errorup_list : %s" % (dm_pt_errorup_list))

            # create a TGraphAsymmErrors object for the current DM
            graph = ROOT.TGraphAsymmErrors(
                len(dm_pt_avg_list),
                array("d", dm_pt_avg_list),
                array("d", dm_poi_val),
                array("d", dm_pt_errordown_list),
                array("d", dm_pt_errorup_list),
                array("d", dm_poi_errlo),
                array("d", dm_poi_errhi),
            )

            # set the title and axis labels for the graph
            if poi == "tes":
                graph.SetTitle("TES vs. pT")
                graph.GetYaxis().SetTitle("Energy scale")
            elif poi == "tid_SF":
                graph.SetTitle("ID Scale Factors vs. pT")
                graph.GetYaxis().SetTitle("ID Scale Factors")
            else:
                graph.SetTitle("poi vs. pT")
                graph.GetYaxis().SetTitle("poi")

            graph.GetXaxis().SetTitle("pT [GeV]")

            # add the graph to the dictionary
            graphs_dict[dm] = graph

        # Save all the TGraphAsymmErrors to a single root file
        #output_file = ROOT.TFile("%s/%s_histograms_%s.root" % (outdir, poi, tag), "RECREATE")
        output_file = ROOT.TFile("%s/TauES_dm_DeepTau2018v2p5VSjet_2022_postEE_VSjetMedium_VSeleVVLoose_Run3_Jan11.root" % (outdir), "RECREATE")


        for dm, graph in graphs_dict.items():
            dm_str = dm.replace("_", "") 
            graph.Write(dm_str)
        output_file.Close()

# Save values un json format 

def ensureDirectory(dirname):
    """Make directory if it does not exist."""
    if not os.path.exists(dirname):
        os.makedirs(dirname)
        print(">>> made directory %s" % dirname)


def main(args):

    print("Using configuration file: %s" % args.config)
    with open(args.config, "r") as file:
        setup = yaml.safe_load(file)

    tag = setup["tag"] if "tag" in setup else ""
    year = args.year
    dm_bins = args.dm_bins
    dmpt_bins = args.dmpt_bins
    poi = args.poi
    indir = "plots_%s" % year
    outdir = "plots_%s" % year
    ensureDirectory(outdir)
    CMSStyle.setCMSEra(year)

    if dmpt_bins:
        plot_dmpt_graph(setup, year, dmpt_bins=dmpt_bins, indir=indir, outdir=outdir, tag=tag, poi=poi)
    elif dm_bins:
        plot_dm_graph(setup, year, indir=indir, outdir=outdir, tag=tag, poi=poi)

    save_tes_json(setup, year, dm_bins, dmpt_bins, indir=indir, outdir=outdir, tag=tag, poi=poi)

if __name__ == "__main__":

    description = """This script makes plot of pt-dependants id SF measurments from txt file and config file."""
    parser = ArgumentParser(
        prog="plot_id_SF", description=description, epilog="Success!"
    )
    parser.add_argument(
        "-y",
        "--year",
        dest="year",
        choices=[
            "2016",
            "2017",
            "2018",
            "UL2016_preVFP",
            "UL2016_postVFP",
            "UL2017",
            "UL2018",
            "UL2018_v10",
            "2022_postEE",
            "2022_preEE",
        ],
        type=str,
        default="UL2018",
        action="store",
        help="select year",
    )
    parser.add_argument(
        "-c",
        "--config",
        dest="config",
        type=str,
        default="TauES_ID/config/FitSetupTES_mutau_noSF_pt_DM.yml",
        action="store",
        help="set config file",
    )
    parser.add_argument(
        "--dmpt-bins",
        dest="dmpt_bins",
        default=False,
        action="store_true",
        help="if true then the mutau channel fits are also split by tau decay-mode and pt",
    )
    parser.add_argument(
        "--dm-bins",
        dest="dm_bins",
        default=False,
        action="store_true",
        help="if true then the mutau channel fits are also split by tau decay-mode",
    )
    parser.add_argument(
        "-p",
        "--poi",
        dest="poi",
        default="tid_SF",
        type=str,
        action="store",
        help="use this parameter of interest",
    )

    args = parser.parse_args()
    main(args)
    print(">>>\n>>> done\n")
