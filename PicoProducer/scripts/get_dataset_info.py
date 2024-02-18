#! /usr/bin/env python
import os, sys, glob, json
import pickle as pk
import numpy as np
from argparse import ArgumentParser
from ROOT import TFile
from TauFW.PicoProducer.storage.utils import getsamples
from TauFW.PicoProducer.analysis.utils import getTotalWeight, getNevt

 
def get_nanoaod_info(args):
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
    n_evt = {}
    n_files = {}
    samples = getsamples(args.era,
                         channel=args.channel,
                         tag=args.tag,
                         dtype=args.dtype,
                         filter='',
                         veto=args.veto,
                         dasfilter='',
                         dasveto='',
                         moddict={},
                         verb=3)
    
    for sample in samples:
        filenames = sample.getfiles(das=False,refresh=False,url=True,limit=-1,verb=0) #Get full filenames for correspondent sample  
        n_evt[sample.name] = 0 #Init empty dict field for a sample
        n_files[sample.name] = len(filenames)
        print(f"Total number of files for {sample.name} is {n_files[sample.name]}")
        for filename in filenames:
            if sample.dtype == 'mc':
                sumw = 0
                sumw = getTotalWeight(filename) #Scan through the Events tree to get a sum of generator weights
                n_evt[sample.name] += sumw
                print ("%s:\t%f"%(filename,sumw))
            elif sample.dtype == 'data':
                n_evt_per_file = 0
                n_evt_per_file = getNevt(filename) #Scan get the number of events of the data file
                n_evt[sample.name] += n_evt_per_file
                print ("%s:\t%f"%(filename,n_evt_per_file))
            else:
                print(f'Unable to determine sample type for:{sample}')
                break
        print(f"Total number of n_events/sum_genw for {sample.name} is {n_evt[sample.name]}")
                
    json_dict = json.dumps({"n_evt"   : n_evt,
                            "n_files" : n_files
                            },
                           indent=4
                           ) #Produce json dictionary
    with open(args.json_file, "w") as outfile:
        print("Writing sumw dict to %s"%(args.json_file))
        outfile.write(json_dict) #Dump json dict to file


def main():
    """
    Main entry point for the script to get the information about NanoAOD files.
    """
    description = "Script that extracts genweights from  MC samples and n events from Data"
    CMSSW_BASE = os.environ['CMSSW_BASE']
    parser = ArgumentParser(prog='modify_cutflow_hist.py',description=description,epilog="Good luck!")
    parser = ArgumentParser(add_help=True)
    parser.add_argument('-o','--json_file',     dest='json_file', default="nanoaod_info.json",
                                                help="path to the json file containing sumw dict")
    parser.add_argument('--veto',               dest='veto', default=[], nargs='+',
                                                help='String to filter files by name')
    parser.add_argument('-e','--era',           dest='era', default='2022_postEE', nargs='?',
                                                help="year or era to specify the sample list")
    parser.add_argument('-c','--channel',       dest='channel', default='', nargs='?',
                                                help="skimming or anallysis channel to run")
    parser.add_argument('--dtype',              dest='dtype', default=['data','mc'], nargs='+',
                                                help="Sample type (data or/and mc) to perform scan on")
    parser.add_argument('-t','--tag',           dest='tag', default="",
                                                help="Additional tag for pico files")
    parser.add_argument('--get_w',              dest='get_nanoaod_w', action='store_true',
                                                help="get weights from nanoaod files")
    
    cmd_args = sys.argv[1:]
    args = parser.parse_args(cmd_args)
    if hasattr(args,'tag') and len(args.tag)>=1 and args.tag[0]!='_': args.tag = '_'+args.tag
    
    print('Acquring weights from nanoaod...')
    get_nanoaod_info(args)
    print(">>> Done!")
        
        
if __name__ == '__main__':
    main()
