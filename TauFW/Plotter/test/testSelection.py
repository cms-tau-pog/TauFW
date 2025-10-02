#! /usr/bin/env python
# Author: Izaak Neutelings (June 2020)
# Description: Test Variable initiation
#   test/testVariables.py
from TauFW.common.tools.log import color
from TauFW.Plotter.plot.utils import LOG
from TauFW.Plotter.plot.Selection import Selection


def main(args):
  verbosity = args.verbosity
  
  #### Test several initializations of Variable object.
  #### Note that key-word arguments starting with 'c' are used for context-dependent attributes
  ###mvisbins  = [0,30,40,50,60,70,75,80,90,100,120,200]
  ###variables = [
  ###  Variable('m_vis',     "m_{vis} [GeV]", 40, 0,200),
  ###  Variable('njets',     "Number of jets", 8, 0,  8),
  ###  Variable('m_vis',     40, 0,200),
  ###  Variable('njets',      8, 0,  8),
  ###  Variable('njets',      8, 0,  8, veto='njets'),
  ###  Variable('st',        20, 0,800, title="S_{T}",only="njets",blind="st>600"),
  ###  Variable('m_vis',     40, 0,200, cbins={'njets':mvisbins},blind=(70,90)),
  ###  Variable('m_vis',      mvisbins, cbins={"njets[^&]*2":(40,0,200)},),
  ###  Variable('pt_1+pt_2', 20, 0,800, title="S_{T}^{tautau}",ctitle={"njets":"S_{T}"}),
  ###]
  selections = [
    Selection(""),
    Selection("baseline", "pt_1>50 && pt_2>50"),
    Selection("njets>=1", "pt_1>50 && pt_2>50 && njets>=1"),
    Selection("1 b tags", "pt_1>50 && pt_2>50 && njets>=2 && nbtags>=1",weight="btagweight"),
  ]
  
  for selection in selections:
    LOG.header(selection.name)
    
    # CHECK SETTINGS
    print(">>> name='%s', filename='%s', title='%s', cut='%s'"%(color(selection.name),color(selection.filename),color(selection.title),color(selection.selection)))
    print(">>> weight=%r, drawcmd=%r"%(selection.weight,selection.drawcmd()))
    
    # ADD SELECTION
    sum1 = selection + "dzeta>-40"
    print('>>> sum1 = selection + "dzeta>-40"')
    print(">>>   name=%r, filename=%r, title=%r"%(sum1.name,sum1.filename,sum1.title))
    print(">>>   selection=%r"%(sum1.selection))
    
    # ADD SELECTION 2
    sum2 = selection + Selection("dzeta","dzeta>-40")
    print('>>> sum2 = selection + Selection("dzeta","dzeta>-40")')
    print(">>>   name=%r, filename=%r, title=%r"%(sum2.name,sum2.filename,sum2.title))
    print(">>>   selection=%r"%(sum2.selection))
    
    # CLONE SELECTION with replace
    clone = selection.clone("ptgt100","pt > 100",replace=(">50",">100"),verb=verbosity)
    print('>>> clone = selection.clone("ptgt100","pt > 100",replace=(">50",">100"))')
    print(">>>   name=%r, filename=%r, title=%r"%(clone.name,clone.filename,clone.title))
    print(">>>   selection=%r"%(clone.selection))
  

if __name__ == "__main__":
  from argparse import ArgumentParser
  description = """Test Selection initiation and features"""
  parser = ArgumentParser(prog="testSelections",description=description,epilog="Good luck!")
  parser.add_argument('-v', '--verbose', dest='verbosity', type=int, default=1, action='store',
                                         help="set verbosity, default=%(default)d" )
  args = parser.parse_args()
  LOG.verbosity = args.verbosity
  main(args)
  print('')
  
