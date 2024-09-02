# -*- coding: utf-8 -*-
# Author: Izaak Neutelings (June 2020)
import os, re, glob
from TauFW.common.tools.utils import isnumber, islist, ensurelist, unpacklistargs, quotestrs, repkey, getyear
from TauFW.common.tools.file import ensuredir, ensuremodule
from TauFW.common.tools.root import ensureTFile, loadmacro
from TauFW.common.tools.log import Logger, color
from TauFW.Plotter.plot.Variable import Variable, Var, ensurevar
from TauFW.Plotter.plot.Selection import Selection, Sel
import TauFW.Plotter.plot.CMSStyle as CMSStyle
import ROOT; ROOT.PyConfig.IgnoreCommandLineOptions = True
from ROOT import gDirectory, gROOT, TH1, THStack, kDotted, kBlack, kWhite
gROOT.SetBatch(True)
LOG  = Logger('Sample')
era  = None # data period: 2016, 2017, 2018, ...
lumi = -1   # integrated luminosity [fb-1]
cme  = 13   # center-of-mass energy [TeV]
xsecs_nlo = { # NLO cross sections to compute k-factor for stitching
  'DYJetsToLL_M-50':     3*2025.74, # NNLO, FEWZ
  'DYJetsToLL_M-10to50':  18610.0, # NLO, aMC@NLO
  'WJetsToLNu':         3*20508.9, # NNLO, FEWZ
}


def getsampleset(datasample,expsamples,sigsamples=[ ],**kwargs):
  """Create sample set from a table of data and MC samples."""
  channel    = kwargs.get('channel',    ""    )
  era        = kwargs.get('era',        ""    )
  fpattern   = kwargs.get('file',       None  ) # file name pattern, e.g. $PICODIR/$SAMPLE_$CHANNEL$TAG.root
  weight     = kwargs.pop('weight',     ""    ) # common weight for MC samples
  dataweight = kwargs.pop('dataweight', ""    ) # weight for data samples
  url        = kwargs.pop('url',        ""    ) # XRootD url
  tag        = kwargs.pop('tag',        ""    ) # extra tag for file name
  
  if not fpattern:
    fpattern = "$PICODIR/$SAMPLE_$CHANNEL$TAG.root"
  if '$PICODIR' in fpattern:
    import TauFW.PicoProducer.tools.config as GLOB
    CONFIG   = GLOB.getconfig(verb=0)
    picodir  = CONFIG['picodir']
    fpattern = repkey(fpattern,PICODIR=picodir)
  if url:
    fpattern = "%s/%s"%(fpattern,url)
  LOG.verb("getsampleset: fpattern=%r"%(fpattern),level=1)
  
  # MC (EXPECTED)
  for i, info in enumerate(expsamples[:]):
    expkwargs = kwargs.copy()
    expkwargs['weight'] = weight
    if len(info)==4:
      group, name, title, xsec = info
    elif len(info)==5 and isinstance(info[4],dict):
      group, name, title, xsec, newkwargs = info
      expkwargs.update(newkwargs)
    else:
      LOG.throw(IOError,"Did not recognize mc row %s"%(info))
    fname = repkey(fpattern,ERA=era,GROUP=group,SAMPLE=name,CHANNEL=channel,TAG=tag)
    #print(fname)
    sample = MC(name,title,fname,xsec,**expkwargs)
    expsamples[i] = sample
  
  # DATA (OBSERVED)
  group = "Data"
  title = 'Observed'
  datakwargs = kwargs.copy()
  datakwargs['weight'] = dataweight
  if not datasample:
    datasample==None
  elif isinstance(datasample,dict) and channel:
    datasample = datasample[channel]
  if isinstance(datasample,str):
    dname = datasample
  elif len(datasample)==2:
    if isinstance(datasample[1],dict): # dictionary
      dname = datasample[0]
      datakwargs.update(datasample[1])
    else: # string
      group, dname = datasample
  elif len(datasample)==3:
    group, dname = datasample[:2]
    if isinstance(datasample[2],dict): # dictionary
      datakwargs.update(datasample[2])
    else: # string
      title = datasample[2]
  elif len(datasample)==4 and isinstance(datasample[3],dict):
    group, dname, title, newkwargs = datasample
    datakwargs.update(newkwargs)
  elif datasample:
    LOG.throw(IOError,"Did not recognize data row %s"%(datasample))
  #print(fnames)
  if datasample:
    fpattern = repkey(fpattern,ERA=era,GROUP=group,SAMPLE=dname,CHANNEL=channel,TAG=tag)
    fnames   = glob.glob(fpattern)
    if len(fnames)==1:
      datasample = Data(dname,title,fnames[0])
    elif len(fnames)>1:
      namerexp = re.compile(dname.replace('?','.').replace('*','.*'))
      dname    = dname.replace('?','').replace('*','')
      datasample = MergedSample(dname,'Observed',data=True)
      for fname in fnames:
        setname = namerexp.findall(fname)[0]
        #print(setname)
        title_ = 'Obs. (%s)'%(setname.split('_')[-1]) if '_Run20' in setname else title
        datasample.add(Data(setname,title_,fname,**datakwargs))
    else:
      LOG.throw(IOError,"Did not find data file %r"%(fpattern))
  
  # SAMPLE SET
  sampleset = SampleSet(datasample,expsamples,sigsamples,**kwargs)
  return sampleset
  

def getmcsample(group,sample,title,xsec,channel,era,tag="",verb=0,**kwargs):
  """Helper function to create MC sample.
  E.g.: getmcsample('DY',"DYJetsToLL_M-50","DYJetsToLL",1.,channel,era,verb=1),"""
  #LOG.header("getmcsamples")
  fname   = kwargs.get('fname', "$PICODIR/$SAMPLE_$CHANNEL$TAG.root" ) # file name pattern of pico files
  user    = kwargs.get('user',   "" )
  picodir = kwargs.get('pico',   "" )
  picodir = ""
  if '$USER' in fname and not user:
    import getpass
    user = getpass.getuser()
  if '$PICODIR' in fname and not picodir:
    import TauFW.PicoProducer.tools.config as GLOB
    CONFIG  = GLOB.getconfig(verb=0)
    picodir = CONFIG['picodir']
  fname_ = repkey(fname,PICODIR=picodir,USER=user,ERA=era,GROUP=group,SAMPLE=sample,CHANNEL=channel,TAG=tag)
  if not os.path.isfile(fname_):
    print(">>> Did not find %r"%(fname_))
  name = sample+tag
  if verb>=1:
    print(">>> getmcsample: %s, %s, %s"%(name,sample,fname_))
  sample = MC(name,title,fname_,xsec,**kwargs)
  return sample
  

def setera(era_,lumi_=None,**kwargs):
  """Set global era and integrated luminosity for Samples and CMSStyle."""
  global era, lumi, cme
  era  = str(era_) #.replace('UL',"")
  lumi = kwargs.get('lumi',lumi_)
  if lumi==None:
    lumi = CMSStyle.lumi_dict.get(era,None)
    if lumi==None: # try again with year
      year = str(getyear(era_))
      lumi = CMSStyle.lumi_dict.get(year,None)
  else:
    kwargs['lumi'] = lumi
  cme = kwargs.get('cme',cme)
  CMSStyle.setCMSEra(era,**kwargs)
  LOG.verb("setera: era = %r, lumi = %r/fb, cme = %r TeV"%(era,lumi,cme),kwargs,2)
  if not lumi or lumi<0:
    LOG.warn("setera: Could not set luminosity for era %r... Returning %s"%(era,lumi))
  return lumi
  

def unpack_sellist_args(*args):
  """Unpack selections at end from arguments."""
  vargs     = [ ]   # unparsed arguments (assumed to be Variable objects)
  sellist   = None  # list of selections (string or Selection object)
  singlesel = True  # only one Selection passed
  if len(args)>=1:
    if isinstance(args[-1],Selection): # convert to list
      sellist   = [args[-1]] # [Selection]
      vargs     = args[:-1]
    elif islist(args[-1]) and any(isinstance(s,Selection) for s in args[-1]):
      sellist   = args[-1] # already a list of selections
      vargs     = args[:-1]
      singlesel = False
    elif isinstance(args[-1],str): # convert to selection string
      sellist   = [Selection(args[-1])]
      vargs     = args[:-1]
    else:
      sellist   = [Selection()] # no selection given
      vargs     = args
  return vargs, sellist, singlesel
  

def unpack_gethist_args(*args,**kwargs):
  """
  Help function to unpack argument list that contain variable(s) and selection(s):
    gethist(str xvar, int nxbins, float xmin, float xmax, str cuts="")
    gethist(str xvar, list xbins, str cuts="")
    gethist(Variable xvar, str cuts="")
    gethist(list varlist, str cuts="")
  where cuts is either a (list of) selection string(s) or Selection object(s),
  and varlist is a list of Variables objects, or a list of tuples defining a variable:
    - [(str xvar, int nxbins, float xmin, float xmax), ... ]
    - [(str xvar, list xbins), ... ]
  Returns (list varlist, list sellist, bool singlevar, bool singlesel)
    - a list of Variable objects,
    - a list of Selection objects,
    - a boolean to flag a single variable was passed
    - a boolean to flag a single selection was passed
  For testing, see test/testUnpacking.py.
  """
  verbosity = LOG.getverbosity(kwargs)
  varlist   = None  # list of Variable objects
  singlevar = False # only one Variable passed
  vargs, sellist, singlesel = unpack_sellist_args(*args)
  if len(vargs)==1: # parse variable arguments
    varlist = vargs[0]
    if isinstance(varlist,Variable):
      varlist   = [varlist]
      singlevar = True
    elif islist(vargs[0]):
      varlist = [ensurevar(v) for v in vargs[0]]
  elif len(vargs) in [2,4]: # fixed-binning or variable binning
    varlist   = [Variable(*vargs)]
    singlevar = True
  if varlist==None or sellist==None:
    LOG.throw(IOError,'unpack_gethist_args: Could not unpack arguments %s, len(args)=%d, varlist=%s, sellist=%r.'%(
                                                                       args,len(args),varlist,sellist))
  LOG.verb("unpack_gethist_args: varlist=%s, sel=%r, singlevar=%r, singlesel=%r"%(varlist,sellist,singlevar,singlesel),verbosity,4)
  return varlist, sellist, singlevar, singlesel
  

def unpack_gethist2D_args(*args,**kwargs):
  """
  Help function to unpack argument list that contain variable pair(s) and selection:
    gethist2D(str xvar, int nxbins, float xmin, float xmax, str yvar, int nybins, float ymin, float ymax, str cuts="")
    gethist2D(str xvar, list xbins, str yvar, list ybins, str cuts="")
    gethist2D(str xvar, int nxbins, float xmin, float xmax, str yvar, list ybins, str cuts="")
    gethist2D(str xvar, list xbins, str yvar, int nybins, float ymin, float ymax, str cuts="")
    gethist2D(Variable xvar, Variable yvar, str cuts="")
    gethist2D(tuple xvar, tuple yvar, str cuts="")
    gethist2D(list xvarlist, list yvarlist, str cuts="")
    gethist2D(list varlist, str cuts="")
    gethist2D(tuple varpair, str cuts="")
  where cuts is either a (list of) selection string(s) or Selection object(s),
  where the tuples xvar and yvar can be of the form
    – (str xvar, int nxbins, float xmin, float xmax)
    – (str xvar, list xbins)
  and the xvarlist and yvarlist are lists of Variables object pairs,
    - [(Variable xvar,Variable yvar), ... ]
  or a list of tuples defining a variable:
    - [(str xvar, int nxbins, float xmin, float xmax, str yvar, int nybins, float ymin, float ymax), ...]
    - [(str xvar, list xbins), ...]
  and varpair is tuple of a single pair of Variable objects:
    - (Variable xvar,Variable yvar)
  Returns (list varlist, list sellist, bool singlevar, bool singlesel)
    - a list of Variable object pairs,
    - a list of Selection objects,
    - a boolean to flag a single variable was passed
    - a boolean to flag a single selection was passed
  For testing, see test/testUnpacking.py.
  """
  verbosity = LOG.getverbosity(kwargs)
  varlist   = None  # list of pairs of Variable objects
  singlevar = False # only one pair of Variable objects passed
  vargs, sellist, singlesel = unpack_sellist_args(*args)
  if len(vargs)==1:
    varlist = vargs[0]
    singlevar = len(varlist)==2 and islist(varlist) and all(isinstance(v,Variable) for v in varlist)
    if singlevar:
      varlist = [varlist]
  elif len(vargs)==2:
    xvars, yvars = vargs
    if isinstance(xvars,Variable) and isinstance(yvars,Variable): # one pair of Variable objects
      varlist = [(xvars,yvars)]
      singlevar = True
    elif all(isinstance(v,Variable) for v in xvars+yvars): # assume two lists of Variable objects
      varlist = zip(xvars,yvars)
    elif len(xvars) in [2,4] and len(yvars) in [2,4] and isinstance(xvars[0],str) and isinstance(yvars[0],str):
      varlist = [Variable(*xvars),Variable(*yvars)]
      singlevar = True
    elif islist(xvars) and islist(yvars) and all(islist(x) for x in xvars) and all(islist(y) for y in yvars):
      varlist = [(Variable(*x),Variable(*y)) for x, y in zip(xvars,yvars)]
  elif len(vargs)==4: # two variable binnings: (str xvar, list xbins), (str yvar, list ybins)
    varlist   = [(Variable(*vargs[0:2]),Variable(*vargs[2:4]))]
    singlevar = True
  elif len(vargs)==6: # one fixed-binning, one variable binning
    if isinstance(vargs[2],str): # (str xvar, int nxbins, float xmin), float xmax, (str yvar, list ybins)
      varlist   = [(Variable(*vargs[0:2]),Variable(*vargs[2:6]))]
      singlevar = True
    elif isinstance(vargs[4],str): # (str xvar, list xbins), (str yvar, int nybins, float ymin, float ymax)
      varlist   = [(Variable(*vargs[0:4]),Variable(*vargs[4:6]))]
      singlevar = True
  elif len(vargs)==8:
    varlist   = [(Variable(*vargs[0:4]),Variable(*vargs[4:8]))]
    singlevar = True
  if varlist==None or sellist==None:
    LOG.throw(IOError,'unpack_gethist2D_args: Could not unpack arguments %s, len(args)=%d, varlist=%s, sellist=%s.'%(args,len(args),varlist,sellist))
  elif isinstance(sellist,str):
    sellist = Selection(str)
  LOG.verb("unpack_gethist2D_args: args=%r"%(args,),verbosity,3)
  LOG.verb("unpack_gethist2D_args: varlist=%s, sellist=%r, singlevar=%r, singlesel=%r"%(varlist,sellist,singlevar,singlesel),verbosity,4)
  return varlist, sellist, singlevar, singlesel
  

def findsample(samples,*searchterms,**kwargs):
  """Help function to get all samples corresponding to some name and optional label."""
  verbosity   = LOG.getverbosity(kwargs)
  filename    = kwargs.get('fname',     ""    )
  unique      = kwargs.get('unique',    False ) # require exactly one match (return Sample object)
  warn        = kwargs.get('warn',      True  ) # warn if nothing found (set to True to suppress)
  recursive   = kwargs.get('recursive', False ) # look in subsamples (if MergedSamples)
  split       = kwargs.get('split',     False ) # look in split samples
  searchterms = unpacklistargs(searchterms)
  LOG.verb("findsample: Looking for sample with search terms %s in list %s..."%(
           searchterms,samples),verbosity,3)
  matches = [ ]
  if split:
    newsamples = [ ]
    for sample in samples:
      if sample.splitsamples:
        LOG.verb("findsample: Splitting sample %s..."%(sample.name),verbosity,3)
        newsamples.extend(sample.splitsamples)
      else:
        newsamples.append(sample)
    samples = newsamples
  for sample in samples:
    if recursive and isinstance(sample,MergedSample):
      kwargs_ = kwargs
      kwargs_['warn'] = False
      matches.extend(findsample(sample.samples,*searchterms,**kwargs_))
    if sample.match(*searchterms,**kwargs) and filename in sample.filename:
      matches.append(sample)
  if not matches:
    if warn:
      LOG.warn("findsample: Could not find a sample with search terms %s..."%(
               quotestrs(list(searchterms)+[filename])))
  elif unique:
    if len(matches)>1:
      LOG.warn("findsample: Found more than one match to %s. Using first match only: %s"%(
               quotestrs(searchterms),quotestrs(matches)))
    return matches[0]
  return matches
  

def findsample_with_flag(samples,flag,*searchterms,**kwargs):
  """Help function to get sample with some flag from a list of samples."""
  matches   = [ ]
  unique    = kwargs.get('unique', False )
  for sample in samples:
    if hasattr(sample,flag) and getattr(sample,flag) and\
       (not searchterms or sample.match(*searchterms,**kwargs)):
      matches.append(sample)
  if not matches:
    LOG.warn("Could not find a sample with %r=True..."%flag)
  elif unique:
    if len(matches)>1:
      LOG.warn("Found more than one signal sample. Using first match only: %s"%(quotestrs(s.name for s in matches)))
    return matches[0]
  return matches
  

def join(samplelist,*searchterms,**kwargs):
  """Join samples from a sample list into one merged sample, that match a set of search terms.
  E.g. samplelist = join(samplelist,'DY','M-50',name='DY_highmass')."""
  verbosity   = LOG.getverbosity(kwargs)
  searchterms = unpacklistargs(searchterms)
  name        = kwargs.get('name',  searchterms[0] ) # name of new merged sample
  title       = kwargs.get('title', None           ) # title of new merged sample
  color       = kwargs.get('color', None           ) # color of new merged sample
  LOG.verb("join: merging '%s' into %r"%("', '".join(searchterms),name),verbosity,level=1)
  
  # GET samples containing names and searchterm
  mergelist = [s for s in samplelist if s.match(*searchterms,incl=True)]
  if len(mergelist)<=1:
    LOG.warn("Could not merge %r: fewer than two %r samples (%d)"%(name,name,len(mergelist)))
    return samplelist
  padding = max([len(s.name) for s in mergelist])+2 # number of spaces
  
  # ADD samples with name and searchterm
  mergedsample = MergedSample(name,title,color=color)
  for sample in mergelist:
    samplestr = repr(sample.name).ljust(padding)
    LOG.verb("  adding %s to %r (%s)"%(samplestr,name,sample.fnameshort),verbosity,level=2)
    mergedsample.add(sample)
  
  # REPLACE matched samples with merged sample in samplelist, preserving the order
  if mergedsample.samples and samplelist:
    if isinstance(samplelist,SampleSet):
      samplelist.replace(mergedsample)
    else:
      oldindex = len(samplelist)
      for sample in mergedsample.samples:
        index = samplelist.index(sample)
        if index<oldindex:
          oldindex = index
        samplelist.remove(sample)
      samplelist.insert(index,mergedsample)
  return samplelist
  

def stitch(samplelist,*searchterms,**kwargs):
  """Stitching samples: merge samples and reweight inclusive
  sample and rescale jet-binned samples, e.g. DY*Jets or W*Jets."""
  verbosity = LOG.getverbosity(kwargs)+2
  name      = kwargs.get('name',      searchterms[0] )
  name_incl = kwargs.get('incl',      searchterms[0] ) # name of inclusive sample
  xsec_incl = kwargs.get('xsec',      None           ) # (N)NLO cross section to compute k-factor
  kfactor   = kwargs.get('kfactor',   None           ) # k-factor
  npartvar  = kwargs.get('npart',     'NUP'          ) # variable name of number of partons in tree; 'NUP', 'LHE_Njets', ...
  cme       = kwargs.get('cme',       13 if '201' in era else 13.6 ) # COM energy
  LOG.verb("stitch: rescale, reweight and merge %r samples"%(name),verbosity,level=1)
  
  # GET list of samples to-be-stitched
  stitchlist = samplelist.samples if isinstance(samplelist,SampleSet) else samplelist
  stitchlist = [s for s in stitchlist if s.match(*searchterms,incl=True)]
  LOG.verb("stitch: samplelist: {','.join(s.name for s in stitchlist)}",verbosity,level=1)
  if len(stitchlist)<2:
    LOG.warn(f"stitch: Could not stitch {name!r}: Fewer than two {name!r} samples ({len(stitchlist)})"
              " match '"+"', '".join(searchterms)+"' -- still applying k-factor to inclusive sample")
    if kfactor:
      sample_incl.norm *= kfactor
    return samplelist
  
  # FIND INCLUSIVE SAMPLE
  sample_incl = None
  sample_mutau = None #"DYJetsToMuTauh_M-50"
  if "2022" in era or "2023" in era: # DYto2L-4Jets_MLL-50_*J, WJetstoLNu-4Jets_*J
    samples_jetIncl = [s for s in stitchlist if s.name==name_incl]
  else: # DY*JetsToLL_M-50, W*JetstoLNu
    samples_jetIncl = [s for s in stitchlist if s.match(name_incl)]
  LOG.verb(f"stitch: samples_jetIncl={samples_jetIncl!r}",verbosity,level=1)
  for sample in samples_jetIncl:
    if sample.match("DYJets*MuTau",incl=False):
      sample_mutau = sample
    else:
      sample_incl = sample
  if not sample_incl:
    print("No inclusive sample to stitch... abort")
    return samplelist
  
  # NAME & TITLE of new stitched sample
  name  = kwargs.get('name',stitchlist[0].name)
  title = kwargs.get('title',gettitle(name,stitchlist[0].title))
  if not title:
    title = sample_incl.title
  
  # Compute k-factor for NLO cross section normalisation
  # TODO: Apply k-factor consistently before or after stitching, not a era-dependent mix
  xsec_incl_initial    = sample_incl.xsec
  if kfactor:
    xsec_incl_corrected = kfactor*xsec_incl_initial
  elif cme==13: # assume 13 TeV for Run 2
    # the below procedure computes the k-factors from the xross-sections specified in xsecs_nlo above
    # this proceudre is used only for Run-2 (13 TeV)
    # for Run-3 (13.6 TeV) we do the kfactor scaling in the cross sections file so this is not needed
    xsec_incl_corrected = xsec_incl or getxsec_nlo(name,*searchterms) or xsec_incl_initial
    kfactor = xsec_incl_corrected / xsec_incl_initial
  else: # assume 13.6 TeV for Run 3
    # if no kfactor is specified and we are not doing Run-2 (cme=13) method then we set kfactor to 1
    # in the Run-3 method the kfactor is applied to the inputted cross-sections, so by setting this to 1 we ensure it does not get applied twice 
    xsec_incl_corrected = xsec_incl_initial
    kfactor = 1.
  LOG.verb("stitch: %s k-factor = %.2f = %.2f / %.2f"%(name,kfactor,xsec_incl_corrected,xsec_incl_initial),verbosity,level=2)
  LOG.verb("stitch: samplelist: {','.join(s.name for s in stitchlist)}",verbosity,level=1)
  
  # STITCH DYJets*MuTau into DYJets
  if sample_mutau:
    # Possibility to add skimming efficiencies of nanoAODs; only needed if cutflow histograms in nTuples are not corrected accordingly
    nanoEff_DYll_nj     = { }
    nanoEff_mutau_nj    = { }
    nanoEff_DYll        = kwargs.get('eff_nanoAOD_DYll',         1.) # Average efficiency
    nanoEff_DYll_nj[0]  = kwargs.get('eff_nanoAOD_DYll_0orp4j',  1.)
    nanoEff_DYll_nj[1]  = kwargs.get('eff_nanoAOD_DYll_1j',      1.)
    nanoEff_DYll_nj[2]  = kwargs.get('eff_nanoAOD_DYll_2j',      1.)
    nanoEff_DYll_nj[3]  = kwargs.get('eff_nanoAOD_DYll_3j',      1.)
    nanoEff_DYll_nj[4]  = kwargs.get('eff_nanoAOD_DYll_4j',      1.)
    nanoEff_mutau       = kwargs.get('eff_nanoAOD_mutau',        1.) # Average efficiency
    nanoEff_mutau_nj[0] = kwargs.get('eff_nanoAOD_mutau_0orp4j', 1.)
    nanoEff_mutau_nj[1] = kwargs.get('eff_nanoAOD_mutau_1j',     1.)
    nanoEff_mutau_nj[2] = kwargs.get('eff_nanoAOD_mutau_2j',     1.)
    nanoEff_mutau_nj[3] = kwargs.get('eff_nanoAOD_mutau_3j',     1.)
    nanoEff_mutau_nj[4] = kwargs.get('eff_nanoAOD_mutau_4j',     1.)
    
    cutflow_incl         = sample_incl.getcutflow()
    effMuTau_incl        = cutflow_incl.GetBinContent(18) / cutflow_incl.GetBinContent(17) * nanoEff_DYll
    effMuTauNjet_incl    = dict()
    effMuTauNjet_incl[0] = cutflow_incl.GetBinContent(19) / cutflow_incl.GetBinContent(17) * nanoEff_DYll_nj[0]
    effMuTauNjet_incl[1] = cutflow_incl.GetBinContent(20) / cutflow_incl.GetBinContent(17) * nanoEff_DYll_nj[1]
    effMuTauNjet_incl[2] = cutflow_incl.GetBinContent(21) / cutflow_incl.GetBinContent(17) * nanoEff_DYll_nj[2]
    effMuTauNjet_incl[3] = cutflow_incl.GetBinContent(22) / cutflow_incl.GetBinContent(17) * nanoEff_DYll_nj[3]
    effMuTauNjet_incl[4] = cutflow_incl.GetBinContent(23) / cutflow_incl.GetBinContent(17) * nanoEff_DYll_nj[4]
    
    cutflow_mutau        = sample_mutau.getcutflow()
    effMuTau_excl        = cutflow_mutau.GetBinContent(18) / cutflow_mutau.GetBinContent(17) * nanoEff_mutau
    effMuTauNjet_excl    = dict()
    effMuTauNjet_excl[0] = cutflow_mutau.GetBinContent(19) / cutflow_mutau.GetBinContent(17) * nanoEff_mutau_nj[0]
    effMuTauNjet_excl[1] = cutflow_mutau.GetBinContent(20) / cutflow_mutau.GetBinContent(17) * nanoEff_mutau_nj[1]
    effMuTauNjet_excl[2] = cutflow_mutau.GetBinContent(21) / cutflow_mutau.GetBinContent(17) * nanoEff_mutau_nj[2]
    effMuTauNjet_excl[3] = cutflow_mutau.GetBinContent(22) / cutflow_mutau.GetBinContent(17) * nanoEff_mutau_nj[3]
    effMuTauNjet_excl[4] = cutflow_mutau.GetBinContent(23) / cutflow_mutau.GetBinContent(17) * nanoEff_mutau_nj[4]
  
  # FIND JET-BINNED samples
  sample_njet = { }
  for sample in stitchlist:
    if sample in samples_jetIncl:
      continue
    else:
      if "2022" in era or "2023" in era: 
        match = re.search(r'_(\d{1,2}J)', sample.name)
        if match:
          njets = int(match.group(1)[:-1])
      else: 
        njets = int(sample.name[int(sample.name.find("Jets")-1)])
      sample_njet[njets] = sample
  LOG.verb(f"stitch: samplelist: {','.join(s.name for s in stitchlist)}",verbosity,level=1)
  
  print("Lumi = %.6g, kfactor = %.6g, xsec = %.6g, sumw = %.6g"%(sample_incl.lumi, kfactor, sample_incl.xsec, sample_incl.sumweights))
  print("Sample_incl.norm = %.6g"%sample_incl.norm)
  #sample_incl.xsec = xsec_incl_corrected
  wIncl = sample_incl.lumi * kfactor * sample_incl.xsec * 1000. / sample_incl.sumweights
  print("Inclusve : Lumi = %.6g, kfactor = %.6g, xsec = %.6g, sumw = %.6g"%(sample_incl.lumi, kfactor, sample_incl.xsec, sample_incl.sumweights))
  print("Inclusive weight = %.6g"%wIncl)
  
  effIncl_njet = dict()
  effMuTau_njet = dict()
  wIncl_njet = dict()
  for njets in sample_njet:
    sample = sample_njet[njets]
    effIncl_njet[njets] = sample.xsec/sample_incl.xsec
    print("%i-jet efficiency in inclusive sample = %.6g"%(njets,effIncl_njet[njets]))
    wIncl_njet[njets] = sample.lumi * kfactor * sample.xsec * 1000. / (sample.sumweights + effIncl_njet[njets]*sample_incl.sumweights)
    print(">>> Lumi=%.6g, kfactor=%.6g, xsec=%.6g, sumw=%.6g, sample.norm=%.6g"%(sample.lumi,kfactor,sample.xsec,sample.sumweights,sample.norm))
    print("Inclusive %i jets weight = %.6g"%(njets,wIncl_njet[njets]))
  
  wIncl_mutau = ""
  wMuTau_njet = dict()
  if sample_mutau:
    wIncl_mutau = sample_incl.lumi * kfactor * sample_incl.xsec * 1000. * effMuTau_incl / ( effMuTau_incl*sample_incl.sumweights + effMuTau_excl*sample_mutau.sumweights )
    print("Inclusive mutau weight = %.6g"%wIncl_mutau)
    for njets in sample_njet:
      sample = sample_njet[njets]
      wMuTau_njet[njets] = sample.lumi * kfactor * sample.xsec * 1000. * effMuTau_njet[njets] / ( effMuTau_njet[njets]*sample.sumweights + effMuTauNjet_excl[njets]*sample_mutau.sumweights + effMuTauNjet_incl[njets]*sample_incl.sumweights )
      print("Inclusive mutau %i jets weight = %.6g"%(njets,wMuTau_njet[njets]))
  
  conditionalWeight_incl = ""
  if sample_mutau:
    if len(sample_njet)>0:
      conditionalWeight_incl = "(%s==0||%s>4 ? (mutaufilter ? %.6g : %.6g) : 1)"%(npartvar, npartvar, wIncl_mutau, wIncl)
    else:
      conditionalWeight_incl = "(mutaufilter ? %.6g : %.6g)"%(wIncl_mutau, wIncl)
    for njets in sample_njet:
      conditionalWeight_incl += " * (%s==%i ? (mutaufilter ? %.6g : %.6g) : 1)"%(npartvar, njets, wMuTau_njet[njets], wIncl_njet[njets])
  else:
    if len(sample_njet)>0:
      conditionalWeight_incl = "(%s==0||%s>4 ? %.6g : 1)"%(npartvar, npartvar, wIncl)
    else:
      conditionalWeight_incl = "(%.6g)"%(wIncl)
    for njets in sample_njet:
      conditionalWeight_incl += " * (%s==%i ? %.6g : 1)"%(npartvar, njets, wIncl_njet[njets])
  conditionalWeight_incl = "("+conditionalWeight_incl+")"
  sample_incl.norm = 1.0
  sample_incl.addweight(conditionalWeight_incl)
  
  conditionalWeight_mutau = ""
  if sample_mutau:
    if len(sample_njet)>0:
      conditionalWeight_mutau = "mutaufilter * (%s==0||%s>4 ? %.6g : 1)"%(npartvar, npartvar, wIncl_mutau)
    else:
      conditionalWeight_mutau = "mutaufilter * %.6g"%(wIncl_mutau)
    for njets in sample_njet:
      conditionalWeight_mutau += " * (%s==%i ? %.6g : 1)"%(npartvar, njets, wMuTau_njet[njets])
    conditionalWeight_mutau = "("+conditionalWeight_mutau+")"
    sample_mutau.norm = 1.0
    sample_mutau.addweight(conditionalWeight_mutau)
  
  for njets in sample_njet:
    if sample_mutau:
      conditionalWeight_njet = "(mutaufilter ? %.6g : %.6g)"%(wMuTau_njet[njets], wIncl_njet[njets])
    else:
      conditionalWeight_njet = "%.6g"%wIncl_njet[njets]
    sample_njet[njets].norm = 1.0
    sample_njet[njets].addweight(conditionalWeight_njet)
    print("sample_njet[njets].weight = ",sample_njet[njets].weight)
  
  # JOIN
  join(samplelist,*searchterms,name=name,title=title,verbosity=5)
  newsample = findsample(samplelist,name,unique=True)
  newsample.sample_incl = sample_incl # for gethist_from_file
  print("samplelist = ",samplelist)
  return samplelist
  

def getxsec_nlo(*searchterms,**kwargs):
  """Returns inclusive (N)NLO cross section for stitching og DY and WJ."""
  # https://twiki.cern.ch/twiki/bin/viewauth/CMS/StandardModelCrossSectionsat13TeV#List_of_processes
  # https://ineuteli.web.cern.ch/ineuteli/crosssections/2017/FEWZ/
  # DY cross sections  5765.4 [  4954.0, 1012.5,  332.8, 101.8,  54.8 ]
  # WJ cross sections 61526.7 [ 50380.0, 9644.5, 3144.5, 954.8, 485.6 ]
  xsec_nlo = 0
  for searchterm in searchterms:
    key = ""
    if 'DY' in searchterm:
      if any('10to50' in s for s in searchterms):
        key ='DYJetsToLL_M-10to50'
      else:
        key = 'DYJetsToLL_M-50'
    elif 'WJ' in searchterm:
      key = 'WJetsToLNu'
    elif searchterm in xsecs_nlo:
      key = searchterm
    if key in xsecs_nlo:
      xsec_nlo = xsecs_nlo[key]
      break
  else:
    LOG.warn("getxsec_nlo: Did not find a DY or WJ match in '%s'!"%("', '".join(searchterms)))
  return xsec_nlo
  

def setaliases(tree,verb=0,**aliases):
  """Add alias to TTree. E.g.
       setaliases(tree,deta='abs(eta1-eta2)',stmet='pt_1+pt_2+jpt_1+met',isdata='0')
       aliases = { 'deta':'abs(eta1-eta2)', 'stmet':'pt_1+pt_2+jpt_1+met', 'isdata':'0' }
       setaliases(tree,**aliases)
  """
  if not tree or not aliases:
    return None
  for alias, formula in aliases.items():
    formula = str(formula)
    LOG.verb("setaliases: Adding alias to tree %r: %r -> %r"%(tree.GetName(),alias,formula),verb,level=5)
    tree.SetAlias(alias,formula)
  return tree
  

def selectbranches(tree,selections,verb=0):
  """Keep and drop branches."""
  # Inspiration:
  # https://github.com/cms-nanoAOD/nanoAOD-tools/blob/master/python/postprocessing/framework/branchselection.py
  for cmd in selections:
    #if isinstance(cmd,str):
    cmd, branch = cmd.split()
    if cmd=='drop':
      LOG.verb("selectbranches: drop %r"%(branch),verb+3,level=2)
      tree.SetBranchStatus(branch,0)
    elif cmd=='keep':
      LOG.verb("selectbranches: keep %r"%(branch),verb+3,level=2)
      tree.SetBranchStatus(branch,1)
  #print("selectbranches: DONE")
  return tree
  

from TauFW.Plotter.sample.Sample import *
from TauFW.Plotter.sample.MergedSample import MergedSample
from TauFW.Plotter.sample.SampleSet import SampleSet
import TauFW.Plotter.sample.SampleStyle as STYLE
