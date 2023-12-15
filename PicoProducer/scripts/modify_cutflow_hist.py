#! /usr/bin/env python
import os, sys, glob, json
import pickle as pk
import numpy as np
from argparse import ArgumentParser, Namespace
from ROOT import TFile
from TauFW.PicoProducer.storage.utils import getsamples
from TauFW.PicoProducer.analysis.utils import getTotalWeight,  getNevt
from IPython import embed

 
def get_nanoaod_info(args):
    """
    Analyzes NanoAOD samples and extracts total number of events
    and the number of files for each sample. Generates a JSON file containing the results.

    Parameters:
    - args (Namespace): Command-line arguments and configurations.
     Args:
    - use_taufw_samples (bool): Flag indicating whether to use TauFW samples.
    - era (str): Data-taking era (e.g., "2016", "2017", "2018").
    - channel (str): Physics analysis channel (e.g., "mutau") that is passed to getsamples function.
    - tag (str): Version tag for the samples.
    - dtype (str): Data type ("mc" for Monte Carlo, "data" for real data).
    - veto (bool): Veto flag for samples.
    - sample_path (str): Path to the directory containing sample files.
    - samples (list): List of sample names to analyze (empty for all samples).
    - sumw_file (str): Output file path for the JSON file containing analysis results.

    Sample Usage:
    ```python
    # Example usage of the function
    args = Namespace(
        use_taufw_samples=True,
        era="2016",
        channel="mutau",
        tag="v2",
        dtype="mc",
        veto=False,
        sample_path="/path/to/samples/",
        samples=["SingleMuonRun2022F", "EGammaRun2022G"],
        sumw_file="output/sumw_info.json"
    )
    get_nanoaod_info(args)
    ```
   
    """
    
    n_evt = {}
    n_files = {}
    if args.use_taufw_samples:
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
    else:
        sample_names = glob.glob1(args.sample_path, '*')
        samples = []
        for the_name in sample_names:
            the_dtype = 'data' if 'Run' in the_name else 'mc'
            files = glob.glob(f'{args.sample_path}{the_name}/*.root')
            the_sample = Namespace(name=the_name,
                                   dtype=the_dtype,
                                   files=files,
                                   )
            samples.append(the_sample)
    for sample in samples:
        if args.use_taufw_samples:
            filenames = sample.getfiles(das=False,refresh=False,url=True,limit=-1,verb=0) #Get full filenames for correspondent sample
        else: 
            filenames = sample.files  
        if (not len(args.samples)) or any([True for sample2choose in args.samples if sample2choose in sample.name]): 
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
    with open(args.sumw_file, "w") as outfile:
        print("Writing sumw dict to %s"%(args.sumw_file))
        outfile.write(json_dict) #Dump json dict to file
            
def check_sample_name(full_filename, args):
    filename = os.path.splitext(os.path.basename(full_filename))[0]
    sample_name = filename.split('_' + args.channel)[0]
    
    faled_check = (args.samples and sample_name not in args.samples) or \
        ( args.veto and (sample_name in args.veto) ) or \
            (all(['data' not in the_dtype for the_dtype in args.dtype]) and 'Run' in sample_name) or \
                (all(['mc' not in the_dtype for the_dtype in args.dtype]) and 'Run' not in sample_name)
    
    return sample_name if not faled_check else None 
   
    

def modify_cutflow_hist(args):
    """
    Modifies the contents of a cutflow histogram in ROOT files based on NanoAOD event information
    stored in a JSON file. It can print the number of events before its update with the values form JSON.

    Parameters:
    - args (Namespace): Command-line arguments and configurations.
     Args:
    - sumw_file (str): Path to the JSON file containing NanoAOD event information.
    - bin (int): Bin index in the cutflow histogram to be modified.
    - pico_dir (str): Directory containing Pico Framework ROOT files.
    - era (str): Data-taking era (e.g., "2016", "2017", "2018").
    - channel (str): Physics analysis channel (e.g., "muon", "electron").
    - tag (str): Version tag for the samples.
    - modify_cutflow (bool): Flag indicating whether to modify the cutflow histogram.


    Sample Usage:
    ```python
    # Example usage of the function
    args = Namespace(
        sumw_file="input/sumw_info.json",
        bin=3,
        pico_dir="/path/to/pico/files",
        era="2022_postEE",
        channel="mutau",
        tag="v2",
        modify_cutflow=True
    )
    modify_cutflow_hist(args)
    ```
    """
    if len(args.sumw_file)>1:
        sumw_file = args.sumw_file
    else:
        print(f'Unable to find json file: {args.sumw_file}')
        exit()
    print('Opening file: %s'%(sumw_file))
    bin_id = int(args.bin)
    with open(sumw_file, "r") as tf:
        json_content = json.load(tf)
        n_evt = json_content['n_evt']      
        filenames = glob.glob(f'{args.pico_dir}/*/*{args.channel}{args.tag}.root')
        print(f'Samples: {filenames}')
        print("\n%40s:\t%15s%15s%15s"%('sample_name', 'cutflow_norm', 'nanoaod_norm', 'difference'))
        for fname in filenames:
            sample = check_sample_name(fname, args)
            
            if sample:
                root_file = TFile(fname, 'UPDATE' if args.modify_cutflow else 'READ' )
                cutflow_hist = root_file.Get('cutflow')
                cf_n   = int(cutflow_hist.GetBinContent(bin_id))
                if sample in n_evt.keys():
                    nano_n = int(n_evt[sample])
                    diff = cf_n - nano_n
                    print("%40s:\t%15d%15d%15d"%(sample, cf_n, nano_n, diff))
                    if args.modify_cutflow:
                        cutflow_hist.SetBinContent(bin_id, float(n_evt[sample]))
                        cutflow_hist.Write()
                else:
                    print('Warning: Did not found normalization factor for %s sample in dict: ' %(fname)+ str(n_evt.keys()))   
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
    CMSSW_BASE = os.environ['CMSSW_BASE']
    parser = ArgumentParser(prog='modify_cutflow_hist.py',description=description,epilog="Good luck!")
    parser = ArgumentParser(add_help=True)
   
    parser.add_argument('-o','--sumw_file',     dest='sumw_file', default="nanoaod_sumw.json",
                                                help="path to the json file containing sumw dict")
    parser.add_argument('--samples',            dest='samples', default=[], nargs='+',
                                                help='String to filter files by name')
    parser.add_argument('--sample_path',        dest='sample_path', default='/eos/cms/store/group/phys_tau/irandreo/Run3_22_postEE_new/',
                                                help="Path to the ")
    parser.add_argument('--pico_dir',           dest='pico_dir', default=f'{CMSSW_BASE}/src/TauFW/PicoProducer/analysis', nargs='?',
                                                help='path to directory containing pico samples')
    parser.add_argument('--dtype',             dest='dtype', default=['data','mc'], nargs='+',
                                                help="Sample type (data or/and mc) to perform scan on")
    parser.add_argument('--veto',               dest='veto', default=[], nargs='+',
                                                help='String to filter files by name')
    parser.add_argument('-e','--era',           dest='era', default='2022_postEE', nargs='?',
                                                help="year or era to specify the sample list")
    parser.add_argument('-c','--channel',       dest='channel', default='mutau', nargs='?',
                                                help="skimming or anallysis channel to run")
    parser.add_argument('--use_taufw_samples',  dest='use_taufw_samples', action='store_true',
                                            help="Use getsamples function form TauFW")
    parser.add_argument('--bin',                dest='bin', default=17, nargs='?',
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
        get_nanoaod_info(args)
    if args.modify_cutflow: print('Modifying cutflow histogram...')
    modify_cutflow_hist(args) 
    print(">>> Done!")
        
        
if __name__ == '__main__':
    main()
