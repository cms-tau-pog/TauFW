# -*- coding: utf-8 -*-
# Author: Izaak Neutelings (September 2021)
# Description: Help functions to create mu_R & mu_F scale variations
from TauFW.Plotter.sample.Sample import LOG, Sample, MergedSample, deletehist, joincuts, joinweights


def getenvelope_scalevars(self,variables,selection,**kwargs):
  """Get variations of scale and make envelopes."""
  verbosity       = LOG.getverbosity(kwargs)
  name            = kwargs.get('name', "%s_scale"%(self.name))
  title           = kwargs.get('title',     self.title )
  weight          = kwargs.get('weight',    ""         )
  extracuts       = kwargs.get('extracuts', ""         )
  tag             = kwargs.get('tag',       ""         )
  renorm          = kwargs.get('renorm',    True       ) # remove renormalization effect
  parallel        = kwargs.get('parallel',  False      )
  if verbosity>=2:
    LOG.header("Varying scale weights for variables %s (%s)"%(self.name,name))
    print ">>> selection=%r"%(selection.selection)
  wtags = [ "0p5_0p5", "0p5_1p0", "1p0_0p5", "1p0_2p0", "2p0_1p0", "2p0_2p0", ]
  
  # GET NORMALIZATION SFs from 'qweight' histogram
  if renorm: # remove normalization effect for each individual scale variation
    sfs     = [ ]
    wgthist = self.gethist_from_file('qweight',incl=True,mode='sumw')
    ibin    = wgthist.GetXaxis().FindBin("1p0_1p0")
    wgtnom  = wgthist.GetBinContent(ibin)
    LOG.verb("Sample.getenvelope_scalevars:   wtag='1p0_1p0', nom=%s"%(wgtnom),verbosity,2)
    if wgtnom<=0:
      LOG.warning("Sample.getenvelope_scalevars: Nominal scale weight %s<=0 (bin %d) for sample %s (%s)!"%(wgtnom,ibin,self.name,name))
    for wtag in wtags:
      ibin = wgthist.GetXaxis().FindBin(wtag)
      wgtvar = wgthist.GetBinContent(ibin)
      if wgtvar<=0:
        LOG.warning("Sample.getenvelope_scalevars: %r scale weight %s<=0 (bin %d) for sample %s (%s)!"%(wtag,wgtvar,ibin,self.name,name))
      sf = wgtnom/wgtvar
      LOG.verb("Sample.getenvelope_scalevars:   wtag=%s, sf = nom/var = %.3g/%.3g = %.3g"%(wtag,wgtnom,wgtvar,sf),verbosity,2)
      sfs.append(sf)
  else:
    sfs = [1.0]*len(wtags)
  
  # CLONE VARIABLES for parallel use in MultiDraw
  subvars  = [ ] # variables x wtags
  var_dict = { } # variables -> [(subvar,sf)]
  for var in variables:
    var_dict[var] = [(var,1.)] # nominal
    subvars.append(var)
    for wtag, sf in zip(wtags,sfs):
      subwgt = "qweight_%s"%(wtag)
      subvar = var.clone(filename="$FILE_%s"%wtag,weight=subwgt)
      var_dict[var].append((subvar,sf))
      LOG.verb("Sample.getenvelope_scalevars:   subvar=%s, weight=%r, sf=%.3g"%(subvar.filename,subvar.weight,sf),verbosity,2)
      subvars.append(subvar)
  
  # HISTOGRAMS
  hists = self.hist(subvars,selection,weight=weight,extracuts=extracuts,tag=tag,
                    split=False,verbosity=verbosity-2,parallel=parallel)
  
  # CREATE ENVELOP
  varhists = [ ]
  for i, variable in enumerate(variables):
    ifirst = i*len(var_dict[var])
    nwgts  = ifirst+len(var_dict[var])
    histup = None
    histdn = None
    for (subvar, sf), hist in zip(var_dict[variable],hists[ifirst:nwgts]):
      hist.Scale(sf) # normalize yield to central value
      LOG.verb("Sample.getenvelope_scalevars:   hist=%s, integral=%.3g"%(hist,hist.Integral()),verbosity,2)
      if histup==None or histdn==None:
        histup = hist.Clone(name+'Up')
        histdn = hist.Clone(name+'Down')
      else:
        for i, val in enumerate(hist):
          #print i, val, hist.GetBinContent(i)
          up = histup.GetBinContent(i)
          dn = histdn.GetBinContent(i)
          if val>up:
            histup.SetBinContent(i,val)
            histup.SetBinError(i,hist.GetBinError(i))
          if val<dn:
            histdn.SetBinContent(i,val)
            histdn.SetBinError(i,hist.GetBinError(i))
      deletehist(hist)
    nevtup = histup.Integral()
    nevtdn = histdn.Integral()
    LOG.verb("Sample.getenvelope_scalevars:   variable=%s, histup=%.3g, histdn=%.3g"%(variable.filename,nevtup,nevtdn),verbosity,2)
    if nevtup<=0 or nevtdn<=0:
      LOG.warning("Sample.getenvelope_scalevars: Found <=0 integral for %r; histup=%.2f, histdn=%.2f!"%(variable.filename,nevtup,nevtdn))
    varhists.append((histup,histdn))
  
  return varhists
       

#def gethist_scalevars(self,subvars,selection,wtags,**kwargs):
#  """Get variations of scale for subsample."""
#  verbosity       = LOG.getverbosity(kwargs)+2
#  name            = kwargs.get('name', "%s_scale"%(self.name))
#  weight          = kwargs.get('weight',    ""         )
#  extracuts       = kwargs.get('extracuts', ""         )
#  tag             = kwargs.get('tag',       ""         )
#  parallel        = kwargs.get('parallel',  False      )
#  if verbosity>=2:
#    LOG.header("varying scale weights for subsample %s (%s)"%(self.name,name))
#    print ">>> selection=%r"%(selection.selection)
#  
#  # ADD SUBSAMPLE HISTOGRAMS
#  hists = [ ]
#  if isinstance(self,MergedSample):
#    print ">>> Sample.gethist_scalevars: cuts=%r, weight=%r, scale=%r, norm=%r, %r"%(self.cuts,self.weight,self.scale,self.norm,self.name)
#    kwargs['cuts']   = joincuts(kwargs.get('cuts'),  self.cuts           )
#    kwargs['weight'] = joinweights(kwargs.get('weight', ""), self.weight ) # pass weight down
#    kwargs['scale']  = kwargs.get('scale', 1.0) * self.scale * self.norm # pass scale down
#    for sample in self.samples:
#      subhists = sample.gethist_scalevars(subvars,selection,wtags,**kwargs)
#      if not hists:
#         hists = subhists[:] # Clone?
#      else:
#         for hist, subhist in zip(hists,subhists):
#           hist.Add(subhist)
#         deletehist(subhists)
#      ###if self.scale!=1 or self.norm!=1:
#      ###  for hist in hists:
#      ###    hist.Scale(self.scale*self.norm)
#  
#  # GET HISTOGRAM & SCALE
#  else:
#    
#    # GET HISTOGRAMS
#    hists = self.gethist(subvars,selection,weight=weight,extracuts=extracuts,tag=tag,
#                         split=False,verbosity=verbosity-2)
#    
#    # GET SCALE
#    sfs     = [ ]
#    wgthist = self.gethist_from_file('qweight')
#    ibin    = wgthist.GetXaxis().FindBin("1p0_1p0")
#    wgtnom  = wgthist.GetBinContent(ibin)
#    LOG.verb("Sample.gethist_scalevars:   wtag='1p0_1p0', nom=%s"%(wgtnom),verbosity,2)
#    if wgtnom<=0:
#      LOG.warning("Sample.gethist_scalevars: Nominal scale weight %s<=0 (bin %d) for sample %s (%s)!"%(wgtnom,ibin,self.name,name))
#    for wtag in wtags:
#      if not wtag:
#        wtag = "1p0_1p0"
#      ibin = wgthist.GetXaxis().FindBin(wtag or "1p0_1p0")
#      wgtvar = wgthist.GetBinContent(ibin)
#      if wgtvar<=0:
#        LOG.warning("Sample.gethist_scalevars: %r scale weight %s<=0 (bin %d) for sample %s (%s)!"%(wtag,wgtvar,ibin,self.name,name))
#      sf = wgtnom/wgtvar
#      LOG.verb("Sample.gethist_scalevars:   wtag=%s, sf = nom/var = %.3g/%.3g = %.3g"%(wtag,wgtnom,wgtvar,sf),verbosity,2)
#      sfs.append(sf)
#    
#    # SCALE HIST
#    for i, hist in enumerate(hists):
#      sf = sfs[i%len(sfs)]
#      hist.Scale(sf)
#      LOG.verb("Sample.gethist_scalevars:   i=%2d: Scale hist=%s (int=%.2f) by sf=%.3f"%(i,repr(hist.GetName()).ljust(45),hist.Integral(),sf),verbosity+3,3)
#  
#  return hists
  

#def getenvelope_scalevars(self,variables,selection,**kwargs):
#  """Get variations of scale and make envelopes."""
#  verbosity = LOG.getverbosity(kwargs)+2
#  name      = kwargs.get('name', "%s_scale"%(self.name))
#  title     = kwargs.get('title',     self.title )
#  if verbosity>=2:
#    LOG.header("varying scale weights for samples %s (%s)"%(self.name,name))
#    print ">>> selection=%r"%(selection.selection)
#  wtags = [ "0p5_0p5", "0p5_1p0", "1p0_0p5", "1p0_2p0", "2p0_1p0", "2p0_2p0", ]
#  
#  # CLONE VARIABLES for multidraw
#  var_dict = { }
#  subvars = [ ]
#  for var in variables:
#    var_dict[var] = [var] # nominal
#    for wtag in wtags:
#      subwgt = "qweight_%s"%(wtag)
#      subvar = var.clone(filename="$FILE_%s"%wtag,weight=subwgt)
#      var_dict[var].append(subvar)
#      if verbosity>=2:
#        print ">>>   subvar=%s, weight=%r"%(subvar.filename,subvar.weight)
#      subvars.append(subvar)
#  
#  # HISTOGRAMS
#  hists = self.gethist_scalevars(subvars,selection,wtags,**kwargs)
#  
#  # CREATE ENVELOP
#  varhists = [ ]
#  for i, variable in enumerate(variables):
#    ifirst = i*len(var_dict[var])
#    nwgts  = ifirst+len(var_dict[var])
#    histup = None
#    histdn = None
#    for subvar, hist in zip(var_dict[variable],hists[ifirst:nwgts]):
#      if verbosity>=2:
#        print ">>>   hist=%s, integral=%.3g"%(hist,hist.Integral())
#      if histup==None or histdn==None:
#        histup = hist.Clone(name+'Up')
#        histdn = hist.Clone(name+'Down')
#        histup.SetTitle(title+" Up")
#        histdn.SetTitle(title+" Down")
#        #print "NOM"
#        #for i, val in enumerate(hist):
#        #  print i, val
#      else:
#        for i, val in enumerate(hist):
#          #print i, val, hist.GetBinContent(i)
#          up = histup.GetBinContent(i)
#          dn = histdn.GetBinContent(i)
#          if val>up:
#            histup.SetBinContent(i,val)
#            histup.SetBinError(i,hist.GetBinError(i))
#          if val<dn:
#            histdn.SetBinContent(i,val)
#            histdn.SetBinError(i,hist.GetBinError(i))
#      close(hist)
#    nevtup = histup.Integral()
#    nevtdn = histdn.Integral()
#    if verbosity>=2:
#      print ">>>   variable=%s, histup=%.3g, histdn=%.3g"%(variable.filename,nevtup,nevtdn)
#    if nevtup<=0 or nevtdn<=0:
#      LOG.warning("getScaleVars: Found <=0 integral for %r; histup=%.2f, histdn=%.2f!"%(variable.filename,nevtup,nevtdn))
#    varhists.append((histup,histdn))
#  
#  return varhists


#Sample.gethist_scalevars = gethist_scalevars # add as class method of Sample
Sample.getenvelope_scalevars = getenvelope_scalevars # add as class method of Sample
