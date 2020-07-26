#! /usr/bin/env python
# Author: Izaak Neutelings (July 2020)
# Description: Test the SampleSet class
#   test/testSampleSet.py -v2
from TauFW.Plotter.sample.utils import LOG, STYLE, setera, CMSStyle, ensuredir,\
                                       Sample, MergedSample, SampleSet
#from TauFW.Plotter.sample.SampleSet import SampleSet
from TauFW.Plotter.plot.Variable import Variable #as Var
from TauFW.Plotter.plot.Stack import Stack
from TauFW.Plotter.plot.Stack import LOG as PLOG
from pseudoSamples import makesamples

selections = [
  ('pt_1>30 && pt_2>30 && abs(eta_1)<2.4 && abs(eta_2)<2.4', 'weight'),
]
variables = [
  Variable('m_vis',            32,  0, 160, blind=(120,130)),
  ###Variable('m_vis',            [0,20,40,50,60,65,70,75,80,85,90,95,100,110,130,160,200]),
  Variable('pt_1',             40,  0, 120),
  Variable('pt_2',             40,  0, 120),
  Variable('pt_1+pt_2',        40,  0, 200),
  Variable('eta_1',            30, -3,   3, ymargin=1.6, ncol=2),
  Variable('eta_2',            30, -3,   3, ymargin=1.6, ncol=2),
  Variable('min(eta_1,eta_2)', 30, -3,   3, fname="minetas"),
  Variable('njets',            10,  0,  10),
]
variables2D = [
  (Variable('pt_1',  50,  0, 100), Variable('pt_2',  50,  0, 100)),
  (Variable('pt_1',  50,  0, 100), Variable('eta_1', 50, -3,   3)),
  #(Variable('pt_2',  50,  0, 100), Variable('eta_2', 50, -3,   3)),
  #(Variable('eta_1', 50, -3,   3), Variable('eta_1', 50, -3,   3)),
  #(Variable('pt_1',  50,  0, 100), Variable('m_vis', 50,  0, 150)),
  #(Variable('pt_2',  50,  0, 100), Variable('m_vis', 50,  0, 150)),
]
text     = "#mu#tau_{h} baseline"
position = 'topright'


def makeSampleSet(sampleset,filedict,join=False):
  """Create a SampleSet."""
  #LOG.header("makeSampleSet")
  datasample = None
  expsamples = [ ]
  for name, title, xsec in sampleset:
    file, tree = filedict[name]
    fname = file.GetName()
    color = None #STYLE.getcolor(name,verb=2)
    data  = name.lower()=='data'
    file.Close()
    sample = Sample(name,title,fname,xsec,color=color,data=data)
    #sample = Sample(name,title,fname,xsec,lumi=lumi,color=color,data=data)
    if sample.isdata:
      datasample = sample
    else:
      expsamples.append(sample)
  print ">>> Joining samples into one set"%(expsamples)
  if join:
    color      = expsamples[0].fillcolor
    bkgsample  = MergedSample('Bkg',"Background",expsamples[1:],color=color)
    expsamples = [expsamples[0],bkgsample]
    expsample  = MergedSample('Exp',"Expected",expsamples,color=color)
    expsamples = [expsample]
  samples = SampleSet(datasample,expsamples)
  samples.split('TT',[
    ('TTT',"ttbar real tau_{h}","genmatch_2==5"),
    ('TTJ',"ttbar fake tau_{h}","genmatch_2!=5"),
  ],start=True)
  print ">>> samples=%s"%samples
  print ">>> "
  samples.printtable()
  samples.printobjs()
  print ">>> "
  return samples
  

def testget(samples):
  """Test SampleSet.get* help functions."""
  LOG.header("testget")
  incl = False
  for regex in [True,False]:
    for unique in [True,False]:
      kwargs = { 'unique':unique, 'incl':incl, 'regex':regex }
      print ">>> unique=%s, incl=%s, regex=%s"%(LOG.getcolor(unique),incl,LOG.getcolor(regex))
      print ">>>   SampleSet.get('DY', unique=%s,regex=%s):  %r"%(unique,regex,samples.get('DY',**kwargs))
      print ">>>   SampleSet.get('ZTT',unique=%s,regex=%s):  %r"%(unique,regex,samples.get('ZTT',**kwargs))
      print ">>>   SampleSet.get('WJ', unique=%s,regex=%s):  %r"%(unique,regex,samples.get('WJ',**kwargs))
      print ">>>   SampleSet.get('TT', unique=%s,regex=%s):  %r"%(unique,regex,samples.get('TT',**kwargs))
      if not regex:
        print ">>>   SampleSet.get('*TT',unique=%s,regex=%s):  %r"%(unique,regex,samples.get('*TT',**kwargs))
        print ">>>   SampleSet.get('?TT',unique=%s,regex=%s):  %r"%(unique,regex,samples.get('?TT',**kwargs))
      else:
        print ">>>   SampleSet.get('.*TT',unique=%s,regex=%s): %r"%(unique,regex,samples.get('.*TT',**kwargs))
        print ">>>   SampleSet.get('.TT',unique=%s,regex=%s):  %r"%(unique,regex,samples.get('.TT', **kwargs))
      print ">>> "
  regex  = False
  for incl in [True,False]:
    for unique in [True,False]:
      kwargs = { 'unique':unique, 'incl':incl, 'regex':regex }
      print ">>> unique=%s, incl=%s, regex=%s"%(LOG.getcolor(unique),LOG.getcolor(incl),regex)
      print ">>>   SampleSet.get('ZTT','TT',unique=%s,incl=%s): %r"%(unique,incl,samples.get('ZTT','TT',**kwargs))
      print ">>>   SampleSet.get('QCD','WJ',unique=%s,incl=%s): %r"%(unique,incl,samples.get('QCD','WJ',**kwargs))
      print ">>> "
  print ">>> SampleSet.get('TT?',unique=False,regex=False,split=True): %r"%(samples.get('TT?',unique=False,regex=False,split=True))
  print ">>> SampleSet.getexp():     %r"%(samples.getexp())
  print ">>> SampleSet.getexp('TT'): %r"%(samples.getexp('TT'))
  #print ">>> SampleSet.getmc():   %r"%(samples.getmc())
  #print ">>> SampleSet.getdata():   %r"%(samples.getdata())
  print ">>> "
  

def plotSampleSet(samples,tag="",singlevar=False):
  """Test SampleSet class: join samples, print out, and plot."""
  LOG.header("testSampleSet")
  
  # GET HISTS
  for selection, weight in selections:
    if singlevar:
      result = samples.gethists(variables[0],selection,split=False)
      result.printall()
      #var, datahist, exphists = result
      #print var
      #print datahist
      #print exphists
    else:
      result = samples.gethists(variables,selection,split=False)
    result.printall()
  
  # PLOT
  outdir = ensuredir("plots")
  fname  = "%s/testSamplesSet_$VAR%s.png"%(outdir,tag)
  for selection, weight in selections:
    if singlevar:
      stack = samples.getstack(variables[0],selection,split=False)
      stack.draw()
      stack.drawlegend(position=position)
      stack.saveas(fname) #tag="_SampleSet",outdir=outdir)
      stack.close()
    else:
      stacks = samples.getstack(variables,selection,split=False)
      for stack in stacks:
        stack.draw()
        stack.drawlegend(position=position)
        stack.saveas(fname) #tag="_SampleSet",outdir=outdir)
        stack.close()
  

def main(args):
  LOG.header("Prepare samples")
  sampleset = [
    ('ZTT',  "Z -> #tau_{mu}#tau_{h}", 1.00),
    ('WJ',   "W + jets",               0.40),
    ('QCD',  "QCD multijet",           0.30),
    ('TT',   "t#bar{t}",               0.15),
    ('Data', "Observed",                -1 ),
  ]
  lumi       = 0.001 # [fb-1] to cancel xsec [pb]
  nevts      = args.nevts
  snames     = [n[0] for n in sampleset]
  scales     = {n[0]: n[2] for n in sampleset} # relative contribtions to pseudo data
  outdir     = ensuredir('plots')
  indir      = outdir
  filedict   = makesamples(nevts,sample=snames,scales=scales,outdir=outdir)
  #CMSStyle.setCMSEra(2018)
  setera(2018,lumi)
  
  samples = makeSampleSet(sampleset,filedict)
  testget(samples)
  plotSampleSet(samples)
  

if __name__ == "__main__":
  import sys
  from argparse import ArgumentParser
  argv = sys.argv
  description = """Test the SampleSet class"""
  parser = ArgumentParser(prog="testSampleSet",description=description,epilog="Good luck!")
  parser.add_argument('-n', '--nevts',   type=int, default=50000, action='store',
                                         help="number of events to generate per sample" )
  parser.add_argument('-v', '--verbose', dest='verbosity', type=int, nargs='?', const=1, default=0, action='store',
                                         help="set verbosity" )
  args = parser.parse_args()
  LOG.verbosity = args.verbosity
  PLOG.verbosity = args.verbosity-1
  main(args)
  print ">>>\n>>> Done."
  
