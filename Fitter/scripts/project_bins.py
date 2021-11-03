#! /usr/bin/env python
# Author: Izaak Neutelings (October 2021)
# Description: Convert histograms to vectors and project onto a 2D plane to study systematics
#              in a new physics search. The plane is spanned by the observed, B-only and S+B vectors.
# Inspired by Kyle Cormier: https://gitlab.cern.ch/kcormier/fit-scripts/-/tree/tool_development
# Usage:
#   ./project_bins.py -w work.root -o plane.png -p lumi shape_jes -T nuisdict.json --show
from __future__ import print_function
import re
import numpy as np
import matplotlib.pyplot as plot
import ROOT; ROOT.PyConfig.IgnoreCommandLineOptions = True
from ROOT import TFile
#from ROOT.RooFit import Cut # for reduce
###from matplotlib.legend_handler import HandlerPatch
###import matplotlib.patches as mpatches
rexp_fname = re.compile(r"(.+\.root):(.+)")


def parsefname(fname,oname='',verb=0):
  """Help function to parse filename of format filename:objectname."""
  match = rexp_fname.match(fname) # expect optional format fname:oname format
  if match:
    fname, oname = match.group(1), match.group(2)
  return fname, oname
  

def getrootobj(fname,oname='',verb=0):
  """Help function to retrive object from ROOT file."""
  if not fname: return None
  if verb>=2:
    print(">>> getrootobj: opening %s..."%(fname))
  fname, oname = parsefname(fname,oname)
  file = TFile.Open(fname,'READ')
  obj  = file.Get(oname) # workspace
  if verb>=2:
    print(">>> getrootobj:   found %s"%(obj))
  return file, obj
  

class Plane:
  
  def __init__(self,*args,**kwargs):
    """Make 2D plane, spanned by two orthonormal N-dim. vectors."""
    # https://kitchingroup.cheme.cmu.edu/blog/2015/01/18/Equation-of-a-plane-through-three-points/
    ortho = kwargs.get('ortho',True)
    verb  = kwargs.get('verb',0)
    if len(args)==2: # plane is spanned by two N-dim. vectors
      v1, v2 = args
    elif len(args)==3: # plane must contain these three N-dim. points
      p1, p2, p3 = args
      v1 = p2 - p1 # create vectors contained in plane
      v2 = p3 - p1
    else:
      raise IOError("Plane.__init__: Input arguments must be 3 points, or 2 vectors! Received %s"%(args,))
    e1 = v1/np.sqrt(sum(v1**2)) # normalize
    e2 = v2/np.sqrt(sum(v2**2)) # normalize
    assert not (e1-e2==0).all() and not (e1+e2==0).all(), "Vectors are not linearly independent! Got: %s and %s"%(v1,v2)
    if ortho: # orthogonalize
      e2 = e2 - np.dot(e1,e2)*e1 # remove e1 component
      e2 /= np.sqrt(sum(e2**2)) # normalize
    if verb>=3:
      print(">>> Plane.__init__: e1=%s"%(e1))
      print(">>> Plane.__init__: e2=%s"%(e2))
    self.e1 = e1 # orthonormal vector (along B-only)
    self.e2 = e2 # orthonormal vector (along S+B, perpendicular to e1)
  
  def project(self,vec,verb=2):
    """Project vector onto plane, and return 2D vector in orthonormal basis."""
    # https://stackoverflow.com/questions/17836880/orthogonal-projection-with-numpy
    if verb>=1:
      print(">>> Plot.project: vec=%s"%(vec))
    x = np.dot(vec,self.e1) # project on e1 (B-only)
    y = np.dot(vec,self.e2) # project on e2 (S+B)
    return np.array([x,y])
  

def project_on_vec(vec1,vec2,verb=0):
  """Project vec1 onto vec2."""
  # https://stackoverflow.com/questions/17836880/orthogonal-projection-with-numpy
  print(">>> project_on_vec")
  if verb>=1:
    print(">>> project_on_vec: vec1=%s, vec2=%s"%(vec1,vec2))
  norm = np.sqrt(sum(vec2**2))
  proj = (np.dot(vec1,vec2)/norm**2)*vec2
  return proj
  

def updatepars(oldpars,fitres,verb=2):
  """Help function to load post-fit values from fitres into workspace."""
  # Inspiration:
  #  https://github.com/cms-analysis/CombineHarvester/blob/653c523ebe6e67e7a8214366bfe6bd99f7d87d99/CombineTools/src/CombineHarvester_Evaluate.cc#L560-L577
  if not fitres: return
  #fitres.constPars().Print('V')
  #fitres.floatParsFinal().Print('V')
  
  # UPDATE FLOATING PARAMETERS
  newpars = fitres.floatParsFinal()
  print(">>> updatepars: updating %d floating parameters"%(newpars.getSize()))
  iter    = newpars.createIterator()
  newpar  = iter.Next()
  while newpar:
    pname  = newpar.GetName()
    pname2 = pname+"_In"
    oldpar = oldpars.find(pname)
    if not oldpar:
      print(">>> updatepars: Warning! Did not find %s..."%(pname))
      continue
    newval = newpar.getVal()
    newup, newdn = newpar.getErrorHi(), newpar.getErrorLo()
    if verb>=2:
      print(">>> updatepars: setting %6.3f %+.3f %+.3f -> %6.3f %+.3f %+.3f  of %s"%(
        oldpar.getVal(),oldpar.getErrorHi(),oldpar.getErrorLo(),newval,newdn,newup,pname))
    oldpar.setVal(newval)
    oldpar.setAsymError(newdn,newup)
    oldpar2 = oldpars.find(pname2)
    if oldpar2:
      if verb>=2:
        print(">>> updatepars: setting %6.3f %+.3f %+.3f -> %6.3f %+.3f %+.3f  of %s"%(
          oldpar2.getVal(),oldpar2.getErrorHi(),oldpar2.getErrorLo(),newval,newdn,newup,pname2))
      oldpar2.setVal(newval)
      oldpar2.setAsymError(newdn,newup)
    newpar = iter.Next()
  
  # UPDATE CONSTANT PARAMETERS
  newpars = fitres.constPars()
  print(">>> updatepars: updating %d constant parameters"%(newpars.getSize()))
  iter    = newpars.createIterator()
  newpar  = iter.Next()
  while newpar:
    pname = newpar.GetName()
    if not pname.endswith('_In'):
      pname  = newpar.GetName()
      pname2 = pname+"_In"
      oldpar = oldpars.find(pname)
      if not oldpar:
        print(">>> updatepars: Warning! Did not find %s..."%(pname))
        continue
      newval = newpar.getVal()
      if verb>=2:
        print(">>> updatepars: setting %6.3f -> %6.3f  of %s"%(oldpar.getVal(),newval,pname))
      oldpar.setVal(newval)
      oldpar2 = oldpars.find(pname2)
      if oldpar2:
        if verb>=2:
          print(">>> updatepars: setting %6.3f -> %6.3f  of %s"%(oldpar2.getVal(),newval,pname2))
        oldpar2.setVal(newval)
    newpar = iter.Next()
  

def getbins_model(mc,fitres=None,params=None,systs=None,title=None,verb=0):
  """Help function to get bin content from RooSimultaneous model config."""
  title   = mc.GetName()
  obsset  = mc.GetObservables() # set of observables
  xvar    = obsset.find('CMS_th1x') # container for histogram bins
  channel = obsset.find('CMS_channel') # RooCategory for channels/categories/"bins"
  pdf     = mc.GetPdf() # RooAbsPdf
  if verb>=1:
    print(">>> getbins_model: getting %s..."%(title))
  
  # LOAD POST-FIT VALUES
  if fitres:
    if verb>=1:
      print(">>> getbins_model: updating %s parameters..."%(title))
    updatepars(mc.GetWorkspace().allVars(),fitres)
  
  # NOMINAL VALUE
  bins = getbins_pdf(pdf,xvar,channel,obsset,verb=verb) # get bins
  
  # PARAMETER VARIATIONS
  if systs and params:
    pset = mc.GetNuisanceParameters()
    gset = mc.GetGlobalObservables()
    for pname1 in params: # loop over parameter names
      pname2 = pname1+"_In"
      par1 = pset.find(pname1)
      par2 = gset.find(pname2)
      if not par1: #or not par2:
        print(">>> getbins_model: Warning! Did not find %r for %r: par1=%r, par2=%r"%(pname1,title,par1,par2))
        continue
      pnom1 = par1.getVal()
      if par2:
        pnom2 = par2.getVal()
        assert pnom1==pnom2, "%s=%r!=%r=%s"%(par1,pnom1,pnom2,par2)
      pup, pdn = pnom1+par1.getErrorHi(), pnom1+par1.getErrorLo()
      #pup2, pdn2 = pnom2+par1.getErrorHi(), pnom2+par1.getErrorLo()
      bins_up, bins_dn = [ ], [ ]
      for pval, bins_ in [(pup,bins_up),(pdn,bins_dn)]:
        if verb>=1:
          print(">>> getbins_model: %s, %s = %s -> %s"%(title,pname1,par1.getVal(),pval))
        par1.setVal(pval)
        if par2:
          par2.setVal(pval)
        bins_.extend(getbins_pdf(pdf,xvar,channel,obsset,verb=verb-1)) # get bins
      par1.setVal(pnom1) # reset
      if par2:
        par2.setVal(pnom2) # reset
      systs[pname1] = (np.array(bins_up),np.array(bins_dn))
  
  return bins
  

def getbins_pdf(pdf,xvar,channel,obsset,verb=0):
  """Help function to get bin content from RooAbsPdf."""
  bins = [ ]
  nchans = channel.numTypes()
  for ichan in range(nchans):
    channel.setIndex(ichan)
    chname = channel.getLabel()
    nbins = xvar.numBins()
    pdf_ = pdf.getPdf(chname)
    intg = pdf_.getNormIntegral(obsset).getVal()
    norm = pdf_.expectedEvents(obsset) if abs(intg-1.)<0.01 else 1. # nchans==1 faster?
    if verb>=2:
      print(">>> getbins_pdf:      channel %d -> %r (norm=%.1f)"%(ichan,chname,pdf_.expectedEvents(obsset)))
    for ibin in range(nbins):
      xvar.setBin(ibin)
      yval = norm*pdf_.getVal() # bin content
      if verb>=2:
        print(">>> getbins_pdf:        bin %2d -> (x,y) = (%4.1f,%6.1f), pdf = %6.4g"%(ibin,xvar.getVal(),yval,pdf_.getVal()))
      bins.append(yval)
  return bins
  

def parseworkspace(wsname,fitres_b=None,fitres_s=None,params=None,parvals=None,bonly=False,verb=0):
  """Parse CMS CombineTool workspace: observed data, B-only, S+B, systematic variations."""
  if verb>=1:
    print(">>> parseworkspace(%r)"%wsname)
  
  # LOAD INPUT
  file_ws, ws = getrootobj(wsname,'w',verb=verb)  # 'w' = default workspace name in CMS CombineTool
  files = [file_ws] # for closing at the end
  if fitres_b:
    file_b, fitres_b = getrootobj(fitres_b,verb=verb)
    files.append(file_b)
  if fitres_s:
    file_s, fitres_s = getrootobj(fitres_s,verb=verb)
    files.append(file_s)
  
  # LOAD MODEL
  data     = ws.data('data_obs') # observed data set
  mc_b     = ws.genobj('ModelConfig_bonly') # B-only model config (RooSimultaneous)
  mc_s     = ws.genobj('ModelConfig') # S + B model config (RooSimultaneous)
  channel  = mc_s.GetObservables().find('CMS_channel') # RooCategory for channels/categories/"bins"
  nchans   = channel.numTypes() #numBins('')
  
  # GET OBSERVED DATA VECTOR
  if verb>=1:
    print(">>> parseworkspace: get observed data...")
  bins_obs = [ ]
  xvar_    = data.get().find('CMS_th1x')
  channel_ = data.get().find('CMS_channel') # same order as model's channels ?
  assert channel_.numTypes()==nchans, "Data set has different number of channels than model!"
  for ichan in range(nchans): # loop in same order as model's channels
    channel.setIndex(ichan)
    ichan_ = channel_.lookupType(channel.getLabel()).getVal() # new ROOT versions: lookupIndex
    channel_.setIndex(ichan_)
    if verb>=2:
      print(">>> parseworkspace:   channel %d: %r"%(ichan_,channel_.getLabel())) # TODO: get integral
    data_ = data.reduce("CMS_channel==%d"%ichan_) # only look at this channel
    nbins  = xvar_.numBins()
    nbins_ = data_.numEntries()
    assert nbins_==nbins, "Reduced dataset has fewer bins (%d) than observable (%d)!"%(nbins_,nbins)
    for ibin in range(nbins):
      xvar_.setBin(ibin)
      data_.get(ibin) # load bin
      yval = data_.weight() # bin content
      if verb>=2:
        print(">>> parseworkspace:     bin %2d -> (x,y) = (%4.1f,%6.1f)"%(ibin,xvar_.getVal(),yval))
      bins_obs.append(yval)
  vec_obs = np.array(bins_obs)
  
  # SET PARAMETERS
  if parvals:
    vars = ws.allVars()
    for param, newval in parvals.items():
      var = vars.find(param)
      if not var:
        print(">>> parseworkspace: Warning! Could not find %r in %s:%s"%(param,oldval,newval))
      oldval = var.getVal()
      var.setVal(newval)
      #if verb>=1:
      print(">>> parseworkspace: set %s = %s -> %s"%(param,oldval,newval))
  
  # GET EXPECTED VECTORS
  systs_b = { } if bonly else None
  systs_s = { }
  bins_b  = getbins_model(mc_b,fitres=fitres_b,params=params,systs=systs_b,title="B-only",verb=verb)
  bins_s  = getbins_model(mc_s,fitres=fitres_s,params=params,systs=systs_s,title="S + B",verb=verb)
  vec_s   = np.array(bins_s)
  vec_b   = np.array(bins_b)
  
  # CHECK
  print(">>> parseworkspace:   observed nbins=%d (non zero=%d)"%(len(bins_obs),np.count_nonzero(vec_obs)))
  if verb>=1:
    print(">>> parseworkspace:   B-only nbins=%d (non zero=%d)"%(len(bins_b),np.count_nonzero(bins_b)))
    print(">>> parseworkspace:   S+B nbins=%d (non zero=%d)"%(len(bins_s),np.count_nonzero(bins_s)))
  
  assert len(bins_b)==len(bins_obs) and len(bins_s)==len(bins_obs),\
    "Different number of bins: obs=%d, bonly=%d, sb=%d"%(len(bins_obs),len(bins_b),len(bins_s))
  
  for file in files:
    if file:
      file.Close()
  
  return vec_obs, vec_b, vec_s, systs_b, systs_s
  

def makelatex(string):
  """Help function to make LaTeX for plots."""
  string = ' '.join(["$%s$"%(s.replace('#','\\')) if ('#' in s or '\\' in s) else s
                     for s in string.split()])
  return string
  

def plotplane(outnames,vec_b,vec_s,systs_b,systs_s,show=False,pardict=None,fit_b=False,fit_s=False,verb=0):
  """Plot 2D vectors."""
  # https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.plot.html
  if verb>=1:
    print(">>> plotplane: len(systs_b)=%s, len(systs_s)=%s"%(len(systs_b),len(systs_s)))
  colors = ['r','b','g','c','m','y']
  if verb>=3:
    print(">>> plotplane: vec_b=%s"%vec_b)
    print(">>> plotplane: vec_s=%s"%vec_s)
  if isinstance(outnames,str):
    outnames = [outnames]
  title_obs = "Observed"
  title_b   = "B-only (%s)"%('postfit' if fit_b else 'prefit')
  title_s   = "S+B (%s)"%('postfit' if fit_s else 'prefit')
  msize     = 11.
  lwidth    = 0.003 # line width of arrow
  xmin = min(0,vec_b[0],vec_s[0])
  xmax = max(0,vec_b[0],vec_s[0])
  ymin = min(0,vec_b[1],vec_s[1])
  ymax = max(0,vec_b[1],vec_s[1])
  ###arrows = [ ]
  
  # PLOT
  cm = 1.0/2.54  # centimeters in inches
  fig, axis = plot.subplots(figsize=(30*cm,20*cm))
  axis.plot(0,0,'ko',label=title_obs,ms=1.1*msize)
  for isys, (vec0, systs) in enumerate([(vec_b,systs_b),(vec_s,systs_s)]):
    if not systs: continue
    for i, (syst, vecs) in enumerate(systs.items()):
      if verb>=2:
        print(">>> plotplane: %s, vecup=%s, vecdn=%s"%(syst,vecs[0],vecs[1]))
      for j, vec in enumerate(vecs):
        width = (j>0)*900*lwidth # only draw head for up variation
        label = None
        if isys==1 and j>0:
          label = pardict.get(syst,syst) if pardict else syst
          if '#' in label or '\\' in label:
            label = makelatex(label)
        color = colors[i%len(colors)]
        arrow = axis.quiver(vec0[0],vec0[1],*vec,color=color,label=label,width=lwidth,headwidth=width,
                            angles='xy',scale_units='xy',scale=1)
        ###if label:
        ###  arrows.append((label,arrow)) # to add arrow to legend
        dvec = vec0+vec
        if dvec[0]<xmin: xmin = dvec[0]
        if dvec[1]<ymin: ymin = dvec[1]
        if dvec[0]>xmax: xmax = dvec[0]
        if dvec[1]>ymax: ymax = dvec[1]
  dx, dy = 0.1*(xmax-xmin), 0.1*(ymax-ymin)
  axis.plot(vec_b[0], vec_b[1], 'bo',label=title_b, ms=msize)
  axis.plot(vec_s[0],vec_s[1],'r*',label=title_s,ms=1.8*msize)
  axis.axis([xmin-dx,xmax+dx,ymin-dy,ymax+dy])
  axis.set_xlabel(r"$|\vec{N}_{Bonly}-\vec{N}_{obs}|$",size=23)
  axis.set_ylabel(r"$|\vec{N}_{S+B}^{\perp}-\vec{N}_{obs}|$",size=23)
  axis.xaxis.set_tick_params(labelsize='large')
  axis.yaxis.set_tick_params(labelsize='large')
  axis.grid()
  
  # LEGEND
  loc  = 'upper' if vec_b[0]>0.5*vec_s[0] else 'lower'
  loc += ' left' if vec_b[0]>0.5*vec_s[0] else ' right'
  #### TODO: arrow in legend:
  #### https://stackoverflow.com/questions/60781312/plotting-arrow-in-front-of-legend-matplotlib
  ###handles, labels = plot.gca().get_legend_handles_labels()
  ###for label, arrow in arrows:
  ###  labels.append(label)
  ###  handles.append(arrow)
  ###axis.legend(handles,labels,loc=loc,numpoints=1,
  ###  handler_map={mpatches.FancyArrow: HandlerPatch(patch_func=make_legend_arrow)})
  axis.legend(loc=loc,numpoints=1)
  
  # SAVE & SHOW
  for outname in outnames:
    if not outname: continue
    print(">>> plotplane: writing %s..."%(outname))
    plot.savefig(outname,dpi=100)
  if show:
    plot.show()
  plot.close()
  

def project_and_plot(outname,vec_obs,vec_b,vec_s,systs_b,systs_s,show=False,pardict=None,fit_b=False,fit_s=False,verb=0):
  """Project given set of vectors onto 2D plane, and plot."""
  if verb>=1:
    print(">>> project_and_plot")
  plane  = Plane(vec_obs,vec_b,vec_s,verb=verb) # 2D plane
  proj_b = plane.project(vec_b-vec_obs)  # B-only in plane
  proj_s = plane.project(vec_s-vec_obs) # SB in plane
  proj_systs_b = { }
  proj_systs_s = { }
  if systs_b:
    for syst, (vecup,vecdn) in systs_b.items():
      print(vecup)
      print(vec_b)
      dvec_up = vecup - vec_b
      dvec_dn = vecdn - vec_b
      proj_systs_b[syst] = (plane.project(dvec_up),plane.project(dvec_dn))
  if systs_s:
    for syst, (vecup,vecdn) in systs_s.items():
      dvec_up = vecup - vec_s
      dvec_dn = vecdn - vec_s
      proj_systs_s[syst] = (plane.project(dvec_up),plane.project(dvec_dn))
  plotplane(outname,proj_b,proj_s,proj_systs_b,proj_systs_s,show=show,pardict=pardict,fit_b=fit_b,fit_s=fit_s,verb=verb)
  

def test(verb=4):
  print(">>> test")
  """For quick testing of main routines."""
  verb = max(verb,1) # verbosity
  vec_obs = np.array([100,35, 9]) # data
  vec_b   = np.array([ 99,33, 6]) # B-only
  vec_s  = np.array([101,34,10]) # S+B
  vec1_up = np.array([102,34, 8])
  vec1_dn = np.array([ 93,32, 5])
  vec2_up = np.array([ 89,36,15])
  vec2_dn = np.array([111,30, 7])
  systs_b = {
    'tid': (vec1_up,vec1_dn),
  }
  systs_s = {
    'tid': (vec2_up,vec2_dn),
  }
  
  # PROJECT & PLOT
  project_and_plot(vec_obs,vec_b,vec_s,systs_b,systs_s,verb=verb)
  

def main(args):
  
  verb      = args.verbosity
  if verb>=1:
    print(">>> main")
  outnames  = args.outnames or ["plane.png"]
  wsname    = args.workspace
  fitres_b  = args.fitres_b
  fitres_s  = args.fitres_s
  bonly     = args.bonly
  show      = args.show
  params    = args.params
  parvals   = args.parvals
  pardict   = args.pardict
  
  # PARAMETER VALUES
  if parvals:
    plist = parvals.split(',')
    parvals = { }
    for param in plist:
      key, value = param.split('=')
      parvals[key] = float(value)
    if verb>=1:
      print(">>> parvals: %r"%(parvals))
  
  # DICTIONARY
  if pardict:
    if pardict.endswith(pardict):
      import json
      with open(pardict,'r') as dfile:
        pardict = json.load(dfile)
    else:
      entries = pardict.split(' ')
      pardict = { }
      for entry in entries:
        key, val = entry.split('=')
        pardict[key] = val
  
  #if wsname:
  vargs = parseworkspace(wsname,fitres_b=fitres_b,fitres_s=fitres_s,params=params,
                                parvals=parvals,bonly=bonly,verb=verb)
  
  # PROJECT & PLOT
  project_and_plot(outnames,*vargs,show=show,pardict=pardict,
                            fit_b=bool(fitres_b),fit_s=bool(fitres_s),verb=verb)
  

if __name__ == '__main__':
  from argparse import ArgumentParser
  description = '''Convert histograms to vectors and project onto a 2D plane to study systematics in a new physics search.
  The plane is spanned by the observed, B-only and S+B vectors. Example of use:
  ./project_bins.py -w work.root -o plane.png -p lumi shape_jes -T nuisdict.json --show'''
  parser = ArgumentParser(prog="checkshapes",description=description,epilog="Good luck!")
  parser.add_argument('-b', "--bonly",        action='store_true',
                                              help="include systematics for B-only" )
  parser.add_argument('-s', "--show",         action='store_true',
                                              help="show plot in interactive mode" )
  parser.add_argument('-o', "--outname",      dest='outnames',default=["plane.png"],nargs='+',
                      metavar="FILE",         help="one or more filenames for output figure" )
  parser.add_argument('-w', "--workspace",
                      metavar="FILE",         help="ROOT file with CMS CombineTool workspace" )
  parser.add_argument('-S', "--fitresult-SB", dest='fitres_s',
                      metavar="FILE:FIT",     help="ROOT file with S+B fitresult, e.g. fitDiagnostics.root:fit_s" )
  parser.add_argument('-B', "--fitresult-Bonly", dest='fitres_b',
                      metavar="FILE:FIT",     help="ROOT file with B-only fitresult, e.g. fitDiagnostics.root:fit_s" )
  #parser.add_argument('-d', "--histograms",
  #                    metavar="FILENAME",     help="ROOT files with TH1 histograms" )
  parser.add_argument('-P', "--setParameters",dest="parvals",
                      metavar="PARAM=VALUE",  help="set physics model parameter to value (comma-separated)" )
  parser.add_argument('-p', "--params",       default=[],nargs='+',
                      metavar="PARAM",        help="project the changes due to these parameters" )
  parser.add_argument('-T', "--translate",    dest='pardict',
                      metavar="JSON",         help="dictionary of nuisance parameters" )
  parser.add_argument('-v', '--verbose',      dest='verbosity',type=int,nargs='?',const=1,default=0,
                      metavar="LEVEL",        help="set verbosity level")
  args = parser.parse_args()
  if args.workspace:
    main(args)
  else: # Run quick test
    test(verb=args.verbosity)
  print(">>> Done")
  
