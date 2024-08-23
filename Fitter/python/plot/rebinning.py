import ROOT as r
import numpy as np
import os
from math import sqrt
from TauFW.Plotter.sample.utils import ensuredir
from TauFW.common.tools.string import repkey

class rebinning():
   def __init__(self, input, obs='', tag='', subtract_nonztt_only=False):
      self.input = repkey(input, OBS=obs, TAG=tag)
      self.inputfile = r.TFile(self.input)
      if subtract_nonztt_only:
         self.subtract_nonZTT()
      else:
         self.find_binedges()
         self.regular_binning()

   def find_binedges(self):
        inputdir = os.path.dirname(self.input)
        self.binedges = {}
        for dirname in [key.GetName() for key in self.inputfile.GetListOfKeys()]:
          self.binedges[dirname] = []
          dir = self.inputfile.Get(dirname)
          bkghist = r.TH1F()
          for histname in [key.GetName() for key in dir.GetListOfKeys()]:
            hist = dir.Get(histname)
            if type(hist) not in [r.TH1F, r.TH1D]: continue 
            if '_' not in histname:
                if bkghist.Integral() == 0:
                    bkghist = hist.Clone()
                else:
                    bkghist.Add(hist)
          err = 0
          bincont = 0
          for ibin in range(1, bkghist.GetNbinsX()+1):
              if ibin == 1:
                  self.binedges[dirname].append(bkghist.GetBinLowEdge(ibin))
              if bkghist.GetBinContent(ibin) == 0: continue
              err += sqrt( pow(err,2) + pow(bkghist.GetBinError(ibin),2))
              bincont += bkghist.GetBinContent(ibin)
              errOcont = err / bincont
              #errOcont = bkghist.GetBinError(ibin)/bkghist.GetBinContent(ibin)
              if errOcont > 0.30:
                  if ibin == bkghist.GetNbinsX():
                      self.binedges[dirname][len(self.binedges[dirname])-1] = bkghist.GetBinLowEdge(ibin) + bkghist.GetBinWidth(ibin)
                      break
                  else:
                     continue
              else:
                   err = 0
                   bincont = 0
                   self.binedges[dirname].append(bkghist.GetBinLowEdge(ibin) + bkghist.GetBinWidth(ibin))

   
   def regular_binning(self):
        inputdir = os.path.dirname(self.input)
        output_dir = ensuredir(os.path.join(inputdir, 'rebinning'))
        outputfile = r.TFile(os.path.join(output_dir, os.path.basename(self.input)), 'recreate')
        print('outputfile {} created'.format(outputfile))
        for dirname in [key.GetName() for key in self.inputfile.GetListOfKeys()]:
          outputfile.mkdir(dirname)
          outputfile.cd(dirname)
          dir = self.inputfile.Get(dirname)
          for idx, histname in enumerate([key.GetName() for key in dir.GetListOfKeys()]):
             hist = dir.Get(histname)
             if type(hist) in [r.TH1F, r.TH1D]:
               newhist = hist.Rebin(len(self.binedges[dirname])-1, hist.GetName(), np.array(self.binedges[dirname]))
               if idx == 0:
                  nonztt = newhist.Clone()
                  nonztt.Reset()
               if histname in ['W', 'QCD', 'VV', 'ST', "TTT","TTL","TTJ", 'ZL', 'ZJ']:
                   if nonztt.Integral() == 0:
                       nonztt = newhist.Clone('nonztt')
                       nonztt.Sumw2()
                   else:
                       nonztt.Add(newhist)
               elif histname == 'data_obs':
                    new_data = newhist.Clone('data_obs_nonztt_subtratced') 
             else:
               newhist = hist
             newhist.Write()
          new_data.Add(nonztt, -1)
          new_data.Write()
        outputfile.Close()
        self.inputfile.Close()

   def subtract_nonZTT(self):
      inputdir = os.path.dirname(self.input)
      output_dir = ensuredir(os.path.join(inputdir, 'subtract_nonztt'))
      outputfile = r.TFile(os.path.join(output_dir, os.path.basename(self.input)), 'recreate')
      print('outputfile {} created'.format(outputfile))
      for dirname in [key.GetName() for key in self.inputfile.GetListOfKeys()]:
          outputfile.mkdir(dirname)
          outputfile.cd(dirname)
          dir = self.inputfile.Get(dirname)
          for idx, histname in enumerate([key.GetName() for key in dir.GetListOfKeys()]):
             hist = dir.Get(histname)
             if type(hist) in [r.TH1F, r.TH1D]:
               if idx == 0:
                  nonztt = hist.Clone()
                  nonztt.Reset()
               if histname in ['W', 'QCD', 'VV', 'ST', "TTT","TTL","TTJ", 'ZL', 'ZJ']:
                   if nonztt.Integral() == 0:
                       nonztt = hist.Clone('nonztt')
                       nonztt.Sumw2()
                   else:
                       nonztt.Add(hist)
               elif histname == 'data_obs':
                    new_data = hist.Clone('data_obs_nonztt_subtratced')
             hist.Write()
          new_data.Add(nonztt, -1)
          new_data.Write()
      outputfile.Close()
      self.inputfile.Close()

def main(args):
  input = args.input
  rebinning(input, subtract_nonztt_only=True)

if __name__ == "__main__":
  from argparse import ArgumentParser
  description = """do rebinning for datacards"""
  parser = ArgumentParser(prog="rebinning",description=description,epilog="Good luck!")
  parser.add_argument('-i', '--input',     dest='input', help="name of input file")
  args = parser.parse_args()
  main(args) 

