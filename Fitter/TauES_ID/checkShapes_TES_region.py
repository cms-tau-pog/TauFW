#! /usr/bin/env python

import os, sys, re
from TauFW.Plotter.sample.utils import CMSStyle, setera
from TauFW.Plotter.plot.utils import LOG, grouphists
from TauFW.Plotter.plot.Stack import Stack
from TauFW.Plotter.plot.Plot import Plot
from TauFW.common.tools.utils import islist, ensurelist, repkey
from TauFW.common.tools.file import ensuredir, ensureTFile
from TauFW.common.tools.log import color, warning, error
from TauFW.Fitter.plot.datacard import plotinputs
import TauFW.Plotter.sample.SampleStyle as STYLE
import ROOT
from ROOT import TFile, TTree, kAzure, kRed, kGreen, kOrange, kMagenta, kYellow
ROOT.gROOT.SetBatch(ROOT.kTRUE)
import yaml

# CMS style
CMSStyle.setTDRStyle()

colors = [ kAzure+5, kRed+1, kGreen+2, kOrange+1, kMagenta-4, kYellow+1 ]



def drawpostfit(setup, fname,region,procs,**kwargs):
  """Plot pre- and post-fit plots PostFitShapesFromWorkspace."""
  print '>>>\n>>> drawpostfit("%s","%s")'%(fname,region)
  outdir    = kwargs.get('outdir',  ""         )
  pname     = kwargs.get('pname',   "$FIT.root" ) # replace $FIT = 'prefit', 'postfit'
  ratio     = kwargs.get('ratio',   True       )
  tag       = kwargs.get('tag',     ""         )
  xtitle    = kwargs.get('xtitle',  None       )
  var       = kwargs.get('var',     None       )
  title     = kwargs.get('title',   None       )
  text      = kwargs.get('text',    ""         )
  tsize     = kwargs.get('tsize',   0.045      )
  xmin      = kwargs.get('xmin',    None       )
  xmax      = kwargs.get('xmax',    None       )
  ymargin   = kwargs.get('ymargin', 1.22       )
  groups    = kwargs.get('group',   [ ]        )
  position  = kwargs.get('pos',     None       ) # legend position
  ncol      = kwargs.get('ncol',    None       ) # legend columns
  square    = kwargs.get('square',  False      )
  era       = kwargs.get('era',     ""         )
  ymax      = None
  fits      = ['prefit','postfit']
  file      = ensureTFile(fname,'READ')
  if outdir:
    ensuredir(outdir)
  if era:
    setera(era)
  
  # DRAW PRE-/POST-FIT
  for fit in fits:
    fitdirname = "%s_%s"%(region,fit)
    dir = file.Get(fitdirname)
    if not dir:
      LOG.warning('drawpostfit: Did not find dir "%s"'%(fitdirname),pre="   ")
      return
    obshist = None
    exphists = [ ]
    
    # GET HIST
    for proc in procs: #reversed(samples):
      hname = "%s/%s"%(fitdirname,proc)
      hist  = file.Get(hname)
      if not hist:
        LOG.warning('drawpostfit: Could not find "%s" template in directory "%s_%s"'%(proc,region,fit),pre="   ")
        continue
      if 'data_obs' in proc:
        obshist = hist
        hist.SetLineColor(1)
        ymax = hist.GetMaximum()*ymargin
      else:
        exphists.append(hist)
      if proc in STYLE.sample_titles:
        hist.SetTitle(STYLE.sample_titles[proc])
      if proc in STYLE.sample_colors:
        hist.SetFillStyle(1001)
        hist.SetFillColor(STYLE.sample_colors[proc])
    if len(exphists)==0:
      LOG.warning('drawpostfit: Could not find any templates in directory "%s"'%(region),pre="   ")
      continue
    if not obshist:
      LOG.warning('drawpostfit: Could not find a data template in directory "%s"'%(region),pre="   ")
      continue
    for groupargs in groups:
      grouphists(exphists,*groupargs,replace=True)
    
    # PLOT
    xtitle     = (xtitle or exphists[0].GetXaxis().GetTitle()) #.replace('[GeV]','(GeV)')
    varname    = formatVariable(var)
    position   = position if position else "x=0.67" if 'post' in fit else "x=0.66"
    title      = setup["tesRegions"][region]["title"] if "title" in setup["tesRegions"][region] else ""
    xmax       = xmax or exphists[0].GetXaxis().GetXmax()
    xmin       = xmin or exphists[0].GetXaxis().GetXmin()
    errtitle   = "Pre-fit stat. + syst. unc." if fit=='prefit' else "Post-fit unc."
    canvasname = "%s_%s%s_%s.root"%(varname,region,tag,fit)
    exts       = ['pdf','root'] if args.pdf else ['root']
    pname_     = repkey(pname,FIT=fit,ERA=era)
    rmin, rmax = (0.28,1.52)
    plot = Stack(xtitle,obshist,exphists)
    plot.draw(xmin=xmin,xmax=xmax,ymax=ymax,square=square,ratio=ratio,rmin=rmin,rmax=rmax,
              staterror=True,errtitle=errtitle)
    plot.drawlegend(position,tsize=tsize,text=text,ncol=ncol)
    if title:
      plot.drawtext(title,bold=False)
    plot.saveas(canvasname,outdir=outdir,ext=exts)
    plot.close()
  
  file.Close()

 

def drawVariations(setup, filename,dirname,samples,variations,**kwargs):
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
  outdir   = kwargs.get('outdir',   "../plots/shapes" )
  position = kwargs.get('position', 'right'  )
  text     = kwargs.get('text',     ""       )
  if not islist(samples): samples = [samples]
  if not dir: print warning('drawVariations: did not find dir "%s"'%(dirname))
  ensureDirectory(outdir)
  ratio = True

  #print(samples)
  
  for sample in samples:
    hists = [ ]
    ratio  = int(len(variations)/2)
    for i, variation in enumerate(variations):
      #print '>>>   sample "%s" for shift "%s"'%(sample, shift)
      name = "%s_%s"%(sample,variation.lstrip('_'))
      print(name)
      print(dir)
      print(sample)
      hist = dir.Get(name)
      print(hist)
      if not hist:
        print warning('drawVariations: did not find "%s" in directory "%s"'%(name,dir.GetName()),pre="   ")
        continue
      sampletitle = sample
      sampletitle += getShiftTitle(variation)
      hist.SetTitle(sampletitle)
      if sample==sampletitle or "nom" in sampletitle.lower(): ratio = i+1
      hists.append(hist)
    
    if len(hists)!=len(variations):
      print warning('drawVariations: number of hists (%d) != number variations (%d)'%(len(hists),len(variations)),pre="   ")
    
    var      = var0 or hists[0].GetXaxis().GetTitle()
    varname  = formatVariable(var)
    vartitle = setup["observables"][varname]["title"]
    shift0   = formatFilename(variations[0])
    shift1   = formatFilename(variations[-1])
    shift    = ""; i=0
    for i, letter in enumerate(shift0):
      if i>=len(shift1): break
      if letter==shift1[i]: shift+=shift0[i]
      else: break
    nshift = "_%s-%s"%(shift0,shift1.replace(shift,""))
    title      = setup["tesRegions"]["title"] if "title" in setup["tesRegions"] else ""
    canvasname = "%s/%s_%s_%s%s%s.root"%(outdir,sample,varname,dirname,tag,nshift.replace('.','p'))
    exts       = ['pdf','root'] if args.pdf else ['root']
    
    plot = Plot(hists)
    plot.draw(vartitle,ratio=ratio,linestyle=False,xmin=xmin,xmax=xmax,rmin=rmin,rmax=rmax)
    plot.drawlegend(position,title=title)
    plot.drawtext(text)
    plot.saveas(canvasname,ext=exts)
    plot.close()
  
  file.Close()
  


def drawUpDownVariation(setup, filename,dirname,samples,shifts,**kwargs):
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
  channel = kwargs.get('channel', "mt"  )
  text    = kwargs.get('text',    ""       )
  ensureDirectory(outdir)
  if not islist(samples): samples = [samples]
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
      vartitle = setup["observables"][varname]["title"]
      tshift   = formatFilename(shift)
      nshift   = ('_'+tshift) if tshift else ""
      title      = setup["regions"][shift]["title"] if (shift in setup["regions"] and "title" in setup["regions"][shift]) else ""
      hist.SetTitle("nominal")
      histUp.SetTitle("up variation")
      histDn.SetTitle("down variation")
      canvasname = "%s/%s_%s_%s%s%s.root"%(outdir,sample.replace('_TES1.000','').replace('.','p'),varname,dirname,tag,nshift)
      exts       = ['pdf','root'] if args.pdf else ['root']
      
      plot = Plot(hists)
      plot.draw(vartitle,title=title,ratio=2,linestyle=False,xmin=xmin,xmax=xmax,errorbars=True,text=text)
      plot.saveas(canvasname,ext=exts)
      plot.close()
  
  file.Close()

def formatFilename(filename):
    """Help function to format filename."""
    filename = re.sub(r"(?:_[em]t)?(?:_DM\d+)?_13TeV",'',filename)
    filename = filename.replace("CMS_",'').replace("ztt_",'').replace("_mt_13TeV",'').replace("_13TeV",'')   
    return filename

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

def ensureDirectory(dirname):
    """Make directory if it does not exist."""
    if not os.path.exists(dirname):
        os.makedirs(dirname)
        print ">>> made directory " + dirname
    return dirname
    
    


def main(args):
    print ""
    
    print "Using configuration file: %s"%args.config
    with open(args.config, 'r') as file:
      setup = yaml.safe_load(file)

    channel = setup["channel"].replace("mu","m").replace("tau","t")

    tesshifts = setup["TESvariations"]["values"]
    testags   = [ ]
    tesvars   = [ ]
    tesvarssmall = ['_TES0.982','_TES0.986','_TES0.990','_TES0.994','_TES0.998']

    for tes in tesshifts:
      nametag  = "_TES%.3f"%(1+tes)
      shifttag = getShiftTitle(nametag) #"" if tes==0 else " %s%% TES"%(("%+.2f"%(100.0*tes)).rstrip('0').rstrip('.'))
      STYLE.sample_titles["ZTT"+nametag] = STYLE.sample_titles['ZTT']+shifttag
      STYLE.sample_titles["QCD"+nametag] = STYLE.sample_titles['QCD']+shifttag
      if (tes*100)%1==0 and -0.04<tes-1<0.03: testags.append(nametag)
      if (tes*100)%3==0 and -0.04<tes-1<0.04: tesvars.append(nametag.replace('_',''))
    for nametag in ['_TES0.996','_TES0.998','_TES1.002','_TES1.004','_TES1.006']:
      shifttag = getShiftTitle(nametag)
      STYLE.sample_titles["ZTT"+nametag] = STYLE.sample_titles['ZTT']+shifttag
#      STYLE.sample_titles["QCD"+nametag] = STYLE.sample_titles['QCD']+shifttag
    
    year        = args.year
    lumi        = 36.5 if year=='2016' else 41.4 if (year=='2017' or year=='UL2017') else 59.5 if (year=='2018' or year=='UL2018') else 19.5 if year=='UL2016_preVFP' else 16.8
    era         = '%s-13TeV'%year
    indir       = "input"
    outdir      = "../plots/shapes_%s"%year
    stackoutdir = "control_%s"%year
    analysis    = 'ztt'

    vars = []
    for obs in setup["observables"]:
      vars.append(obs)

    CMSStyle.setCMSEra(year)   
    
    # SAMPLES
    shapesamples  = setup["processes"]
    shapesamples.remove("data_obs")
    stacksamples  = setup["processes"]
    extrastacksamples  = [
      ('_TES0p997',['ZTT_TES0.997']+stacksamples),
      ('_TES0p998',['ZTT_TES0.998']+stacksamples),
      ('_TES1p001',['ZTT_TES1.001']+stacksamples),
      ('_TES1p003',['ZTT_TES1.003']+stacksamples),
      ('_TES1p007',['ZTT_TES1.007']+stacksamples),
    ]
    #grouplist = [ (['^TT*','ST*'],'TT','ttbar and single top'), ]
    grouplist = []

    shifts   = [ "",
       "shape_dy",
       "shape_tid"
      #  "shape_mTauFakeSF",
      #  "shape_mTauFake_$CAT",
      #  "shape_jTauFake_$CAT",
    ]
    
    if args.postfit and args.filename and args.dirnames:
      for dirname in args.dirnames:
        xmin, xmax = xlimits(args.filename,dirname)
        app_dict   = {'ZTT':getShiftTitle(tag)}
        region         = getregion(args.filename) #dirname
        var = 'm_vis'
        for v in vars:
          if v in args.filename:
            var = v

        outdir     = args.outdirname if args.outdirname else "postfit_%s"%year
        drawpostfit(setup, args.filename,dirname,stacksamples2,year=year,xmin=xmin,xmax=xmax,pos='x=0.6', var=var, apptitle=app_dict,tag=tag,outdir=outdir,group=grouplist)

    else:
      tag = setup["tag"] if "tag" in setup else ""
      for var in vars:
        print var
        filename = "%s/%s_%s_tes_%s.inputs-%s%s.root"%(indir,analysis,channel,var,era,tag)
        for region in setup["observables"][var]["fitRegions"]:
          print region
          xmin = setup["observables"][var]["binning"][1]
          xmax = setup["observables"][var]["binning"][2]
          #drawUpDownVariation(setup, filename,region,shapesamples,shifts,outdir=outdir,xmin=xmin,xmax=xmax,tag=tag,text=region,position='x=0.68',var=var)
          for nametag in testags:
            samples = [ re.sub('ZTT_TES.*','ZTT%s'%nametag,s) for s in stacksamples ]
            testag = tag+nametag.replace('.','p')
            #drawVariations(setup, filename,region,'ZTT',tesvars,outdir=outdir,xmin=xmin,xmax=xmax,tag=tag,position='x=0.68',var=var)
            drawVariations(setup, filename,region,'ZTT',tesvarssmall,outdir=outdir,xmin=xmin,xmax=xmax,rmin=0.92,rmax=1.08,tag=tag,position='x=0.68',var=var)
    
    print ">>>\n>>> done\n"
    
    
    
    
    
if __name__ == '__main__':
  from argparse import ArgumentParser
  argv = sys.argv
  description = '''This script makes shape variations from input root files for datacards.'''
  parser = ArgumentParser(prog="checkshapes_TES",description=description,epilog="Succes!")
  parser.add_argument('filename', type=str, nargs='?', action='store', metavar='FILENAME', help="file with shapes" ),
  parser.add_argument('-y', '--year',        dest='year', choices=['2016','2017','2018','UL2016_preVFP','UL2016_postVFP','UL2017','UL2018'], type=str, default='2018', action='store', help="select year")
  parser.add_argument('-c', '--config', dest='config', type=str, default='TauES/config/defaultFitSetupTES_mutau.yml', action='store', help="set config file containing sample & fit setup" )
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
  main(args)
  print "\n>>> Done."





