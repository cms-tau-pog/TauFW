#! /usr/bin/env python
# Author: Izaak Neutelings (August 2020)
# Description: Simple plotting script for pico analysis tuples
# Instructions:
#   ./plot_v10.py -y 2018 -c mutau
#   ./plot_v10.py -y 2018 -c config/setup_mutau.yml
#   ./plot_v10.py -y 2018 -c mutau -S baseline -V m_vis
#>>>>IMPORTANT!!
#>>>>Run with --serial option if using py3:
#   ./plot_v10.py -y 2018 -c mutau --serial
from config.samples_v12 import *
from TauFW.Plotter.plot.string import filtervars
from TauFW.Plotter.plot.utils import LOG as PLOG
from TauFW.Plotter.plot.Plot import Plot, deletehist
import TauFW.Plotter.sample.SampleStyle as STYLE
import yaml

def plot(sampleset,setup,region,parallel=True,tag="",extratext="",outdir="plots",era="",
         varfilter=None,selfilter=None,fraction=False,pdf=False):
  """Test plotting of SampleSet class for data/MC comparison."""
  LOG.header("plot")
  
  # Define the channel : mutau only supported for now 
  channel  = setup["channel"]
  
  selections = [ ]

  # Check region and use the right TES value from 
  print("Region = %s" %(region))
  if region in setup['regions']: # add extra regions on top of baseline
      print(region)
      if region == 'DM0' :
        #channel = "mutau_TES0p914"
        #channel = "mutau_TES0p930"
        channel = "mutau_TES0p932"
        #channel = "mutau_DM0_mt65"
      # elif region == 'DM0_pt1' :
      #   #channel = "mutau_TES0p914"
      #   #channel = "mutau_TES0p930"
      #   channel = "mutau_TES0p892"
      # elif region == 'DM0_pt2' :
      #   #channel = "mutau_TES0p914"
      #   #channel = "mutau_TES0p930"
      #   channel = "mutau_TES0p952"
      elif region == 'DM1':
        #channel = "mutau_TES0p980"
        channel = "mutau_TES0p984"
        #channel = "mutau_TES0p901"
        #channel = "mutau_DM1_mt65"
      elif region == 'DM10':
        #channel = "mutau_TES0p998"
        #channel = "mutau_TES0p972" 
        #channel = "mutau_TES1p012"
        channel = "mutau_TES1p002"
        #channel = "mutau_DM10_mt65"
      elif region == 'DM11':
        #channel = "mutau_TES1p012"
        #channel = "mutau_TES1p008"
        #channel = "mutau_TES1p018"
        channel = "mutau_TES1p006"
        #channel = "mutau_DM11_mt65"
      else :
        channel = setup["channel"]

      print("Channel = %s" %(channel))
      skwargs = setup['regions'][region].copy() # extra key-word options
      assert 'definition' in skwargs
      selstr = setup['baselineCuts']+" && "+skwargs.pop('definition')
      selections.append(Sel(region,selstr,**skwargs))

  # Define selection     
  selections = filtervars(selections,selfilter) # filter variable list with -S/--sel flag
  
  # VARIABLES
  variables = [
    Var('pt_1',  "Muon pt",    40,  0, 120, ctitle={'etau':"Electron pt",'tautau':"Leading tau_h pt",'mumu':"Leading muon pt",'emu':"Electron pt"},cbins={"nbtag\w*>":(40,0,200)}),
    Var('pt_2',  "tau_h pt",   40,  0, 120, ctitle={'tautau':"Subleading tau_h pt",'mumu':"Subleading muon pt",'emu':"Muon pt"},cbins={"nbtag\w*>":(40,0,200)}),
    Var('eta_1', "Muon eta",   30, -3,   3, ctitle={'etau':"Electron eta",'tautau':"Leading tau_h eta",'mumu':"Leading muon eta",'emu':"Electron eta"},ymargin=1.7,pos='T',ncols=2),
    Var('eta_2', "tau_h eta",  30, -3,   3, ctitle={'etau':"Electron eta",'tautau':"Subleading tau_h eta",'mumu':"Subleading muon eta",'emu':"Muon eta"},ymargin=1.7,pos='T',ncols=2),
    Var('mt_1',  "mt(mu,MET)", 40,  0, 200, ctitle={'etau':"mt(mu,MET)",'tautau':"mt(tau,MET)",'emu':"mt(e,MET)"},cbins={"nbtag\w*>":(50,0,250)}),
    Var("jpt_1",  29,   10,  300, veto=[r"njets\w*==0"]),
    Var("jpt_2",  29,   10,  300, veto=[r"njets\w*==0"]),
    Var("jeta_1", 53, -5.4,  5.2, ymargin=1.6,pos='T',ncols=2,veto=[r"njets\w*==0"]),
    Var("jeta_2", 53, -5.4,  5.2, ymargin=1.6,pos='T',ncols=2,veto=[r"njets\w*==0"]),
    Var('npv',    40,  0,  80),
    Var('njets',   8,  0,   8),
    Var('nbtag', "Number of b jets (Medium, pt > 30 GeV)", 8, 0, 8),
    Var('met',    50,  0, 150,cbins={"nbtag\w*>":(50,0,250)}),
   #Var('genmet', 50,  0, 150, fname="$VAR_log", logyrange=4, data=False, logy=True, ncols=2, pos='TT'),
    Var('pt_ll',   "p_{T}(mutau_h)", 25, 0, 200, ctitle={'etau':"p_{T}(etau_h)",'tautau':"p_{T}(tau_htau_h)",'emu':"p_{T}(emu)"}),
    Var('dR_ll',   "DR(mutau_h)",    30, 0, 6.0, ctitle={'etau':"DR(etau_h)",'tautau':"DR(tau_htau_h)",'emu':"DR(emu)"}),
    Var('deta_ll', "deta(mutau_h)",  20, 0, 6.0, ctitle={'etau':"deta(etau_h)",'tautau':"deta(tautau)",'emu':"deta(emu)"},logy=True,pos='TRR',cbins={"abs(deta_ll)<":(10,0,3)}), #, ymargin=8, logyrange=2.6
    Var('dzeta',  56, -180, 100, pos='L;y=0.87',units='GeV',cbins={"nbtag\w*>":(35,-220,130)}),
  ]
  if 'tau' in channel: # mutau, etau, tautau
    loadmacro("python/macros/mapDecayModes.C") # for mapRecoDM
    dmlabels  = ["h^{#pm}","h^{#pm}h^{0}","h^{#pm}h^{#mp}h^{#pm}","h^{#pm}h^{#mp}h^{#pm}h^{0}","Other"]
    variables += [
      Var('m_vis',          40,  0, 200, fname="mvis",ctitle={'mumu':"m_mumu",'emu':"m_emu"},logy=False, cbins={"pt_\d>":(50,0,250),"nbtag\w*>":(60,0,300)},cpos={"pt_\d>[1678]0":'LL;y=0.88'}),
      #Var('m_vis',          20,  0, 200, fname="mvis_coarse",ctitle={'mumu':"m_mumu",'emu':"m_emu"},logy=False, cbins={"pt_\d>":(25,0,250),"nbtag\w*>":(30,0,300)},cpos={"pt_\d>[1678]0":'LL;y=0.88'}),
      # Var("m_2",            30,  0,   3, title="m_tau",veto=["njet","nbtag","dm_2==0"]),
      # Var("dm_2",           14,  0,  14, fname="dm_2",title="Reconstructed tau_h decay mode",veto="dm_2==",position="TMC",ymargin=1.2),
      #Var("mapRecoDM(dm_2)", 5,  0,   5, fname="dm_2_label",title="Reconstructed tau_h decay mode",veto="dm_2==",position="TT",labels=dmlabels,ymargin=1.2),
      #Var("pzetavis", 50,    0, 200 ),
      #Var('rawDeepTau2017v2p1VSjet_2', "rawDeepTau2017v2p1VSjet", 50, 0.00, 1, ymin = 1e3, ncols=2,pos='L;y=0.85',logy=True,ymargin=1.5,cbins={"VSjet_2>":(60,0.4,1)}),
      # Var('rawDeepTau2017v2p1VSjet_2', "rawDeepTau2017v2p1VSjet", 60, 0.85, 1, ymin = 1e2, fname="$VAR_zoom",ncols=2,pos='L;y=0.85'),
      # Var('rawDeepTau2017v2p1VSjet_2', "rawDeepTau2017v2p1VSjet", 35, 0.88, 1, ymin = 1e2, fname="$VAR_zoom1",ncols=2,pos='L;y=0.85'),
      # Var('rawDeepTau2017v2p1VSjet_2', "rawDeepTau2017v2p1VSjet", 63, 0.88, 1, ymin = 1e2, fname="$VAR_zoom2",ncols=2,pos='L;y=0.85'),
      # Var('rawDeepTau2017v2p1VSjet_2', "rawDeepTau2017v2p1VSjet", 125, 0.88, 1, ymin = 1e2, fname="$VAR_zoom3",ncols=2,pos='L;y=0.85'),
      # Var('rawDeepTau2017v2p1VSe_2',   "rawDeepTau2017v2p1VSe",   90, 0.10, 1, ymin = 1e2, fname="$VAR_zoom",ncols=2,logy=True,logyrange=4,pos='L;y=0.85'),
      # Var('rawDeepTau2017v2p1VSmu_2',  "rawDeepTau2017v2p1VSmu",  50, 0.80, 1, ymin = 1e1, fname="$VAR_zoom",ncols=2,logy=True,logyrange=5,pos='L;y=0.85'),
      # # #Var('rawDeepTau2018v2p5VSjet_2', "rawDeepTau2018v2p5VSjet", 50, 0.00, 1, ymin = 1e3, ncols=2,pos='L;y=0.85',logy=True,ymargin=1.5,cbins={"VSjet_2>":(60,0.4,1)}),
      # Var('rawDeepTau2018v2p5VSjet_2', "rawDeepTau2018v2p5VSjet", 20, 0.95, 1, ymin = 1e2, fname="$VAR_zoom",ncols=2,pos='L;y=0.85'),
      # # Var('rawDeepTau2018v2p5VSjet_2', "rawDeepTau2018v2p5VSjet", 21, 0.96, 1, ymin = 1e2, fname="$VAR_zoom0",ncols=2,pos='L;y=0.85'),
      # # Var('rawDeepTau2018v2p5VSjet_2', "rawDeepTau2018v2p5VSjet", 42, 0.96, 1, ymin = 1e2, fname="$VAR_zoom1",ncols=2,pos='L;y=0.85'),
      # # Var('rawDeepTau2018v2p5VSjet_2', "rawDeepTau2018v2p5VSjet", 84, 0.96, 1, ymin = 1e2, fname="$VAR_zoom2",ncols=2,pos='L;y=0.85'),
      # # Var('rawDeepTau2018v2p5VSjet_2', "rawDeepTau2018v2p5VSjet", 250, 0.96, 1, ymin = 1e2, fname="$VAR_zoom3",ncols=2,pos='L;y=0.85'),
      # Var('rawDeepTau2018v2p5VSe_2',   "rawDeepTau2018v2p5VSe",   80, 0.20, 1, ymin = 1e2, fname="$VAR_zoom",ncols=2,logy=True,logyrange=4,pos='L;y=0.85'),
      # Var('rawDeepTau2018v2p5VSmu_2',  "rawDeepTau2018v2p5VSmu",  25, 0.90, 1, ymin = 1e1, fname="$VAR_zoom",ncols=2,logy=True,logyrange=5,pos='L;y=0.85'),
      # Var('rawDeepTau2018v2p5VSjet_2', "rawDeepTau2018v2p5VSjet", 50, 0.00, 1, ymin = 1e1, fname="$VAR_allRange", ncols=2,pos='L;y=0.85',logy=True,ymargin=1.5),
      #Var('rawDeepTau2018v2p5VSe_2',   "rawDeepTau2018v2p5VSe",   50, 0.00, 1, ymin = 1e3, fname="$VAR_allRange", ncols=2,pos='L;y=0.85',logy=True,ymargin=1.5),
      #Var('rawDeepTau2018v2p5VSmu_2',  "rawDeepTau2018v2p5VSmu",  50, 0.00, 1, ymin = 1e3, fname="$VAR_allRange", ncols=2,pos='L;y=0.85',logy=True,ymargin=1.5),

    ]

  variables  = filtervars(variables,varfilter)  # filter variable list with -V/--var flag
  
  # PLOT
  outdir = ensuredir(repkey(outdir,CHANNEL=channel,ERA=era))
  exts   = ['png','pdf'] if pdf else ['png'] # extensions
  for selection in selections:
    print(">>> Selection %r: %r"%(selection.title,selection.selection))
    
    # Mapping for region replacement
    region_mapping = {'DM0': 'dm_2==0', 'DM1': 'dm_2==1', 'DM10': 'dm_2==10', 'DM11': 'dm_2==11'}
    region_cut = region_mapping.get(region, region)


    # Extract relevant parameters for modifying the sample
    sampleAppend = ""
    
    if region == "DM0":
      dy_shape_val =  0.355279177427
    elif region == "DM1":
      dy_shape_val = -0.714294493198
    elif region == "DM10":
      dy_shape_val =  0.264388531446
    elif region == "DM11":
      dy_shape_val = -0.808251798153
    else:
      dy_shape_val = 1

    dy_weight_ZTT = "(genmatch_2==5 ? 1+((zptweight+0.1*(zptweight-1))*%s ): 1)" %(dy_shape_val)
    dy_weight_ZL = "(genmatch_2>0 && genmatch_2<5 ? 1+((zptweight+0.1*(zptweight-1))*%s): 1)" %(dy_shape_val)
    dy_weight_ZJ = "(genmatch_2==0 ? 1+((zptweight+0.1*(zptweight-1))*%s ): 1)" %(dy_shape_val)

    # Create a new sample set with systematic variations
    # sampleset.gethists(obsset,selection,method=method,split=True,
    #                            parallel=parallel,filter=filters,veto=vetoes,replaceweight=weightReplaced)


    stacks = sampleset.getstack(variables,selection,method='QCD_OSSS',scale=1, parallel=parallel)

    # sampleset.get("ZTT", unique=True,split=True,method='QCD_OSSS').setextraweight(dy_weight_ZTT)
    # sampleset.get("ZL", unique=True,split=True,method='QCD_OSSS').setextraweight(dy_weight_ZL)
    # sampleset.get("ZJ", unique=True,split=True,method='QCD_OSSS').setextraweight(dy_weight_ZJ)


    print("sampleset = %s" %(sampleset))

    # Applying SFs on specific processes -- do after splitting and renaming! 
    if "scaleFactors" in setup:
        #print("scaleFactors")
        for SF in setup["scaleFactors"]:
            #print("Scale Factor =" , SF)
            SFset = setup["scaleFactors"][SF]
            print("Reweighting with SF -- %s -- for the following processes: %s"%(SF, SFset["processes"]))
            for proc in SFset["processes"]:
                #print("proc : %s" %(proc))
                for cond in SFset["values"]:
                  #print("cond = ", cond)
                  #print("region_cut = ", region_cut)
                  if cond == region_cut : 
                    weight = SFset["values"][cond]
                    print("Applying weight: %s to process %s" %(weight,proc))
                    for stack, variable in stacks.items():
                      for h in stack.hists:
                        if proc in h.GetName().split('_')[1]:
                          #print("hist name =" , h.GetName()) 
                          #print("hist name split('_')[1] =" , h.GetName().split('_')[1]) 
                          h.Scale(weight) 

    print("stacks = %s" %(stacks))
    

    fname  = "%s/$VAR_%s-%s-%s$TAG"%(outdir,channel.replace('mu','m').replace('tau','t'),selection.filename,era)
    text   = "%s: %s"%(channel.replace('mu',"#mu").replace('tau',"#tau_{h}"),selection.title)
    if extratext:
      text += ("" if '\n' in extratext[:3] else ", ") + extratext
    #for stack, variable in stacks.iteritems():
    for stack, variable in stacks.items(): # python 3
      position = "" #variable.position or 'topright'
      stack.draw(fraction=fraction)
      stack.drawlegend() #position)
      stack.drawtext(text)
      stack.saveas(fname,ext=exts,tag=tag)
      stack.close()
  

def main(args):
  configs   = args.configs
  eras      = args.eras
  parallel  = args.parallel
  varfilter = args.varfilter
  selfilter = args.selfilter
  notauidsf = args.notauidsf
  extratext = args.text
  fraction  = args.fraction
  pdf       = args.pdf
  outdir    = "plots/$ERA/$CHANNEL"
  fname     = "$PICODIR/$SAMPLE_$CHANNEL$TAG.root"
  #fname     =  "/nfs/user/pmastra/DeepTau2p5/analysis/$ERA/$CHANNEL/$GROUP/$SAMPLE_$CHANNEL$TAG.root" 


  # LOOP over configs / channels
  for config in configs:
    if not config.endswith(".yml"): # config = channel name
      config = "config/setup_%s.yml"%(config) # assume this file name pattern
    print(">>> Using configuration file: %s"%config)
    with open(config, 'r') as file:
      setup = yaml.safe_load(file)
    tag = setup.get('tag',"")+args.tag
    
    for era in eras:
        setera(era) # set era for plot style and lumi-xsec normalization
        #addsfs = setup["samples"].get("addSFs",[]) #"getTauIDSF(dm_2,genmatch_2)"]
        addsfs = [ ] #"getTauIDSF(dm_2,genmatch_2)"]

        rmsfs  = [ ] if (setup['channel']=='mumu' or not notauidsf) else ['idweight_2','ltfweight_2'] # remove tau ID SFs
        
      
        split  = ['DY','ST','TT'] 

        sampleset = getsampleset(setup['channel'],era,fname=fname,rmsf=rmsfs,addsf=addsfs,split=split)
       
        print("split = ", split)
        print(">>>>>>>sampleset")

        split_list = [["ZTT","genmatch_2==5"], ["ZL","genmatch_2>0 && genmatch_2<5"], ["ZJ","genmatch_2==0"], 
                  ["TTT","genmatch_2==5"], ["TTL","genmatch_2>0 && genmatch_2<5"], ["TTJ","genmatch_2==0"], 
                  ["ST","genmatch_2==5 && genmatch_2<5"],["STJ","genmatch_2<5"]]

        sampleset.split(split_list)

        for region in setup["regions"] : 
          plot(sampleset,setup,region,parallel=parallel,tag=tag,extratext=extratext,outdir=outdir,era=era,
                  varfilter=varfilter,selfilter=selfilter,fraction=fraction,pdf=pdf)
        sampleset.close()
    

if __name__ == "__main__":
  from argparse import ArgumentParser, RawTextHelpFormatter
  eras = ['2016','2017','2018','UL2016_preVFP','UL2016_postVFP','UL2017','UL2018','2022_preEE','2022_postEE', '2023C']
  description = """Simple plotting script for pico analysis tuples"""
  parser = ArgumentParser(prog="plot",description=description,epilog="Good luck!")
  parser.add_argument('-y', '--era',     dest='eras', nargs='*', choices=eras, default=['2017'],
                                         help="set era" )
  parser.add_argument('-c', '--config', '--channel',
                                         dest='configs', type=str, nargs='+', default=['config/setup_mutau.yml'], action='store',
                                         help="config file(s) containing channel setup for samples and selections, default=%(default)r" )
  parser.add_argument('-V', '--var',     dest='varfilter', nargs='+',
                                         help="only plot the variables passing this filter (glob patterns allowed)" )
  parser.add_argument('-S', '--sel',     dest='selfilter', nargs='+',
                                         help="only plot the selection passing this filter (glob patterns allowed)" )
  parser.add_argument('-s', '--serial',  dest='parallel', action='store_false',
                                         help="run Tree::MultiDraw serial instead of in parallel" )
  parser.add_argument('-F', '--fraction',dest='fraction', action='store_true',
                                         help="include fraction stack in ratio plot" )
  parser.add_argument('-p', '--pdf',     dest='pdf', action='store_true',
                                         help="create pdf version of each plot" )
  parser.add_argument('-r', '--nosf',    dest='notauidsf', action='store_true',
                                         help="remove DeepTau ID SF" )
  parser.add_argument('-t', '--tag',     default="", help="extra tag for output" )
  parser.add_argument('-T', '--text',    default="", help="extra text on plot" )
  parser.add_argument('-v', '--verbose', dest='verbosity', type=int, nargs='?', const=1, default=0, action='store',
                                         help="set verbosity" )
  args = parser.parse_args()
  LOG.verbosity = args.verbosity
  PLOG.verbosity = args.verbosity
  main(args)
  print("\n>>> Done.")
  
