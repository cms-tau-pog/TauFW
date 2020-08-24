#! /usr/bin/env python
# Author: Izaak Neutelings (August 2020)
# Description: Create input histograms for datacards
#   ./createInputs.py
#from TauFW.common.tools.file import ensuremodule
import os, sys
from collections import OrderedDict
sys.path.append("../../Plotter/") # for config.samples
from config.samples import *
from TauFW.common.tools.log import color
from TauFW.common.tools.file import ensureTDirectory, ensureTFile, gethist
from TauFW.Plotter.plot.utils import deletehist
from TauFW.Plotter.plot.utils import LOG as PLOG
from TauFW.Plotter.plot.Stack import Stack
from TauFW.Plotter.plot.Plot import Plot
from ROOT import gStyle, TFile, TH1, TNamed, kBlack


def createInputs(fname,sampleset,observables,bins,**kwargs):
  """Test plotting of SampleSet class for data/MC comparison."""
  #LOG.header("createInputs")
  outdir        = kwargs.get('outdir',        ""    )
  tag           = kwargs.get('tag',           ""    ) # file tag
  htag          = kwargs.get('htag',          ""    ) # hist tag for systematic
  filters       = kwargs.get('filter',        None  ) # only create histograms for these samples
  vetoes        = kwargs.get('veto',          None  ) # veto these samples
  parallel      = kwargs.get('parallel',      True  ) # MultiDraw histograms in parallel
  recreate      = kwargs.get('recreate',      False ) # recreate ROOT file
  replaceweight = kwargs.get('replaceweight', None  ) # replace weight
  extraweight   = kwargs.get('weight',        ""    ) # extraweight
  shiftQCD      = kwargs.get('shiftQCD',      0     ) # e.g 0.30 for 30%
  verbosity     = kwargs.get('verb',          0     )
  option        = 'RECREATE' if recreate else 'UPDATE'
  method        = 'QCD_OSSS' if filters==None or 'QCD' in filters else None
  
  # FILE LOGISTICS
  files = { }
  ensuredir(outdir)
  fname = os.path.join(outdir,fname)
  for obs in observables:
    ftag    = tag+obs.tag
    fname_  = repkey(fname,OBS=obs,TAG=ftag)
    file    = TFile.Open(fname_,option)
    for selection in bins:
      if not obs.plotfor(selection): continue
      obs.changecontext(selection)
      ensureTDirectory(file,selection.filename,cd=True,verb=1)
      if recreate:
        TNamed("selection",selection.selection).Write()
        #TNamed("weight",sampleset.weight).Write()
    files[obs] = file
  
  # GET HISTS
  if htag:
    print ">>> systematic uncertainty = %s"%(color(htag.lstrip('_'),'grey'))
  for selection in bins:
    bin   = selection.filename # bin name
    print ">>>\n>>> "+color(" %s "%(bin),'magenta',bold=True,ul=True)
    if recreate or verbosity>=1:
      print ">>> %r"%(selection.selection)
    hists = sampleset.gethists(observables,selection,method=method,split=True,
                               parallel=parallel,filter=filters,veto=vetoes)
    
    # SAVE HIST
    ljust = 4+max(11,len(htag)) # extra space
    TAB   = LOG.table("%10.1f %10d  %-18s  %s")
    TAB.printheader('events','entries','variable','process'.ljust(ljust))
    for obs, hist in hists.iterhists():
      name    = hist.GetName().lstrip(obs.filename).strip('_')+htag # histname = $VAR_$NAME
      name    = repkey(name,BIN=bin) # HIST = $PROCESS_$SYSTEMATIC
      drawopt = 'E1' if 'data' in name else 'EHIST'
      lcolor  = kBlack if any(s in name for s in ['data','ST','VV']) else hist.GetFillColor()
      hist.SetOption(drawopt)
      hist.SetLineColor(lcolor)
      hist.SetFillStyle(0)
      hist.SetName(name)
      hist.GetXaxis().SetTitle(obs.title)
      for i, yval in enumerate(hist):
        if yval<0:
          print ">>> replace bin %d (%.3f<0) of %r"%(i,yval,hist.GetName())
          hist.SetBinContent(i,0)
      files[obs].cd(bin) # $FILE:$BIN/$PROCESS_$SYSTEMATC
      hist.Write(name,TH1.kOverwrite)
      TAB.printrow(hist.GetSumOfWeights(),hist.GetEntries(),obs.printbins(),name)
      deletehist(hist)
  
  for obs, file in files.iteritems():
    file.Close()
  

def main(args):
  channels  = args.channels
  eras      = args.eras
  parallel  = args.parallel
  verbosity = args.verbosity
  plot      = True
  outdir    = ensuredir("input")
  plotdir   = ensuredir(outdir,"plots")
  analysis  = 'ztt_tid' # $PROCESS_$ANALYSIS
  tag       = ""
  
  for era in eras:
    for channel in channels:
      
      # GET SAMPLES
      join       = ['VV','TT','ST']
      sname      = "$PICODIR/$SAMPLE_$CHANNEL$TAG.root"
      sampleset  = getsampleset(channel,era,fname=sname,join=join,split=None,table=False)
      
      # SPLIT & RENAME (HTT convention)
      GMR = "genmatch_2==5"
      GML = "genmatch_2>0 && genmatch_2<5"
      GMJ = "genmatch_2==0"
      GMF = "genmatch_2<5"
      sampleset.split('DY',[('ZTT',GMR),('ZL',GML),('ZJ',GMJ),])
      sampleset.split('TT',[('TTT',GMR),('TTL',GML),('TTJ',GMJ)])
      sampleset.split('ST',[('STT',GMR),('STJ',GMF),])
      sampleset.rename('WJ','W')
      sampleset.datasample.name = 'data_obs'
      
      # VARIATIONS
      varsamples = OrderedDict([ # samples to be varied
        ('Nom',     ['ZTT','ZL','ZJ','W','VV','STT','STJ','TTT','TTL','TTJ','QCD_SS','data_obs']),
        ('TESUp',   ['ZTT','TTT']),
        ('TESDown', ['ZTT','TTT']),
        ('LTFUp',   ['ZL', 'TTL']),
        ('LTFDown', ['ZL', 'TTL']),
        ('JTFUp',   ['ZJ', 'TTJ', 'W']),
        ('JTFDown', ['ZJ', 'TTJ', 'W']),
      ])
      samplesets = { # sets of samples per variation
        'Nom':     sampleset, # nominal
        'TESUp':   sampleset.shift(varsamples['TESUp'],  "_TES1p030","_TESUp",  " +3% TES", split=True,filter=False,share=True),
        'TESDown': sampleset.shift(varsamples['TESDown'],"_TES0p970","_TESDown"," -3% TES", split=True,filter=False,share=True),
        'LTFUp':   sampleset.shift(varsamples['LTFUp'],  "_LTF1p030","_LTFUp",  " +3% LTF", split=True,filter=False,share=True),
        'LTFDown': sampleset.shift(varsamples['LTFDown'],"_LTF0p970","_LTFDown"," -3% LTF", split=True,filter=False,share=True),
        'JTFUp':   sampleset.shift(varsamples['JTFUp'],  "_JTF1p100","_JTFUp",  " +10% JTF",split=True,filter=False,share=True),
        'JTFDown': sampleset.shift(varsamples['JTFDown'],"_JTF0p900","_JTFDown"," -10% JTF",split=True,filter=False,share=True),
      }
      keys = samplesets.keys() if verbosity>=1 else ['Nom','TESUp','TESDown']
      for shift in keys:
        samplesets[shift].printtable(merged=True,split=True)
        if verbosity>=2:
          samplesets[shift].printobjs(file=True)
      
      # OBSERVABLES (VARIABLES)
      observables = [
        Var('m_vis', 30, 50, 200),
        Var('m_vis', 15, 50, 200, tag="_10"), # coarser binning
      ]
      
      # BINS (SELECTIONS)
      tauwps    = ['VVLoose','VLoose','Loose','Medium','Tight','VTight','VVTight']
      tauwpbits = { wp: 2**(i+1) for i, wp in enumerate(tauwps)}
      iso_1     = "iso_1<0.15"
      iso_2     = "idDecayModeNewDMs_2 && idDeepTau2017v2p1VSjet_2>=$WP && idDeepTau2017v2p1VSe_2>=2 && idDeepTau2017v2p1VSmu_2>=8"
      baseline  = "q_1*q_2<0 && %s && %s && !lepton_vetoes_notau && metfilter"%(iso_1,iso_2)
      bins = [
        #Sel('baseline',repkey(baseline,WP=16)),
      ]
      for wpname in tauwps:
        wpbit = tauwpbits[wpname]
        bins.append(Sel(wpname,repkey(baseline,WP=wpbit)))
      
      # DATACARD INPUTS
      # https://twiki.cern.ch/twiki/bin/viewauth/CMS/SMTauTau2016
      chshort = channel.replace('tau','t').replace('mu','m')
      fname   = "%s/%s_$OBS_%s-%s$TAG%s.inputs.root"%(outdir,analysis,chshort,era,tag)
      pname   = "%s/%s_$OBS_%s-$BIN-%s$TAG%s.png"%(plotdir,analysis,chshort,era,tag)
      
      createInputs(fname,samplesets['Nom'],    observables,bins,recreate=True)
      createInputs(fname,samplesets['TESUp'],  observables,bins,filter=varsamples['TESUp']  )
      createInputs(fname,samplesets['TESDown'],observables,bins,filter=varsamples['TESDown'])
      createInputs(fname,samplesets['LTFUp'],  observables,bins,filter=varsamples['LTFUp']  )
      createInputs(fname,samplesets['LTFDown'],observables,bins,filter=varsamples['LTFDown'])
      createInputs(fname,samplesets['JTFUp'],  observables,bins,filter=varsamples['JTFUp']  )
      createInputs(fname,samplesets['JTFDown'],observables,bins,filter=varsamples['JTFDown'])
      
      # PLOT
      if plot:
        print ">>>\n>>> "+color(" plotting... ",'magenta',bold=True,ul=True)
        for obs in observables:
          ftag   = tag+obs.tag
          fname_ = repkey(fname,OBS=obs,TAG=ftag)
          file   = ensureTFile(fname_,'UPDATE')
          for set, samples in varsamples.iteritems():
            if set=='Nom':
              settag     = ""
              allsamples = samples[:]
            else:
              settag     = '_'+set
              allsamples = [s+settag if s in samples else s for s in varsamples['Nom']]
            for selection in bins:
              if not obs.plotfor(selection): continue
              obs.changecontext(selection)
              bin       = selection.filename
              directory = ensureTDirectory(file,bin,cd=True)
              exphists  = [ ]
              datahist  = None
              text      = "%s %s"%(channel.replace("mu","#mu").replace("tau","#tau_{h}"),selection)
              if set=='Nom':
                gStyle.Write('style',TH1.kOverwrite)
              
              # STACK
              for sample in allsamples:
                hname   = sample
                hist    = gethist(directory,hname)
                hist.SetDirectory(0)
                hist.SetLineColor(kBlack)
                hist.SetFillStyle(1001)
                if sample=='data_obs':
                  datahist = hist
                else:
                  exphists.append(hist)
              pname_ = repkey(pname,OBS=obs,BIN=bin,TAG=ftag+settag)
              stack  = Stack(obs,datahist,exphists)
              stack.draw()
              stack.drawlegend(ncols=2,twidth=0.9)
              stack.drawtext(text)
              stack.saveas(pname_,ext=['png'])
              stack.canvas.Write("stack"+settag,TH1.kOverwrite)
              stack.close()
              
              # VARIATIONS
              if 'Up' in set:
                varset  = set.replace('Up','')
                uptag   = settag
                downtag = settag.replace('Up','Down')
                for sample in samples:
                  hists = [ ]
                  for var in [uptag,"",downtag]:
                    hname = sample+var
                    hist  = gethist(directory,hname)
                    hists.append(hist)
                  vartag  = "%s_%s_%s"%(ftag,sample,varset)
                  pname_  = repkey(pname,OBS=obs,BIN=bin,TAG=vartag)
                  plot    = Plot(hists)
                  plot.draw(ratio=True)
                  plot.drawlegend()
                  plot.drawtext(text)
                  plot.saveas(pname_,ext=['png'])
                  gStyle.Write('style',TH1.kOverwrite)
                  plot.canvas.Write("plot_%s_%s"%(sample,varset),TH1.kOverwrite)
                  plot.close()
          
          file.Close()
    
  

if __name__ == "__main__":
  from argparse import ArgumentParser
  argv = sys.argv
  description = """Create input histograms for datacards"""
  parser = ArgumentParser(prog="createInputs",description=description,epilog="Good luck!")
  parser.add_argument('-y', '--era',     dest='eras', nargs='*', choices=['2016','2017','2018','UL2017'], default=['2017'], action='store',
                                         help="set era" )
  parser.add_argument('-c', '--channel', dest='channels', nargs='*', choices=['mutau'], default=['mutau'], action='store',
                                         help="set channel" )
  parser.add_argument('-s', '--serial',  dest='parallel', action='store_false',
                                         help="run Tree::MultiDraw serial instead of in parallel" )
  parser.add_argument('-v', '--verbose', dest='verbosity', type=int, nargs='?', const=1, default=0, action='store',
                                         help="set verbosity" )
  args = parser.parse_args()
  LOG.verbosity = args.verbosity
  PLOG.verbosity = args.verbosity
  main(args)
  print "\n>>> Done."
  
