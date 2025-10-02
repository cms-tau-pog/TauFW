#! /usr/bin/env python
# Also see
#   https://twiki.cern.ch/twiki/bin/view/CMSPublic/WorkBookPickEvents
#   https://twiki.cern.ch/twiki/bin/view/CMSPublic/WorkBookDataSamples
#   https://github.com/cms-sw/cmssw/blob/CMSSW_11_1_X/PhysicsTools/Utilities/configuration/copyPickMerge_cfg.py
import os, re
from subprocess import Popen, PIPE, STDOUT, CalledProcessError
import ROOT; ROOT.PyConfig.IgnoreCommandLineOptions = True
from ROOT import TFile
#from ROOT import gROOT, gStyle, gPad, gDirectory, TFile, TTree, TH2F, TCanvas, TLegend, TLatex, kBlue, kRed, kOrange
#gStyle.SetOptStat(False)
#gROOT.SetBatch(True)
rexp_evts = re.compile(r"^(\d+):(\d+):(\d+)$")
_dasurl = "root://cms-xrd-global.cern.ch/" #"root://xrootd-cms.infn.it/"


def execute(cmd,fatal=True,verb=0):
  """Execute shell command."""
  cmd = str(cmd)
  out = ""
  if verb>=1:
    print ">>> Executing: %r"%(cmd)
  try:
    process = Popen(cmd,stdout=PIPE,stderr=STDOUT,bufsize=1,shell=True) #,universal_newlines=True
    for line in iter(process.stdout.readline,""):
      if verb>=1: # real time print out (does not work for python scripts without flush)
        print line.rstrip()
      out += line
    process.stdout.close()
    retcode = process.wait()
    out = out.strip()
  except Exception as e:
    if verb<1:
      print out
    print ">>> Failed: %r"%(cmd)
    raise e
  if retcode and fatal:
    if verb<1:
      print out
    raise CalledProcessError(retcode,cmd)
  return out
  

def dasgoclient(query,**kwargs):
  """Call dasgoclient with given query."""
  try:
    verb   = kwargs.get('verb',  0  )
    limit  = kwargs.get('limit', 0  )
    option = kwargs.get('opts',  "" )
    dascmd = 'dasgoclient --query="%s"'%(query)
    if limit>0:
      dascmd += " --limit=%d"%(limit)
    if option:
      dascmd += " "+option.strip()
    if verb>=1:
      print repr(dascmd)
    cmdout    = execute(dascmd,verb=verb-1)
  except CalledProcessError as err:
    print "Failed to call 'dasgoclient' command %r"%(dascmd)
    raise err
  return cmdout
  

def getdasfiles(datasets,lumis=[],url=None,verb=0):
  """Help function to get files from DAS."""
  files = [ ]
  if isinstance(datasets,str):
    datasets = [datasets]
  for dataset in datasets:
    files_ = dasgoclient("file dataset=%s"%(dataset),verb=verb-1).split()
    if lumis: # TODO: check per event
      if verb>=2:
        print ">>> getdasfiles: Filtering by lumi..."
      for file in files_:
        if verb>=2:
          print ">>> getdasfiles: file=%s"%(file)
        lumis_ = [int(l) for l in dasgoclient("lumi file=%s"%(file),verb=verb-2).strip('[]').split(',')]
        if verb>=3:
          print ">>> getdasfiles: lumis=%s"%(lumis_)
        if any(l in lumis_ for l in lumis):
          files.append(file)
    else:
      files.extend(files_)
  if url:
    files = [url+f for f in files]
  if verb>=1:
    print ">>> getdasfiles: files=%s"%(files)
  return files
  

def parse_or(strs,protect=False,verb=0):
  """Help function to parse cuts."""
  cutstr = ""
  if isinstance(strs,str):
    cutstr = strs
  elif len(strs)>1:
    cutstr = " || ".join('('+s+')' for s in strs if s)
    if protect:
      cutstr = '('+cutstr+')'
  elif len(strs)==1 and strs[0]:
    cutstr = strs[0]
  if verb>=2:
    print ">>> parse_or(%r) = %r"%(strs,cutstr)
  return cutstr
  

def parse_evt_cut(evttree,verb=0):
  """Help function to create selection string from list of events."""
  if verb>=2:
    print ">>> parse_evt_cut: evttree=%r"%(evttree)
  cutstr = ""
  if evttree:
    runstrs = [ ]
    for run in sorted(evttree.keys()):
      lumistrs = [ ]
      for lumi in sorted(evttree[run].keys()):
        evtstr = ' || '.join("EventAuxiliary.event()==%d"%e for e in evttree[run][lumi])
        if len(evttree[run][lumi])>1:
          evtstr = '('+evtstr+')'
        elif len(evttree[run][lumi])<1:
          continue
        lumistrs.append("EventAuxiliary.luminosityBlock()==%d && %s"%(lumi,evtstr))
      runstrs.append("EventAuxiliary.run()==%d && %s"%(run,parse_or(lumistrs,protect=True,verb=verb-1)))
    cutstr = parse_or(runstrs,verb=verb-1)
  if verb>=2:
    print ">>> parse_evt_cut: cutstr=%r"%(cutstr)
  return cutstr

# def parse_evts_list(evtlist,verb=0):
#   """Help function to create selection string from list of events."""
#   cutstr = ""
#   evttree = { }
#   for substr in evtlist:
#     match = rexp_evts.match(substr)
#     if not match:
#       print ">>> parse_evts: Warning! Did not recognize %r! Ignoring..."%(substr)
#       continue
#     run, lumi, evt = [int(x) for x in match.groups()]
#     evttree.setdefault(run,{}).setdefault(lumi,[]).append(evt)
#   if verb>=2:
#     print ">>> parse_evts_list: evttree=%r"%(evttree)
#   runstrs = [ ]
#   for run in sorted(evttree.keys()):
#     lumistrs = [ ]
#     for lumi in sorted(evttree[run].keys()):
#       evtstr = ' || '.join("EventAuxiliary.event()==%d"%e for e in evttree[run][lumi])
#       if len(evttree[run][lumi])>1:
#         evtstr = '('+evtstr+')'
#       elif len(evttree[run][lumi])<1:
#         continue
#       lumistrs.append("EventAuxiliary.luminosityBlock()==%d && %s"%(lumi,evtstr))
#     runstrs.append("EventAuxiliary.run()==%d && %s"%(run,parse_or(lumistrs,protect=True,verb=verb)))
#   cutstr = parse_or(runstrs,verb=verb)
#   return cutstr
#   
# 
# def parse_evts(evts,verb=0):
#   """Help function to create selection string for events."""
#   cutstr = ""
#   if not evts:
#     cutstr = ""
#   elif not isinstance(evts,str):
#     cutstr = parse_evts_list(evts,verb=verb)
#   elif ',' in evts:
#     cutstr = parse_evts_list(evts.split(','),verb=verb)
#   elif rexp_evts.match(evts): # just one run:lumi:evt
#     match = rexp_evts.match(evts)
#     run, lumi, evt = [int(x) for x in match.groups()]
#     cutstr = "EventAuxiliary.run()==%d && EventAuxiliary.luminosityBlock()==%d && EventAuxiliary.event()==%d"%(run,lumi,evt)
#   elif os.path.isfile(evts):
#     with open(evts,'r') as file:
#       evtlist = file.read().splitlines()
#     cutstr = parse_evts_list(evtlist,verb=verb)
#   else:
#     print ">>> parse_evts: Warning! Did not recognize event list or file %r! Ignoring..."%(evts)
#   return cutstr
  

# def parse_evt(evtstr,verb=0):
#   """Help function to parse single event in run:lumi:evt format."""
#   match = rexp_evts.match(evtstr)
#   evt = None
#   if match:
#     evt = [int(x) for x in match.groups()]
#   else:
#     print ">>> parse_evt: Did not recognize event %r! Must be of format run:lumi:evt. Ignoring..."%(evt)
#   return evt
  

def parse_evtlist(evtlist,verb=0):
  """Help function to parse list of events in run:lumi:evt format."""
  evttree = { }
  for evtstr in evtlist:
    match = rexp_evts.match(evtstr)
    if match:
      run, lumi, evt = [int(x) for x in match.groups()]
      evttree.setdefault(run,{}).setdefault(lumi,[]).append(evt)
    else:
      print ">>> parse_evtlist: Did not recognize event %r! Must be of format run:lumi:evt. Ignoring..."%(evtstr)
  return evttree
  

def parse_evts(evts,verb=0):
  """Help function to create event tree."""
  evttree = { }
  if evts and isinstance(evts,str):
    if ',' in evts:
      evttree = parse_evtlist(evts.split(','))
    elif rexp_evts.match(evts): # just one run:lumi:evt
      evttree = parse_evtlist([evts])
    elif os.path.isfile(evts):
      with open(evts,'r') as file:
        evtlist = file.read().splitlines()
        evttree = parse_evtlist(evtlist)
  if not evttree:
    print ">>> parse_evts: Warning! Did not recognize event list or file %r! Ignoring..."%(evts)
  elif verb>=1:
    print ">>> parse_evts: evttree=%r"%(evttree)
  return evttree
  

#def countlumi(fname):
#  """Test function to count occurences of some lumi."""
#  file  = TFile.Open(fname)
#  tree  = file.Get('Events')
#  dcmd  = "EventAuxiliary.luminosityBlock()"
#  nevts = tree.Draw(dcmd,"","gOff")
#  print nevts
#  vec_lumi = tree.GetV1()
#  tally = { }
#  for i in range(nevts):
#    lumi = float(vec_lumi[i])
#    if lumi in tally:
#      tally[lumi] += 1
#    else:
#      tally[lumi] = 0
#  for lumi in sorted(tally.keys()):
#    print ">>> %6d: %5d"%(lumi,tally[lumi])
  

def pickevts(fnames,evtstr,verb=0):
  """Count occurences of some lumi."""
  if isinstance(fnames,str):
    fnames = [fnames]
  dcmd = "EventAuxiliary.run():EventAuxiliary.luminosityBlock():EventAuxiliary.event()"
  if verb>=2:
    print ">>> pickevts: dcmd=%r, evtstr=%r..."%(dcmd,evtstr) 
  for fname in fnames:
    if verb>=1:
      print ">>> pickevts: Opening %r..."%(fname) 
    file  = TFile.Open(fname)
    tree  = file.Get('Events')
    nevts = tree.Draw(dcmd,evtstr,"gOff")
    vec_run  = tree.GetV1()
    vec_lumi = tree.GetV2()
    vec_evt  = tree.GetV3()
    if nevts>0:
      print ">>> %s"%(fname)
      for i in range(nevts):
        run  = int(vec_run[i])
        lumi = int(vec_lumi[i])
        evt  = int(vec_evt[i])
        print ">>>   %d:%d:%d"%(run,lumi,evt)
    elif verb>=1:
      print ">>> pickevts: Nothing found in %s"%(fname)
  

def main(args):
  verbosity  = args.verbosity
  files      = args.files
  events     = args.events
  limit      = args.limit
  filterlumi = args.filterlumi
  url        = args.url #"root://cms-xrd-global.cern.ch/" #"root://xrootd-cms.infn.it/"
  evttree    = parse_evts(events,verb=verbosity)
  evtcut     = parse_evt_cut(evttree,verb=verbosity)
  
  if all(f.lower().endswith('.root') for f in files):
    if url:
      for i, file in enumerate(files[:]):
        if not '://' in file:
          files[i] = url+file
  elif all(d.startswith('/') and d.count('/')==3 for d in files):
    lumis = set()
    if not url:
      url = _dasurl
    if filterlumi:
      for run in evttree.keys():
        lumis.update(evttree[run].keys())
    files = getdasfiles(files,lumis=lumis,url=url,verb=verbosity)
  else:
    raise IOError("Did not recognize input, must be root files or DAS datasets. Got: %r"%(files))
  if limit>1 and len(files)>limit:
    files = files[:limit]
  
  if evtcut:
    pickevts(files,evtcut,verb=verbosity)
  else:
    print ">>> Please specify a list of events via -e"
  

if __name__ == '__main__':
  from argparse import ArgumentParser
  description = '''Find files that contain specified events given by run:lumi:events.'''
  parser = ArgumentParser(prog="pileup",description=description,epilog="Succes!")
  #parser.add_argument('-i', '--inputdir', dest='indir', help="eras to run" )
  parser.add_argument('files',              nargs='+', help="files or dataset to look for" )
  parser.add_argument('-u', '--url',        default=None, help="URL for file, default=None, %s for DAS"%(_dasurl) )
  parser.add_argument('-e', '--events',     help="events to pick in run:lumi:event format via comma separated string or text file" )
  parser.add_argument('-l', '--limit',      default=-1, type=int, help="limit number of files" )
  parser.add_argument('-L', '--filterlumi', action='store_true', help="pre-filter files with lumiblocks via DAS (faster)" )
  parser.add_argument('-v', '--verbose',    dest='verbosity', type=int, nargs='?', const=1, default=0, action='store',
                                            help="set verbosity" )
  args = parser.parse_args()
  
  main(args)
  print ">>>\n>>> Done\n"
  
