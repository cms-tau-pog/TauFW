# Author: Izaak Neutelings (May 2019)
# Description: Configuration of JEC/JER versions
import os, re
from TauFW.PicoProducer import datadir
from TauFW.common.tools.file import ensurefile


def getjson(era,dtype='data'):
  """Get JSON file of data."""
  # https://twiki.cern.ch/twiki/bin/viewauth/CMS/TWikiLUM
  # https://twiki.cern.ch/twiki/bin/viewauth/CMS/PdmV2016Analysis
  json = None
  if dtype=='data':
    if era==2016:
      json = 'Cert_271036-284044_13TeV_ReReco_07Aug2017_Collisions16_JSON.txt'
    elif era==2017:
      json = 'Cert_294927-306462_13TeV_PromptReco_Collisions17_JSON.txt'
    else:
      json = 'Cert_314472-325175_13TeV_PromptReco_Collisions18_JSON.txt'
  json = ensurefile(datadir,'json',json)
  return json
  

def getera(filename,year,dtype='data'):
  """Get era of data filename."""
  era = ""
  if dtype=='data':
    if isinstance(filename,list):
      filename = filename[0]
    matches = re.findall(r"Run(201[678])([A-Z]+)",filename)
    if not matches:
      print "Warning! Could not find an era in %s"%filename
    elif year!=matches[0][0]:
      print "Warning! Given year does not match the data file %s"%filename
    else:
      era = matches[0][1]
  return era
  

def getjmecalib(year,era="",redoJEC=False,doSys=False,dtype='data'):
  """Get JME calibrator for dataset of a given year and era."""
  # https://twiki.cern.ch/twiki/bin/view/CMS/JECDataMC
  # https://twiki.cern.ch/twiki/bin/view/CMS/JetResolution
  # https://github.com/cms-jet/JECDatabase/raw/master/tarballs/
  # https://github.com/cms-jet/JRDatabase/tree/master/textFiles/
  # https://github.com/cms-nanoAOD/nanoAOD-tools/tree/master/data/jme
  # https://github.com/cms-nanoAOD/nanoAOD-tools/blob/master/python/postprocessing/modules/jme/jetRecalib.py
  # https://github.com/cms-nanoAOD/nanoAOD-tools/blob/master/python/postprocessing/modules/jme/jetmetUncertainties.py
  #from PhysicsTools.NanoAODTools.postprocessing.modules.jme import jetmetUncertainties
  #from PhysicsTools.NanoAODTools.postprocessing.modules.jme.jetmetUncertainties import jetmetUncertaintiesProducer
  from PhysicsTools.NanoAODTools.postprocessing.modules.jme import jetRecalib
  from PhysicsTools.NanoAODTools.postprocessing.modules.jme.jetmetHelperRun2 import createJMECorrector
  if dtype=='data':
    calibrators = { }
    if year==2016:
      calibrators = {
        'BCD': jetRecalib.jetRecalib2016BCD,
        'EF':  jetRecalib.jetRecalib2016EF,
        'GH':  jetRecalib.jetRecalib2016GH,
      }
    elif year==2017:
      calibrators = {
        'B':  jetRecalib.jetRecalib2017B,
        'C':  jetRecalib.jetRecalib2017C,
        'DE': jetRecalib.jetRecalib2017DE,
        'F':  jetRecalib.jetRecalib2017F,
      }
    else:
      calibrators = {
        'A': jetRecalib.jetRecalib2018A,
        'B': jetRecalib.jetRecalib2018B,
        'C': jetRecalib.jetRecalib2018C,
        'D': jetRecalib.jetRecalib2018D,
      }
    for eraset in calibrators:
      if era in eraset:
        return calibrators[eraset]()
    raise "Could not find an appropiate calibrator for year %s and era %s..."%(year,era)
  else:
    jmeUncs = 'Total' if doSys else ''
    MET     = 'METFixEE2017' if year==2017 else 'MET'
    return createJMECorrector(True,year,jesUncert=jmeUncs,redojec=redoJEC,jetType='AK4PFchs',
                              noGroom=True,metBranchName=MET,applySmearing=True)()
    #if year==2016:
    #  #jetmetUncertainties2016 = jetmetUncertaintiesProducer("2016", "Summer16_07Aug2017_V11_MC", jesUncs)
    #  return jetmetUncertainties2016
    #  #return jetmetUncertainties.jetmetUncertainties2016
    #elif year==2017:
    #  jetmetUncertainties2017 = jetmetUncertaintiesProducer("2017", "Fall17_17Nov2017_V32_MC", jesUnc, metBranchName='METFixEE2017', globalTagProd='102X_mc2017_realistic_v7') # GT nanoAODv6
    #  return jetmetUncertainties2017
    #  #return jetmetUncertainties.jetmetUncertainties2017
    #else:
    #  jetmetUncertainties2018 = jetmetUncertaintiesProducer("2018", "Autumn18_V19_MC", jesUncs)
    #  return jetmetUncertainties2018
    #  #return jetmetUncertainties.jetmetUncertainties2018
  
