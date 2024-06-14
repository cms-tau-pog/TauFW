# -*- coding: utf-8 -*-
# Author: Izaak Neutelings (May 2024)
# Description: Data-driven method to estimate QCD from SS region.
import os, re
from TauFW.Plotter.plot.string import invertcharge, invertiso
from TauFW.Plotter.sample.SampleSet import LOG, SampleSet, Variable, Selection, deletehist, getcolor, makehistname
#from ctypes import c_double
#print ">>> Loading %s"%(__file__)
#gROOT.Macro(modulepath+'/QCD/QCD.C+')


def QCD_ABCD(self, variables, selections, **kwargs):
  """Estimate the QCD in a data-driven way with the ABCD method:
  
  For ditau, region C is "OS & anti-isolated", where C/D = OS/SS ratio:
     OS         SS
     A=SR       B        isolated: both taus pass tight
     C=shape    D        anti-isolated: one tau medium, one tau (!tight && loose)
  
  For etau & mutau, region C is "SS & isolated", where B/D = OS/SS ratio:
     OS         SS
     A=SR       C=shape  isolated: lepton tight isolation (e.g. iso_1<0.15)
     B          D        anti-isolated: light lepton !tight & loose isolation (e.g. 0.15<iso_1<0.50)
  
  For emu & mumu, region C is "SS & isolated", where B/D = OS/SS ratio:
     OS         SS
     A=SR       C=shape  isolated: lepton tight isolation (e.g. iso_1<0.15)
     B          D        anti-isolated: one lepton fails tight isolation (e.g. iso_1<0.15 && 0.15<iso_2<0.50)
  
  Define QCD as the observed data minus background MC.
  Use the three controls regions B, C, and D:
  * The shape is determined in region C.
  * The transfer factor is computed as B/D, the ratio between number of events in regions B and D.
  * Estimate the total yield in region A (SR) as C*B/D, applied to normalized shape from region C.
  """
  verbosity     = LOG.getverbosity(kwargs)+1
  if verbosity>=2:
    LOG.header("Estimating QCD with ABCD")
  samples       = self.samples
  name          = kwargs.get('name',            'QCD'          )
  title         = kwargs.get('title',           "QCD multijet" )
  tag           = kwargs.get('tag',             ""             )
  weight        = kwargs.get('weight',          ""             )
  dataweight    = kwargs.get('dataweight',      ""             )
  replaceweight = kwargs.get('replaceweight',   ""             )
  scale         = kwargs.get('scale',           None           ) # OS/SS ratio (SS -> OS extrapolation scale)
  shift         = kwargs.get('qcdshift',        0.0            ) # for systematics
  negthres      = kwargs.get('negthres',        0.25           ) # threshold for warning about negative QCD bins
  weight_shape  = weight # TODO: unset tau ID SF for anti-isolated region ?
  
  # PREPARE SELECTIONS for shape & normalization (invert OS -> SS, relax isolation, ...)
  if 'tautau' in self.channel: # fully hadronic channels: tautau
    iso_expr = re.compile(r"(idDeepTau\w*VSjet)_1>=(\d+)")
  elif 'tau' in self.channel: # semileptonic channels: etau, mutau
    iso_expr = re.compile(r"(iso_1|pfRelIso\w+_1)<([\d\.]+)") # lepton relative isolation
  else: # fully leptonic channels: emu, mumu
    iso_expr = re.compile(r"(iso_[12]|pfRelIso\w+_[12])<([\d\.]+)") # lepton relative isolation
  selection_dict    = { } # { selection: selection_sr }
  selections_shape  = [ ] # selections for region C to compute shape
  selections_common = [ ] # common selections for ABCD regions to compute transfer factor
  for selection_sr in selections:
    cuts_sr  = selection_sr.selection # region A: OS, tight isolation
    if 'tautau' in self.channel:
      match = iso_expr.search(cuts_sr)
      if match:
        tauid     = match.group(1) # DeepTauVSjet
        wp_tight  = int(match.group(2)) # DeepTauVSjet Tight: 16
      else:
        tauid     = "idDeepTau"
        wp_tight  = 16 # bit for idDeepTau*VSjet
        LOG.warning(f"SampleSet.QCD_ABCD: Did not find tau ID VSjet WP {iso_expr.pattern!r} in {cuts_sr!r}"
                    f" for {self.channel} channel! Assuming tauid={tauid!r}, tight WP={wp_tight}...")
      wp_medium   = int(wp_tight/2) # DeepTauVSjet Medium: 8
      wp_loose    = int(wp_tight/4) # DeepTauVSjet Loose: 4
      xvar        = Variable("(q_1*q_2>0)?1:-1",2,-2,2,fname='chargesign') # charge sign +1/-1
      # isolation codes = 0: both taus fail medium, 1: at least one medium & one !tight, 2: both tight
      yvar        = Variable(f"({tauid}_1>={wp_tight} && {tauid}_2>={wp_tight}) ? 2 : "
                             f"({tauid}_1>={wp_medium} || {tauid}_2>={wp_medium}) ? 1 : 0",2,1,3,fname='isolation')
      cuts_shape  = f"(({tauid}_1>={wp_medium} && {tauid}_2<{wp_tight} && {tauid}_2>={wp_loose}) ||"+\
                    f" ({tauid}_2>={wp_medium} && {tauid}_1<{wp_tight} && {tauid}_1>={wp_loose}))"
      cuts_shape  = invertiso(cuts_sr,to=cuts_shape,verbosity=verbosity) # replace tight isolation requirement
      cuts_common = f"{tauid}_1>={wp_loose} && {tauid}_2>={wp_loose}"
      cuts_common = invertiso(cuts_sr,to=cuts_common,verbosity=verbosity) # replace tight isolation requirement with loosest
      cuts_common = invertcharge(cuts_common,target='',verbosity=verbosity) # remove charge sign requirement
      selection_shape  = Selection(f"{selection_sr.title} (OS, anti-isolated)",cuts_shape) # region C for shape computation
      selection_common = Selection(f"{selection_sr.title} (relaxed isolated)",cuts_common) # common selections for full ABCD region
    elif 'tau' in self.channel: # semileptonic channels: etau, mutau
      LOG.warning(f"SampleSet.QCD_ABCD: {self.channel} channel not validated!")
      wp_loose    = 0.50
      match = iso_expr.search(cuts_sr)
      if match:
        iso_1     = match.group(1) # lepton relative isolation
        wp_tight  = float(match.group(2)) # upper cut for tight isolation
      else:
        iso_1     = "iso_1"
        wp_tight  = 0.15
        LOG.warning(f"SampleSet.QCD_ABCD: Did not find lepton isolation {iso_expr.pattern!r} in {cuts_sr!r}"
                    f" for {self.channel} channel! Assuming iso_1={iso_1!r}, tight WP={wp_tight}...")
      xvar        = Variable(iso_1,[0,wp_tight,wp_loose]) # isolation regions
      yvar        = Variable("(q_1*q_2>0)?1:-1",2,-2,2,fname='chargesign') # charge sign +1/-1
      cuts_shape  = invertcharge(cuts_sr,target='SS',verbosity=verbosity) # invert OS -> SS
      cuts_common = invertcharge(cuts_sr,target='',verbosity=verbosity) # remove charge sign requirement
      cuts_common = invertiso(cuts_common,to=f"{iso_1}<{wp_loose}",verbosity=verbosity) # relax tight isolation requirement
      selection_shape  = Selection(f"{selection_sr.title} (SS, isolated)",cuts_shape) # region C for shape computation
      selection_common = Selection(f"{selection_sr.title} (relaxed isolated)",cuts_common) # common selections for full ABCD region
    else: # fully leptonic channels: emu, mumu
      LOG.warning(f"SampleSet.QCD_ABCD: {self.channel} channel not validated!")
      wp_loose    = 0.50
      matches = iso_expr.findall(cuts_sr)
      if len(matches)>=2:
        iso_1, wp1_tight = matches[0] # leading lepton ?
        iso_2, wp2_tight = matches[0] # subleading lepton ?
      else:
        iso_1     = "iso_1"
        iso_2     = "iso_2"
        wp1_tight = 0.15
        wp2_tight = 0.15
        LOG.warning(f"SampleSet.QCD_ABCD: Did not find lepton isolation {iso_expr.pattern!r} in {cuts_sr!r} for {self.channel} channel! "
                    f"Assuming iso_1={iso_1!r} & iso_2={iso_2!r} with tight WPs {wp1_tight} & {wp1_tight}, resp. ...")
      xvar        = Variable(f"({iso_1}<{wp1_tight} && {iso_2}<{wp2_tight}) ? 2 : "
                             f"({iso_1}>={wp1_tight} || {iso_2}>={wp2_tight}) ? 1 : 0",2,1,3) # isolation regions
      yvar        = Variable("(q_1*q_2>0)?1:-1",2,-2,2,fname='chargesign') # charge sign +1/-1
      cuts_shape  = invertcharge(cuts_sr,target='SS',verbosity=verbosity) # invert OS -> SS
      cuts_common = invertcharge(cuts_sr,target='',verbosity=verbosity) # remove charge sign requirement
      cuts_common = invertiso(cuts_common,to=f"{iso_1}<{wp_loose} && {iso_2}<{wp_loose}",verbosity=verbosity) # relax tight isolation requirement
      selection_shape  = Selection(f"{selection_sr.title} (SS, isolated)",cuts_shape) # region C for shape computation
      selection_common = Selection(f"{selection_sr.title} (relaxed isolated)",cuts_common) # common selections for full ABCD region
    ###else:
    ###  LOG.warning(f"SampleSet.QCD_ABCD: {self.channel} channel not implemented!")
    ###  return { }
    selection_dict[selection_shape]  = selection_sr # cache for reuse
    selection_dict[selection_common] = selection_sr # cache for reuse
    selections_shape.append(selection_shape)
    selections_common.append(selection_common)
    if verbosity+2>=3:
      print(f">>> SampleSet.QCD_ABCD: weight_shape={weight_shape!r}")
      print(f">>>   cuts_sr     = {selection_sr.selection!r}")
      print(f">>>   cuts_shape  = {selection_shape.selection!r}")
      print(f">>>   cuts_common = {selection_common.selection!r}")
      print(f">>>   (xvar,yvar) = ({xvar.name!r}, {yvar.name!r})")
  
  # COMPUTE NORMALIZATION on the fly: transfer factor from total yields of ABCD regions
  # TODO: add cuts based on ranges of variables to be plotted to reduce phase space ?
  scale_dict = { }
  vargs = (xvar,yvar) # (x,y) = (charge sign,isolation)
  hists = self.gethists2D(vargs,selections_common,weight=weight,dataweight=dataweight,tag=tag, #ncores=ncores,
                          signal=False,method=None,split=False,task="Estimating QCD ABCD yields",verbosity=verbosity-1)
  for selection_common in hists:
    selection_sr = selection_dict[selection_common]
    datahist = hists[selection_common].data
    exphists = hists[selection_common].exp
    if not datahist:
      LOG.warning("SampleSet.QCD_ABCD: No data to make DATA driven QCD!")
      scale_dict[selection_sr] = 1.0
      continue
    exphist  = exphists[0].Clone("totexp_ABCD")
    qcdhist  = exphists[0].Clone(f"{name}_ABCD")
    exphist.Reset() # set all bin content to zero
    for hist in exphists: # sum all expected background estimated with MC
      if 'qcd' in hist.GetName().lower() or 'qcd' in hist.GetTitle().lower():
        LOG.warn(f">>> SampleSet.QCD_ABCD: Omitting QCD (?) background {hist!r} from ABCD region...")
        continue
      exphist.Add(hist)
    qcdhist.Reset() # set all bin content to zero
    qcdhist.Add(datahist) # QCD = observed data
    qcdhist.Add(exphist,-1) # subtract all MC backgrounds from data
    # TODO: use IntegralAndError/GetBinError to estimate error on scale factor
    n_A = qcdhist.GetBinContent(1,2) # region A: OS, isolated (signal region)
    n_B = qcdhist.GetBinContent(2,2) # region B: SS, isolated
    n_C = qcdhist.GetBinContent(1,1) # region C: OS, anti-isolated (shape)
    n_D = qcdhist.GetBinContent(2,1) # region D: SS, anti-isolated
    if verbosity+1>=2:
      nexp = sum(h.Integral() for h in exphists)
      print(f">>> SampleSet.QCD_ABCD: Total observed data = {datahist.Integral():.1f}, total expected (non-QCD) = {exphist.Integral():.1f}")
      print(f">>> common = {selection_common.selection!r}")
      print(f">>>   {'OS':>12} {'SS':>12}  (total yields in ABCD regions)")
      print(f">>>   {n_A:12.1f} {n_B:12.1f}  isolated")
      print(f">>>   {n_C:12.1f} {n_D:12.1f}  anti-isolated")
    if n_D==0:
      LOG.warning(f"SampleSet.QCD_ABCD: n_D={n_D}! Setting to 1 to avoid division by zero...")
      n_D = 1.0
    scale = n_C*n_B/n_D # OS/SS factor
    if verbosity>=1:
      trans = n_B/n_D # B/D = transfer factor
      if 'tautau' in self.channel:
        print(f">>> SampleSet.QCD_ABCD: B/D=transfer={trans:.3f}, C/D=OS/SS={n_C/n_D:.3f}, scale=B*(C/D)={scale:.3f}, shift={shift:.3f}")
      else:
        print(f">>> SampleSet.QCD_ABCD: B/D=transfer={trans:.3f}, scale=B*(C/D)={scale:.3f}, shift={shift:.3f}")
    scale_dict[selection_sr] = scale # apply to normalize shape below
    deletehist([qcdhist,exphist,datahist]+exphists) # clean histogram from memory
  
  # GET HISTOGRAMS: shapes from region C
  # Create QCD histograms as (data - MC)_C * (C*B/D)
  qcdhists = { }
  hists = self.gethists(variables,selections_shape,weight=weight_shape,dataweight=dataweight,replaceweight=replaceweight,tag=tag,
                        signal=False,split=False,blind=False,task="Estimating QCD",verbosity=verbosity-1)
  for selection_shape in hists:
    selection_sr = selection_dict[selection_shape]
    qcdhists[selection_sr] = { }
    for variable, histset in hists[selection_shape].items():
      datahist = histset.data
      exphists = histset.exp
      qcdhname = makehistname(variable,selection_sr,name,tag).rstrip('_') # $VAR_$SEL_$PROCESS$TAG
      
      # CHECK data
      if not datahist:
        LOG.warning("SampleSet.QCD: No data to make DATA driven QCD!")
        return None
      
      # QCD HIST = ( DATA - MC )_C
      exphist = exphists[0].Clone('totexp_shape')
      exphist.Reset() # set all bin content to zero
      for hist in exphists:
        if 'qcd' in hist.GetName().lower() or 'qcd' in hist.GetTitle().lower():
          LOG.warn(f">>> SampleSet.QCD_ABCD: Omitting QCD (?) background {hist!r} from shape...")
          continue
        exphist.Add(hist)
      qcdhist = exphists[0].Clone(qcdhname)
      qcdhist.Reset() # set all bin content to zero
      qcdhist.Add(datahist) # QCD = observed data in region C
      qcdhist.Add(exphist,-1) # subtract total MC expectation in SS
      qcdhist.SetTitle(title)
      qcdhist.SetFillColor(getcolor('QCD'))
      qcdhist.SetOption('HIST')
      qcdhists[selection_sr][variable] = qcdhist
      
      # ENSURE positive bins
      nneg = 0
      nbins = qcdhist.GetXaxis().GetNbins()+2 # include under-/overflow
      for i in range(0,nbins):
        bin = qcdhist.GetBinContent(i)
        if bin<0:
          qcdhist.SetBinContent(i,0)
          qcdhist.SetBinError(i,1)
          nneg += 1
      if nbins and nneg/nbins>negthres:
        LOG.warning(f"SampleSet.QCD_ABCD: {variable.name!r} has {nneg}/{nbins}>{100.0*negthres:.1f}% negative bins! Set to 0 +- 1.",pre="  ")
      
      # SCALE region C -> A
      nqcd = qcdhist.Integral() # to normalize shape
      if nqcd>0:
        scale = scale_dict[selection_sr]*(1.0+shift) # OS/SS scale & systematic variation
        qcdhist.Scale(scale/nqcd) # normalize shape & scale SS -> OS
      
      # YIELDS
      if verbosity>=2:
        nexp = exphist.Integral()
        nobs = datahist.Integral()
        print(f">>> SampleSet.QCD_ABCD: yields: obs={nobs:.1f}, exp={nexp:.1f}, qcd={nqcd:.1f}, scale={scale:.3f}")
      
      # CLEAN
      deletehist([datahist,exphist]+exphists) # clean histogram from memory
  
  return qcdhists # dictionary: { selection: { variable: TH1 } } to be inserted into HistSet
  

SampleSet.QCD_ABCD = QCD_ABCD # add as class method of SampleSet, which will be called in SampleSet.gethists