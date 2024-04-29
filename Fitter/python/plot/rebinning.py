import ROOT as r
import numpy as np
import os
from TauFW.Plotter.sample.utils import ensuredir
from TauFW.common.tools.string import repkey

class rebinning():
   def __init__(self, input, obs='', tag=''):
      self.input = repkey(input, OBS=obs, TAG=tag)
      self.inputfile = r.TFile(self.input)
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
          for ibin in range(1, bkghist.GetNbinsX()+1):
              if ibin == 1:
                  self.binedges[dirname].append(bkghist.GetBinLowEdge(ibin))
              if bkghist.GetBinError(ibin)/bkghist.GetBinContent(ibin) > 0.20:
                  if ibin == bkghist.GetNbinsX():
                      self.binedges[dirname][len(self.binedges[dirname])-1] = bkghist.GetBinLowEdge(ibin) + bkghist.GetBinWidth(ibin)
                      break
                  else:
                     continue
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
          for histname in [key.GetName() for key in dir.GetListOfKeys()]:
             hist = dir.Get(histname)
             if type(hist) in [r.TH1F, r.TH1D]:
               newhist = hist.Rebin(len(self.binedges[dirname])-1, hist.GetName(), np.array(self.binedges[dirname]))
             else:
               newhist = hist
             newhist.Write()
        
        outputfile.Close()
        self.inputfile.Close()

def main(args):
  input = args.input
  rebinning(input)

if __name__ == "__main__":
  from argparse import ArgumentParser
  description = """do rebinning for datacards"""
  parser = ArgumentParser(prog="rebinning",description=description,epilog="Good luck!")
  parser.add_argument('-i', '--input',     dest='input', help="name of input file")
  args = parser.parse_args()
  main(args) 

