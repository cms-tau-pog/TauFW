#! /bin/usr/env python
# Author: Izaak Neutelings (October 2021)
# https://twiki.cern.ch/twiki/bin/viewauth/CMS/MissingETRun2Corrections#xy_Shift_Correction_MET_phi_modu
# https://lathomas.web.cern.ch/lathomas/METStuff/XYCorrections/XYMETCorrection_withUL17andUL18andUL16.h
#from corrections import modulepath, ensureTFile
from math import sqrt
from ROOT import TMath


class METCorrectionTool:
    
  def __init__( self, year=2017, isMC=True):
    """Load Z pT weights."""
    assert year in [2016,2017,2018], "METCorrectionTool: You must choose a year from: 2016, 2017, or 2018."
    
    # MC
    usemetv2 = False
    if isMC:
      if year==2016:
        corrs = (-0.195191, -0.170948, -0.0311891, +0.787627)
      elif year==2017:
        usemetv2 = True
        corrs = (-0.217714, +0.493361, 0.177058,  -0.336648)
      elif year==2018:
        corrs = (0.296713, -0.141506, 0.115685, +0.0128193)
    
    # DATA
    else:
      if year==2016:
        corrs = {
          (272007,275376): (-0.0478335, -0.108032, 0.125148,  +0.355672), # 2016B
          (275657,276283): (-0.0916985, +0.393247, 0.151445,  +0.114491), # 2016C
          (276315,276811): (-0.0581169, +0.567316, 0.147549,  +0.403088), # 2016D
          (276831,277420): (-0.065622,  +0.536856, 0.188532,  +0.495346), # 2016E
          (277772,278808): (-0.0313322, +0.39866,  0.16081,   +0.960177), # 2016F
          (278820,280385): ( 0.040803,  -0.290384, 0.0961935, +0.666096), # 2016G
          (280919,284044): ( 0.0330868, -0.209534, 0.141513,  +0.816732), # 2016H
        }
      elif year==2017:
        usemetv2 = True
        corrs = {
          (297020,299329): (-0.19563,  +1.51859,  0.306987, -1.84713),  # 2017B
          (299337,302029): (-0.161661, +0.589933, 0.233569, -0.995546), # 2017C
          (302030,303434): (-0.180911, +1.23553,  0.240155, -1.27449),  # 2017D
          (303435,304826): (-0.149494, +0.901305, 0.178212, -0.535537), # 2017E
          (304911,306462): (-0.165154, +1.02018,  0.253794, +0.75776),  # 2017F
        }
      elif year==2018:
        corrs = {
          (315252,316995): (0.362865, -1.94505, 0.0709085, -0.307365), # 2018A
          (316998,319312): (0.492083, -2.93552, 0.17874,   -0.786844), # 2018B
          (319313,320393): (0.521349, -1.44544, 0.118956,  -1.96434),  # 2018C
          (320394,325273): (0.531151, -1.37568, 0.0884639, -1.57089),  # 2018D
        }
    
    self.usemetv2 = usemetv2
    self.corrs    = corrs
    self.isMC     = isMC
    
  
  def correct(self,oldmet,oldmetphi,npv,run=-1):
    
    if npv>100: npv = 100
    xcorr = 0.
    ycorr = 0.
    if self.isMC:
      xcorr = self.corrs[0]*npv + self.corrs[1]
      ycorr = self.corrs[2]*npv + self.corrs[3]
    else:
      for (runa,runb), corrs in self.corrs.items():
        if runa<=run<=runb:
          xcorr = corrs[0]*npv + corrs[1]
          ycorr = corrs[2]*npv + corrs[3]
          break
      else:
        print(">>> METCorrectionTool.correct: Could not find run %d in %s"%(run,list(self.corrs.keys())))
        return met, metphi
    
    metx = oldmet*TMath.Cos(oldmetphi) - xcorr
    mety = oldmet*TMath.Sin(oldmetphi) - ycorr
    met  = sqrt( metx*metx + mety*mety )
    metphi = 0
    if(metx==0 and mety>0):
      metphi = TMath.Pi()
    elif(metx==0 and mety<0):
      metphi = -TMath.Pi()
    elif(metx>0):
      metphi = TMath.ATan(mety/metx)
    elif(metx<0 and mety>0):
      metphi = TMath.ATan(mety/metx) + TMath.Pi()
    elif(metx<0 and mety<0):
      metphi = TMath.ATan(mety/metx) - TMath.Pi()
    
    return met, metphi
    
