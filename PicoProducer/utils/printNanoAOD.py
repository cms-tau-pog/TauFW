#! /usr/bin/env python
# Author: Izaak Neutelings (April 2022)
import os, glob
from ROOT import TFile, TH1F, gDirectory

pdfsets = {
  # https://lhapdf.hepforge.org/pdfsets
   '91400': ("PDF4LHC15_nnlo_30_pdfas",    'HESS+AS'), # https://lhapdfsets.web.cern.ch/current/PDF4LHC15_nnlo_30_pdfas/PDF4LHC15_nnlo_30_pdfas.info
  '260000': ("NNPDF30_nlo_as_0118",        'REPL'   ), # https://lhapdfsets.web.cern.ch/current/NNPDF30_nlo_as_0118/NNPDF30_nlo_as_0118.info
  '262000': ("NNPDF30_lo_as_0118",         'REPL'   ), # https://lhapdfsets.web.cern.ch/current/NNPDF30_lo_as_0118/NNPDF30_lo_as_0118.info
  '292200': ("NNPDF30_nlo_nf_5_pdfas",     'REPL+AS'), # https://lhapdfsets.web.cern.ch/current/NNPDF30_nlo_nf_5_pdfas/NNPDF30_nlo_nf_5_pdfas.info
  '306000': ("NNPDF31_nnlo_hessian_pdfas", 'HESS+AS'), # https://lhapdfsets.web.cern.ch/current/NNPDF31_nnlo_hessian_pdfas/NNPDF31_nnlo_hessian_pdfas.info
}

pdfmems = {
  # https://lhapdf.hepforge.org/pdfsets
   '91400': [(  0, "central, 0.118"  ),   # https://lhapdfsets.web.cern.ch/current/PDF4LHC15_nnlo_30_pdfas/PDF4LHC15_nnlo_30_pdfas.info
             ( 31, "central, 0.1165" ),
             ( 32, "central, 0.1195" ),],
  '260000': [(  0, "average"         ),], # https://lhapdfsets.web.cern.ch/current/NNPDF30_nlo_as_0118/NNPDF30_nlo_as_0118.info
  '262000': [(  0, "average"         ),], # https://lhapdfsets.web.cern.ch/current/NNPDF30_lo_as_0118/NNPDF30_lo_as_0118.info
  '292200': [(  0, "average, 0.118"  ),   # https://lhapdfsets.web.cern.ch/current/NNPDF30_nlo_nf_5_pdfas/NNPDF30_nlo_nf_5_pdfas.info
             (101, "central, 0.117"  ),
             (102, "central, 0.119"  ),],
  '306000': [(  0, "central, 0.118"  ),   # https://lhapdfsets.web.cern.ch/current/NNPDF31_nnlo_hessian_pdfas/NNPDF31_nnlo_hessian_pdfas.info
             (101, "central, 0.116"  ),
             (102, "central, 0.120"  ),],
}
pdfsets['260001'] = pdfsets['260000']
pdfsets['292201'] = pdfsets['292200']
pdfmems['260001'] = pdfmems['260000']
pdfmems['292201'] = pdfmems['292200']


def warning(string,**kwargs):
  print ">>> \033[1m\033[93m%sWARNING!\033[0m\033[93m %s\033[0m"%(kwargs.get('pre',""),string)
  

def main(args):
  simple    = False #args.simple
  verbosity = args.verbosity
  
  nmax  = -1
  sedir = "/pnfs/psi.ch/cms/trivcat/store/user/ineuteli/samples/NANOAOD_201*"
  samples = sorted(glob.glob(sedir+"/*/*/NANOAODSIM"))
  filters = [
    #'ST'
  ]
  vetoes = [
    "LQ", "_old/",
    "W2J", "W3J", "W4J",
    "DY2J", "DY3J", "DY4J",
    "DYJetsToLL_M-1", "DYJetsToLL_M-3", "DYJetsToLL_M-4", "DYJetsToLL_M-5",
  ]
  
  i = 1
  for sample in samples:
    if filters and not any(f in sample for f in filters): continue
    if vetoes and any(v in sample for v in vetoes): continue
    sampleshort = '/'.join(sample.split('/')[-3:-1])
    #print ">>>\n>>> %s"%(sample)
    #print ">>>\n>>> %s"%(sampleshort)
    files = glob.glob(sample+"/*root")[:1]
    if not files:
      warning("No file found for %s"%(sample))
      continue
    fname = files[0]
    #print ">>> %s"%(fname)
    file = TFile.Open(fname)
    if not file or file.IsZombie():
      warning("Could not open file for %s!"%(sampleshort))
      continue
    tree = file.Get('Events')
    if not tree:
      warning("No 'Events' tree found for %s!"%(sampleshort))
      continue
    #npdf = tree.GetBranch('nLHEPdfWeight')
    pdfw = tree.GetBranch('LHEPdfWeight')
    if not pdfw:
      warning("No 'LHEPdfWeight' branch found for %s!"%(sampleshort))
      continue
    hist = TH1F('hist',"LHEPdfWeight",150,0,150)
    out  = tree.Draw("nLHEPdfWeight >> hist","",'gOff')
    npdf = int(hist.GetMean())
    gDirectory.Delete('hist')
    title = pdfw.GetTitle().replace("LHE pdf variation weights",'').replace("(w_var / w_nominal)",''
                          ).replace("for LHA IDs",'').replace(" - ",'-').strip()
    pdfset, errtype = '?', '?'
    for pdfid in pdfsets:
      if pdfid in title:
        pdfset, errtype = pdfsets[pdfid]
        break
    print ">>>  %4s %15s %-27s %-7s %s"%(npdf,title,pdfset,errtype,sampleshort)
    i += 1
    if nmax>0 and i>=nmax: break
  print ">>> "
  

if __name__ == '__main__':
  from argparse import ArgumentParser
  description = """Print NANOAOD."""
  parser = ArgumentParser(prog="printNanoAOD",description=description,epilog="Succes!")
  parser.add_argument('-v', '--verbose', dest='verbosity', type=int, nargs='?', const=1, default=0, action='store',
                                         help="set verbosity" )
  parser.add_argument('-n', '--nevts',   dest='checkevts', action='store_true',
                                         help="check number of events per sample" )
  args = parser.parse_args()
  main(args)
  

