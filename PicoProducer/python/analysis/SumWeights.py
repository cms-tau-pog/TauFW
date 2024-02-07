#! /usr/bin/env python3
# Author: Izaak Neutelings (June 2021)
# Description: Simple module to compile sum of weights in MC
# Instructions:
# Locally:
#   python3 python/analysis/SumWeights.py
# Or with PicoProducer:
#   pico.py channel sumw python/analysis/SumWeights.py
#   pico.py run -c sumw -y UL2018 -s DYJetsToLL_M-50
# https://cms-nanoaod-integration.web.cern.ch/integration/cms-swmaster/mc106Xul16_doc.html
# Float_t LHE scale variation weights (w_var / w_nominal);
#   [0] is MUF="0.5" MUR="0.5"; [1] is MUF="1.0" MUR="0.5"; [2] is MUF="2.0" MUR="0.5";
#   [3] is MUF="0.5" MUR="1.0"; [4] is MUF="1.0" MUR="1.0"; [5] is MUF="2.0" MUR="1.0";
#   [6] is MUF="0.5" MUR="2.0"; [7] is MUF="1.0" MUR="2.0"; [8] is MUF="2.0" MUR="2.0"
import ROOT; ROOT.PyConfig.IgnoreCommandLineOptions = True # to avoid conflict with argparse
from ROOT import TFile, TH1D
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module


class SumWeights(Module):
  """Simple module to fill sum of weights histogram."""
  
  def __init__(self,fname,**kwargs):
    self.outfile         = TFile(fname,'RECREATE')
    self.sumw_scale      = TH1D('sumw_scale',     'Sum of #mu_{F} & #mu_{R} scale variation weights', 10, 0, 10)
    self.sumw_scale_genw = TH1D('sumw_scale_genw','Sum of #mu_{F} & #mu_{R} scale variation weights (weighted)', 10, 0, 10)
    for i, label in enumerate(['0p5_0p5','1p0_0p5','2p0_0p5',
                               '0p5_1p0','1p0_1p0','2p0_1p0',
                               '0p5_2p0','1p0_2p0','2p0_2p0',]):
      self.sumw_scale.GetXaxis().SetBinLabel(i+1,label)
      self.sumw_scale_genw.GetXaxis().SetBinLabel(i+1,label)
    self.sumw_scale.SetDirectory(self.outfile)
    self.sumw_scale_genw.SetDirectory(self.outfile)
  
  def endJob(self):
    """Wrap up after running on all events and files"""
    self.outfile.Write()
    nevts = self.sumw_scale.GetBinContent(self.sumw_scale.GetXaxis().FindBin('1p0_1p0'))
    sumw  = self.sumw_scale_genw.GetBinContent(self.sumw_scale_genw.GetXaxis().FindBin('1p0_1p0'))
    if nevts>0:
      print(f">>> Average (nominal) gen-weight: {sumw} / {nevts} = {sumw/nevts}")
    for hist in [self.sumw_scale,self.sumw_scale_genw]:
      print(f">>> {hist.GetTitle().replace('#','').replace('{','').replace('}','')}:")
      sumw_nom = hist.GetBinContent(hist.GetXaxis().FindBin('1p0_1p0'))
      if sumw_nom<=0: continue
      for i in range(1,hist.GetXaxis().GetNbins()+1):
        name = hist.GetXaxis().GetBinLabel(i)
        if name=="": continue
        sumw = hist.GetBinContent(i)
        ave  = sumw/sumw_nom
        print(f">>>   {name:<8s} {sumw:8.1f} / {sumw_nom:8.1f}  = {ave:5.2f}")
    self.outfile.Close()
  
  def analyze(self, event):
    """Process event, return True (pass, go to next module) or False (fail, go to next event)."""
    assert event.nLHEScaleWeight==9, f"Got event.nLHEScaleWeight={event.nLHEScaleWeight}, expected 9..."
    for ibin in range(0,event.nLHEScaleWeight): # Ren. & fact. scale
      #if idx>=event.nLHEScaleWeight: break
      self.sumw_scale.Fill(     ibin,event.LHEWeight_originalXWGTUP*event.LHEScaleWeight[ibin])
      self.sumw_scale_genw.Fill(ibin,event.LHEWeight_originalXWGTUP*event.LHEScaleWeight[ibin]*event.genWeight)
    return False
  

# QUICK SCRIPT
if __name__ == '__main__':
  import os
  from PhysicsTools.NanoAODTools.postprocessing.framework.postprocessor import PostProcessor
  from TauFW.PicoProducer.processors import moddir
  from argparse import ArgumentParser
  parser = ArgumentParser()
  parser.add_argument('-i',   '--infiles', nargs='+')
  parser.add_argument('-o',   '--outdir', default='.')
  parser.add_argument('-tag', '--tag', default='', help="extra tag for name of output file")
  parser.add_argument('-n',   '--maxevts', type=int, default=10000)
  args = parser.parse_args()
  maxevts   = args.maxevts if args.maxevts>0 else None
  outfname  = "sumw%s.root"%(args.tag)
  modules   = [SumWeights(outfname)]
  branchsel = os.path.join(moddir,"keep_and_drop_sumw.txt")
  if args.infiles:
    infiles = args.infiles
  else:
    # dasgoclient --query="/DYJetsToLL_M-50_TuneCP5_13TeV-amcatnloFXFX-pythia8/RunIISummer20UL18*NanoAODv9*/NANOAODSIM"
    # dasgoclient --query="/DYJetsToLL_M-50_TuneCP5_13TeV-amcatnloFXFX-pythia8/RunIISummer20UL18NanoAODv9-106X_upgrade2018_realistic_v16_L1v1-v2/NANOAODSIM file" | head
    url = "root://cms-xrd-global.cern.ch/"
    infiles = [
      url+"/store/mc/RunIISummer20UL18NanoAODv9/DYJetsToLL_M-50_TuneCP5_13TeV-amcatnloFXFX-pythia8/NANOAODSIM/106X_upgrade2018_realistic_v16_L1v1-v2/230000/7B930101-EB91-4F4E-9B90-0861460DBD94.root",
      #url+"/store/mc/RunIISummer20UL18NanoAODv9/DYJetsToLL_M-50_TuneCP5_13TeV-amcatnloFXFX-pythia8/NANOAODSIM/106X_upgrade2018_realistic_v16_L1v1-v2/230000/BF8F0CF8-4DD5-904E-AD60-2E425E19EC6F.root",
      #url+"/store/mc/RunIISummer20UL18NanoAODv9/DYJetsToLL_M-50_TuneCP5_13TeV-amcatnloFXFX-pythia8/NANOAODSIM/106X_upgrade2018_realistic_v16_L1v1-v2/230000/85999D7A-3836-6446-AED2-136D6FC874BA.root",
      #url+"/store/mc/RunIISummer20UL18NanoAODv9/DYJetsToLL_M-50_TuneCP5_13TeV-amcatnloFXFX-pythia8/NANOAODSIM/106X_upgrade2018_realistic_v16_L1v1-v2/230000/1A59D67A-325A-E742-BFFE-2FE5F69EB01B.root",
    ]
  processor = PostProcessor(args.outdir,infiles,modules=modules,maxEntries=maxevts,
                            branchsel=branchsel,noOut=True)
  processor.run()
  
