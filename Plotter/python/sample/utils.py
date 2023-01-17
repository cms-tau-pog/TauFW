# -*- coding: utf-8 -*-
# Author: Izaak Neutelings (June 2020)
import os, re, glob
from TauFW.common.tools.utils import isnumber, islist, ensurelist, unwraplistargs, quotestrs, repkey, getyear
from TauFW.common.tools.file import ensuredir, ensureTFile, ensuremodule
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
    #print fname
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
  #print fnames
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
        #print setname
        datasample.add(Data(setname,'Observed',fname,**datakwargs))
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
    print ">>> Did not find %r"%(fname_)
  name = sample+tag
  if verb>=1:
    print ">>> getmcsample: %s, %s, %s"%(name,sample,fname_)
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
  cme = kwargs.get('cme',13)
  CMSStyle.setCMSEra(era,**kwargs)
  LOG.verb("setera: era = %r, lumi = %r/fb, cme = %r TeV"%(era,lumi,cme),kwargs,2)
  if not lumi or lumi<0:
    LOG.warn("setera: Could not set luminosity for era %r... Returning %s"%(era,lumi))
  return lumi
  

def unwrap_gethist_args(*args,**kwargs):
  """
  Help function to unwrap argument list that contain variable(s) and selection:
    gethist(str xvar, int nxbins, float xmin, float xmax, str cuts="")
    gethist(str xvar, list xbins, str cuts="")
    gethist(Variable xvar, str cuts="")
    gethist(list varlist, str cuts="")
  where varlist is a list of Variables objects, or a list of tuples defining a variable:
    - [(str xvar, int nxbins, float xmin, float xmax), ... ]
    - [(str xvar, list xbins), ... ]
  Returns a list of Variable objects, a Selection object, and a boolean to flag a single
  instead of a list of variables was given:
    - (list vars, str cut, bool single)
  For testing, see test/testUnwrapping.py.
  """
  vars   = None     # list of Variable objects
  sel    = None     # selection (string or Selection object)
  single = False    # only one Variable passed
  if len(args)>=1:
    if isinstance(args[-1],Selection):
      sel   = args[-1]
      vargs = args[:-1]
    elif isinstance(args[-1],str):
      sel   = Selection(args[-1])
      vargs = args[:-1]
    else:
      sel   = Selection() # no selection given
      vargs = args
  if len(vargs)==1:
    vars  = vargs[0]
    if isinstance(vars,Variable):
      vars   = [vars]
      single = True
    elif islist(vargs[0]):
      vars = [ensurevar(v) for v in vargs[0]]
  elif len(vargs) in [2,4]:
    vars   = [Variable(*vargs)]
    single = True
  if vars==None or sel==None:
    LOG.throw(IOError,'unwrap_gethist_args: Could not unwrap arguments %s, len(args)=%d, vars=%s, sel=%s.'%(
                                                                       args,len(args),vars,sel.selection))
  LOG.verb("unwrap_gethist_args: vars=%s, sel=%r, single=%r"%(vars,sel.selection,single),level=4)
  return vars, sel, single
  

def unwrap_gethist2D_args(*args,**kwargs):
  """
  Help function to unwrap argument list that contain variable pair(s) and selection:
    gethist2D(str xvar, int nxbins, float xmin, float xmax, str yvar, int nybins, float ymin, float ymax, str cuts="")
    gethist2D(str xvar, list xbins, str yvar, list ybins, str cuts="")
    gethist2D(str xvar, int nxbins, float xmin, float xmax, str yvar, list ybins, str cuts="")
    gethist2D(str xvar, list xbins, str yvar, int nybins, float ymin, float ymax, str cuts="")
    gethist2D(Variable xvar, Variable yvar, str cuts="")
    gethist2D(tuple xvar, tuple yvar, str cuts="")
    gethist2D(list xvarlist, list yvarlist, str cuts="")
    gethist2D(list varlist, str cuts="")
    gethist2D(tuple varpair, str cuts="")
  where the tuples xvar and yvar can be of the form
    – (str xvar, int nxbins, float xmin, float xmax)
    – (str xvar, list xbins)
  and the [xy]varlist is a list of Variables object pairs,
    - [(Variable xvar,Variable yvar), ... ]
  or a list of tuples defining a variable:
    - [(str xvar, int nxbins, float xmin, float xmax, str yvar, int nybins, float ymin, float ymax), ...]
    - [(str xvar, list xbins), ...]
  and varpair is tuple of a single pair of Variable objects:
    - (Variable xvar,Variable yvar)
  Returns a list of Variable pairs, a Selection object, and a boolean to flag a single
  instead of a list of variables was given:
    (list varpairs, str cut, bool single)
  For testing, see test/testUnwrapping.py.
  """
  verbosity = LOG.getverbosity(kwargs)
  vars   = None     # list of Variable objects
  sel    = None     # selection (string or Selection object)
  single = False    # only one Variable passed
  if len(args)>=1:
    if isinstance(args[-1],Selection):
      sel   = args[-1]
      vargs = args[:-1]
    elif isinstance(args[-1],str):
      sel   = Selection(args[-1])
      vargs = args[:-1]
    else:
      sel   = Selection() # no selection given
      vargs = args
  if len(vargs)==1:
    vars = vargs[0]
    single = len(vars)==2 and islist(vars) and all(isinstance(v,Variable) for v in vars)
    if single:
      vars = [vars]
  elif len(vargs)==2:
    xvars, yvars = vargs
    if isinstance(xvars,Variable) and isinstance(yvars,Variable):
      vars = [(xvars,yvars)]
      single = True
    elif all(isinstance(v,Variable) for v in xvars+yvars): # assume list
      vars = zip(xvars,yvars)
    elif len(xvars) in [2,4] and len(yvars) in [2,4] and isinstance(xvars[0],str) and isinstance(yvars[0],str):
      vars = [Variable(*xvars),Variable(*yvars)]
      single = True
    elif islist(xvars) and islist(yvars) and all(islist(x) for x in xvars) and all(islist(y) for y in yvars):
      vars = [(Variable(*x),Variable(*y)) for x, y in zip(xvars,yvars)]
  elif len(vargs)==4:
    vars   = [(Variable(*vargs[0:2]),Variable(*vargs[2:4]))]
    single = True
  elif len(vargs)==6:
    if isinstance(vargs[2],str):
      vars   = [(Variable(*vargs[0:2]),Variable(*vargs[2:6]))]
      single = True
    elif isinstance(vargs[4],str):
      vars   = [(Variable(*vargs[0:4]),Variable(*vargs[4:6]))]
      single = True
  elif len(vargs)==8:
    vars   = [(Variable(*vargs[0:4]),Variable(*vargs[4:8]))]
    single = True
  if vars==None or sel==None:
    LOG.throw(IOError,'unwrap_gethist2D_args: Could not unwrap arguments %s, len(args)=%d, vars=%s, sel=%s.'%(args,len(args),vars,sel))
  elif isinstance(sel,str):
    sel = Selection(str)
  LOG.verb("unwrap_gethist2D_args: args=%r"%(args,),verbosity,3)
  LOG.verb("unwrap_gethist2D_args: vars=%s, sel=%r, single=%r"%(vars,sel.selection,single),verbosity,4)
  return vars, sel, single
  

def findsample(samples,*searchterms,**kwargs):
  """Help function to get all samples corresponding to some name and optional label."""
  verbosity   = LOG.getverbosity(kwargs)
  filename    = kwargs.get('fname',    ""    )
  unique      = kwargs.get('unique',   False )
  warn        = kwargs.get('warn',     True  )
  split       = kwargs.get('split',    False )
  searchterms = unwraplistargs(searchterms)
  matches     = [ ]
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
    if sample.match(*searchterms,**kwargs) and filename in sample.filename:
      matches.append(sample)
  if not matches:
    if warn:
      LOG.warn("findsample: Could not find a sample with search terms %s..."%(quotestrs(list(searchterms)+[filename])))
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
  verbosity = LOG.getverbosity(kwargs)
  name      = kwargs.get('name',  searchterms[0] ) # name of new merged sample
  title     = kwargs.get('title', None           ) # title of new merged sample
  color     = kwargs.get('color', None           ) # color of new merged sample
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
  verbosity = LOG.getverbosity(kwargs)
  name      = kwargs.get('name',      searchterms[0] )
  name_incl = kwargs.get('incl',      searchterms[0] ) # name of inclusive sample
  xsec_incl = kwargs.get('xsec',      None           ) # (N)NLO cross section to compute k-factor
  kfactor   = kwargs.get('kfactor',   None           ) # k-factor

####################################################################################
# Efficiency values should be adapted when removing "quick fix" for mutau flag removing radiating taus!
####################################################################################
  effMuTau_incl = kwargs.get('eff_mutau_incl', 0.005086       ) # efficiency mutau (pT>18, |eta|<2.5) in DYJetsToLL_M-50
  effMuTau_excl = kwargs.get('eff_mutau_excl', 0.58383   ) # efficiency mutau (pT>18, |eta|<2.5) in DYJetsToMuTauh_M-50
  effMuTau_njet = dict()
  effMuTau_njet[1] = kwargs.get('eff_mutau_1jet', 0.005593  ) # efficiency mutau (pT>18, |eta|<2.5) in DY1JetsToLL_M-50
  effMuTau_njet[2] = kwargs.get('eff_mutau_2jet', 0.006309  ) # efficiency mutau (pT>18, |eta|<2.5) in DY2JetsToLL_M-50
  effMuTau_njet[3] = kwargs.get('eff_mutau_3jet', 0.006932  ) # efficiency mutau (pT>18, |eta|<2.5) in DY3JetsToLL_M-50
  effMuTau_njet[4] = kwargs.get('eff_mutau_4jet', 0.007856  ) # efficiency mutau (pT>18, |eta|<2.5) in DY4JetsToLL_M-50
  effMuTauNjet_incl = dict()
  effMuTauNjet_incl[0] = kwargs.get('eff_mutau_0orp4jet_incl', 0.0035283673 )
  effMuTauNjet_incl[1] = kwargs.get('eff_mutau_1jet_incl', 0.0010102964 )
  effMuTauNjet_incl[2] = kwargs.get('eff_mutau_2jet_incl', 0.0003650867 )
  effMuTauNjet_incl[3] = kwargs.get('eff_mutau_3jet_incl', 0.0001165299 )
  effMuTauNjet_incl[4] = kwargs.get('eff_mutau_4jet_incl', 0.0000658845 )
  effMuTauNjet_excl = dict()
  effMuTauNjet_excl[0] = kwargs.get('eff_mutau_0orp4jet_excl', 0.40987941 )
  effMuTauNjet_excl[1] = kwargs.get('eff_mutau_1jet_excl', 0.11475415 )
  effMuTauNjet_excl[2] = kwargs.get('eff_mutau_2jet_excl', 0.039009160 )
  effMuTauNjet_excl[3] = kwargs.get('eff_mutau_3jet_excl', 0.012867714 )
  effMuTauNjet_excl[4] = kwargs.get('eff_mutau_4jet_excl', 0.0073231573 )

  npartvar  = kwargs.get('npart',     'NUP'          ) # variable name of number of partons in tree; 'NUP', 'LHE_Njets', ...
  LOG.verb("stitch: rescale, reweight and merge %r samples"%(name),verbosity,level=1)

  # GET list samples to-be-stitched
  stitchlist = samplelist.samples if isinstance(samplelist,SampleSet) else samplelist
  stitchlist = [s for s in stitchlist if s.match(*searchterms,incl=True)]
  if len(stitchlist)<2:
    LOG.warn("stitch: Could not stitch %r: fewer than two %s samples (%d) match '%s'"%(
                 name,name,len(stitchlist),"', '".join(searchterms)))
    return samplelist
  for s in stitchlist:
    print ">>>   %s"%s.name

  sample_incl = None
  sample_mutau = None #"DYJetsToMuTauh_M-50"
  samples_jetIncl = [s for s in stitchlist if s.match(name_incl)]
  for sample in samples_jetIncl:
    if sample.match("DYJets*MuTau",incl=False):
      sample_mutau = sample
    else:
      sample_incl = sample
  if not sample_incl:
    print "No inclusive sample to stitch... abort"
    return samplelist

  # Compute k-factor for NLO cross section normalisation
  nevts_incl      = sample_incl.sumweights
  xsec_incl_LO    = sample_incl.xsec
  if kfactor:
    xsec_incl_NLO = kfactor*xsec_incl_LO
  else:
    xsec_incl_NLO = xsec_incl or getxsec_nlo(name,*searchterms) or xsec_incl_LO
    kfactor       = xsec_incl_NLO / xsec_incl_LO
  LOG.verb("  %s k-factor = %.2f = %.2f / %.2f"%(name,kfactor,xsec_incl_NLO,xsec_incl_LO),verbosity,level=2)
  

  name  = kwargs.get('name',stitchlist[0].name)
  title = kwargs.get('title',gettitle(name,stitchlist[0].title))
  if not title:
    title = sample_incl.title

  sample_njet = dict()
  for sample in stitchlist:
    if sample in samples_jetIncl:
      continue
    else:
      print sample.name
      njets = int(sample.name[int(sample.name.find("Jets")-1)])
      print "...jet multiplcity: %i"%njets
      sample_njet[njets] = sample

  print "Lumi = %.6g, kfactor = %.6g, xsec = %.6g, sumw = %.6g"%(sample_incl.lumi, kfactor, sample_incl.xsec, sample_incl.sumweights)
  print "Sample_incl.norm = %.6g"%sample_incl.norm
  wIncl = sample_incl.lumi * kfactor * sample_incl.xsec * 1000. / sample_incl.sumweights
  print "Inclusive weight = %.6g"%wIncl

  effIncl_njet = dict()
  wIncl_njet = dict()
  for njets in sample_njet:
    sample = sample_njet[njets]
    effIncl_njet[njets] = sample.xsec/sample_incl.xsec
    print "%i-jet efficiency in inclusive sample = %.6g"%(njets,effIncl_njet[njets])
    wIncl_njet[njets] = sample.lumi * kfactor * sample.xsec * 1000. / (sample.sumweights + effIncl_njet[njets]*sample_incl.sumweights)
    print "Lumi = %.6g, kfactor = %.6g, xsec = %.6g, sumw = %.6g"%(sample.lumi, kfactor, sample.xsec, sample.sumweights)
    print "Sample.norm = %.6g"%sample.norm
    print "Inclusive %i jets weight = %.6g"%(njets,wIncl_njet[njets])

  wIncl_mutau = ""
  wMuTau_njet = dict()
  if sample_mutau:
    wIncl_mutau = sample_incl.lumi * kfactor * sample_incl.xsec * 1000. * effMuTau_incl / ( effMuTau_incl*sample_incl.sumweights + effMuTau_excl*sample_mutau.sumweights )
    print "Inclusive mutau weight = %.6g"%wIncl_mutau
    for njets in sample_njet:
      sample = sample_njet[njets]
      wMuTau_njet[njets] = sample.lumi * kfactor * sample.xsec * 1000. * effMuTau_njet[njets] / ( effMuTau_njet[njets]*sample.sumweights + effMuTauNjet_excl[njets]*sample_mutau.sumweights + effMuTauNjet_incl[njets]*sample_incl.sumweights )
      print "Inclusive mutau %i jets weight = %.6g"%(njets,wMuTau_njet[njets])

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
  sample_incl.norm = 1.0
  conditionalWeight_incl = "("+conditionalWeight_incl+")"
  sample_incl.addweight(conditionalWeight_incl)

  conditionalWeight_mutau = ""
  if sample_mutau:
    if len(sample_njet)>0:
      conditionalWeight_mutau = "mutaufilter * (%s==0||%s>4 ? %.6g : 1)"%(npartvar, npartvar, wIncl_mutau)
    else:
      conditionalWeight_mutau = "mutaufilter * %.6g"%(wIncl_mutau)
    for njets in sample_njet:
      conditionalWeight_mutau += " * (%s==%i ? %.6g : 1)"%(npartvar, njets, wMuTau_njet[njets])
    sample_mutau.norm = 1.0
    conditionalWeight_mutau = "("+conditionalWeight_mutau+")"
    sample_mutau.addweight(conditionalWeight_mutau)

  for njets in sample_njet:
    conditionalWeight_njet = ""
    if sample_mutau:
      conditionalWeight_njet = "(mutaufilter ? %.6g : %.6g)"%(wMuTau_njet[njets], wIncl_njet[njets])
    else:
      conditionalWeight_njet = "(%.6g)"%wIncl_njet[njets]
    sample_njet[njets].norm = 1.0
    conditionalWeight_njet = "("+conditionalWeight_njet+")"
    sample_njet[njets].addweight(conditionalWeight_njet)

  # JOIN
  join(samplelist,*searchterms,name=name,title=title,verbosity=5)
  newsample = findsample(samplelist,name,unique=True)
  newsample.sample_incl = sample_incl
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
  

def setaliases(tree,aliases):
  if not tree or not aliases:
    return None
  for alias, formula in aliases.items():
    tree.SetAlias(alias,formula)
  return tree
  

def loadmacro(macro,verb=0):
  line = ".L %s+O"%(macro)
  LOG.verb("loadmacro: Loading macro %r..."%(macro),level=1)
  return gROOT.ProcessLine(line)
  

from TauFW.Plotter.sample.Sample import *
from TauFW.Plotter.sample.MergedSample import MergedSample
from TauFW.Plotter.sample.SampleSet import SampleSet
import TauFW.Plotter.sample.SampleStyle as STYLE
