from postfit_TES import drawpostfit
import yaml

def main(args):
    configs   = args.configs
    for config in configs:
        if not config.endswith(".yml"): # config = channel name
            config = "config/setup_%s.yml"%(config) # assume this file name pattern
        print(">>> Using configuration file: %s"%config)
        with open(config, 'r') as file:
            setup = yaml.safe_load(file)
        tag = setup.get('tag',"")

    for region in setup["regions"]:
        if region == "baseline": continue

        else:
            print(">>>   Region: %s"%(region))
            era = "UL2018_v10" ## Hardcoded
            # Define the parameters
            fname = './output_%s/fitDiag/PostFitShape_%s_%s_%s.root' %(era,era,tag,region)
            # bin = 'DM0'  # This should match the bin name in your ROOT file
            procs = setup["processes"]  # Replace with the actual processes in your file
            # procs = ["ZTT","ZL","ZJ","W","VV","ST","TTT","TTL","TTJ","QCD","data_obs"]  # Replace with the actual processes in your file
            text = setup["regions"][region]["title"]
            print(">>>   Title: %s"%(text))


            # Call the function
            drawpostfit(fname, region, procs, outdir='output_plots', pname='$FIT.png', ratio=True, era=era,text=text)


if __name__ == "__main__":
    from argparse import ArgumentParser, RawTextHelpFormatter
    description = """Simple plotting script for postfit plots"""

    parser = ArgumentParser(prog="plot",description=description,epilog="Good luck!")

    parser.add_argument('-c', '--config', '--channel',
                                         dest='configs', type=str, nargs='+', default=['config/setup_mutau.yml'], action='store',
                                         help="config file(s) containing channel setup for samples and selections, default=%(default)r" )
    
    args = parser.parse_args()
 
    main(args)
    print("\n>>> Done.")