#! /usr/bin/env python
import os, sys, glob, json
import pickle as pk
import numpy as np
from argparse import ArgumentParser
from ROOT import TFile
from TauFW.PicoProducer.storage.utils import getsamples
from TauFW.PicoProducer.analysis.utils import getTotalWeight

 
def get_nanoaod_sumw(args):
    """
    Get the sum of event weights (sumw) from NanoAOD and generate a JSON file to store them

    This function takes a set of arguments, including the era, channel, and tag identifiers,
    and a list of sample names to extract the sumw for. It retrieves the list of NanoAOD samples 
    from storage, iterates through their files, and sums the event weights for each file. The calculated
    sumw values are stored in a dictionary and saved as a JSON file.

    Args:
        args (Namespace): A namespace containing the following attributes:
            - vetoes (list): List of sample name substrings to exclude (optional).
            - era (str): Era identifier.
            - channel (str): Channel identifier.
            - tag (str): Tag identifier.
            - sumw_file (str): Path to the output JSON file for storing sumw values.

    Returns:
        None

    Prints:
        - Sample names being processed.
        - Sumw values for each file of each sample.
        - Information about writing the sumw dictionary to the JSON file.

    Example usage:
       $  python3 modify_cutflow_hist.py --get_w --veto 'SingleMuon' 'DY*' --sumw_file $CMSSW_BASE/nanoaod_sumw.json

    """
    vetoes       = args.vetoes
    dtype        = ['mc']
    sumw_dict = {}
    path2sampleP_dir = "/eos/user/o/oponcet/TauPOG/Run3_v1/2022_postEE/"
    samples = glob.glob1(path2sampleP_dir, '*')
    print(samples)
    for sample in samples:
        print(sample)
        filenames = glob.glob(f'{path2sampleP_dir}{sample}/*.root')
        if not any([True for veto in args.vetoes if veto in sample]):
            sumw_dict[sample] = 0
            for filename in filenames:
                sumw = 0
                sumw = getTotalWeight(filename) 
                sumw_dict[sample] += sumw
                print ("%s:\t%f"%(filename,sumw))
    json_sumw_dict = json.dumps(sumw_dict, indent=4)
    with open(args.sumw_file, "w") as outfile:
        print("Writing sumw dict to %s"%(args.sumw_file))
        outfile.write(json_sumw_dict)


# def check_sample_name(sample_name_full, keys):
#     print("sample_name_full = ", sample_name_full)
#     print("keys = ", keys)
#     for sample_name in keys:
#         print("sample_name in key = ", sample_name)
#         if sample_name in sample_name_full:
#             print("sample_name to retrun = ", sample_name)
#             return sample_name
#     return None
            
def check_sample_name(sample_name_full, keys):
    sample_name = sample_name_full.replace("_mutau", "").replace("_mumu", "").replace("_etau", "")
    # print("sample_name_full = ", sample_name_full)
    # print("sample_name cut = ", sample_name)
    # print("keys = ", keys)
    if sample_name in keys:
        #print("sample_name to retrun = ", sample_name)
        return sample_name
    return None
       

def modify_cutflow_hist(args):
    """
    Modify the cutflow histogram in ROOT files based on normalization factors.

    This function takes a set of arguments, including the location of a JSON file
    containing normalization factors and a list of ROOT files with cutflow histograms.
    It updates the cutflow histogram in each ROOT file with the corresponding
    normalization factor from the JSON file.

    Args:
        args (Namespace): A namespace containing the following attributes:
            - sumw_file (str): Path to the JSON file containing normalization factors.
            - bin (int): Bin index to update in the cutflow histogram.
            - pico_dir (str): Directory containing ROOT files (optional).
            - era (str): Era identifier.
            - channel (str): Channel identifier.
            - tag (str): Tag identifier.
            - vetoes (list): List of sample name substrings to exclude (optional).
            - modify_cutflow (bool): True to modify the cutflow histogram, False to read it and compare with the info from JSON.
    Example usage:
       $ python3 modify_cutflow_hist.py --veto 'SingleMuon' 'DY*' --sumw_file $CMSSW_BASE/nanoaod_sumw.json 
       $ python3 modify_cutflow_hist.py -m --veto 'SingleMuon' 'DY*' --sumw_file $CMSSW_BASE/nanoaod_sumw.json

    """
    if len(args.sumw_file)>=1:
        sumw_file = args.sumw_file
    else:
        print(f'Unable to find file with weights:{args.sumw_file}')
        exit()
    print('Opening file: %s'%(sumw_file))
    bin_id = int(args.bin)
    with open(sumw_file, "r") as tf:
        norm_dict = json.load(tf)
        if len(args.pico_dir) > 1: sample_dir = args.pico_dir
        else: sample_dir = "$CMSSW_BASE/src/TauFW/PicoProducer/"
        print("sample_dir ", sample_dir)
        #samples = glob.glob(sample_dir + '/analysis/' + args.era + '/*/*' + args.channel + args.tag + '.root')
        samples = glob.glob(sample_dir + args.era + '/*/*' + args.channel + args.tag + '.root')
        print("samples ", samples)
        print('Samples: ' + str(map(os.path.basename, samples)))
        print("\n%40s:\t%15s%15s%15s"%('sample_name', 'cutflow_norm', 'nanoaod_norm', 'difference'))
        for sample in samples:
            sample_name_full = os.path.splitext(os.path.basename(sample))[0]
            if any([True for veto in args.vetoes if veto in sample_name_full]) : continue
            root_file = TFile(sample, 'UPDATE' if args.modify_cutflow else 'READ' )
            cutflow_hist = root_file.Get('cutflow')
            sample_name = check_sample_name(sample_name_full, norm_dict.keys())
            if sample_name:
                if args.modify_cutflow: cutflow_hist.SetBinContent(bin_id, float(norm_dict[sample_name]))
                cf_n   = int(cutflow_hist.GetBinContent(bin_id))
                nano_n = int(norm_dict[sample_name])
                diff = cf_n - nano_n
                print("%40s:\t%15d%15d%15d"%(sample_name, cf_n, nano_n, diff))
                if args.modify_cutflow: cutflow_hist.Write()  
            else:
                print('ERROR: Did not found normalization factor for %s sample in dict: ' %(sample_name_full)+ str(norm_dict.keys()))   
            root_file.Close()

def main():
    """
    Main entry point for the script to update cutflow genweights using NanoAOD values.

    This script is designed to update the cutflow genweights with values obtained directly
    from NanoAOD and stored in a JSON file.
    It provides various command-line options for customization.

    Args:
        All keys from parser
    Example usage:
        $ python3 modify_cutflow_hist.py -o nanoaod_sumw.json --pico_dir /path/to/pico -e UL2018 -c mutau
        $ python3 modify_cutflow_hist.py --get_w -m
    """
    description = "Script that upades cutflow genweights with values obtained directly from NanoAOD and stored at pkl file"
    parser = ArgumentParser(prog='modify_cutflow_hist.py',description=description,epilog="Good luck!")
    parser = ArgumentParser(add_help=True)
    parser.add_argument('-o','--sumw_file',     dest='sumw_file', default="nanoaod_sumw.json",
                                                help="path to the json file containing sumw dict")
    parser.add_argument('--pico_dir',           dest='pico_dir', default='', nargs='?',
                                                help='path to directory containing pico samples')
    parser.add_argument('--veto',               dest='vetoes', default=[], nargs='+',
                                                help='String to filter files by name')
    parser.add_argument('-e','--era',           dest='era', default='2022_postEE', nargs='?',
                                                help="year or era to specify the sample list")
    parser.add_argument('-c','--channel',       dest='channel', default='', nargs='?',
                                                help="skimming or anallysis channel to run")
    parser.add_argument('--bin',                dest='bin', default=16, nargs='?',
                                                help='')
    parser.add_argument('-t','--tag',           dest='tag', default="",
                                                help="Additional tag for pico files")
    parser.add_argument('--get_w',              dest='get_nanoaod_w', action='store_true',
                                                help="get weights from nanoaod files")
    parser.add_argument('-m','--modify',        dest='modify_cutflow', action='store_true',)
    
    cmd_args = sys.argv[1:]
    args = parser.parse_args(cmd_args)
    if hasattr(args,'tag') and len(args.tag)>=1 and args.tag[0]!='_': args.tag = '_'+args.tag
    
    if args.get_nanoaod_w:
        print('Acquring weights from nanoaod...')
        get_nanoaod_sumw(args)
    if args.modify_cutflow: print('Modifying cutflow histogram...')
    modify_cutflow_hist(args) 
    print(">>> Done!")
        
        
if __name__ == '__main__':
    main()
