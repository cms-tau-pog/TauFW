#! /usr/bin/env python
# Author: Izaak Neutelings (June 2021)
# Description: Help script to getPileupProfiles to filter run numbers in JSON file.
#              Also see compareJSON.py --and JSON1.json JSON2.json INTERSECTION.json
# Instructions:
#   ./filterRunsJSON.py -y 2016 -r 271036-278770
#   ./filterRunsJSON.py -y 2016 -r 278769-284044
#   ./filterRunsJSON.py -d ../json/2016/Cert_271036-284044_13TeV_ReReco_07Aug2017_Collisions16_JSON.txt ../json/2016/Cert_271036-284044_13TeV_Legacy2016_Collisions16_JSON.txt
#   ./filterRunsJSON.py -d ../json/2017/Cert_294927-306462_13TeV_PromptReco_Collisions17_JSON.txt ../json/2017/Cert_294927-306462_13TeV_UL2017_Collisions17_GoldenJSON.txt
#   ./filterRunsJSON.py -d ../json/2018/Cert_314472-325175_13TeV_PromptReco_Collisions18_JSON.txt ../json/2018/Cert_314472-325175_13TeV_Legacy2018_Collisions18_JSON.txt
#   compareJSON.py --diff ../json/2016/Cert_271036-284044_13TeV_ReReco_07Aug2017_Collisions16_JSON.txt ../json/2016/Cert_271036-284044_13TeV_Legacy2016_Collisions16_JSON.txt
#   compareJSON.py --diff ../json/2017/Cert_294927-306462_13TeV_PromptReco_Collisions17_JSON.txt ../json/2017/Cert_294927-306462_13TeV_UL2017_Collisions17_GoldenJSON.txt
import os, sys, re, json
from TauFW.PicoProducer import datadir
from TauFW.common.tools.file import ensuredir
#from TauFW.common.tools.utils import getyear
year_rexp = re.compile(r"(?<!\d)(20\d{2})(?!\d)")
range_rexp = re.compile(r"(?<!\d)(\d{6})-(\d{6})(?!\d)")


def getyear(era):
  match = year_rexp.search(era)
  if not match:
    raise IOError("getyear: Did not recognize year in era %r"%era)
  year = int(match.group(1))
  return year
  

def getJSON(era):
  """Return hardcorded name of certification JSON for a given era"""
  year    = getyear(era)
  jsondir = os.path.join(datadir,'json',str(year))
  if '2016' in era:
    if 'UL' in era and 'VFP' not in era:
      jname = os.path.join(jsondir,"Cert_271036-284044_13TeV_Legacy2016_Collisions16_JSON.txt") # complete UL2016
    elif 'UL' in era and "preVFP" in era:
      # https://twiki.cern.ch/twiki/bin/view/CMS/PdmVLegacy2016preVFPAnalysis
      jname = os.path.join(jsondir,"Cert_271036-278770_13TeV_UL2016_preVFP_Collisions16_JSON.txt") # create yourself first !
    elif 'UL' in era and "postVFP" in era:
      # https://twiki.cern.ch/twiki/bin/view/CMS/PdmVLegacy2016postVFPAnalysis
      jname = os.path.join(jsondir,"Cert_278769-284044_13TeV_UL2016_postVFP_Collisions16_JSON.txt") # create yourself first !
    else: # 2016 legacy
      # https://twiki.cern.ch/twiki/bin/viewauth/CMS/PdmV2016Analysis
      # /afs/cern.ch/cms/CAF/CMSCOMM/COMM_DQM/certification/Collisions16/13TeV/ReReco/Final/Cert_271036-284044_13TeV_23Sep2016ReReco_Collisions16_JSON.txt"
      # /afs/cern.ch/cms/CAF/CMSCOMM/COMM_DQM/certification/Collisions16/13TeV/Final/Cert_271036-284044_13TeV_PromptReco_Collisions16_JSON.txt
      # /afs/cern.ch/cms/CAF/CMSCOMM/COMM_DQM/certification/Collisions16/13TeV/PileUp/pileup_latest.txt
      jname = os.path.join(jsondir,"Cert_271036-284044_13TeV_ReReco_07Aug2017_Collisions16_JSON.txt")
  elif '2017' in era:
    if 'UL' in era:
      # https://twiki.cern.ch/twiki/bin/view/CMS/PdmVLegacy2017Analysis
      jname = os.path.join(jsondir,"Cert_294927-306462_13TeV_UL2017_Collisions17_GoldenJSON.txt")
    else:
      # https://twiki.cern.ch/twiki/bin/viewauth/CMS/PdmV2017Analysis
      # /afs/cern.ch/cms/CAF/CMSCOMM/COMM_DQM/certification/Collisions16/13TeV/Final/Cert_271036-284044_13TeV_PromptReco_Collisions16_JSON.txt
      # /afs/cern.ch/cms/CAF/CMSCOMM/COMM_DQM/certification/Collisions17/13TeV/PileUp/pileup_latest.txt
      jname = os.path.join(jsondir,"Cert_294927-306462_13TeV_PromptReco_Collisions17_JSON.txt")
  elif '2018' in era:
    if 'UL' in era:
      # https://twiki.cern.ch/twiki/bin/view/CMS/PdmVLegacy2018Analysis
      jname = os.path.join(jsondir,"Cert_314472-325175_13TeV_Legacy2018_Collisions18_JSON.txt")
    else:
      # https://twiki.cern.ch/twiki/bin/viewauth/CMS/PdmV2018Analysis
      # /afs/cern.ch/cms/CAF/CMSCOMM/COMM_DQM/certification/Collisions18/13TeV/PromptReco
      # /afs/cern.ch/cms/CAF/CMSCOMM/COMM_DQM/certification/Collisions18/13TeV/PileUp/pileup_latest.txt
      jname = os.path.join(jsondir,"Cert_314472-325175_13TeV_PromptReco_Collisions18_JSON.txt")
  else:
    raise IOError("getJSONs: Did not recognize era %r"%era)
  return jname
  

def getRuns(era):
  """Return hardcorded dictionairy of run numbers per era for a given era"""
  if '2016' in era:
    if 'UL' in era and 'preVFP' in era:
      datasets = {
        'B': (272007,275376),
        'C': (275657,276283),
        'D': (276315,276811),
        'E': (276831,277420),
        'F': (277772,278770), # end 2016 pre VFP, https://twiki.cern.ch/twiki/bin/view/CMS/PdmVDatasetsUL2016
      }
    elif 'UL' in era and 'postVFP' in era:
      datasets = {
        'F': (278769,278808), # start 2016 post VFP, https://twiki.cern.ch/twiki/bin/view/CMS/PdmVDatasetsUL2016
        'G': (278820,280385),
        'H': (280919,284044),
      }
    else: # 2016 legacy
      datasets = {
        'B': (272007,275376),
        'C': (275657,276283),
        'D': (276315,276811),
        'E': (276831,277420),
        'F': (277772,278808),
        'G': (278820,280385),
        'H': (280919,284044),
      }
  elif '2017' in era:
    datasets = {
      'B': (297020,299329),
      'C': (299337,302029),
      'D': (302030,303434),
      'E': (303435,304826),
      'F': (304911,306462),
    }
  elif '2018' in era:
    datasets = {
      'A': (315252,316995),
      'B': (317080,319310),
      'C': (319337,320065),
      'D': (320673,325175),
    }
  else:
    raise IOError("getJSONs: Did not recognize era %r"%era)
  return datasets
  

def cleanPeriods(periods):
  """Clean up periods."""
  if not periods: return periods
  for i, period in enumerate(periods):
    period = period.upper()
    assert all(s in 'ABCDEFGH' for s in period), "Did not recognize era '%s'!"%(period)
    periods[i] = ''.join(sorted(period))
  return periods
  

def getPeriodRunNumbers(era,datasets=None):
  """Get runnumbers for an period (e.g. 'B', 'BCD' or 'GH')."""
  start  = -1
  end    = -1
  if datasets==None:
    datasets = getRuns(era)
  for set in era:
    assert set in datasets, "Dataset '%s' not in list %s"%(set,datasets)
    setstart, setend = datasets[set]
    if start<0 or end<0:
      start, end = setstart, setend
      continue
    if setstart<start:
      start = setstart
    if setend>end:
      end = setend
  assert start>0 and end>0, "Invalid runnumbers %s to %s"%(start,end)
  return start, end
  

def filterJSONByRunNumberRange(jsoninname,era="",period=None,rrange=None,start=None,end=None,outdir='json',verb=0):
  """Split a given JSON file by start and end run number."""
  outdir = ensuredir(outdir)
  if period:
    datasets = getRuns(era)
    start, end = getPeriodRunNumbers(period,datasets)
    eraname = "Run%s%s"%(era,period)
  elif rrange:
    match = range_rexp.match(rrange)
    if not match:
      raise IOERROR("Could not find range pattern in %r. Format should be e.g. 123456-1234567"%(rrange))
    start, end = int(match.group(1)), int(match.group(2))
    eraname = "%s-%s"%(start,end)
  elif start>0 and end>0:
    eraname = "%s-%s"%(start,end)
  else:
    raise IOError("filterJSONByRunNumberRange: Please set either period (e.g. period='BCD'), "
                  "or the range (e.g. rrange='272007-278770'), or start and end (start=272007, end=278770)")
  jsonoutname = os.path.join(outdir,range_rexp.sub(eraname,os.path.basename(jsoninname)))
  print ">>> filterJSONByRunNumberRange: %r for period=%r, range=%s-%s"%(eraname,period,start,end)
  
  # READ JSON IN
  with open(jsoninname,'r') as jsonin:
    data = json.load(jsonin)
  
  # FILTER run number range
  nkeep = 0
  ndrop = 0
  for element in sorted(data.keys()):
    if element.isdigit():
      runnumber = int(element)
      if runnumber<start or runnumber>end:
        ndrop += 1
        if verb>=2: print ">>>     dropping %s"%runnumber
        del data[element]
      else:
        nkeep += 1
        if verb>=2: print ">>>     keeping %s"%runnumber
    else:
      print "Warning! filterJSONByRunNumberRange: element is not an integer (run number): '%s'"%element
  
  # WRITE JSON OUT
  with open(jsonoutname,'w') as jsonout:
    data = json.dump(data,jsonout,sort_keys=True)
  
  # SUMMARY
  print ">>>   output: %r"%(jsonoutname)
  print ">>>   saved %s / %s run numbers"%(nkeep,nkeep+ndrop)
  
  return jsonoutname
  

def compareJSONs(jnames,verb=0):
  """Compare JSON files."""
  print ">>> Comparing JSONs..."
  run_dicts = { }
  runs = set()
  for jname in jnames:
    with open(jname,'r') as file:
      data = json.load(file)
      run_dicts[jname] = { }
      for run, lumis in data.items():
        run_dicts[jname][int(run)] = lumis # replace unicode with integer
      runs |= set(run_dicts[jname].keys())
  runstatus = { j: { 'miss': [ ], 'diff': { } } for j in jnames }
  if verb>=2:
    print ">>> All runs (union):"
    print runs
  for run in sorted(runs):
    lumis = [ ]
    lumi_dict = { }
    for jname in jnames:
      if run in run_dicts[jname]:
        lumi = sorted(run_dicts[jname][run]) # compare lumi list later
        if lumi not in lumis:
          lumis.append(lumi)
        lumi_dict[jname] = lumi
      else:
        runstatus[jname]['miss'].append(run) # missing run
    if len(lumis)>=2: # at least two lumi list are different
      for jname in lumi_dict:
        runstatus[jname]['diff'][run] = run_dicts[jname][run] # different lumi list
  print ">>> "
  for jname in jnames:
    nruns = len(run_dicts[jname])
    print ">>>   %s (%d runs)"%(jname,nruns)
    nmiss = len(runstatus[jname]['miss'])
    ndiff = len(runstatus[jname]['diff'])
    misslist = ', '.join("\033[1m%s\033[0m"%(r) for r in runstatus[jname]['miss'])
    difflist = ', '.join("\033[1m%s\033[0m: %s"%(r,runstatus[jname]['diff'][r]) for r in sorted(runstatus[jname]['diff'].keys()))
    print ">>>     missing runs (%d/%d):\n>>>       %s"%(nmiss,nruns,misslist or "none")
    print ">>>     different limis (%d/%d):\n>>>       %s"%(ndiff,nruns,difflist or "none")
    print ">>> "
  

def main(args):
  eras      = args.eras
  injson    = args.injson
  periods   = args.periods
  rrange    = args.rrange
  diffs     = args.diffs
  outdir    = args.outdir
  verbosity = args.verbosity
  for era in eras:
    if diffs:
      compareJSONs(diffs,verb=verbosity)
    elif periods:
      periods = cleanPeriods(periods)
      jname   = injson or getJSON(era)
      outdir  = ensuredir("json")
      for period in periods:
        jsonout = filterJSONByRunNumberRange(jname,era,period=period,outdir=outdir,verb=verbosity)
    elif rrange:
      jname   = injson or getJSON(era)
      jsonout = filterJSONByRunNumberRange(jname,era,rrange=rrange,outdir=outdir,verb=verbosity)
    else:
      print ">>> Please specifiy a period (-p BCD) or a range of run numbers (-r 272007-278770)"
      print ">>> JSON for %r: %s"%(era,jname)
      print ">>> datasets: "
      datasets  = getRuns(era)
      for period in sorted(datasets.keys()):
        start, end = datasets[period]
        print ">>>   %s: %s-%s"%(period,start,end)
  

if __name__ == '__main__':
  from argparse import ArgumentParser
  argv = sys.argv
  description = '''This script helps to filter runs in CMS JSON certification files.'''
  parser = ArgumentParser(prog="filter_json",description=description,epilog="Good luck!")
  parser.add_argument('-y', '-e', '--era', dest='eras', nargs='+', default="",
                      metavar='ERA',       help="select era" )
  parser.add_argument('-i', '--injson',    dest='injson',
                                           help="input JSON file for filter" )
  parser.add_argument('-o', '--outdir',    dest='outdir', default='json',
                                           help="output directory" )
  parser.add_argument('-r', '--range',     dest='rrange',
                      metavar='START-END', help="filter JSON profiles given range (e.g. 272007-278770)" )
  parser.add_argument('-p', '--period',    dest='periods', type=str, nargs='+', default=[ ],
                                           help="filter JSON file for given data taking period (e.g. B, BCD, GH, ...)" )
  parser.add_argument('-d', '--diff',      dest='diffs', nargs='+',
                                           help="compare two JSONs, find difference" )
  parser.add_argument('-v', '--verbose',   dest='verbosity', type=int, nargs='?', const=1, default=0,
                                           help="set verbosity" )
  args = parser.parse_args()
  main(args)
  print ">>> Done!"
  
