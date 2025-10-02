#! /usr/bin/env python
# Author: Izaak Neutelings (October 2020)
import os, sys, re, glob, json
from datetime import datetime
from collections import OrderedDict
import ROOT; ROOT.PyConfig.IgnoreCommandLineOptions = True
from ROOT import TFile
from TauFW.common.tools.file import ensuredir, ensurefile, ensureinit, getline
from TauFW.common.tools.utils import execute, chunkify, repkey, alphanum_key, lreplace
from TauFW.common.tools.log import Logger, color, bold
from argparse import ArgumentParser
os.chdir(GLOB.basedir)
CONFIG = GLOB.getconfig(verb=0)
LOG    = Logger()


  


###########
#   LIST   #
###########

def main_list(args):
  """List contents of configuration for those lazy to do 'cat config/config.json'."""
  if args.verbosity>=1:
    print ">>> main_list", args
  verbosity = args.verbosity
  cfgname   = CONFIG._path
  if verbosity>=1:
    print '-'*80
    print ">>> %-14s = %s"%('cfgname',cfgname)
    print ">>> %-14s = %s"%('config',CONFIG)
    print '-'*80
  
  print ">>> Configuration %s:"%(cfgname)
  for variable, value in CONFIG.iteritems():
    variable = "'"+color(variable)+"'"
    if isinstance(value,dict):
      print ">>>  %s:"%(variable)
      for key, item in value.iteritems():
        if isinstance(item,basestring): item = str(item)
        print ">>>    %-12r -> %r"%(str(key),str(item))
    else:
      if isinstance(value,basestring): value = str(value)
      print ">>>  %-24s = %r"%(variable,value)
  



############
#   MAIN   #
############

if __name__ == "__main__":
  
  # COMMON
  description = "Central script to process nanoAOD for skimming or analysis."
  parser = ArgumentParser(prog='pico.py',description=description,epilog="Good luck!")
  parser_cmn = ArgumentParser(add_help=False)
  parser_cmn.add_argument('-v', '--verbose',    dest='verbosity', type=int, nargs='?', const=1, default=0,
                                                help="set verbosity" )
#   parser_sam = ArgumentParser(add_help=False,parents=[parser_cmn])
#   parser_lnk = ArgumentParser(add_help=False,parents=[parser_cmn])
#   parser_sam.add_argument('-c','--channel',     dest='channels', choices=CONFIG.channels.keys(), default=[ ], nargs='+',
#                                                 help='skimming or analysis channel to run')
#   parser_sam.add_argument('-y','-e','--era',    dest='eras', choices=CONFIG.eras.keys(), default=[ ], nargs='+',
#                                                 help='year or era to specify the sample list')
#   parser_sam.add_argument('-s', '--sample',     dest='samples', type=str, nargs='+', default=[ ],
#                           metavar='PATTERN',    help="filter these samples; glob patterns like '*' and '?' wildcards are allowed" )
#   parser_sam.add_argument('-x', '--veto',       dest='vetoes', nargs='+', default=[ ],
#                           metavar='PATTERN',    help="exclude/veto these samples; glob patterns are allowed" )
#   parser_sam.add_argument('--dtype',            dest='dtypes', choices=GLOB._dtypes, default=GLOB._dtypes, nargs='+',
#                                                 help='filter these data type(s)')
#   parser_sam.add_argument('-D','--das',         dest='checkdas', action='store_true',
#                                                 help="check DAS for total number of events" )
#   parser_sam.add_argument('--dasfiles',         dest='dasfiles', action='store_true',
#                                                 help="get files from DAS (instead of local storage, if predefined)" )
#   parser_sam.add_argument('-t','--tag',         dest='tag', default="",
#                                                 help='tag for output file name')
#   parser_sam.add_argument('-f','--force',       dest='force', action='store_true',
#                                                 help='force overwrite')
#   parser_sam.add_argument('-d','--dry',         dest='dryrun', action='store_true',
#                                                 help='dry run: prepare job without submitting for debugging purposes')
#   parser_sam.add_argument('-E', '--opts',       dest='extraopts', type=str, nargs='+', default=[ ],
#                           metavar='KEY=VALUE',  help="extra options for the skim or analysis module, "
#                                                      "passed as list of 'KEY=VALUE', separated by spaces")
#   parser_job = ArgumentParser(add_help=False,parents=[parser_sam])
#   parser_job.add_argument('-p','--prefetch',    dest='prefetch', action='store_true',
#                                                 help="copy remote file during job to increase processing speed and ensure stability" )
#   parser_job.add_argument('-T','--test',        dest='testrun', type=int, nargs='?', const=10000, default=0,
#                           metavar='NJOBS',      help='run a test with limited nummer of jobs and events, default nevts=%(const)d' )
#   parser_job.add_argument('--getjobs',          dest='checkqueue', type=int, nargs='?', const=1, default=-1,
#                           metavar='N',          help="check job status: 0 (no check), 1 (check once), -1 (check every job)" ) # speed up if batch is slow
#   parser_chk = ArgumentParser(add_help=False,parents=[parser_job])
#   parser_job.add_argument('-B','--batch-opts',  dest='batchopts', default=None,
#                                                 help='extra options for the batch system')
#   parser_job.add_argument('-M','--time',        dest='time', default=None,
#                                                 help='maximum run time of job')
#   parser_job.add_argument('-q','--queue',       dest='queue', default=None,
#                                                 help='queue of batch system (job flavor on HTCondor)')
#   parser_job.add_argument('-P','--prompt',      dest='prompt', action='store_true',
#                                                 help='ask user permission before submitting a sample')
#   parser_job.add_argument('-n','--filesperjob', dest='nfilesperjob', type=int, default=-1,
#                                                 help='number of files per job, default=%d'%(CONFIG.nfilesperjob))
#   parser_job.add_argument('--split',            dest='split_nfpj', type=int, nargs='?', const=2, default=1,
#                           metavar='N',          help="divide default number of files per job, default=%(const)d" )
#   parser_job.add_argument('--tmpdir',           dest='tmpdir', type=str, default=None,
#                                                 help="for skimming only: temporary output directory befor copying to outdir")
  
  # SUBCOMMANDS
  subparsers = parser.add_subparsers(title="sub-commands",dest='subcommand',help="sub-command help")
  help_lst = "list histograms"
  help_ren = "rename histograms"
  help_reb = "rebin histograms"
  help_rmv = "remove histograms"
  help_srt = "sort histograms"
  help_sum = "sum histograms"
  help_sqs = "set bins with low number of events or large rel. unc. to zero"
  parser_lst = subparsers.add_parser('list',     parents=[parser_cmn], help=help_lst, description=help_lst)
  parser_get = subparsers.add_parser('rename',   parents=[parser_cmn], help=help_ren, description=help_ren)
  parser_reb = subparsers.add_parser('rebin',    parents=[parser_cmn], help=help_reb, description=help_reb)
  parser_rmv = subparsers.add_parser('rm',       parents=[parser_cmn], help=help_rmv, description=help_rmv)
  parser_srt = subparsers.add_parser('sort',     parents=[parser_cmn], help=help_srt, description=help_srt)
  parser_sum = subparsers.add_parser('sum',      parents=[parser_cmn], help=help_sum, description=help_sum)
  parser_sqs = subparsers.add_parser('squash',   parents=[parser_cmn], help=help_sqs, description=help_sqs)
#   parser_get.add_argument('variable',           help='variable to change in the config file')
#   parser_get.add_argument('variable',           help='variable to get information on')
#   parser_set.add_argument('variable',           help='variable to change in the config file')
#   parser_set.add_argument('key',                help='channel or era key name', nargs='?', default=None)
#   parser_set.add_argument('value',              help='value for given value')
#   parser_rmv.add_argument('variable',           help='variable to remove from the config file')
#   parser_rmv.add_argument('key',                help='channel or era key name to remove', nargs='?', default=None)
#   parser_chl.add_argument('key',                metavar='channel', help='channel key name')
#   parser_chl.add_argument('value',              metavar='module',  help='module linked to by given channel')
#   parser_era.add_argument('key',                metavar='era',     help='era key name')
#   parser_era.add_argument('value',              metavar='samples', help='samplelist linked to by given era')
#   parser_ins.add_argument('type',               choices=['standalone','cmmsw'], #default=None,
#                                                 help='type of installation: standalone or compiled in CMSSW')
#   parser_get.add_argument('-U','--URL',         dest='inclurl', action='store_true',
#                                                 help="include XRootD url in filename for 'get files'" )
#   parser_get.add_argument('-L','--limit',       dest='limit', type=int, default=-1,
#                           metavar='NFILES',     help="limit number files in list for 'get files'" )
#   parser_get.add_argument('-l','--local',       dest='checklocal', action='store_true',
#                                                 help="compute total number of events in storage system (not DAS) for 'get files' or 'get nevents'" )
#   parser_get.add_argument('-w','--write',       dest='write', type=str, nargs='?', const=str(CONFIG.filelistdir), default="",
#                           metavar='FILE',       help="write file list, default=%(const)r" )
#   parser_run.add_argument('-m','--maxevts',     dest='maxevts', type=int, default=None,
#                                                 help='maximum number of events (per file) to process')
#   parser_run.add_argument('-n','--nfiles',      dest='nfiles', type=int, default=1,
#                                                 help="maximum number of input files to process (per sample), default=%(default)d")
#   parser_run.add_argument('-S', '--nsamples',   dest='nsamples', type=int, default=1,
#                                                 help="number of samples to run, default=%(default)d")
#   parser_run.add_argument('-i', '--input',      dest='infiles', nargs='+', default=[ ],
#                                                 help="input files (nanoAOD)")
#   parser_run.add_argument('-o', '--outdir',     dest='outdir', type=str, default='output',
#                                                 help="output directory, default=%(default)r")
#   parser_run.add_argument('-p','--prefetch',    dest='prefetch', action='store_true',
#                                                 help="copy remote file during run to increase processing speed and ensure stability" )
#   parser_sts.add_argument('-l','--log',         dest='showlogs', type=int, nargs='?', const=-1, default=0,
#                           metavar='NLOGS',      help="show log files of failed jobs: 0 (show none), -1 (show all), n (show max n)" )
#   parser_hdd.add_argument('-r','--clean',       dest='cleanup', action='store_true',
#                                                 help="remove job output after hadd'ing" )
  
  # SUBCOMMAND ABBREVIATIONS, e.g. 'pico.py s' or 'pico.py sub'
  args = sys.argv[1:]
  if args:
    subcmds = [ # fix order for abbreviations
      'channel','era',
      'run','submit','resubmit','status','hadd','clean',
      'install','list','set','rm'
    ]
    for subcmd in subcmds:
      if args[0] in subcmd[:len(args[0])]: # match abbreviation
        args[0] = subcmd
        break
  args = parser.parse_args(args)
  if hasattr(args,'tag') and len(args.tag)>=1 and args.tag[0]!='_':
    args.tag = '_'+args.tag
  
  # SUBCOMMAND MAINs
  os.chdir(CONFIG.basedir)
  if args.subcommand=='install':
    main_install(args)
  if args.subcommand=='list':
    main_list(args)
  else:
    print ">>> subcommand '%s' not implemented!"%(args.subcommand)
  
  print ">>> Done!"
  

