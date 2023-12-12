#! /usr/bin/env python3
# Author: Izaak Neutelings (April 2020)
import os, sys, glob, json
#import ROOT; ROOT.PyConfig.IgnoreCommandLineOptions = True
try:
  from TauFW.common.tools.file import ensurefile, ensureinit
  from TauFW.common.tools.string import repkey, rreplace
  from TauFW.PicoProducer import basedir
  from TauFW.PicoProducer.analysis.utils import ensuremodule
  from TauFW.PicoProducer.storage.utils import getsamples
  from TauFW.PicoProducer.pico.common import *
except ImportError as err:
  print("\033[1m\033[31mImportError for TauFW modules: Please check if you compiled with `scram b`."
        "For releases older than CMSSW_12_X, please use pico2.py with python2.\033[0m")
  raise err
  

###############
#   INSTALL   #
###############

def main_install(args):
  """NOT IMPLEMENTED YET! Install producer."""
  # TODO:
  #  - guess location (lxplus/PSI/...)
  #  - set defaults of config file
  #  - outside CMSSW: create symlinks for standalone
  if args.verbosity>=1:
    print(">>> main_install", args)
  verbosity = args.verbosity
  


############
#   MAIN   #
############

if __name__ == "__main__":
  
  # COMMON
  from argparse import ArgumentParser
  description = "Central script to process nanoAOD for skimming or analysis."
  parser = ArgumentParser(prog='pico.py',description=description,epilog="Good luck!")
  parser_cmn = ArgumentParser(add_help=False)
  parser_cmn.add_argument('-v', '--verbose',    dest='verbosity', type=int, nargs='?', const=1, default=0,
                                                help="set verbosity")
  parser_sam = ArgumentParser(add_help=False,parents=[parser_cmn])
  parser_lnk = ArgumentParser(add_help=False,parents=[parser_cmn])
  parser_sam.add_argument('-c','--channel',     dest='channels', choices=CONFIG.channels.keys(), default=[ ], nargs='+',
                                                help="skimming or analysis channel to run")
  parser_sam.add_argument('-y','-e','--era',    dest='eras', choices=CONFIG.eras.keys(), default=[ ], nargs='+',
                                                help="year or era to specify the sample list")
  parser_sam.add_argument('-s', '--sample',     dest='samples', type=str, nargs='+', default=[ ],
                          metavar='PATTERN',    help="filter these samples; glob patterns like '*' and '?' wildcards are allowed")
  parser_sam.add_argument('-Z', '--dasfilter',  dest='dasfilters', type=str, nargs='+', default=[ ],
                          metavar='PATTERN',    help="filter these DAS paths; glob patterns like '*' and '?' wildcards are allowed")
  parser_sam.add_argument('-x', '--veto',       dest='vetoes', nargs='+', default=[ ],
                          metavar='PATTERN',    help="exclude/veto these samples; glob patterns are allowed")
  parser_sam.add_argument('-X', '--dasveto',    dest='dasvetoes', nargs='+', default=[ ],
                          metavar='PATTERN',    help="exclude/veto these DAS paths; glob patterns are allowed")
  parser_sam.add_argument('--dtype','--dt',     dest='dtypes', choices=GLOB.dtypes, default=GLOB.dtypes, nargs='+',
                                                help="filter these data type(s)")
  parser_sam.add_argument('-D','--das',         dest='checkdas', action='store_true',
                                                help="check DAS for total number of events")
  parser_sam.add_argument('--dasfiles',         dest='dasfiles', action='store_true',
                                                help="get files from DAS (instead of local storage, if predefined)")
  parser_sam.add_argument('-t','--tag',         dest='tag', default="",
                                                help="tag for output file name")
  parser_sam.add_argument('-f','--force',       dest='force', action='store_true',
                                                help="force overwrite")
  parser_sam.add_argument('-d','--dry',         dest='dryrun', action='store_true',
                                                help="dry run: prepare job without submitting for debugging purposes")
  parser_sam.add_argument('-E', '--opts',       dest='extraopts', type=str, nargs='+', default=[ ],
                          metavar='KEY=VALUE',  help="extra options for the skim or analysis module, "
                                                     "passed as list of 'KEY=VALUE', separated by spaces")
  parser_sam.add_argument('-C','--ncores',      dest='ncores', type=int, default=CONFIG.ncores,
                                                help="number of cores to run event checks or validation in parallel, default=%(default)s")
  parser_job = ArgumentParser(add_help=False,parents=[parser_sam]) # common for submit, resubmit, status, ...
  parser_job.add_argument('--checkqueue',       dest='checkqueue', type=int, nargs='?', const=1, default=-1,
                          metavar='N',          help="check job status: 0 (no check), 1 (check once, fast), -1 (check every job, slow, default)") # speed up if batch is slow
  parser_job.add_argument('--skipevts',         dest='checkevts', action='store_false',
                                                help="skip validation and counting of events in output files (faster)")
  parser_job.add_argument('--checkexpevts',     dest='checkexpevts', action='store_true', default=None,
                                                help="check if the actual number of processed events is the same as the expected number")
  parser_chk = ArgumentParser(add_help=False,parents=[parser_job]) # common for status, hadd, haddclean, clean
  parser_hdd_ = ArgumentParser(add_help=False,parents=[parser_chk]) # common for hadd and haddclean
  parser_job.add_argument('--preselect',        dest='preselect', type=str, default=None,
                                                help="preselection to be shipped to skimjob.py during run command")
  parser_job.add_argument('-p','--prefetch',    dest='prefetch', action='store_true',
                                                help="copy remote file during job to increase processing speed and ensure stability")
  parser_job.add_argument('-B','--batch-opts',  dest='batchopts', default=CONFIG.batchopts,
                                                help="extra options for the batch system, default=%(default)r")
  parser_job.add_argument('-M','--time',        dest='time', default=None,
                                                help="maximum run time of job")
  parser_job.add_argument('-q','--queue',       dest='queue', default=str(CONFIG.queue),
                                                help="queue of batch system (job flavor on HTCondor)")
  parser_job.add_argument('-P','--prompt',      dest='prompt', action='store_true',
                                                help="ask user permission before submitting a sample")
  parser_job.add_argument('-T','--test',        dest='testrun', type=int, nargs='?', const=2000, default=0,
                          metavar='NEVTS',      help="run a test with limited nummer of jobs and events, default nevts=%(const)d")
  parser_job.add_argument('-n','--filesperjob', dest='nfilesperjob', type=int, default=-1,
                                                help="number of files per job, default=%d"%(CONFIG.nfilesperjob))
  parser_job.add_argument('-m','--maxevts',     dest='maxevts', type=int, default=None,
                          metavar='NEVTS',      help="maximum number of events per job to process (split large files, group small ones), default=%d"%(CONFIG.maxevtsperjob))
  parser_job.add_argument('--split',            dest='split_nfpj', type=int, nargs='?', const=2, default=1,
                          metavar='NFILES',     help="divide default number of files per job, default=%(const)d")
  parser_job.add_argument('--tmpdir',           dest='tmpdir', type=str, default=None,
                                                help="for skimming only: temporary output directory befor copying to outdir")
  parser_hdd_.add_argument('--haddcmd',         dest='haddcmd', default=CONFIG.haddcmd,
                                                help="alternative hadd command, e.g. haddnano.py")
  parser_hdd_.add_argument('-m','--maxopenfiles',dest='maxopenfiles', type=int, default=CONFIG.maxopenfiles,
                           metavar='NFILES',    help="maximum numbers to be opened during hadd, default=%(default)d")
  
  # SUBCOMMANDS
  subparsers = parser.add_subparsers(title="sub-commands",dest='subcommand',help="sub-command help")
  help_ins = "install"
  help_lst = "list configuration"
  help_get = "get information from configuration or samples"
  help_set = "set given variable in the configuration file"
  help_rmv = "remove given variable from the configuration file"
  help_wrt = "write files to text file"
  help_chl = "link a channel to a module in the configuration file"
  help_era = "link an era to a sample list in the configuration file"
  help_run = "run nanoAOD processor locally"
  help_sub = "submit processing jobs"
  help_res = "resubmit failed processing jobs"
  help_sts = "status of processing jobs"
  help_hdd = "hadd processing job output"
  help_hdc = "hadd processing job output & remove job output"
  help_cln = "remove job output"
  parser_ins = subparsers.add_parser('install',  parents=[parser_cmn],  help=help_ins, description=help_ins)
  parser_lst = subparsers.add_parser('list',     parents=[parser_cmn],  help=help_lst, description=help_lst)
  parser_get = subparsers.add_parser('get',      parents=[parser_sam],  help=help_get, description=help_get)
  parser_set = subparsers.add_parser('set',      parents=[parser_cmn],  help=help_set, description=help_set)
  parser_rmv = subparsers.add_parser('rm',       parents=[parser_cmn],  help=help_rmv, description=help_rmv)
  parser_wrt = subparsers.add_parser('write',    parents=[parser_sam],  help=help_wrt, description=help_wrt)
  parser_chl = subparsers.add_parser('channel',  parents=[parser_lnk],  help=help_chl, description=help_chl)
  parser_era = subparsers.add_parser('era',      parents=[parser_lnk],  help=help_era, description=help_era)
  parser_run = subparsers.add_parser('run',      parents=[parser_sam],  help=help_run, description=help_run)
  parser_sub = subparsers.add_parser('submit',   parents=[parser_job],  help=help_sub, description=help_sub)
  parser_res = subparsers.add_parser('resubmit', parents=[parser_job],  help=help_res, description=help_res)
  parser_sts = subparsers.add_parser('status',   parents=[parser_chk],  help=help_sts, description=help_sts)
  parser_hdd = subparsers.add_parser('hadd',     parents=[parser_hdd_], help=help_hdd, description=help_hdd)
  parser_hdc = subparsers.add_parser('haddclean',parents=[parser_hdd_], help=help_hdc, description=help_hdc)
  parser_cln = subparsers.add_parser('clean',    parents=[parser_chk],  help=help_cln, description=help_cln)
  #parser_get.add_argument('variable',           help='variable to change in the config file')
  parser_get.add_argument('variable',           help="variable to get information on",choices=['samples','files','nevents','nevts',]+list(CONFIG.keys()))
  parser_set.add_argument('variable',           help="variable to set or change in the config file")
  parser_set.add_argument('key',                help="channel or era key name", nargs='?', default=None)
  parser_set.add_argument('value',              help="value for given value")
  parser_wrt.add_argument('listname',           help="file name of text file for file list, default=%(default)r", nargs='?', default=str(CONFIG.filelistdir))
  parser_rmv.add_argument('variable',           help="variable to remove from the config file")
  parser_rmv.add_argument('key',                help="channel or era key name to remove", nargs='?', default=None)
  parser_chl.add_argument('key',                metavar='channel', help="channel key name")
  parser_chl.add_argument('value',              metavar='module',  help="module linked to by given channel")
  parser_era.add_argument('key',                metavar='era',     help="era key name")
  parser_era.add_argument('value',              metavar='samples', help="samplelist linked to by given era")
  parser_ins.add_argument('type',               choices=['standalone','cmmsw'], #default=None,
                                                help="type of installation: standalone or compiled in CMSSW")
  parser_get.add_argument('-U','--url',         dest='inclurl', action='store_true',
                                                help="include XRootD url in filename for 'get files'")
  parser_get.add_argument('-L','--limit',       dest='limit', type=int, default=-1,
                          metavar='NFILES',     help="limit number files in list for 'get files'")
  parser_get.add_argument('-l','--local',       dest='checklocal', action='store_true',
                                                help="compute total number of events in storage system (not DAS) for 'get files' or 'get nevents'")
  parser_get.add_argument('-w','--write',       dest='write', type=str, nargs='?', const=str(CONFIG.filelistdir), default="",
                          metavar='FILE',       help="write file list, default=%(const)r")
  parser_get.add_argument('-S','--split',       dest='split', action='store_true',
                                                help="split samples with multiple datasets (extensions)")
  parser_wrt.add_argument('-n','--nevts',       dest='getnevts', action='store_true',
                                                help="get nevents per file")
  parser_wrt.add_argument('-S','--split',       dest='split', action='store_true',
                                                help="split samples with multiple datasets (extensions)")
  parser_wrt.add_argument(     '--skipempty',   dest='skipempty', action='store_true',
                                                help="do not write file with zero events")
  parser_wrt.add_argument('-T','--try',         dest='retries', type=int, default=1, action='store',
                                                help="number of retries if file is not found")
  parser_run.add_argument('-m','--maxevts',     dest='maxevts', type=int, default=None,
                          metavar='NEVTS',      help="maximum number of events (per file) to process")
  parser_run.add_argument('--preselect',        dest='preselect', type=str, default=None,
                                                help="preselection to be shipped to skimjob.py during run command")
  parser_run.add_argument('-n','--nfiles',      dest='nfiles', type=int, default=1,
                                                help="maximum number of input files to process (per sample), default=%(default)d")
  parser_run.add_argument('-S', '--nsamples',   dest='nsamples', type=int, default=1,
                                                help="number of samples to run, default=%(default)d")
  parser_run.add_argument('-i', '--input',      dest='infiles', nargs='+', default=[ ],
                                                help="input files (nanoAOD)")
  parser_run.add_argument('-o', '--outdir',     dest='outdir', type=str, default='output',
                                                help="output directory, default=%(default)r")
  parser_run.add_argument('-p','--prefetch',    dest='prefetch', action='store_true',
                                                help="copy remote file during run to increase processing speed and ensure stability")
  parser_sts.add_argument('-l','--log',         dest='showlogs', type=int, nargs='?', const=-1, default=0,
                          metavar='NLOGS',      help="show log files of failed jobs: 0 (show none), -1 (show all), n (show max n)")
  #parser_hdd.add_argument('--keep',             dest='cleanup', action='store_false',
  #                                              help="do not remove job output after hadd'ing")
  parser_hdd.add_argument('-r','--clean',       dest='cleanup', action='store_true',
                                                help="remove job output (to be used after hadd'ing)")
  
  # SUBCOMMAND ABBREVIATIONS, e.g. 'pico.py s' or 'pico.py sub'
  args = sys.argv[1:]
  if args:
    subcmds = [ # fix order for abbreviations
      'channel','era',
      'run','submit','resubmit','status','hadd','haddclean','clean',
      'install','list','set','rm','write',
    ]
    for subcmd in subcmds:
      if args[0] in subcmd[:len(args[0])]: # match abbreviation
        args[0] = subcmd
        break
  args = parser.parse_args(args)
  if hasattr(args,'tag') and len(args.tag)>=1 and args.tag[0]!='_':
    args.tag = '_'+args.tag
  if args.subcommand==None:
    parser.print_help()
    exit(0)
  
  # VERBOSITY
  if args.verbosity>=2:
    SLOG.setverbosity(args.verbosity-1)
  
  # SUBCOMMAND MAINs
  os.chdir(basedir) #CONFIG.basedir
  if args.subcommand=='install':
    main_install(args)
  if args.subcommand=='list':
    from TauFW.PicoProducer.pico.config import main_list
    main_list(args)
  elif args.subcommand=='get':
    from TauFW.PicoProducer.pico.config import main_get
    main_get(args)
  elif args.subcommand=='set':
    from TauFW.PicoProducer.pico.config import main_set
    main_set(args)
  elif args.subcommand=='write':
    from TauFW.PicoProducer.pico.config import main_write
    main_write(args)
  elif args.subcommand in ['channel','era']:
    from TauFW.PicoProducer.pico.config import main_link
    main_link(args)
  elif args.subcommand=='rm':
    from TauFW.PicoProducer.pico.config import main_rm
    main_rm(args)
  elif args.subcommand=='run':
    from TauFW.PicoProducer.pico.run import main_run
    main_run(args)
  elif args.subcommand in ['submit','resubmit']:
    from TauFW.PicoProducer.pico.job import main_submit
    main_submit(args)
  elif args.subcommand in ['status','hadd','haddclean','clean']:
    from TauFW.PicoProducer.pico.job import main_status
    main_status(args)
  else:
    print(">>> subcommand '%s' not implemented!"%(args.subcommand))
  
  print(">>> Done!")
  
