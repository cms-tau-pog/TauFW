#! /usr/bin/env python
# Author: Izaak Neutelings (Februari 2021)
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
argv = sys.argv
description = '''This script creates datacards with CombineHarvester.'''
parser = ArgumentParser(prog="harvestercards",description=description,epilog="Succes!")
parser.add_argument('-y', '--era',      dest='eras', nargs='*', choices=['2016','2017','2018','UL2017','UL2018','UL2016_preVFP','UL2016_postVFP', '2022_postEE', '2022_preEE'], default=['UL2017'], action='store',
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
parser.add_argument('-wp', '--workpoint',  dest='workpoint', choices=['VVLoose','Medium','Tight'], type=str, default=['Tight'], help="set wp")

args = parser.parse_args()


def main(args):
    print("")
    analysis = 'zee_fr'
    obsset   = args.observables
    channels = args.channels
    eras     = args.eras
    tag      = ""
    bin      = args.workpoint
    title    = "m_{T} < 60 GeV, 60 GeV < m_{vis} < 120 GeV, Barrel" #"etau, DeepTau2017v2p1VSe"
    fname    = "$DIR/$ANALYSIS_$OBS_$CHANNEL-$BIN-$ERA$TAG.shapes.root"
    pname    = "$DIR/$OBS_$CHANNEL-$BIN-$ERA$TAG_$FIT.png"
    #outfile  = "$TAG/$ANALYSIS_%s_$CHANNEL-$ERA%s.inputs.root"%(obs,tag+outtag)
    
    # PLOT SETTINGS
    ZTT = "Z -> #tau#tau" # "Z -> #tau_{#mu}#tau_{h}"
    #STYLE.sample_colors['ZTT'] = STYLE.kOrange-4
        
    procs = [
      'ZTT', 'ZL', 'ZJ', 'W', 'VV', 'ST','TTT', 'TTL', 'TTJ', 'QCD', 'data_obs' #'STT', 'STJ'
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
    exts    = [ 'png', 'pdf', 'root', 'C' ]
    
    # PLOT
    for era in eras:
      setera(era,extra="")
      for channel in channels:
        for obs in obsset:
            ZL = "Z -> ee"
            procs_ = [
                'ZTT', 'ZL', 'ZJ', 'W', 'VV', 'ST','TTT', 'TTL', 'TTJ', 'QCD', 'data_obs'
            ]   
            analysis = 'ETauFR'
            etas= ['eta0to1p46','eta1p56to2p5']
            if bin =="Tight":
                dms = [0, 1]
            else:    
                dms = [0, 1 , 10, 11]
            #procs_ = procs[:]
            pos    = 'x=0.56,y=0.88'
            ncol   = 1
            regs =['pass','fail']
            for eta in etas:
               for idm in dms:
                  if eta =='eta0to1p46':
                      title = "0 < #eta < 1.46, dm %s"%(idm)
                  elif eta== 'eta1p56to2p5':
                      title = "1.56 < #eta < 2.50 , dm %s"%(idm) 
                  for reg in regs:
                      if reg == "pass":
                          title += " , Pass"
                      else:
                          title = title.replace(" , Pass", " ") 
                          print(title)
                          title += " , Fail"
                      fname    = "$DIR/$ANALYSIS$BIN_$ETA_dm$DM_PostFitShape.root"
                      pname    = "$DIR/$ANALYSIS_$OBS_$CHANNEL-$BIN-$ERA-$ETA-dm$DM-$REG-$TAG_$FIT.png"
                      indir  = "output/%s/%s"%(era,analysis)
                      outdir = ensuredir("plots/%s"%era)
                      xtitle = title_dict.get(obs)
                      fname_ = repkey(fname,DIR=indir,ANALYSIS=analysis,OBS=obs,CHANNEL=channel,ETA=eta,DM=idm,BIN=bin,ERA=era,TAG=tag)
                      pname_ = repkey(pname,DIR=outdir,ANALYSIS=analysis,OBS=obs,CHANNEL=channel,ETA=eta,DM=idm,BIN=bin,ERA=era,REG=reg,TAG=tag)
                      bin_merged=bin+"_"+reg
                      drawpostfit(fname_,bin_merged,procs_,pname=pname_,tag=tag,group=groups,title=title,xtitle=xtitle,
                                  tsize=tsize,pos=pos,ncol=ncol,ratio=ratio,square=square,reg=reg,exts=exts)
    

if __name__ == '__main__':
    main(args)
    print(">>>\n>>> done\n")
    
