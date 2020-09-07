#! /usr/bin/env python
# Author: Izaak Neutelings (January 2019)
# https://twiki.cern.ch/twiki/bin/viewauth/CMS/PdmV2017Analysis
# https://twiki.cern.ch/twiki/bin/viewauth/CMS/PdmV2018Analysis
# https://twiki.cern.ch/twiki/bin/view/CMS/TWikiLUM#PileupInformation
import os, sys, re, shutil, json
from argparse import ArgumentParser
import ROOT; ROOT.PyConfig.IgnoreCommandLineOptions = True
from TauFW.common.tools.file import ensuredir, ensureTFile, gethist
from TauFW.common.tools.utils import repkey, getyear
from TauFW.PicoProducer import datadir
from TauFW.Plotter.plot.Plot import Plot, CMSStyle, deletehist
from ROOT import gROOT, gDirectory, gStyle, gPad, TFile, TTree, TCanvas, TH1, TH1F, TLine, TLegend,\
                 kBlack, kRed, kAzure, kGreen, kOrange, kMagenta, kYellow
#gROOT.SetBatch(True)
#gStyle.SetOptStat(False)
#gStyle.SetOptTitle(False)
linecolors = [ kRed+1, kAzure+5, kGreen+2, kOrange+1, kMagenta-4, kYellow+1,
               kRed-9, kAzure-4, kGreen-2, kOrange+6, kMagenta+3, kYellow+2, ]
argv = sys.argv
description = '''This script makes pileup profiles for MC and data.'''
parser = ArgumentParser(prog="pileup",description=description,epilog="Succes!")
parser.add_argument('-y', '-e', '--era', dest='eras', nargs='+',
                    metavar='ERA',       help="select era" )
parser.add_argument('-c', '--channel',   dest='channel', default='mutau',
                                         help="select channel" )
parser.add_argument('-t', '--type',      dest='types', choices=['data','mc','flat'], type=str, nargs='+', default=['data','mc'],
                                         help="make profile for data and/or MC" )
parser.add_argument('-P', '--period',    dest='periods', type=str, nargs='+', default=[ ],
                                         help="make data profiles for given data taking period (e.g. B, BCD, GH, ...)" )
parser.add_argument('-p', '--plot',      dest='plot', default=False, action='store_true', 
                                         help="plot profiles" )
parser.add_argument('-v', '--verbose',   dest='verbosity', type=int, nargs='?', const=1, default=0,
                                         help="set verbosity" )
args = parser.parse_args()


def getMCProfile(outfname,samples,channel,era,tag=""):
  """Get pileup profile in MC by adding Pileup_nTrueInt histograms from a given list of samples."""
  print '>>> getMCProfile("%s")'%(outfname)
  nprofiles = 0
  histname  = 'pileup'
  tothist   = None
  for sample, infname in samples:
    print ">>>   %s"%(infname)
    file, hist = gethist(infname,histname,retfile=True)
    if not file:
      print ">>> Did not find %s..."%(infname)
      continue
    if not hist:
      print ">>> Did not find %s:%r..."%(infname,histname)
      continue
    if tothist==None:
      tothist = hist.Clone('pileup')
      tothist.SetTitle('pileup')
      #tothist.SetTitle('MC average')
      tothist.SetDirectory(0)
      nprofiles += 1
    else:
      tothist.Add(hist)
      nprofiles += 1
    file.Close()
  print ">>>   added %d MC profiles, %d entries, %.1f mean"%(nprofiles,tothist.GetEntries(),tothist.GetMean())
  
  file = TFile(outfname,'RECREATE')
  tothist.Write('pileup')
  tothist.SetDirectory(0)
  file.Close()
  
  return tothist
  

def getDataProfile(outfname,JSON,pileup,bins,era,minbias,local=False):
  """Get pileup profile in data with pileupCalc.py tool."""
  print '>>> getDataProfile("%s",%d,%s)'%(outfname,bins,minbias)
  
  # CREATE profile
  if local:
    JSON   = copy2local(JSON)
    pileup = copy2local(pileup)
    command = "./pileupCalc.py -i %s --inputLumiJSON %s --calcMode true --maxPileupBin %d --numPileupBins %d --minBiasXsec %d %s --verbose"%(JSON,pileup,bins,bins,minbias*1000,outfname)
  else:
    command = "pileupCalc.py -i %s --inputLumiJSON %s --calcMode true --maxPileupBin %d --numPileupBins %d --minBiasXsec %d %s"%(JSON,pileup,bins,bins,minbias*1000,outfname)
  print ">>>   executing command (this may take a while):"
  print ">>>   " + command
  os.system(command)
  
  # GET profile
  histname = 'pileup'
  if not os.path.isfile(outfname):
    print ">>>   Warning! getDataProfile: Could find output file %s!"%(outfname)
    return
  file, hist = gethist(outfname,histname,retfile=True)
  hist.SetName("%s_%s"%(histname,str(minbias).replace('.','p')))
  hist.SetTitle("Data %s, %.1f pb"%(era,minbias))
  hist.SetDirectory(0)
  bin0 = 100.0*hist.GetBinContent(0)/hist.Integral()
  bin1 = 100.0*hist.GetBinContent(1)/hist.Integral()
  if bin0>0.01 or bin1>0.01:
    print ">>>   Warning! First to bins have %.2f%% (0) and %.2f%% (1)"%(bin0,bin1)
    hist.SetBinContent(0,0.0)
    hist.SetBinContent(1,0.0)
  print ">>>   pileup profile in data with min. bias %s mb has a mean of %.1f"%(minbias,hist.GetMean())
  file.Close()
  
  return hist
  

def getGenProfile(outfname,era):
  """Create generator pileup profile."""
  print ">>> getGenProfile(%s):"%(era)
  if era=='2016':
    bins = [
      # https://github.com/cms-sw/cmssw/blob/CMSSW_9_4_X/SimGeneral/MixingModule/python/mix_2016_25ns_Moriond17MC_PoissonOOTPU_cfi.py
      1.78653e-05, 2.56602e-05, 5.27857e-05, 8.88954e-05, 0.000109362,
      0.000140973, 0.000240998, 0.00071209,  0.00130121,  0.00245255, 
      0.00502589,  0.00919534,  0.0146697,   0.0204126,   0.0267586,
      0.0337697,   0.0401478,   0.0450159,   0.0490577,   0.0524855,
      0.0548159,   0.0559937,   0.0554468,   0.0537687,   0.0512055,
      0.0476713,   0.0435312,   0.0393107,   0.0349812,   0.0307413,
      0.0272425,   0.0237115,   0.0208329,   0.0182459,   0.0160712,
      0.0142498,   0.012804,    0.011571,    0.010547,    0.00959489,
      0.00891718,  0.00829292,  0.0076195,   0.0069806,   0.0062025,
      0.00546581,  0.00484127,  0.00407168,  0.00337681,  0.00269893,
      0.00212473,  0.00160208,  0.00117884,  0.000859662, 0.000569085,
      0.000365431, 0.000243565, 0.00015688,  9.88128e-05, 6.53783e-05,
      3.73924e-05, 2.61382e-05, 2.0307e-05,  1.73032e-05, 1.435e-05,
      1.36486e-05, 1.35555e-05, 1.37491e-05, 1.34255e-05, 1.33987e-05,
      1.34061e-05, 1.34211e-05, 1.34177e-05, 1.32959e-05, 1.33287e-05,
      0.0, 0.0, 0.0, 0.0,
      0.0, 0.0, 0.0, 0.0,
      0.0, 0.0, 0.0, 0.0,
      0.0, 0.0, 0.0, 0.0,
      0.0, 0.0, 0.0, 0.0,
    ]
  elif era=='2017':
    # https://github.com/cms-sw/cmssw/blob/CMSSW_9_4_X/SimGeneral/MixingModule/python/mix_2017_25ns_WinterMC_PUScenarioV1_PoissonOOTPU_cfi.py
    bins = [
      3.39597497605e-05, 6.63688402133e-06, 1.39533611284e-05, 3.64963078209e-05, 6.00872171664e-05, 9.33932578027e-05,
      0.000120591524486, 0.000128694546198, 0.000361697233219, 0.000361796847553, 0.000702474896113, 0.00133766053707,
      0.00237817050805,  0.00389825605651,  0.00594546732588,  0.00856825906255,  0.0116627396044,   0.0148793350787, 
      0.0179897368379,   0.0208723871946,   0.0232564170641,   0.0249826433945,   0.0262245860346,   0.0272704617569,
      0.0283301107549,   0.0294006137386,   0.0303026836965,   0.0309692426278,   0.0308818046328,   0.0310566806228,
      0.0309692426278,   0.0310566806228,   0.0310566806228,   0.0310566806228,   0.0307696426944,   0.0300103336052,
      0.0288355370103,   0.0273233309106,   0.0264343533951,   0.0255453758796,   0.0235877272306,   0.0215627588047,
      0.0195825559393,   0.0177296309658,   0.0160560731931,   0.0146022004183,   0.0134080690078,   0.0129586991411,
      0.0125093292745,   0.0124360740539,   0.0123547104433,   0.0123953922486,   0.0124360740539,   0.0124360740539,
      0.0123547104433,   0.0124360740539,   0.0123387597772,   0.0122414455005,   0.011705203844,    0.0108187105305,
      0.00963985508986,  0.00827210065136,  0.00683770076341,  0.00545237697118,  0.00420456901556,  0.00367513566191,
      0.00314570230825,  0.0022917978982,   0.00163221454973,  0.00114065309494,  0.000784838366118, 0.000533204105387,
      0.000358474034915, 0.000238881117601, 0.0001984254989,   0.000157969880198, 0.00010375646169,  6.77366175538e-05,
      4.39850477645e-05, 2.84298066026e-05, 1.83041729561e-05, 1.17473542058e-05, 7.51982735129e-06, 6.16160108867e-06,
      4.80337482605e-06, 3.06235473369e-06, 1.94863396999e-06, 1.23726800704e-06, 7.83538083774e-07, 4.94602064224e-07,
      3.10989480331e-07, 1.94628487765e-07, 1.57888581037e-07, 1.2114867431e-07,  7.49518929908e-08, 4.6060444984e-08,
      2.81008884326e-08, 1.70121486128e-08, 1.02159894812e-08, 0.0,               #0.0,
    ]
  elif era=='2018':
    # https://github.com/cms-sw/cmssw/blob/CMSSW_10_4_X/SimGeneral/MixingModule/python/mix_2018_25ns_JuneProjectionFull18_PoissonOOTPU_cfi.py
    bins = [
        4.695341e-10, 1.206213e-06, 1.162593e-06, 6.118058e-06, 1.626767e-05,
        3.508135e-05, 7.12608e-05,  0.0001400641, 0.0002663403, 0.0004867473,
        0.0008469,    0.001394142,  0.002169081,  0.003198514,  0.004491138,
        0.006036423,  0.007806509,  0.00976048,   0.0118498,    0.01402411,
        0.01623639,   0.01844593,   0.02061956,   0.02273221,   0.02476554,
        0.02670494,   0.02853662,   0.03024538,   0.03181323,   0.03321895,
        0.03443884,   0.035448,     0.03622242,   0.03674106,   0.0369877,
        0.03695224,   0.03663157,   0.03602986,   0.03515857,   0.03403612,
        0.0326868,    0.03113936,   0.02942582,   0.02757999,   0.02563551,
        0.02362497,   0.02158003,   0.01953143,   0.01750863,   0.01553934,
        0.01364905,   0.01186035,   0.01019246,   0.008660705,  0.007275915,
        0.006043917,  0.004965276,  0.004035611,  0.003246373,  0.002585932,
        0.002040746,  0.001596402,  0.001238498,  0.0009533139, 0.0007282885,
        0.000552306,  0.0004158005, 0.0003107302, 0.0002304612, 0.0001696012,
        0.0001238161, 8.96531e-05,  6.438087e-05, 4.585302e-05, 3.23949e-05,
        2.271048e-05, 1.580622e-05, 1.09286e-05,  7.512748e-06, 5.140304e-06,
        3.505254e-06, 2.386437e-06, 1.625859e-06, 1.111865e-06, 7.663272e-07,
        5.350694e-07, 3.808318e-07, 2.781785e-07, 2.098661e-07, 1.642811e-07,
        1.312835e-07, 1.081326e-07, 9.141993e-08, 7.890983e-08, 6.91468e-08,
        6.119019e-08, 5.443693e-08, 4.85036e-08,  4.31486e-08,  3.822112e-08
    ]
  else:
    print ">>>   Warning! No generator pileup profile for era %s"%(era)
  
  nbins = len(bins)
  hist  = TH1F('pileup','pileup',nbins,0,nbins)
  hist.Sumw2()
  for i, binc in enumerate(bins,1):
    hist.SetBinContent(i,binc)
  
  file = ensureTFile(outfname,'RECREATE')
  hist.Write('pileup')
  hist.SetDirectory(0)
  file.Close()
  return hist
  

def getFlatProfile(outfname,max=75,nbins=100,xmin=0,xmax=100):
  """Create flat profile."""
  print ">>> getFlatProfile()"
  hist = TH1F('pileup','pileup',nbins,xmin,xmax)
  hist.Sumw2()
  binc = 1./max
  for i in xrange(1,max+1):
    hist.SetBinContent(i,binc)
  hist.Scale(1./hist.Integral())
  file = TFile(outfname,'RECREATE')
  hist.Write('pileup')
  hist.SetDirectory(0)
  file.Close()
  return hist
  

def compareMCProfiles(samples,channel,era,tag=""):
  """Compare MC profiles."""
  print ">>> compareMCProfiles()"
  
  hname   = 'pileup'
  htitle  = 'MC average'
  outdir  = ensuredir("plots")
  avehist = None
  hists   = [ ]
  if tag and tag[0]!='_':
    tag = '_'+tag
  if 'pmx' in tag:
    htitle += " %s pre-mixing"%("old" if "old" in tag else "new")
  
  # GET histograms
  for sample, fname in samples:
    print ">>>   %s"%(fname)
    file, hist = gethist(fname,hname,retfile=True)
    hist.SetName(sample)
    hist.SetTitle(sample)
    hist.SetDirectory(0)
    if avehist==None:
      avehist = hist.Clone('average%s'%tag)
      avehist.SetTitle(htitle)
      avehist.SetDirectory(0)
    else:
      avehist.Add(hist)
    hist.Scale(1./hist.Integral())
    hists.append(hist)
    file.Close()
  
  # PLOT
  hists  = [avehist]+hists
  colors = [kBlack]+linecolors
  avehist.Scale(1./avehist.Integral())
  pname  = "%s/pileup_MC_%s%s"%(outdir,era,tag)
  xtitle = "Number of true interactions"
  plot   = Plot(hists,ratio=True)
  plot.draw(xtitle=xtitle,ytitle="A.U.",rtitle="MC / Ave.",
            textsize=0.032,rmin=0.45,rmax=1.55,denom=2,colors=colors)
  plot.drawlegend('TTR',tsize=0.04,latex=False)
  plot.saveas(pname+".png")
  plot.saveas(pname+".pdf")
  plot.close(keep=True)
  for hist in hists: # clean memory
    if hist==avehist:
      continue
    if hist.GetDirectory():
      gDirectory.Delete(hist.GetName())
    else:
      hist.Delete()
  
  return avehist
  

def compareDataMCProfiles(datahist,mchist,era,minbias,tag="",rmin=0.75,rmax=1.25):
  """Compare data/MC profiles."""
  print ">>> compareDataMCProfiles()"
  mctitle = "MC average"
  outdir  = ensuredir("plots")
  hists   = [datahist,mchist]
  colors  = [kBlack]+linecolors
  width   = 0.36 if 'pmx' in tag else 0.26
  if isinstance(era,str) and "Run" in era:
    width =  max(width,0.26+(len(era)-5)*0.02)
  if tag and tag[0]!='_':
    tag = '_'+tag
  if 'pmx' in tag:
    mctitle += " (%s pre-mixing)"%("old" if "old" in tag else "new")
  
  datahist.SetTitle("Data %s, %.1f pb"%(era,minbias))
  mchist.SetTitle(mctitle)
  datahist.Scale(1./datahist.Integral())
  mchist.Scale(1./mchist.Integral())
  
  xtitle = "Number of interactions"
  pname  = "%s/pileup_Data-MC_%s_%s%s"%(outdir,era,str(minbias).replace('.','p'),tag)
  plot   = Plot(hists,ratio=True)
  plot.draw(xtitle=xtitle,ytitle="A.U.",rtitle="Data / MC",
            textsize=0.045,rmin=rmin,rmax=rmax,denom=2,colors=colors)
  plot.drawlegend('TCR',width=width)
  plot.saveas(pname+".png")
  plot.saveas(pname+".pdf")
  plot.close(keep=True)
  deletehist(datahist) # clean memory
  

def filterJSONByRunNumberRange(jsoninname,jsonoutname,start,end,verb=0):
  """Split a given JSON file by start and end run number."""
  print ">>> filterJSONByRunNumberRange: %s %s - %s"%(jsonoutname,start,end)
  
  # READ JSON IN
  with open(jsoninname,'r') as jsonin:
    data = json.load(jsonin)
  
  # FILTER run number range
  nkeep = 0
  ndrop = 0
  for element in sorted(data.keys()):
    if element.isdigit():
      runnumber = int(element)
      if runnumber<start or runnumber>end:
        ndrop += 1
        if verb>=1: print "  dropping %s"%runnumber
        del data[element]
      else:
        nkeep += 1
        if verb>=1: print "  keeping %s"%runnumber
    else:
      print "Warning! filterJSONByRunNumberRange: element is not an integer (run number): '%s'"%element
  
  # WRITE JSON OUT
  with open(jsonoutname,'w') as jsonout:
    data = json.dump(data,jsonout,sort_keys=True)
  
  # SUMMARY
  print ">>>   saved %s / %s run numbers"%(nkeep,nkeep+ndrop)
  
  return jsonoutname
  

def cleanEras(eras):
  """Clean up eras."""
  if not eras: return eras
  for i, era in enumerate(eras):
    era = era.upper()
    assert all(s in 'ABCDEFGH' for s in era), "Did not recognize era '%s'!"%era
    eras[i] = ''.join(sorted(era))
  return eras
  

def getPeriodRunNumbers(era,datasets):
  """Get runnumbers for an period (e.g. 'B', 'BCD' or 'GH')."""
  start  = -1
  end    = -1
  for set in era:
    assert set in datasets, "Dataset '%s' not in list %s"%(set,datasets)
    setstart, setend = datasets[set]
    if start<0 or end<0:
      start, end = setstart, setend
      continue
    if setstart<start:
      start = setstart
    if setend>end:
      end = setend
  assert start>0 and end>0, "Invalid runnumbers %s to %s"%(start,end)
  return start, end


def copy2local(filename):
  """Copy file to current directory, and return new name."""
  fileold = filename
  assert os.path.isfile(fileold), "Copy failed! Old file %s does not exist!"%(fileold)
  filenew = filename.split('/')[-1]
  if filenew==re.sub(r"^\./","",fileold):
    print ">>> Warning! copy2local: No sense in copying %s to %s"%(fileold,filenew)
  shutil.copyfile(fileold,filenew)
  assert os.path.isfile(filenew), "Copy failed! New file %s does not exist!"%(filenew)
  return filenew
  

def main():
  
  eras      = args.eras
  periods   = cleanEras(args.periods)
  channel   = args.channel
  types     = args.types
  verbosity = args.verbosity
  minbiases = [ 69.2 ] if periods else [ 69.2, 80.0, 69.2*1.046, 69.2*0.954 ]
  
  for era in args.eras:
    year       = getyear(era)
    mcfilename = "MC_PileUp_%s.root"%(era)
    jsondir    = os.path.join(datadir,'json',str(year))
    pileup     = os.path.join(jsondir,"pileup_latest.txt")
    CMSStyle.setCMSEra(year)
    if era=='2016':
      # https://twiki.cern.ch/twiki/bin/viewauth/CMS/PdmV2017Analysis
      # /afs/cern.ch/cms/CAF/CMSCOMM/COMM_DQM/certification/Collisions16/13TeV/ReReco/Final/Cert_271036-284044_13TeV_23Sep2016ReReco_Collisions16_JSON.txt"
      # /afs/cern.ch/cms/CAF/CMSCOMM/COMM_DQM/certification/Collisions16/13TeV/Final/Cert_271036-284044_13TeV_PromptReco_Collisions16_JSON.txt
      # /afs/cern.ch/cms/CAF/CMSCOMM/COMM_DQM/certification/Collisions16/13TeV/PileUp/pileup_latest.txt
      JSON     = os.path.join(jsondir,"Cert_271036-284044_13TeV_ReReco_07Aug2017_Collisions16_JSON.txt")
      datasets = {
        'B': (272007,275376),
        'C': (275657,276283),
        'D': (276315,276811),
        'E': (276831,277420),
        'F': (277772,278808),
        'G': (278820,280385),
        'H': (280919,284044),
      }
      campaign = "Moriond17"
      samples  = [
        ( 'TT', "TT",                   ),
        ( 'DY', "DYJetsToLL_M-10to50",  ),
        ( 'DY', "DYJetsToLL_M-50",      ),
        ( 'DY', "DY1JetsToLL_M-50",     ),
        ( 'DY', "DY2JetsToLL_M-50",     ),
        ( 'DY', "DY3JetsToLL_M-50",     ),
        ( 'WJ', "WJetsToLNu",           ),
        ( 'WJ', "W1JetsToLNu",          ),
        ( 'WJ', "W2JetsToLNu",          ),
        ( 'WJ', "W3JetsToLNu",          ),
        ( 'WJ', "W4JetsToLNu",          ),
        ( 'ST', "ST_tW_top",            ),
        ( 'ST', "ST_tW_antitop",        ),
        ( 'ST', "ST_t-channel_top",     ),
        ( 'ST', "ST_t-channel_antitop", ),
        #( 'ST', "ST_s-channel",         ),
        ( 'VV', "WW",                   ),
        ( 'VV', "WZ",                   ),
        ( 'VV', "ZZ",                   ),
      ]
    elif '2017' in era:
      # https://twiki.cern.ch/twiki/bin/viewauth/CMS/PdmV2017Analysis
      # /afs/cern.ch/cms/CAF/CMSCOMM/COMM_DQM/certification/Collisions16/13TeV/Final/Cert_271036-284044_13TeV_PromptReco_Collisions16_JSON.txt
      # /afs/cern.ch/cms/CAF/CMSCOMM/COMM_DQM/certification/Collisions17/13TeV/PileUp/pileup_latest.txt
      JSON     = os.path.join(jsondir,"Cert_294927-306462_13TeV_PromptReco_Collisions17_JSON.txt") 
      datasets = {
        'B': (297020,299329),
        'C': (299337,302029),
        'D': (302030,303434),
        'E': (303435,304826),
        'F': (304911,306462),
      }
      samples_bug = [ ]
      samples_fix = [ ]
      if 'UL' in era:
        campaign = "Summer19"
        samples_fix = [
          #( 'DY', "DYJetsToLL_M-10to50",  ),
          ( 'DY', "DYJetsToLL_M-50",      ),
          ( 'DY', "DY1JetsToLL_M-50",     ),
          ( 'DY', "DY2JetsToLL_M-50",     ),
          ( 'DY', "DY3JetsToLL_M-50",     ),
          ( 'DY', "DY4JetsToLL_M-50",     ),
          #( 'TT', "TTTo2L2Nu",            ),
          ( 'TT', "TTToHadronic",         ),
          #( 'TT', "TTToSemiLeptonic",     ),
          ( 'WJ', "WJetsToLNu",           ),
          ( 'WJ', "W1JetsToLNu",          ),
          ( 'WJ', "W2JetsToLNu",          ),
          ( 'WJ', "W3JetsToLNu",          ),
          ( 'WJ', "W4JetsToLNu",          ),
          ( 'ST', "ST_tW_top",            ),
          ( 'ST', "ST_tW_antitop",        ),
          ( 'ST', "ST_t-channel_top",     ),
          ( 'ST', "ST_t-channel_antitop", ),
          #( 'ST', "ST_s-channel",         ),
          #( 'VV', "WW",                   ),
          #( 'VV', "WZ",                   ),
          #( 'VV', "ZZ",                   ),
        ]
      else:
        campaign = "Winter17_V2"
        samples_bug = [
          ( 'DY', "DYJetsToLL_M-50",      ),
          ( 'WJ', "W3JetsToLNu",          ),
          ( 'VV', "WZ",                   ),
        ]
        samples_fix = [
          ( 'DY', "DYJetsToLL_M-10to50",  ),
          ( 'DY', "DY1JetsToLL_M-50",     ),
          ( 'DY', "DY2JetsToLL_M-50",     ),
          ( 'DY', "DY3JetsToLL_M-50",     ),
          ( 'DY', "DY4JetsToLL_M-50",     ),
          ( 'TT', "TTTo2L2Nu",            ),
          ( 'TT', "TTToHadronic",         ),
          ( 'TT', "TTToSemiLeptonic",     ),
          ( 'WJ', "WJetsToLNu",           ),
          ( 'WJ', "W1JetsToLNu",          ),
          ( 'WJ', "W2JetsToLNu",          ),
          ( 'WJ', "W4JetsToLNu",          ),
          ( 'ST', "ST_tW_top",            ),
          ( 'ST', "ST_tW_antitop",        ),
          ( 'ST', "ST_t-channel_top",     ),
          ( 'ST', "ST_t-channel_antitop", ),
          #( 'ST', "ST_s-channel",         ),
          ( 'VV', "WW",                   ),
          ( 'VV', "ZZ",                   ),
        ]
      samples = samples_bug + samples_fix
    else:
      # https://twiki.cern.ch/twiki/bin/viewauth/CMS/PdmV2018Analysis
      # /afs/cern.ch/cms/CAF/CMSCOMM/COMM_DQM/certification/Collisions18/13TeV/PromptReco
      # /afs/cern.ch/cms/CAF/CMSCOMM/COMM_DQM/certification/Collisions18/13TeV/PileUp/pileup_latest.txt
      JSON     = os.path.join(jsondir,"Cert_314472-325175_13TeV_PromptReco_Collisions18_JSON.txt")
      datasets = {
        'A': (315252,316995),
        'B': (317080,319310),
        'C': (319337,320065),
        'D': (320673,325175),
      }
      campaign = "Autumn18"
      samples = [
        ( 'TT', "TTTo2L2Nu",            ),
        ( 'TT', "TTToHadronic",         ),
        ( 'TT', "TTToSemiLeptonic",     ),
        ( 'DY', "DYJetsToLL_M-10to50",  ),
        ( 'DY', "DYJetsToLL_M-50",      ),
        ( 'DY', "DY1JetsToLL_M-50",     ),
        ( 'DY', "DY2JetsToLL_M-50",     ),
        ( 'DY', "DY3JetsToLL_M-50",     ),
        ( 'DY', "DY4JetsToLL_M-50",     ),
        #( 'WJ', "WJetsToLNu",           ),
        ( 'WJ', "W1JetsToLNu",          ),
        ( 'WJ', "W2JetsToLNu",          ),
        ( 'WJ', "W3JetsToLNu",          ),
        ( 'WJ', "W4JetsToLNu",          ),
        ( 'ST', "ST_tW_top",            ),
        ( 'ST', "ST_tW_antitop",        ),
        ( 'ST', "ST_t-channel_top",     ),
        ( 'ST', "ST_t-channel_antitop", ),
        #( 'ST', "ST_s-channel",         ),
        ( 'VV', "WW",                   ),
        ( 'VV', "WZ",                   ),
        ( 'VV', "ZZ",                   ),
      ]
    
    # SAMPLES FILENAMES
    fname = "$PICODIR/$SAMPLE_$CHANNEL.root"
    if '$PICODIR' in fname:
      import TauFW.PicoProducer.tools.config as GLOB
      CONFIG = GLOB.getconfig(verb=verbosity)
      fname  = repkey(fname,PICODIR=CONFIG['picodir'])
    for i, (group,sample) in enumerate(samples):
      fname      = repkey(fname,ERA=era,GROUP=group,SAMPLE=sample,CHANNEL=channel)
      samples[i] = (sample,fname)
    if verbosity>=1:
      print ">>> samples = %r"%(samples)
    
    # JSON
    jsons = { }
    if periods:
      outdir = ensuredir("json")
      for period in periods:
        start, end = getPeriodRunNumbers(period,datasets)
        erarun     = "Run%d%s"%(era,period)
        jsonout    = "json/"+re.sub(r"\d{6}-\d{6}",erarun,JSON.split('/')[-1])
        filterJSONByRunNumberRange(JSON,jsonout,start,end,verb=verbosity)
        jsons[erarun] = jsonout
    else:
      jsons[era] = JSON
    
    # DATA
    datahists = { period: [ ] for period in jsons }
    if 'data' in types:
      for period, json in jsons.iteritems():
        for minbias in minbiases:
          filename = "Data_PileUp_%s_%s.root"%(period,str(minbias).replace('.','p'))
          datahist = getDataProfile(filename,json,pileup,100,era,minbias)
          datahists[period].append((minbias,datahist))
    elif args.plot:
      for era in jsons:
        for minbias in minbiases:
          filename = "Data_PileUp_%s_%s.root"%(era,str(minbias).replace('.','p'))
          file, hist = gethist(filename,'pileup',retfile=True)
          if not file or not hist: continue
          hist.SetDirectory(0)
          file.Close()
          datahists[era].append((minbias,hist))
    
    # MC
    if 'mc' in types:
      mcfilename = "MC_PileUp_%s.root"%(era)
      #mcfilename = "MC_PileUp_%s_%s.root"%(era,campaign)
      getMCProfile(mcfilename,samples,channel,era)
      if args.plot:
        mchist = compareMCProfiles(samples,channel,era)
        for era in jsons:
          for minbias, datahist in datahists[era]:
            compareDataMCProfiles(datahist,mchist,era,minbias)
        deletehist(mchist) # clean memory
      if era=='2017': # also check new/old pmx separately
        mcfilename_bug = mcfilename.replace(".root","_old_pmx.root")
        mcfilename_fix = mcfilename.replace(".root","_new_pmx.root")
        getMCProfile(mcfilename_bug,samples_bug,channel,era)
        getMCProfile(mcfilename_fix,samples_fix,channel,era)
        if args.plot:
          mchist_bug = compareMCProfiles(samples_bug,channel,era,tag="old_pmx")
          mchist_fix = compareMCProfiles(samples_fix,channel,era,tag="new_pmx")
          for era in jsons:
            for minbias, datahist in datahists[era]:
              compareDataMCProfiles(datahist,mchist_bug,era,minbias,tag="old_pmx")
              compareDataMCProfiles(datahist,mchist_fix,era,minbias,tag="new_pmx")
    
    # FLAT
    if 'flat' in types:
      filename  = "MC_PileUp_%d_FlatPU0to75.root"%era
      hist_flat = getFlatProfile(filename,75)
      for era in jsons:
        for minbias, datahist in datahists[era]:
          compareDataMCProfiles(datahist,hist_flat,era,minbias,tag="FlatPU0to75",rmin=0.0,rmax=3.1)
  

if __name__ == '__main__':
  print
  main()
  print ">>> done\n"
  
