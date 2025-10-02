# Description: Common configuration file for creating pico sample set plotting scripts
# Author: Jacopo Malvaso (August 2022)
import re
from TauFW.Plotter.sample.utils import LOG, STYLE, ensuredir, repkey, joincuts, joinweights, ensurelist,\
                                       setera, getyear, loadmacro, Sel, Var
from TauFW.Plotter.sample.utils import getsampleset as _getsampleset

def getsampleset(channel,era,**kwargs):
  verbosity = LOG.getverbosity(kwargs)
  year     = getyear(era) # get integer year
  fname    = kwargs.get('fname', "$PICODIR/$SAMPLE_$CHANNEL$TAG.root" ) # file name pattern of pico files
  split    = kwargs.get('split',    ['DY'] if 'tau' in channel else [ ] ) # split samples (e.g. DY) into genmatch components
  join     = kwargs.get('join',     ['WJ'] ) # join samples 
  rmsfs    = ensurelist(kwargs.get('rmsf', [ ])) # remove the tau ID SF, e.g. rmsf=['idweight_2','ltfweight_2']
  addsfs   = ensurelist(kwargs.get('addsf', [ ])) # add extra weight to all samples
  weight   = kwargs.get('weight',   None         ) # weight for all MC samples
  dyweight = kwargs.get('dyweight', 'zptweight'  ) # weight for DY samples
  ttweight = kwargs.get('ttweight', 'ttptweight' ) # weight for ttbar samples
  kfactor_mu = kwargs.get('kfactor_mu', 'kfactor_mu') 
  filter   = kwargs.get('filter',   None         ) # only include these MC samples
  vetoes   = kwargs.get('vetoes',   None         ) # veto these MC samples
  #tag      = kwargs.get('tag',      ""           ) # extra tag for sample file names
  table    = kwargs.get('table',    True         ) # print sample set table
  setera(era) # set era for plot style and lumi-xsec normalization

   # SM BACKGROUND MC SAMPLES
  if era=='2018': 
   expsamples = [ # table of MC samples to be converted to Sample objects
   # GROUP NAME                     TITLE                 XSEC      EXTRA OPTIONS
   ('WMu',                "WToMuNu",  "WToMuNu",   1.0*7.273),# {'extraweight': kfactor_mu}
   #('WJ',              "WJetsToLNu", "W + jets", 52760*1.166 ),
   ('WJ',    "WJetsToLNuHT100to200", "W + jets", 1395.0*1.166),
   ('WJ',    "WJetsToLNuHT200to400", "W + jets", 407.9*1.166),
   ('WJ',    "WJetsToLNuHT400to600", "W + jets", 57.48*1.166),
   ('WJ',    "WJetsToLNuHT600to800", "W + jets", 12.87*1.166 ),
   ('WJ',   "WJetsToLNuHT800to1200", "W + jets", 5.366*1.166),
   ('WJ',  "WJetsToLNuHT1200to2500", "W + jets", 1.074*1.166),
    ]
  else:
    LOG.throw(IOError,"Did not recognize era %r!"%(era))
  # OBSERVED DATA SAMPLES
  if 'munu'   in channel: dataset = "SingleMuon_Run%d?"%year
  else:
    LOG.throw(IOError,"Did not recognize channel %r!"%(channel))
  datasample = ('Data',dataset) # GROUP, NAME

  # FILTER
  if filter:
    expsamples = [s for s in expsamples if any(f in s[0] for f in filter)]
  if vetoes:
    expsamples = [s for s in expsamples if not any(v in s[0] for v in vetoes)]
  
  # SAMPLE SET
  if weight=="":
    weight = ""
  elif channel in ['munu']:
    weight = "genweight*trigweight*puweight*idisoweight_1"
  else: # mumu, emu, ...
    weight = "genweight*trigweight*puweight*idisoweight_1*idisoweight_2"
  for sf in rmsfs: # remove (old) SFs, e.g. for SF measurement
    weight = weight.replace(sf,"").replace("**","*").strip('*')
  for sf in addsfs:  # add extra SFs, e.g. for SF measurement
    weight = joinweights(weight,sf)
  kwargs.setdefault('weight',weight) # common weight for MC
  kwargs.setdefault('fname', fname)  # default filename pattern
  sampleset = _getsampleset(datasample,expsamples,channel=channel,era=era,**kwargs)
  LOG.verb("weight = %r"%(weight),verbosity,1)
  # JOIN
  sampleset.join('WJ', name='Other' ) 
  
  if table:
    sampleset.printtable(merged=True,split=True)
  print(">>> common weight: %r"%(weight))
  return sampleset
  
