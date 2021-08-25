#! /usr/bin/env python

import os, sys, re
#sys.path.append('../plots')
from argparse import ArgumentParser
import PlotTools.PlotTools
from PlotTools.SampleTools import getColor, sample_dict
from PlotTools.SettingTools import isList, ensureList, ensureTFile
from PlotTools.PlotTools import Plot, ceilToSignificantDigit, groupHistsInList, getHist
from PlotTools.PrintTools import color, warning, error
import PlotTools.CMS_lumi as CMS_lumi, PlotTools.tdrstyle as tdrstyle
import PlotTools.SettingTools as GLOB
import ROOT
from ROOT import TFile, TTree, kAzure, kRed, kGreen, kOrange, kMagenta, kYellow
ROOT.gROOT.SetBatch(ROOT.kTRUE)

argv = sys.argv
description = '''This script makes shape variations from input root files for datacards.'''
parser = ArgumentParser(prog="checkshapes_TES",description=description,epilog="Succes!")
parser.add_argument(      'filename',      type=str, nargs='?', action='store',
                    metavar='FILENAME',    help="file with shapes" ),
parser.add_argument('-y', '--year',        dest='year', choices=[2016,2017,2018], type=int, default=2018, action='store',
                                           help="select year")
parser.add_argument('-c', '--channel',     dest='channels', choices=['mt','et'], type=str, nargs='+', default=['mt'], action='store',
                                           help="select channels")
parser.add_argument('-t', '--tag',         dest='tags', type=str, nargs='+', default=[ '' ], action='store',
                    metavar="TAGS",        help="tags for the input file" )
parser.add_argument('-d', '--decayMode',   dest='DMs', type=str, nargs='*', default=[ ], action='store',
                    metavar="DECAY",       help="decay mode" )
parser.add_argument('-o', '--observable',  dest='observables', type=str, nargs='*', default=[ ], action='store',
                    metavar='VARIABLE',    help="name of observable for TES measurement" )
parser.add_argument('-r', '--shift-range', dest='shiftRange', type=str, default="0.940,1.060", action='store',
                    metavar="RANGE",       help="range of TES shifts" )
parser.add_argument(      '--dirnames',    dest='dirnames', type=str, nargs='*', default=[ ], action='store',
                    metavar="DIRNAMES",    help="list of TDirectory names for given root file" )
parser.add_argument('-p', '--postfit',     dest='postfit', default=False, action='store_true',
                                           help="do pre-/post-fit" )
parser.add_argument(      '--out-dir',     dest='outdirname', type=str, default="", action='store',
                    metavar='DIRNAME',     help="name of output directory" )
parser.add_argument(      '--pdf',         dest='pdf', default=False, action='store_true',
                                           help="save plot as pdf as well" )
parser.add_argument('-v', '--verbose',     dest='verbose', default=False, action='store_true',
                                           help="set verbose" )
args = parser.parse_args()

category_dict  = {
  'DM0':  "h^{#pm}",
  'DM1':  "h^{#pm}#pi^{0}",
  'DM10': "h^{#pm}h^{#mp}h^{#pm}",
  'DM11': "h^{#pm}h^{#mp}h^{#pm}#pi^{0}",
}
variable_dict  = { 'm_2': "m_{tau}", 'pt_2': "tau p_{T}" } #tau mass
variation_dict = { }
colors = [ kAzure+5, kRed+1, kGreen+2, kOrange+1, kMagenta-4, kYellow+1 ]



def drawStacks(filename,dirname,samples,shifts=[ "" ],**kwargs):
  """Compare shapes."""
  print '>>>\n>>> drawStacks("%s","%s")'%(filename,dirname)
  
  file    = TFile(filename,'READ')
  dir     = file.Get(dirname)
  channel = kwargs.get('channel', ""        )
  tag     = kwargs.get('tag',     ""        )
  var0    = kwargs.get('var',     None      )
  xmin    = kwargs.get('xmin',    None      )
  xmax    = kwargs.get('xmax',    None      )
  outdir  = kwargs.get('outdir',  "control" )
  blind   = kwargs.get('blind',   [ ]       )
  group   = kwargs.get('group',   [ ]       )
  ensureDirectory(outdir)
  if not isList(samples): samples = [samples]
  if not dir: print warning('drawStacks: did not find dir "%s"'%(dirname),pre="   ")
  if channel: channel += '-'
  ensureDirectory(outdir)
  
  for shift in shifts:
    if '$' in shift:
      shift = shift.replace('$CAT',dirname).replace('$CHANNEL',channel)
    variations = [ 'Up', 'Down' ] if shift else [""]
    for variation in variations:
      histsB   = [ ]
      histsD   = [ ]
      samplesS = [ ]
      nShifted = 0
      for sample in reversed(samples):
        hist = None
        if shift: # SHIFTED
          sample1 = "%s_%s%s"%(sample,shift,variation)
          hist    = dir.Get(sample1)
          nShifted+=1
          if not hist:
            hist = dir.Get(sample)
        else: # NOMINAL
          hist = dir.Get(sample)
        if not hist:
          print warning('drawStacks: could not find "%s" template in directory "%s"'%(sample,dir.GetName()),pre="   ")
          continue
        hist.SetName(hist.GetName().replace('_ttbar','').replace('_ztt',''))
        hist.SetTitle(sample_dict[sample])
        if 'data_obs' in sample:
          histsD.append(hist)
          hist.SetLineColor(1)
          if blind:
            for bin in range(hist.FindBin(blind[0]),hist.FindBin(blind[1]+2)):
              hist.SetBinContent(bin,0)
        else:
          histsB.append(hist)
      
      if len(histsB)==0 or (shift and nShifted==0):
        print warning('drawStacks: could not find any "%s" templates in directory "%s"'%(shift,dir.GetName()),pre="   ")
        continue
      
      for groupargs in group:
        histsB = groupHistsInList(histsB,*groupargs)
      
      var      = var0 or histsB[0].GetXaxis().GetTitle()
      varname  = formatVariable(var)
      vartitle = variable_dict.get(var,var)
      tshift   = formatFilename(shift)
      nshift   = ('_'+tshift+variation) if tshift else ""
      title    = formatCategory(dirname,tshift,variation,channel=channel.rstrip('-'))
      canvasname = "%s/%s_%s%s%s%s.png"%(outdir,var,channel,dirname,tag,nshift)
      exts       = ['pdf','png'] if args.pdf else ['png']
      
      plot = Plot(histsD,histsB,stack=True)
      plot.plot(vartitle,title=title,ratio=True,staterror=True,xmin=xmin,xmax=xmax)
      plot.saveAs(canvasname,ext=exts)
      plot.close()
  
  file.Close()
  


def drawPrePostFit(filename,dirname,samples,**kwargs):
    """Create pre- and post-fit plots from histograms and data."""
    print '>>>\n>>> drawPrePostFit("%s","%s")'%(filename,dirname)
    
    usertitle       = kwargs.get('title',          None      )
    ratio           = kwargs.get('ratio',          True      )
    tag             = kwargs.get('tag',            ""        )
    var0            = kwargs.get('var',            None      )
    xmin            = kwargs.get('xmin',           None      )
    xmax            = kwargs.get('xmax',           None      )
    ymargin         = kwargs.get('ymargin',        1.22      )
    dirnametag      = kwargs.get('dirnametag',     dirname   )
    outdir          = kwargs.get('outdir',         "plots"   )
    group           = kwargs.get('group',          [ ]       )
    signals         = kwargs.get('signal',         [ ]       )
    signaltitles    = kwargs.get('signaltitle',    [ ]       )
    signalheader    = kwargs.get('signalheader',   ""        )
    signalfilenames = kwargs.get('signalfile',     [ ]       ) # files to take signal from
    signalstrengths = kwargs.get('r',              [ ]       )
    upscale         = kwargs.get('upscale',        1.0       )
    userposition    = kwargs.get('position',       ''        )
    text            = kwargs.get('text',           ""        )
    append_dict     = kwargs.get('apptitle',       { }       )
    signalPostfit   = kwargs.get('signalPostfit',  "postfit" )
    signalposition  = kwargs.get('signalposition', 'x=0.08'  )
    ymax            = None
    #signalPostScale = 1.0
    ensureDirectory(outdir)
    signals         = ensureList(signals)
    signaltitles    = ensureList(signaltitles)
    signalstrengths = ensureList(signalstrengths)
    fits            = ['prefit','postfit']
    file            = ensureTFile(filename,'READ')
    if not file:
      print error('drawPrePostFit: did not find file "%s"'%(filename),pre="   ")
      exit(1)
    
    # ARRANGE signal sample files, (histogram) names and titles
    signalfiles = [ ]
    signallist  = [ ]
    if len(signals)>0 and len(signaltitles)==0:
      signaltitles = [sample_dict[s]+append_dict.get(s,"") for s in signals]
    elif len(signals)==1 and len(signals)<len(signaltitles):
      signals = signals*len(signaltitles)
    if len(signals)>0 and len(signalstrengths)==0:
      signalstrengths = [1.0]*len(signals)
    if len(signals)!=len(signaltitles):
      print error('drawPrePostFit: len(signals) = %d != %d = len(signaltitles)'%(len(signals),len(signaltitles)),pre="   ")
      exit(1)
    if len(signalfilenames)+1==len(signals):
      signalfilenames += [filename]+signalfilenames
    elif len(signalfilenames)!=len(signals):
      print error('drawPrePostFit: len(signalfilenames) = %d != %d = len(signals)'%(len(signalfilenames),len(signals)),pre="   ")
      exit(1)
    if len(signalfilenames)!=len(signals):
      print error('drawPrePostFit: len(signalfilenames) = %d != %d = len(signals)'%(len(signalfilenames),len(signals)),pre="   ")
      exit(1)
    for signalfilename in signalfilenames:
      signalfile = file if signalfilename==filename else ensureTFile(signalfilename,'READ')
      signalfiles.append(signalfile)
    signallist = zip(signalfiles,signals,signaltitles,signalstrengths)
    
    # DRAW PRE-/POST-FIT
    for fit in fits:
      fitdirname = "%s_%s"%(dirname,fit)
      dir = file.Get(fitdirname)
      if not dir:
        print warning('drawPrePostFit: did not find dir "%s"'%(fitdirname),pre="   ")
        return
      histsD = [ ]
      histsB = [ ]
      histsS = [ ]
      
      # DATA & BACKGROUNDS
      for sample in reversed(samples):
        histname = "%s/%s"%(fitdirname,sample)
        stitle   = sample_dict[sample]+append_dict.get(sample,"")
        hist     = file.Get(histname)
        if not hist:
          print warning('drawPrePostFit: could not find "%s" template in directory "%s_%s"'%(sample,dirname,fit),pre="   ")
          continue
        if 'data_obs' in sample:
          histsD.append(hist)
          hist.SetLineColor(1)
          ymax = hist.GetMaximum()*ymargin
        else:
          histsB.append(hist)
        hist.SetTitle(stitle)
      
      # SIGNALS
      for signalfile, sample, stitle, signalr in signallist:
        histname = "%s/%s"%(fitdirname,sample)
        hist     = signalfile.Get(histname)
        if not hist:
          print warning('drawPrePostFit: could not find "%s" template in directory "%s_%s"'%(sample,dirname,fit),pre="   ")
          continue
        scale = upscale/signalr if 'post' in fit else upscale
        hist.Scale(scale)
        histsS.append(hist)
        hist.SetTitle(stitle)
      
      if len(histsB)==0:
        print warning('drawPrePostFit: could not find any templates in directory "%s"'%(dirname),pre="   ")
        continue
      if len(histsD)==0:
        print warning('drawPrePostFit: could not find a data template in directory "%s"'%(dirname),pre="   ")
        continue
      
      for groupargs in group:
        histsB = groupHistsInList(histsB,*groupargs)
      
      var            = var0 or histsB[0].GetXaxis().GetTitle()
      varname        = formatVariable(var)
      vartitle       = variable_dict.get(var,var)
      position       = userposition if userposition else "x=0.67" if 'post' in fit else "x=0.66"
      title          = formatCategory(dirname) if usertitle==None else usertitle
      errortitle     = "pre-fit stat. + syst. unc." if 'pre' in fit else "post-fit unc."
      canvasname     = "%s/%s_%s%s_%s.png"%(outdir,varname,dirnametag,tag,fit)
      exts           = ['pdf','png'] if args.pdf else ['png']
      
      plot = Plot(histsD,histsB,histsS,stack=True)
      plot.plot(vartitle,xmin=xmin,xmax=xmax,ymax=ymax,
                ratio=ratio,staterror=True,colors=colors,linewidth=3,
                title=title,text=text,errortitle=errortitle,position=position,
                signallegend=signalheader,signaltitle=signalheader,signalposition=signalposition)
      plot.saveAs(canvasname,ext=exts)
      plot.close()
  


def drawVariations(filename,dirname,samples,variations,**kwargs):
  """Compare variations, e.g. sample ZTT with variations ['TES0.97','TES1.03']."""
  print '>>>\n>>> drawVariations("%s","%s")'%(filename,dirname)
  
  file     = TFile(filename,'READ')
  dir      = file.Get(dirname) 
  tag      = kwargs.get('tag',      ""       )
  var0     = kwargs.get('var',      None     )
  xmin     = kwargs.get('xmin',     None     )
  xmax     = kwargs.get('xmax',     None     )
  rmin     = kwargs.get('rmin',     None     )
  rmax     = kwargs.get('rmax',     None     )
  outdir   = kwargs.get('outdir',   "shapes" )
  position = kwargs.get('position', 'right'  )
  text     = kwargs.get('text',     ""       )
  if not isList(samples): samples = [samples]
  if not dir: print warning('drawVariations: did not find dir "%s"'%(dirname))
  ensureDirectory(outdir)
  ratio = True
  
  for sample in samples:
    hists = [ ]
    ratio  = int(len(variations)/2)
    for i, variation in enumerate(variations):
      #print '>>>   sample "%s" for shift "%s"'%(sample, shift)
      name = "%s_%s"%(sample,variation.lstrip('_'))
      hist = dir.Get(name)
      if not hist:
        print warning('drawVariations: did not find "%s" in directory "%s"'%(name,dir.GetName()),pre="   ")
        continue
      sampletitle = sample
      if variation in variation_dict:
        sampletitle += variation_dict[variation]
      else:
        sampletitle += getShiftTitle(variation)
      hist.SetTitle(sampletitle)
      if sample==sampletitle or "nom" in sampletitle.lower(): ratio = i+1
      hists.append(hist)
    
    if len(hists)!=len(variations):
      print warning('drawVariations: number of hists (%d) != number variations (%d)'%(len(hists),len(variations)),pre="   ")
    
    var      = var0 or hists[0].GetXaxis().GetTitle()
    varname  = formatVariable(var)
    vartitle = variable_dict.get(var,var)
    shift0   = formatFilename(variations[0])
    shift1   = formatFilename(variations[-1])
    shift    = ""; i=0
    for i, letter in enumerate(shift0):
      if i>=len(shift1): break
      if letter==shift1[i]: shift+=shift0[i]
      else: break
    nshift = "_%s-%s"%(shift0,shift1.replace(shift,""))
    title  = formatCategory(dirname,shift)
    canvasname = "%s/%s_%s_%s%s%s.png"%(outdir,sample,varname,dirname,tag,nshift.replace('.','p'))
    exts       = ['pdf','png'] if args.pdf else ['png']
    
    plot = Plot(hists)
    plot.plot(vartitle,title=title,text=text,ratio=ratio,linestyle=False,xmin=xmin,xmax=xmax,rmin=rmin,rmax=rmax,position=position)
    plot.saveAs(canvasname,ext=exts)
    plot.close()
  
  file.Close()
  


def drawUpDownVariation(filename,dirname,samples,shifts,**kwargs):
  """Compare up/down variations of systematics, e.g. sample ZTT with it up and down variations for 'TES0.97'.
  One can add several backgrounds with the same systematics into one by passing e.g. 'ZTT+ZJ+ZL=DY'."""
  print '>>>\n>>> drawUpDownVariation("%s","%s")'%(filename,dirname)
  
  file    = TFile(filename,'READ')
  dir     = file.Get(dirname)
  tag     = kwargs.get('tag',     ""       )
  var0    = kwargs.get('var',     None     )
  xmin    = kwargs.get('xmin',    None     )
  xmax    = kwargs.get('xmax',    None     )
  outdir  = kwargs.get('outdir',  "shapes" )
  channel = kwargs.get('channel', "mutau"  )
  text    = kwargs.get('text',    ""       )
  ensureDirectory(outdir)
  if not isList(samples): samples = [samples]
  if not dir: print warning('drawUpDownVariation: did not find dir "%s"'%(dirname))
  
  for sample in samples:
    for shift in shifts:
      if not shift: continue
      if '$' in shift:
        shift = shift.replace('$CAT',dirname).replace('$CHANNEL',channel)
      print '>>>   sample "%s" for shift "%s"'%(sample, shift)
      
      skip = False
      matches = re.findall(r"(.+\+.+)=(.*)",sample) # e.g. "ZTT+ZJ+ZL=DY"
      if len(matches)==0:
        sampleUp = "%s_%sUp"%(sample,shift)
        sampleDn = "%s_%sDown"%(sample,shift)
        hist   = dir.Get(sample)
        histUp = dir.Get(sampleUp)
        histDn = dir.Get(sampleDn)
        if hist and not histUp and not histDn:
          print warning('drawUpDownVariation: did not find the variations "%s" or "%s" in directory "%s"'%(sampleUp,sampleDn,dir.GetName()),pre="   ")
          skip = True; continue
        names  = [ sampleUp, sample, sampleDn]
        hists  = [ histUp, hist, histDn ]
        for hist1, name in zip(hists,names):
          if not hist1:
            print warning('drawUpDownVariation: did not find "%s" in directory "%s"'%(name,dir.GetName()),pre="   ")
            skip = True; break
      else: # add samples
        hist, histUp, histDn = None, None, None
        sample = matches[0][1]
        for subsample in matches[0][0].split('+'):
          print '>>>     adding subsample "%s"'%(subsample)
          subsampleUp = "%s_%sUp"%(subsample,shift)
          subsampleDn = "%s_%sDown"%(subsample,shift)
          subhist     = dir.Get(subsample)
          subhistUp   = dir.Get(subsampleUp)
          subhistDn   = dir.Get(subsampleDn)
          subhists    = [ subhistUp, subhist, subhistDn ]
          subnames    = [ subsampleUp, subsample, subsampleDn ]
          for hist1, name in zip(subhists,subnames):
            if not hist1:
              print warning('drawUpDownVariation: did not find "%s" in directory "%s"'%(name,dir.GetName()),pre="   ")
              skip = True; break
          if skip: break
          if hist:   hist.Add(subhist)
          else:      hist = subhist
          if histUp: histUp.Add(subhistUp)
          else:      histUp = subhistUp
          if histDn: histDn.Add(subhistDn)
          else:      histDn = subhistDn
        hist.SetTitle(sample)
        histUp.SetTitle("%s_%sUp"%(sample,shift))
        histDn.SetTitle("%s_%sDown"%(sample,shift))
        hists  = [ histUp, hist, histDn ]
      if skip: continue
      
      var      = var0 or hist.GetXaxis().GetTitle()
      varname  = formatVariable(var)
      vartitle = variable_dict.get(var,var)
      tshift   = formatFilename(shift)
      nshift   = ('_'+tshift) if tshift else ""
      title    = formatCategory(sample,tshift)
      hist.SetTitle("nominal")
      histUp.SetTitle("up variation")
      histDn.SetTitle("down variation")
      canvasname = "%s/%s_%s_%s%s%s.png"%(outdir,sample.replace('_TES1.000','').replace('.','p'),varname,dirname,tag,nshift)
      exts       = ['pdf','png'] if args.pdf else ['png']
      
      plot = Plot(hists)
      plot.plot(vartitle,title=title,ratio=2,linestyle=False,xmin=xmin,xmax=xmax,errorbars=True,text=text)
      plot.saveAs(canvasname,ext=exts)
      plot.close()
  
  file.Close()

def formatFilename(filename):
    """Help function to format filename."""
    filename = re.sub(r"(?:_[em]t)?(?:_DM\d+)?_13TeV",'',filename)
    filename = filename.replace("CMS_",'').replace("ztt_",'').replace("_mt_13TeV",'').replace("_13TeV",'')
    return filename

def formatCategory(category,shift="",var="",channel=""):
    """Help function to format category."""
    if "TES" in category:
      category = category[:category.index('TES')].rstrip('_')+getShiftTitle(category)
    if category in category_dict:
      category = category_dict[category]
    else:
      for key in category_dict:
        if key in category:
          category = re.sub(key,category_dict[key],category)
    string = category.replace('-',' ')
    if 'emuCR' in category:
      string = "e#mu: "+string.replace("emuCR","")
    else:
      string = "#mu#tau: "+string
    if shift:
      string += " - %s"%formatFilename(shift).replace('_',' ').replace(" et"," e#tau").replace(" mt"," #mu#tau")
    if var:
      string += " %s"%(var)
    string = '{%s}'%(string)
    return string
    
def formatVariable(variable,shift=""):
    """Help function to format category."""
    if 'Up' in variable:
      variable = re.sub("_[^_-]+Up","",variable)
    elif 'Down' in variable:
      variable = re.sub("_[^_-]+Down","",variable)
    return variable
    
def getShiftTitle(string):
    """Help function to format title, e.g. '_TES0p970' -> '-3% TES'."""
    matches = re.findall(r"([a-zA-Z]+)(\d+[p\.]\d+)",string)
    if not matches: return ""
    if len(matches)>1:
      print warning('getShiftTitle: Found more than one match for shift: %s'%(matches))
    param, shift = matches[0]
    shift = float(shift.replace('p','.'))-1.
    if not shift: return "" #re.sub(r"_?[a-zA-Z]+\d+[p\.]\d+","",string)
    title = " %s%% %s"%(("%+.2f"%(100.0*shift)).rstrip('0').rstrip('.'),param)
    return title
    
def getDM(string):
    """Help function to get DM from string."""
    matches = re.findall(r"_?(DM\d+)",string)
    if not matches: return ""
    if len(matches)>1:
      print warning('getDM: Found more than one match for shift: %s'%(matches))
    return matches[0]
    
def ensureDirectory(dirname):
    """Make directory if it does not exist."""
    if not os.path.exists(dirname):
        os.makedirs(dirname)
        print ">>> made directory " + dirname
    return dirname
    
def xlimits(var,DM):
    xmin, xmax = None, None
    if "m_2" in var:
      xmin = 0.78 if DM=='DM10' else 0.78 if DM=='DM11' else 0.20
      xmax = 1.70 if DM=='DM10' else 1.60 if DM=='DM11' else 1.50
    elif "m_vis" in var:
      xmax = 140 if 'ZTT' in var else None
    elif "pt_2" in var:
      xmin, xmax = 10, 150
    return xmin, xmax
    


def main():
    print ""
    
    global sample_dict
    
    (minshift,maxshift,steps) = ( -0.060, 0.060, 0.01 )
    tesshifts = [ s*steps for s in xrange(int(minshift/steps),int(maxshift/steps)+1) ]
    testags   = [ ]
    tesvars   = [ ]
    tesvarssmall = [ 'TES0.998', 'TES1.000', 'TES1.002' ]
    for tes in tesshifts:
      nametag  = "_TES%.3f"%(1+tes)
      shifttag = getShiftTitle(nametag) #"" if tes==0 else " %s%% TES"%(("%+.2f"%(100.0*tes)).rstrip('0').rstrip('.'))
      sample_dict["ZTT"+nametag] = sample_dict['ZTT']+shifttag
      sample_dict["QCD"+nametag] = sample_dict['QCD']+shifttag
      variation_dict[nametag.replace('_','')] = shifttag
      if (tes*100)%1==0 and -0.04<tes<0.03: testags.append(nametag)
      if (tes*100)%3==0 and -0.04<tes<0.04: tesvars.append(nametag.replace('_',''))
    for nametag in ['_TES0.997','_TES0.998','_TES1.001','_TES1.003','_TES1.007']:
      shifttag = getShiftTitle(nametag)
      sample_dict["ZTT"+nametag] = sample_dict['ZTT']+shifttag
      sample_dict["QCD"+nametag] = sample_dict['QCD']+shifttag
    
    year        = args.year
    lumi        = 36.5 if year==2016 else 41.4 if year==2017 else 59.5
    era         = '%d-13TeV'%year
    indir       = "input_%d"%year
    outdir      = "shapes_%d"%year
    stackoutdir = "control_%d"%year
    tags        = args.tags
    analysis    = 'ztt'
    channels    = args.channels
    vars        = [ 'm_2', 'm_vis' ]
    DMs         = [ 'DM0', 'DM1', 'DM10', 'DM11' ]
    if args.observables: vars = args.observables
    if args.DMs:         DMs  = args.DMs
    doFR        = True and False
    
    GLOB.luminosity = lumi
    GLOB.era = year
    
    # SAMPLES
    shapesamples  = [
      'ZTT_TES1.000', 'TTT', 'TTL', 'TTJ', 'ST', 'ZJ', 'ZL', 'W', 'VV', 'QCD',
      #'ZTT_TES1.000', 'TTT', 'TTL', 'TTJ', 'STT', 'STJ', 'ZJ', 'ZL', 'W', 'VV', 'QCD_TES1.000',
    ]
    stacksamples  = [
      'ZTT_TES1.000', 'ZL', 'ZJ', 'TTT', 'TTL', 'TTJ', 'W', 'ST', 'VV', 'QCD', 'data_obs'
      #'ZTT_TES1.000', 'ZL', 'ZJ', 'TTT', 'TTL', 'TTJ', 'W', 'STT', 'STJ', 'VV', 'QCD_TES1.000', 'data_obs'
    ]
    extrastacksamples  = [
      ('_TES0p997',['ZTT_TES0.997', 'ZL', 'ZJ', 'TTT', 'STT', 'STJ', 'VV', 'data_obs', 'JTF']),
      ('_TES0p998',['ZTT_TES0.998', 'ZL', 'ZJ', 'TTT', 'STT', 'STJ', 'VV', 'data_obs', 'JTF']),
      ('_TES1p001',['ZTT_TES1.001', 'ZL', 'ZJ', 'TTT', 'STT', 'STJ', 'VV', 'data_obs', 'JTF']),
      ('_TES1p003',['ZTT_TES1.003', 'ZL', 'ZJ', 'TTT', 'STT', 'STJ', 'VV', 'data_obs', 'JTF']),
      ('_TES1p007',['ZTT_TES1.007', 'ZL', 'ZJ', 'TTT', 'STT', 'STJ', 'VV', 'data_obs', 'JTF']),
    ]
    grouplist = [ (['^TT*','ST*'],'TT','ttbar and single top'), ]
    stacksamples2 = [ s.replace('_TES1.000','') for s in stacksamples]
    shifts   = [ "",
       "shape_dy",
       "shape_tid",
       "shape_mTauFakeSF",
       "shape_mTauFake_$CAT",
       "shape_jTauFake_$CAT",
       ###"shape_m_mt",
       ###"shape_jes",
       ###"shape_jer",
       ###"shape_uncEn",
    ]
    if doFR:
      shapesamples.remove('QCD_TES1.000');  shapesamples.remove('W');  shapesamples.remove('ZJ');  shapesamples.append('JTF')
      stacksamples.remove('QCD_TES1.000');  stacksamples.remove('W');  stacksamples.remove('ZJ');  stacksamples.append('JTF')
      stacksamples2.remove('QCD'); stacksamples2.remove('W'); stacksamples2.remove('ZJ'); stacksamples2.append('JTF');
    
    if args.postfit and args.filename and args.dirnames:
      tag = tags[0]
      for dirname in args.dirnames:
        xmin, xmax = xlimits(args.filename,dirname)
        app_dict   = {'ZTT':getShiftTitle(tag)}
        DM         = getDM(args.filename) #dirname
        var        = 'm_vis' if 'm_vis' in args.filename else 'm_2'
        position   = 'x=0.58' if var=='m_vis' else 'x=0.63' if DM=='DM10' else 'x=0.06' if DM=='DM11' else 'x=0.60'
        outdir     = args.outdirname if args.outdirname else "postfit_%d"%year
        drawPrePostFit(args.filename,dirname,stacksamples2,year=year,xmin=xmin,xmax=xmax,position=position,
                       var=var,
                       apptitle=app_dict,tag=tag,outdir=outdir,group=grouplist)
    else:
      for tag in tags:
        for channel in channels:
          ###shifts = [s.replace('$CHANNEL',channel) for s in shifts0]
          for var in vars:
            if "_0p"  in tag and var=='m_vis': continue
            if "_45"  in tag and var=='m_2':   continue
            if "_85"  in tag and var=='m_2':   continue
            if "_100" in tag and var=='m_2':   continue
            if "_200" in tag and var=='m_2':   continue
            filename = "%s/%s_%s_tes_%s.inputs-%s%s.root"%(indir,analysis,channel,var,era,tag)
            #filename = "%s/%s_%s_%s%s.input-%s.root"%(indir,analysis,channel,var,tag,era)
            for DM in DMs:
              if DM=='DM0' and 'm_2' in var: continue
              if DM=='DM11' and "newDM" not in tag and "DeepTau" not in tag: continue
              xmin, xmax = xlimits(var+tag,DM)
              position = 'x=0.08' if DM=='DM11' and var=='m_2' else 'x=0.68'
              drawUpDownVariation(filename,DM,shapesamples,shifts,outdir=outdir,xmin=xmin,xmax=xmax,tag=tag,text=DM,position=position)
              #for extratag, stacklist in extrastacksamples:
              #  drawStacks(filename,DM,stacklist,[""],xmin=xmin,xmax=xmax,tag=tag+extratag,group=grouplist)
              for nametag in testags:
                samples = [ re.sub('ZTT_TES.*','ZTT%s'%nametag,s) for s in stacksamples ]
                testag = tag+nametag.replace('.','p')
                drawStacks(filename,DM,samples,outdir=stackoutdir,xmin=xmin,xmax=xmax,tag=testag,group=grouplist)
              drawVariations(filename,DM,'ZTT',tesvars,outdir=outdir,xmin=xmin,xmax=xmax,tag=tag,position=position)
              drawVariations(filename,DM,'ZTT',tesvarssmall,outdir=outdir,xmin=xmin,xmax=xmax,rmin=0.92,rmax=1.08,tag=tag,position=position)      
    
    print ">>>\n>>> done\n"
    
    
    
    
    
if __name__ == '__main__':
    main()




