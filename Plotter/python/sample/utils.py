# -*- coding: utf-8 -*-
# Author: Izaak Neutelings (June 2020)
import re, glob
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
  'WJetsToLNu':           61526.7,
}


def getsampleset(datasample,expsamples,sigsamples=[ ],**kwargs):
  """Create sample set from a table of data and MC samples."""
  channel    = kwargs.get('channel',    ""   )
  era        = kwargs.get('era',        ""   )
  fpattern   = kwargs.get('file',       None ) # file name pattern, e.g. $PICODIR/$SAMPLE_$CHANNEL$TAG.root
  weight     = kwargs.pop('weight',     ""   ) # common weight for MC samples
  dataweight = kwargs.pop('dataweight', ""   ) # weight for data samples
  url        = kwargs.pop('url',        ""   ) # XRootD url
  tag        = kwargs.pop('tag',        ""   ) # extra tag for file name
  
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
  title = 'Observed'
  datakwargs = kwargs.copy()
  datakwargs['weight'] = dataweight
  if isinstance(datasample,dict) and channel:
    datasample = datasample[channel]
  if len(datasample)==2:
    group, name = datasample
  elif len(datasample)==3:
    group, name = datasample[:2]
    if isinstance(datasample[2],dict): # dictionary
      datakwargs.update(datasample[2])
    else: # string
      title = datasample[2]
  elif len(datasample)==4 and isinstance(datasample[3],dict):
    group, name, title, newkwargs = datasample
    datakwargs.update(newkwargs)
  else:
    LOG.throw(IOError,"Did not recognize data row %s"%(datasample))
  fpattern = repkey(fpattern,ERA=era,GROUP=group,SAMPLE=name,CHANNEL=channel,TAG=tag)
  fnames   = glob.glob(fpattern)
  #print fnames
  if len(fnames)==1:
    datasample = Data(name,title,fnames[0])
  elif len(fnames)>1:
    namerexp = re.compile(name.replace('?','.').replace('*','.*'))
    name     = name.replace('?','').replace('*','')
    datasample = MergedSample(name,'Observed',data=True)
    for fname in fnames:
      setname = namerexp.findall(fname)[0]
      #print setname
      datasample.add(Data(setname,'Observed',fname,**datakwargs))
  else:
    LOG.throw(IOError,"Did not find data file %r"%(fpattern))
  
  # SAMPLE SET
  sampleset = SampleSet(datasample,expsamples,sigsamples,**kwargs)
  return sampleset
  

def setera(era_,lumi_=None,**kwargs):
  """Set global era and integrated luminosity for Samples and CMSStyle."""
  global era, lumi, cme
  era   = str(era_) #.replace('UL',"")
  lumi  = kwargs.get('lumi',lumi_)
  if lumi==None:
    lumi = CMSStyle.lumi_dict.get(era,None)
    if lumi==None: # try again with year
      year  = str(getyear(era_))
      lumi  = CMSStyle.lumi_dict.get(year,None)
  else:
    kwargs['lumi'] = lumi
  cme  = kwargs.get('cme', 13 )
  CMSStyle.setCMSEra(era,**kwargs)
  LOG.verb("setera: era = %r, lumi = %r/fb, cme = %r TeV"%(era,lumi,cme),kwargs,2)
  if not lumi or lumi<0:
    LOG.warning("setera: Could not set luminosity for era %r... Returning %s"%(era,lumi))
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
  

def getsample(samples,*searchterms,**kwargs):
  """Help function to get all samples corresponding to some name and optional label."""
  verbosity   = LOG.getverbosity(kwargs)
  filename    = kwargs.get('fname',    ""    )
  unique      = kwargs.get('unique',   False )
  warning     = kwargs.get('warn',     True  )
  split       = kwargs.get('split',    False )
  matches     = [ ]
  if split:
    newsamples = [ ]
    for sample in samples:
      if sample.splitsamples:
        LOG.verb("getsample: Splitting sample %s..."%(sample.name),verbosity,3)
        newsamples.extend(sample.splitsamples)
      else:
        newsamples.append(sample)
    samples = newsamples
  for sample in samples:
    if sample.match(*searchterms,**kwargs) and filename in sample.filename:
      matches.append(sample)
  if not matches and warning:
    LOG.warning("getsample: Could not find a sample with search terms %s..."%(quotestrs(searchterms+(filename,))))
  elif unique:
    if len(matches)>1:
      LOG.warning("getsample: Found more than one match to %s. Using first match only: %s"%(
                  quotestrs(searchterms),quotestrs(matches)))
    return matches[0]
  return matches
  

def getsample_with_flag(samples,flag,*searchterms,**kwargs):
  """Help function to get sample with some flag from a list of samples."""
  matches   = [ ]
  unique    = kwargs.get('unique', False )
  for sample in samples:
    if hasattr(sample,flag) and getattr(sample,flag) and\
       (not searchterms or sample.match(*searchterms,**kwargs)):
      matches.append(sample)
  if not matches:
    LOG.warning("Could not find a sample with %r=True..."%flag)
  elif unique:
    if len(matches)>1:
      LOG.warning("Found more than one signal sample. Using first match only: %s"%(quotestrs(s.name for s in matches)))
    return matches[0]
  return matches
  

def join(samplelist,*searchterms,**kwargs):
  """Join samples from a sample list into one merged sample, that match a set of search terms.
  E.g. samplelist = join(samplelist,'DY','M-50',name='DY_highmass')."""
  verbosity = LOG.getverbosity(kwargs)
  name      = kwargs.get('name',  searchterms[0] ) # name of new merged sample
  title     = kwargs.get('title', None           ) # title of new merged sample
  color     = kwargs.get('color', None           ) # color of new merged sample
  LOG.verbose("join: merging '%s' into %r"%("', '".join(searchterms),name),verbosity,level=1)
  
  # GET samples containing names and searchterm
  mergelist = [s for s in samplelist if s.match(*searchterms,incl=True)]
  if len(mergelist)<=1:
    LOG.warning("Could not merge %r: fewer than two %r samples (%d)"%(name,name,len(mergelist)))
    return samplelist
  padding = max([len(s.name) for s in mergelist])+2 # number of spaces
  
  # ADD samples with name and searchterm
  mergedsample = MergedSample(name,title,color=color)
  for sample in mergelist:
    samplestr = repr(sample.name).ljust(padding)
    LOG.verbose("  adding %s to %r (%s)"%(samplestr,name,sample.fnameshort),verbosity,level=2)
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
  eff_mutau = kwargs.get('eff_mutau', 0.008009       ) # efficiency mutau (pT>18, |eta|<2.5) in DYJetsToLL_M-50
  eff_mutau_excl = kwargs.get('eff_mutau', 0.701     ) # efficiency mutau (pT>18, |eta|<2.5) in DYJetsToTauTauToMuTauh_M-50
  npartvar  = kwargs.get('npart',     'NUP'          ) # variable name of number of partons in tree; 'NUP', 'LHE_Njets', ...
  LOG.verbose("stitch: rescale, reweight and merge %r samples"%(name),verbosity,level=1)
  
  # GET list samples to-be-stitched
  stitchlist = samplelist.samples if isinstance(samplelist,SampleSet) else samplelist
  stitchlist = [s for s in stitchlist if s.match(*searchterms,incl=True)]
  if len(stitchlist)<2:
    LOG.warning("stitch: Could not stitch %r: fewer than two %s samples (%d) match '%s'"%(
                 name,name,len(stitchlist),"', '".join(searchterms)))
    for s in stitchlist:
      print ">>>   %s"%s.name
    if len(stitchlist)==0:
      return samplelist
  name  = kwargs.get('name',stitchlist[0].name)
  title = kwargs.get('title',gettitle(name,stitchlist[0].title))
  if not title:
    title = sample_incl.title
  
  # FIND inclusive sample
  sample_incls = [s for s in stitchlist if s.match(name_incl)]
  sample_mutau = None # DYJetsToTauTauToMuTauh_M-50
  if len(sample_incls)==2: # look for DYJetsToTauTauToMuTauh_M-50
    for sample in sample_incls:
      if sample.match("DYJets*MuTau",incl=False):
        sample_mutau = sample
        stitchlist.remove(sample) # stitch in parallel
        sample_incls.remove(sample)
  if len(sample_incls)==0:
    LOG.warning('stitch: Could not find inclusive sample "%s"! Just joining...'%(name))
    return join(samplelist,*searchterms,**kwargs)
  elif len(sample_incls)>1:
    LOG.warning("stitch: Found more than one inclusive sample %r with '%s' searchterms: %s"%(
                name,"', '".join(searchterms),sample_incls))
  
  # (N)NLO/LO k-factor
  sample_incl     = sample_incls[0]
  nevts_incl      = sample_incl.sumweights
  xsec_incl_LO    = sample_incl.xsec
  if kfactor:
    xsec_incl_NLO = kfactor*xsec_incl_LO
  else:
    xsec_incl_NLO = xsec_incl or getxsec_nlo(name,*searchterms) or xsec_incl_LO
    kfactor       = xsec_incl_NLO / xsec_incl_LO
  LOG.verbose("  %s k-factor = %.2f = %.2f / %.2f"%(name,kfactor,xsec_incl_NLO,xsec_incl_LO),verbosity,level=2)
  
  # GET effective number of events per jet bin
  neffs = [ ]
  if verbosity>=2:
    print ">>>   Get effective number of events per jet bin:"
    LOG.ul("%-19s %12s = %12s + %12s * %7s / %6s"%('name','neff','nevts','nevts_incl','xsec','xsec_incl_LO'),pre="    ")
  for sample in stitchlist:
    nevts = sample.sumweights # number of events in this sample
    neff  = nevts # effective number of events after stitching
    xsec  = sample.xsec # LO inclusive or jet-binned cross section
    if sample==sample_incl: #.match(name_incl):
      LOG.verb("%-19s %12.2f = %12.1f"%(sample.name,neff,nevts),verbosity,2,pre="    ")
    else:
      neff = nevts + nevts_incl*xsec/xsec_incl_LO # effective number of events (no k-factor to preserve npart distribution)
      LOG.verb("%-19s %12.2f = %12.1f + %12.2f * %7.2f / %6.2f"%(sample.name,neff,nevts,nevts_incl,xsec,xsec_incl_LO),verbosity,2,pre="    ")
    neffs.append(neff)
  
  # GET effective number of events in mutau phase space (pT>18, |eta|<2.5)
  neffs_mutau = [ ]
  if sample_mutau:
    print ">>>   Get effective number of events in mutau phase space (pT>18, |eta|<2.5):"
    LOG.ul("%-19s %12s = %9s * %12s + %9s * %12s"%('name','neff','eff_mutau','nevts_mutau','eff_mutau','neff_incl'),pre="    ")
    LOG.verb("%-19s %12s %26.1f"%(sample_mutau.name,"",sample_mutau.sumweights),verbosity,2,pre="    ")
    nevts_excl = sample_mutau.sumweights
    for sample, neff in zip(stitchlist,neffs):
      neff_mutau = eff_mutau_excl*nevts_excl + eff_mutau*neff
      neffs_mutau.append(neff_mutau)
      LOG.verb("%-19s %12.2f = %9.5f * %12.1f + %9.5f * %12.2f"%(
        sample.name,neff_mutau,eff_mutau_excl,nevts_excl,eff_mutau,neff),verbosity,2,pre="    ")
  
  # SET normalization with effective luminosity
  weights_incl  = [ ] # normalization for NUP==npart component in incl. sample
  weights_mutau = [ ] # normalization for NUP==npart component in incl. sample in mutau phase space
  npart_max     = -1
  if verbosity>=2:
    print ">>>   Get lumi-xsec normalization:"
    LOG.ul('%-18s %5s %9s = %9s * %7s * %8s * 1000 / %8s'%('name','npart','norm','lumi','kfactor','xsec','neff'+' '*9),pre="    ")
  for i, (sample,neff) in enumerate(zip(stitchlist,neffs)):
    if sample==sample_incl: #.match(name_incl):
      npart = 0
    else: # get number of jets/partons from name pattern
      matches = re.findall("(\d+)Jets",sample.fnameshort)      
      if len(matches)==0:
        LOG.throw(IOError,'stitch: Could not stitch %r: no "\\d+Jets" pattern found in %r!'%(name,sample.name))
      elif len(matches)>1:
        LOG.warning('stitch: More than one "\\d+Jets" match found in %r! matches = %s'%(sample.name,matches))
      npart = int(matches[0])
    xsec = sample.xsec # LO inclusive or jet-binned xsec
    norm = sample.lumi * kfactor * xsec * 1000 / neff # normalization for NUP==npart component in jet-incl. sample
    weights_incl.append("(%s==%d?%.6g:1)"%(npartvar,npart,norm))
    LOG.verb('%-18s %5d %9.4f = %9.2f * %7.3f * %8.2f * 1000 / %12.2f'%(
      sample.name,npart,norm,sample.lumi,kfactor,xsec,neff),verbosity,2,pre="    ")
    if sample_mutau: # normalization for NUP==npart in mutau phase space
      neff_mutau = neffs_mutau[i]
      norm_mutau = sample.lumi * kfactor * eff_mutau * xsec * 1000 / neff_mutau # for mutau phase space
      weights_mutau.append("(%s==%d?%.6g:1)"%(npartvar,npart,norm_mutau))
      weight_mutau = "(mutaufilter?%.6g:%.6g)"%(norm_mutau,norm)
      LOG.verb('%-18s %5d %9.4f = %9.2f * %7.3f * %8.2f * 1000 / %12.2f (mutau)'%(
        sample.name,npart,norm_mutau,sample.lumi,kfactor,eff_mutau*xsec,neff_mutau),verbosity,2,pre="    ")
    if npart>npart_max:
      npart_max = npart
    if sample==sample_incl: # jet-inclusive sample
      if len(stitchlist)>=2:
        sample.norm = 1.0 # apply lumi-xsec normalization via weights instead of Sample.norm attribute
      elif sample_mutau:
        sample.norm = 1.0 # apply lumi-xsec normalization via weights instead of Sample.norm attribute
        sample_mutau.norm = 1.0
        sample.addweight(weight_mutau)
        sample_mutau.addweight(weight_mutau)
        LOG.verb("  Mutau stitch weight:\n>>>     %r"%(weight_mutau),verbosity,2)
      else:
        sample.norm = norm # apply lumi-xsec normalization directly
    else: # jet-binned sample
      if sample_mutau: # stitch jet-binned sample with mutau
        sample.norm = 1.0 # apply lumi-xsec normalization via weights instead of Sample.norm attribute
        sample.addweight(weight_mutau) # reweight mutau phase space
      else:
        sample.norm = norm # apply lumi-xsec normalization directly
  
  # IF NO JET BINNED SAMPLE
  if len(stitchlist)==1:
    if not sample_mutau: # do not join
      return samplelist # only k-factor was applied to lumi-xsec normalization (of jet-incl. sample)
  else:
    
    # ADD weights for NUP > npart_max, same as NUP==0
    if npart_max>0:
      for weight in weights_incl:
        if "==0" in weight:
          weights_incl.append(weight.replace("==0",">%d"%(npart_max))); break
      for weight in weights_mutau:
        if "==0" in weight:
          weights_mutau.append(weight.replace("==0",">%d"%(npart_max))); break
    else:
      LOG.warning("   found no maximum %s (%d)..."%(npartvar,npartvar,npart_max))
    
    # SET stich weight of inclusive sample
    if sample_mutau:
      stitchweights = "(mutaufilter?(%s):(%s))"%('*'.join(weights_mutau),'*'.join(weights_incl))
      weight_mutau = "(mutaufilter?(%s):0)"%('*'.join(weights_mutau))
      sample_mutau.norm = 1.0
      sample_mutau.addweight(weight_mutau)
      LOG.verbose("  Mutau stitch weight:\n>>>     %r"%(weight_mutau),verbosity,2)
    else:
      stitchweights = '*'.join(weights_incl)
    LOG.verbose("  Inclusive stitch weight:\n>>>     %r"%(stitchweights),verbosity,2)
    sample_incl.addweight(stitchweights)
  
  # JOIN
  join(samplelist,*searchterms,name=name,title=title,verbosity=verbosity)
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
    LOG.warning("getxsec_nlo: Did not find a DY or WJ match in '%s'!"%("', '".join(searchterms)))
  return xsec_nlo
  

from TauFW.Plotter.sample.Sample import *
from TauFW.Plotter.sample.MergedSample import MergedSample
from TauFW.Plotter.sample.SampleSet import SampleSet
import TauFW.Plotter.sample.SampleStyle as STYLE
