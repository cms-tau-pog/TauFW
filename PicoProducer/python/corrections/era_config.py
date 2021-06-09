# Author: Izaak Neutelings (May 2019)
# Description: Configuration of JEC/JER versions
import os, re
from TauFW.PicoProducer import datadir
from TauFW.common.tools.file import ensurefile
from TauFW.common.tools.utils import getyear


def getjson(era,dtype='data'):
  """Get JSON file of data."""
  # https://twiki.cern.ch/twiki/bin/viewauth/CMS/TWikiLUM
  # https://twiki.cern.ch/twiki/bin/viewauth/CMS/PdmV2016Analysis
  json = None
  year = getyear(era)
  if dtype=='data':
    if 'UL' in era:
      if year==2016:
        json = 'Cert_271036-284044_13TeV_Legacy2016_Collisions16_JSON.txt'
      elif year==2017:
        json = 'Cert_294927-306462_13TeV_UL2017_Collisions17_GoldenJSON.txt'
      elif year==2018:
        json = 'Cert_314472-325175_13TeV_Legacy2018_Collisions18_JSON.txt'
    else:
      if year==2016:
        json = 'Cert_271036-284044_13TeV_ReReco_07Aug2017_Collisions16_JSON.txt'
      elif year==2017:
        json = 'Cert_294927-306462_13TeV_PromptReco_Collisions17_JSON.txt'
      elif year==2018:
        json = 'Cert_314472-325175_13TeV_PromptReco_Collisions18_JSON.txt'
      print "Warning! Using outdated certified run JSON file %s for era %s... Please move to UltraLegacy (UL)!"%(json,era)
    assert json!=None, "getjson: Did not find certified run JSON for era %r, year %r"%(era,year)
  json = ensurefile(datadir,'json',str(year),json)
  return json
  

def getperiod(filename,year=None,dtype='data'):
  """Get run era/period (A-H) of data filename containing Run20[0-4][0-9][A-Z].
  If the optional parameter 'year' is given, double check match corresponds."""
  period = ""
  if dtype=='data':
    if isinstance(filename,list):
      filename = filename[0]
    matches = re.findall(r"Run(20[0-4][0-9])([A-Z]+)",filename)
    if not matches:
      print "Warning! Could not find an era in %s"%filename
    elif year and str(year)!=matches[0][0]:
      print "Warning! Given year (%r) does not match the data file %s (%r)"%(year,filename,''.join(matches[0]))
    else:
      period = matches[0][1]
  return period
  

def getjmecalib(era,period="",redoJEC=False,doSys=False,dtype='data'):
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
  #from PhysicsTools.NanoAODTools.postprocessing.modules.jme import jetRecalib
  from PhysicsTools.NanoAODTools.postprocessing.modules.jme.jetmetHelperRun2 import createJMECorrector
  year = getyear(era) # get year as integer
  if dtype=='data':
    #calibrators = { }
    #if year==2016:
    #  calibrators = {
    #    'BCD': jetRecalib.jetRecalib2016BCD,
    #    'EF':  jetRecalib.jetRecalib2016EF,
    #    'GH':  jetRecalib.jetRecalib2016GH,
    #  }
    #elif year==2017:
    #  calibrators = {
    #    'B':  jetRecalib.jetRecalib2017B,
    #    'C':  jetRecalib.jetRecalib2017C,
    #    'DE': jetRecalib.jetRecalib2017DE,
    #    'F':  jetRecalib.jetRecalib2017F,
    #  }
    #else:
    #  calibrators = {
    #    'A': jetRecalib.jetRecalib2018A,
    #    'B': jetRecalib.jetRecalib2018B,
    #    'C': jetRecalib.jetRecalib2018C,
    #    'D': jetRecalib.jetRecalib2018D,
    #  }
    #for eraset in calibrators:
    #  if period in eraset:
    #    return calibrators[eraset]()
    #raise "Could not find an appropiate calibrator for year %s and era %s..."%(year,period)
    return createJMECorrector(False,era,runPeriod=period,jesUncert=jmeUncs,redojec=redoJEC,jetType='AK4PFchs',
                              noGroom=True,metBranchName=MET,applySmearing=False)()
  else:
    jmeUncs = 'Total' if doSys else ''
    MET     = 'METFixEE2017' if (year==2017 and 'UL' not in era) else 'MET'
    return createJMECorrector(True,era,jesUncert=jmeUncs,redojec=redoJEC,jetType='AK4PFchs',
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
  
