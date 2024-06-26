#! /usr/bin/env python
# Author: Izaak Neutelings (Februari 2021) edited by Paola Mastrapasqua (Feb 2024)
import os, sys, re
#sys.path.append('../plots')
from TauFW.common.tools.file import ensuredir
from TauFW.common.tools.utils import repkey
from TauFW.Plotter.plot.utils import LOG
from TauFW.Plotter.plot.Stack import Stack # Var
from TauFW.Plotter.sample.utils import setera
from TauFW.Fitter.plot.postfit import drawpostfit
import TauFW.Plotter.plot.Plot as PLOT
import TauFW.Plotter.sample.SampleStyle as STYLE
from argparse import ArgumentParser
#PLOT.LOG.verbosity=100
argv = sys.argv
description = '''This script generate post fit plots.'''
parser = ArgumentParser(prog="harvestercards",description=description,epilog="Succes!")
parser.add_argument('-y', '--era',      dest='eras', nargs='*', default=['2018UL'], action='store',
                                        help="set era" )
parser.add_argument('-c', '--channel',  dest='channels', choices=['mt','et'], type=str, nargs='+', default=['mt'], action='store',
                                        help="channels to submit")
parser.add_argument('-t', '--tag',      dest='tags', type=str, nargs='+', default=[""], action='store',
                    metavar='TAG',      help="tag for input and output file names")
parser.add_argument('-e', '--outtag',   dest='outtag', type=str, default="", action='store',
                    metavar='TAG',      help="extra tag for output files")
parser.add_argument('-o', '--obs',      dest='observables', type=str, nargs='*', default=[ 'mvis' ], action='store',
                    metavar='VARIABLE', help="name of observable for TES measurement" )
parser.add_argument('-n', '--noshapes', dest='noshapes', default=False, action='store_true',
                                        help="do not include shape uncertainties")
parser.add_argument('-v', '--verbose',  dest='verbose',  default=False, action='store_true',
                                        help="set verbose")
parser.add_argument('-wp', '--workpoint',  dest='workpoint', type=str, default=['Medium'], help="set wp")

args = parser.parse_args()


def main(args):
    print("")
    analysis = 'zee_fr'
    obsset   = args.observables
    channels = args.channels
    eras     = args.eras
    tag      = ""
    bin      = args.workpoint
    title    = "m_{T} < 60 GeV, 60 GeV < m_{vis} < 120 GeV" 
    fname    = "$DIR/$ANALYSIS_$OBS_$CHANNEL-$BIN-$ERA$TAG.shapes.root"
    pname    = "$DIR/$OBS_$CHANNEL-$BIN-$ERA$TAG_$FIT.png"
    #outfile  = "$TAG/$ANALYSIS_%s_$CHANNEL-$ERA%s.inputs.root"%(obs,tag+outtag)
    
    # PLOT SETTINGS
    ZTT = "Z -> #tau#tau" # "Z -> #tau_{#mu}#tau_{h}"
    #STYLE.sample_colors['ZTT'] = STYLE.kOrange-4
        
    procs = [
      'ZTT', 'ZL', 'ZJ', 'W', 'VV', 'TTT', 'TTL', 'TTJ', 'QCD', 'data_obs' #'STT', 'STJ'
    ]
    groups  = [
      #(['^TT*'],'Top','ttbar'), #,STYLE.sample_colors['TT']),
      #(['^TT*','ST*'],'Top','ttbar and single top'),
      #(['W*','ZJ','VV','ST*'],'EWK','Electroweak'), #,STYLE.sample_colors['EWK']),

    ]
    title_dict = {
      'mvis': "m_{vis} (GeV)",
      'mtau': "#mu(#tau_{h}) (GeV)",
      'etau': "e(#tau_{h}) (GeV)",
    }
    tsize   = 0.054
    PLOT._lsize = 0.040 # label size
    ratio   = True
    square  = not ratio and False
    exts    = [ 'png', 'pdf', 'root' ]
    
    # PLOT
    for era in eras:
      setera(era,extra="")
      for channel in channels:
        for obs in obsset:
            ZL = "Z -> ee"
            procs_ = [
                'ZTT', 'ZL', 'ZJ', 'W', 'VV', 'TTT', 'TTL', 'TTJ', 'QCD', 'data_obs'
            ]   
            analysis = 'ztt' 
            dms = [0, 1 , 10, 11]
            
            pos    = 'x=0.56,y=0.88'
            ncol   = 1
        
            for idm in dms:  
               title = "dm %s"%(idm)
               fname    = "$DIR/$ANALYSIS_$BIN_$ERA_dm$DM_PostFitShape.root"
               pname    = "$DIR/$ANALYSIS_$OBS_$CHANNEL-$BIN-$ERA-dm$DM-$TAG_$FIT.png"
               indir  = "."
               outdir = ensuredir("plots/%s"%era)
               xtitle = title_dict.get(obs)
               fname_ = repkey(fname,DIR=indir,ANALYSIS=analysis,OBS=obs,CHANNEL=channel,DM=idm,BIN=bin,ERA=era,TAG=tag)
               pname_ = repkey(pname,DIR=outdir,ANALYSIS=analysis,OBS=obs,CHANNEL=channel,DM=idm,BIN=bin,ERA=era,TAG=tag)
               drawpostfit(fname_,"mt",procs_,pname=pname_,tag=tag,group=groups,title=title,xtitle=xtitle,tsize=tsize,pos=pos,ncol=ncol,ratio=ratio,square=square,exts=exts)
    

if __name__ == '__main__':
    main(args)
    print(">>>\n>>> done\n")
    
