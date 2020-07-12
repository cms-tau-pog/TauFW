# -*- coding: utf-8 -*-
# Author: Izaak Neutelings (June 2020)
import re
from TauFW.common.tools.utils import isnumber, islist, ensurelist, unwraplistargs
from TauFW.common.tools.file import ensuredir, ensureTFile
from TauFW.common.tools.log import Logger, color
from TauFW.Plotter.plot.Variable import Variable, ensurevar
import TauFW.Plotter.plot.CMSStyle as CMSStyle
import ROOT; ROOT.PyConfig.IgnoreCommandLineOptions = True
from ROOT import gDirectory, gROOT, TH1, THStack, kDotted, kBlack, kWhite
gROOT.SetBatch(True)
LOG  = Logger('Sample')
era  = None # data period: 2016, 2017, 2018, ...
lumi = -1   # integrated luminosity [fb-1]
cme  = 13   # center-of-mass energy [TeV]
lumi_dict      = {
  '7':      5.1,    '2016': 35.9,
  '8':      19.7,   '2017': 41.5,
  '2012':   19.7,   '2018': 59.7,
  'Run2':   137.1,
  'Phase2': 3000,
}
xsecs_nlo = { # NLO cross sections to compute k-factor for stitching
  'DYJetsToLL_M-50':     3*2025.74,
  'DYJetsToLL_M-10to50':  18610.0,
  'WJetsToLL':            61526.7,
}


def setera(era_,lumi_=None,**kwargs):
  """Set global era and integrated luminosity for Samples and CMSStyle."""
  global era, lumi, cme
  era   = str(era_)
  lumi  = kwargs.get('lumi',lumi_)
  if lumi==None:
    lumi = lumi_dict.get(era,None)
  else:
    kwargs['lumi'] = lumi
  cme  = kwargs.get('cme', 13 )
  CMSStyle.setCMSEra(era,**kwargs)
  LOG.verb("setera: era = %r, lumi = %r/fb, cme = %r TeV"%(era,lumi,cme),kwargs,2)
  return lumi
  

def unwrap_MergedSamples_args(*args,**kwargs):
  """
  Help function to unwrap arguments for MergedSamples initialization:
    - name (str)
    - name, title (str, str)
    - name, samples (str, list)
    - name, title, samples (str, str, list)
  where samples is a list of Sample objects.
  """
  strings = [ ]
  name    = "noname"
  title   = "No title"
  samples = [ ]
  #args    = unwraplistargs(args)
  for arg in args:
    if isinstance(arg,str):
      strings.append(arg)
    elif isinstance(arg,Sample):
      samples.append(arg)
    elif islist(arg) and all(isinstance(s,Sample) for s in arg):
      for sample in arg:
        samples.append(sample)
  if len(strings)==1:
    name, title = strings[0], strings[0]
  elif len(strings)>1:
    name, title = strings[:2]
  elif len(samples)>1:
    name, title = '-'.join([s.name for s in samples]), ', '.join([s.title for s in samples])
  LOG.verb("unwrap_MergedSamples_args: name=%r, title=%r, samples=%s"%(name,title,samples),level=3)
  return name, title, samples
  

def unwrap_gethist_args(*args,**kwargs):
  """
  Help function to unwrap argument list that contain variable(s) and selection:
    - variable, cuts
    - varlist, cuts
  where cuts is a string and variable can be
    - xvar, nxbins, xmin, xmax (str, int, float, float)
    - xvar, xbins (str, list)
    - var (Variable)
  or valist is a list of such variables.
  """
  vars   = None  # list of Variable objects
  sel    = None  # selection (string)
  single = False # only one Variable passed
  if len(args)==2:
    vars   = args[0]
    sel    = args[1]
    if isinstance(vars,Variable):
      vars   = [vars]
      single = True
    elif islist(args[0]):
      vars = [ensurevar(v) for v in args[0]]
  elif len(args) in [3,5]:
    vars   = [Variable(*args[len(args)-1])]
    sel    = args[-1]
    single = True
  if vars==None or sel==None:
    LOG.throw(IOError,'unwrap_gethist_args: Could not unwrap arguments %s, len(args)=%d, vars=%s, sel=%s.'%(args,len(args),vars,sel))
  LOG.verb("unwrap_gethist_args: vars=%s, sel=%r, single=%r"%(vars,sel,single),level=3)
  return vars, sel, single
  

def unwrap_gethist_args_2D(*args,**kwargs):
  """
  Help function to unwrap argument list that contain variable(s) and selection:
    - xvar, yvar, cuts
    - xvarlist, yvarlist, cuts
    - (xvar,yvar), cuts
    - varlist, cuts
    - xvar, nxbins, xmin, xmax, yvar, nybins, ymin, ymax, cuts
  where xvar and yvar are Variable objects or arguments, and [xy]varlist is a list of such pairs.
  """
  vars   = None  # list of Variable objects
  sel    = None  # selection (string)
  single = False # only one pair of Variable objects passed
  if len(args)==2:
    vars, sel = args
    single = len(vars)==2 and islist(vars) and isinstance(vars[0],Variable) and isinstance(vars[1],Variable)
    if single:
      vars = [vars]
  elif len(args)==3:
    xvars, yvars, sel = args
    if isinstance(xvars,Variable) and isinstance(yvars,Variable):
      vars = [(xvars,yvars)]
      single = True
    elif all(isinstance(v,Variable) for v in xvars+yvars):
      vars = zip(xvars,yvars)
    elif len(xvars) in [3,5] and len(yvars) in [3,5]:
      vars = [Variable(*xvars),Variable(*yvars)]
      single = True
  elif len(args)==9:
    vars   = [Variable(*args[0:4]),Variable(*args[4:8])]
    sel    = args[-1]
    single = True
  if vars==None or sel==None:
    LOG.throw(IOError,'unwrap_gethist_args_2D: Could not unwrap arguments %s, len(args)=%d, vars=%s, sel=%s.'%(args,len(args),vars,sel))
  LOG.verb("unwrap_gethist_args_2D: vars=%s, sel=%r, single=%r"%(vars,sel,single),level=3)
  return vars, sel, single
  

def join(samplelist,*searchterms,**kwargs):
  """Join samples from a sample list into one merged sample, that match a set of search terms.
  E.g. samplelist = join(samplelist,'DY','M-50',name='DY_highmass')."""
  verbosity = LOG.getverbosity(kwargs,1)
  name      = kwargs.get('name',  searchterms[0] ) # name of new merged sample
  title     = kwargs.get('title', None           ) # title of new merged sample
  color     = kwargs.get('color', None           ) # color of new merged sample
  LOG.verbose("join: merging '%s' into %s"%("', '".join(searchterms),name),verbosity,level=1)
  
  # GET samples containing names and searchterm
  mergelist = [s for s in samplelist if s.match(*searchterms,incl=False)]
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
  verbosity = LOG.getverbosity(kwargs,1)
  name      = kwargs.get('name',    searchterms[0] )
  name_incl = kwargs.get('incl',    searchterms[0] ) # name of inclusive sample
  xsec_incl = kwargs.get('xsec',    None           ) # (N)NLO cross section to compute k-factor
  kfactor   = kwargs.get('kfactor', None           ) # k-factor
  npartvar  = kwargs.get('npart',   'NUP'          ) # variable name of number of partons
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
  title = kwargs.get('title',stitchlist[0].title)
  
  # FIND inclusive sample
  sample_incls = [s for s in stitchlist if s.match(name_incl)]
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
    xsec_incl_NLO = xsec_incl or xsec_incl_LO #getxsec_nlo(name,*searchterms)
    kfactor       = xsec_incl_NLO / xsec_incl_LO
  LOG.verbose("  %s k-factor = %.2f = %.2f / %.2f"%(name,kfactor,xsec_incl_NLO,xsec_incl_LO),verbosity,level=2)
  
  # GET effective number of events per jet bin
  # assume first sample in the list is the inclusive sample
  neffs     = [ ]
  if verbosity>=2:
    print ">>>   Get effective number of events:"
    LOG.ul("%-15s %8s = %8s + %12s * %7s / %10s"%('name','neff','nevts','nevts_incl','xsec','xsec_incl_LO'),pre="    ")
  for sample in stitchlist:
    nevts = sample.sumweights
    neff  = nevts
    xsec  = sample.xsec # LO inclusive or jet-binned cross section
    if sample==sample_incl: #.match(name_incl):
      LOG.verbose("%-15s %8s = %8.1f"%(sample.name,neff,nevts),verbosity,2,pre="    ")
    else:
      neff = nevts + nevts_incl*xsec/xsec_incl_LO # effective luminosity, no k-factor to preserve npart distribution
      LOG.verbose("%-15s %8.4f = %8.1f + %12.2f * %7.2f / %10.2f"%(sample.name,neff,nevts,nevts_incl,xsec,xsec_incl_LO),verbosity,2,pre="    ")
    neffs.append(neff)
  
  # SET normalization with effective luminosity
  weights   = [ ]
  norm_incl = -1
  npart_max = -1
  if verbosity>=2:
    print ">>>   Get lumi-xsec normalization:"
    LOG.ul('%-15s %7s %9s = %7s * %7s * %8s * 1000 / %8s'%('name','npart','norm','lumi','kfactor','xsec','neff'),pre="    ")
  for sample, neff in zip(stitchlist,neffs):
    if sample==sample_incl: #.match(name_incl):
      npart = 0
    else:
      matches = re.findall("(\d+)Jets",sample.fnameshort)      
      if len(matches)==0:
        LOG.throw(IOError,'stitch: Could not stitch %r: no "\\d+Jets" pattern found in %r!'%(name,sample.name))
      elif len(matches)>1:
        LOG.warning('stitch: More than one "\\d+Jets" match found in %r! matches = %s'%(sample.name,matches))
      npart = int(matches[0])
    xsec = sample.xsec # LO inclusive or jet-binned xsec
    norm = sample.lumi * kfactor * xsec * 1000 / neff
    if npart==0:
      norm_incl = norm # new normalization of inclusive sample (with k-factor included)
    if npart>npart_max:
      npart_max = npart
    weights.append("(NUP==%d?%.6g:1)"%(npart,norm))
    LOG.verbose('%-15s %7d %9.4f = %7.2f * %7.3f * %8.2f * 1000 / %8.2f'%(sample.name,npart,norm,sample.lumi,kfactor,xsec,neff),verbosity,2,pre="    ")
    if sample==sample_incl: #.match(name_incl):
      sample.norm = 1.0 # apply lumi-xsec normalization via weights instead of Sample.norm attribute
    else:
      sample.norm = norm # apply lumi-xsec normalization
  if len(stitchlist)==1:
    return samplelist # only k-factor was applied to lumi-xsec normalization
  
  # ADD weights for NUP > npart_max
  if norm_incl>0 and npart_max>0:
    weights.append("(NUP>%d?%.6g:1)"%(npart_max,norm_incl))
  else:
    LOG.warning("   found no weight for %s==0 (%.1f) or no maximum %s (%d)..."%(npartvar,norm_incl,npartvar,npart_max))
  
  # SET stich weight of inclusive sample
  stitchweights = '*'.join(weights)
  if npartvar!='NUP':
    stitchweights = stitchweights.replace('NUP',npartvar)
  LOG.verbose("  Inclusive stitch weight:\n>>>     %r"%(stitchweights),verbosity,2)
  sample_incl.addweight(stitchweights)
  if not title:
    title = sample_incl.title
  
  # JOIN
  join(samplelist,*searchterms,name=name,title=title,verbosity=verbosity)
  return samplelist
  

#def getxsec_nlo(*searchterms,**kwargs):
#  """Returns inclusive (N)NLO cross section for stitching og DY and WJ."""
#  # see /shome/ytakahas/work/TauTau/SFrameAnalysis/TauTauResonances/plot/config.py
#  # https://twiki.cern.ch/twiki/bin/viewauth/CMS/StandardModelCrossSectionsat13TeV#List_of_processes
#  # https://ineuteli.web.cern.ch/ineuteli/crosssections/2017/FEWZ/
#  # DY cross sections  5765.4 [  4954.0, 1012.5,  332.8, 101.8,  54.8 ]
#  # WJ cross sections 61526.7 [ 50380.0, 9644.5, 3144.5, 954.8, 485.6 ]
#  from Sample import Sample
#  isDY          = False
#  isDY_M10to50  = ""
#  isDY_M50      = ""
#  isWJ          = False
#  for searchterm in searchterms:
#    searchterm = searchterm.replace('*','')
#    if "DY" in searchterm:
#      isDY = True
#    if "10to50" in searchterm:
#      isDY_M10to50 = "M-10to50"
#    if "50" in searchterm and not "10" in searchterm:
#      isDY_M50 = "M-50"
#    if "WJ" in searchterm:
#      isWJ = True
#  if isDY and isWJ:
#    LOG.error("crossSections - Detected both isDY and isWJ!")
#    exit(1)
#  elif isWJ:
#    return xsecsNLO['WJ']
#  elif isDY:
#    if isDY_M10to50 and isDY_M50:
#      LOG.error('crossSections - Matched to both "M-10to50" and "M-50"!')
#      exit(1)
#    if not (isDY_M10to50 or isDY_M50):
#      LOG.error('crossSections - Did not match to either "M-10to50" or "M-50" for DY!')
#      exit(1)
#    return xsecsNLO['DY'][isDY_M10to50+isDY_M50]
#  else:
#    LOG.error("crossSections - Did not find a DY or WJ match!")
#    exit(1)
  

from TauFW.Plotter.sample.Sample import *
from TauFW.Plotter.sample.MergedSample import MergedSample
from TauFW.Plotter.sample.SampleSet import SampleSet
import TauFW.Plotter.sample.SampleStyle as STYLE
