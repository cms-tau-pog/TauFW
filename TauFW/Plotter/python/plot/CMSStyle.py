# Initiated by: Gautier Hamel de Monchenault (Saclay)
# Translated in Python by: Joshua Hardenbrook (Princeton)
# Edited: Izaak Neutelings (July 2018)
# CMS guidelines:
#   https://ghm.web.cern.ch/ghm/plots/
#   https://twiki.cern.ch/twiki/bin/view/CMS/Internal/FigGuidelines
#   https://twiki.cern.ch/twiki/bin/view/CMS/Internal/Publications
#   https://twiki.cern.ch/twiki/bin/view/CMS/PhysicsApprovals
# CMS luminosity:
#   https://twiki.cern.ch/twiki/bin/viewauth/CMS/TWikiLUM
#   https://twiki.cern.ch/twiki/bin/view/CMSPublic/LumiPublicResults#Multi_year_plots
# ROOT settings:
#   https://root.cern.ch/doc/master/classTAttText.html
# Instructions:
# 1a) Set extra text and luminosity with CMSStyle.setCMSEra:
#   import TauFW.Plotter.plot.CMSStyle as CMSStyle
#   CMSStyle.setCMSEra(2018) # use default settings
#   CMSStyle.setCMSEra(2018,lumi=59.7,cme=13,extra="Preliminary") # override default
#   CMSStyle.setCMSEra(era='Run 2',lumi=None,thesis=True,extra="(CMS simulation)")
# 1b) Or set it manually:
#   CMSStyle.extraText = "Preliminary"
#   CMSStyle.lumiText = "59.7 fb^{#minus1} (13 TeV)"
#   CMSStyle.outOfFrame = True
# 2) Pass TCanvas:
#   CMSStyle.setTDRStyle() # set CMS TDR style
#   CMSStyle.setCMSLumiStyle(gPad,0) # add CMS text & lumi
from __future__ import print_function # for python3 compatibility
from ROOT import TStyle, TPad, TLatex, TASImage, kBlack, kWhite, TGaxis
import re

cmsText        = "CMS"
cmsTextFont    = 61 # 60: Arial bold (helvetica-bold-r-normal)
# Guidelines for labels:
#   https://twiki.cern.ch/twiki/bin/view/CMS/Internal/FigGuidelines#Use_of_the_Preliminary_Simulatio
#   https://twiki.cern.ch/twiki/bin/view/CMS/PhysicsApprovals#Student_presentations_of_unappro
#   E.g. "Preliminary", "Simulation", "Simulation Preliminary", "Supplementary", "Work in progress", ...
#extraText      = "Preliminary"
extraText      = "Internal"
lumiText       = ""
extraTextFont  = 52 # 50: Arial italics (helvetica-medium-o-normal)
lumiTextSize   = 0.90
lumiTextOffset = 0.20
cmsTextSize    = 1.00
cmsTextOffset  = 0.15
extraOverCmsTextSize = 0.78
relPosX        = 0.044 # relative x position of "extraText" w.r.t. cmsText
relPosY        = 0.035
relExtraDY     = 1.2
drawLogo       = False
outOfFrame     = True
lumi_dict      = {
  '7':      5.1,  '2016': 36.3, 'UL2016_preVFP':  19.5,
  '8':      19.7, '2017': 41.5, 'UL2016_postVFP': 16.8,
  '2012':   19.7, '2018': 59.7, 'UL2016': 36.3, # actually 19.5+16.8=36.3
  'Run2':   138,                'UL2017': 41.5,
                                'UL2018': 59.8,
  'Run3':   64.0, # to be updated
  'Phase2': 3000,
  '2022': 35.0842,
  '2022_preEE': 8.077,
  '2022_postEE': 27.0072,
  '2023': 26.585,
  '2023C' : 17.060,
  '2023D' : 9.525,
  '2024' : 90.355,
}
cme_dict       = {
  '7':      7,    '2016': 13,
  '8':      8,    '2017': 13,
  '2012':   8,    '2018': 13,
  'Run2':   13,   '2022': 13.6,
  'Run3':   13.6, '2023': 13.6,
  '2024':   13.6, 'Phase2': 14,   
}
era_dict       = {
  '7':      "",         'Run1': "Run 1",
  '8':      "",         'Run2': "Run 2",
  '13':     "Run 2",    'Run3': "Run 3",
  'Phase1': "Phase I",
  'Phase2': "Phase II",
  'UL2016_preVFP': "UL2016", #(pre VFP)
  'UL2016_postVFP': "UL2016", #(post VFP)
  'UL2016': "UL2016",
  'UL2017': "UL2017",
  'UL2018': "UL2018",
  '2022_preEE': "2022 (preEE)",
  '2022_postEE': "2022 (postEE)",
  '2023C': "2023C (pre BPix)",
  '2023D': "2023D (post BPix)",
  '2024': "2024",
}


def getyear(era):
  """If possible, return string of year without extra text.
  E.g. 'UL2016_preVFP' -> '2016', 'UL2018' -> '2018', etc.
  """
  if era:
    match = re.search(r"(?<!\d)(20\d{2})(?!\d)",era)
    if match:
      return match.group(1)
  return era
  

def setCMSText(**kwargs):
  """Set global CMS text and extra text."""
  global cmsText, extraText, cmsTextSize, cmsTextFont, extraTextFont, lumiText, lumiTextSize, relPosX
  if kwargs.get('thesis',False): # special labels for results not approved, nor unendorsed by CMS
    # Set CMS style for thesis with for results not approved, nor unendorsed by CMS.
    # https://twiki.cern.ch/twiki/bin/view/CMS/PhysicsApprovals#Thesis_endorsement
    kwargs.setdefault('cms',          "Private work" )
    kwargs.setdefault('extra',        "(CMS data/simulation)" )
    kwargs.setdefault('cmsTextFont',  42         ) # 40: Arial (helvetica-medium-r-normal)
    kwargs.setdefault('extraTextFont',42         ) # 40: Arial (helvetica-medium-r-normal)
    kwargs.setdefault('cmsTextSize',  0.74       )
    kwargs.setdefault('lumiTextSize', 0.84       )
    kwargs.setdefault('relPosX',      2.36*0.045 )
  if 'cms' in kwargs:
    cmsText = kwargs['cms'] # CMS text in bold, e.g. "CMS"
  if 'cmsTextSize' in kwargs:
    cmsTextSize = kwargs['cmsTextSize']
  if 'cmsTextFont' in kwargs:
    cmsTextFont = kwargs['cmsTextFont']
  if 'extra' in kwargs:
    extraText = kwargs['extra'] # extra text, e.g. 'Preliminary'
  if 'extraTextFont' in kwargs:
    extraTextFont = kwargs['extraTextFont']
  if 'lumiText' in kwargs:
    lumiText = kwargs['lumiText'] # luminosity text, e.g. '138 fb^{#minus1} (13 TeV)'
  if 'lumiTextSize' in kwargs:
    lumiTextSize = kwargs['lumiTextSize'] # text size for both extraText & lumiText
  if 'relPosX' in kwargs:
    relPosX = kwargs['relPosX'] # relative x position between 'CMS' and extra text
  if kwargs.get('verb',0)>=2:
    print(">>> setCMSText: cmsText=%r, extraText=%r, lumiText=%r"%(cmsText,extraText,lumiText))
  return extraText
  

def setCMSEra(*eras,**kwargs):
  """Set global CMS lumiText for given era(s)."""
  global cmsText, extraText, lumiText
  strings = [ ]
  if 'lumiText' in kwargs: # set by user
    strings.append(kwargs['lumiText'])
  elif eras: # set automatically based on given era(s)
    for i, era in enumerate(eras):
      cmes = kwargs.get('cme',None)
      if cmes and isinstance(cmes,(list,tuple)):
        kwargs['cme'] = cmes[i] # asumme same length as eras
      strings.append(getCMSLumiText(era,**kwargs))
  else: # try to set lumiText with just lumi & cme
    return setCMSLumi(**kwargs)
  verb = kwargs.pop('verb', 0 ) # verbosity level, disable for setCMSText
  setCMSText(**kwargs) # set cmsText, extraText
  lumiText = ' + '.join(s for s in strings if s) # set globally
  if verb>=2:
    print(">>> setCMSEra: cmsText=%r, extraText=%r, eras=%r, lumiText=%r"%(cmsText,extraText,eras,lumiText))
  return lumiText
  

def setCMSLumi(lumi=None,cme=None,**kwargs):
  """Set global CMS lumiText for given integrated luminosity & CME."""
  global cmsText, extraText, lumiText
  strings = [ ]
  verb = kwargs.pop('verb', 0 ) # verbosity level, disable for setCMSText
  if 'lumiText' in kwargs: # set by user
    strings.append(kwargs['lumiText'])
  elif lumi: # print lumi
    lumis = lumi if isinstance(lumi,(list,tuple)) else [lumi] # ensure list
    cmes  = cme if isinstance(cme,(list,tuple)) else [cme] # ensure list
    for i, lumi_ in enumerate(lumis):
      kwargs['lumi'] = lumi_
      kwargs['cme']  = cmes[i] if i<len(cmes) else cmes[-1]
      strings.append(getCMSLumiText(**kwargs))
  elif cme: # only print CME
    strings = ["(%s TeV)"%cme]
  elif verb>=1:
    print(">>> setCMSLumi: Warning! No lumi or CME passed !?")
  setCMSText(**kwargs) # set cmsText, extraText
  lumiText = ' + '.join(s for s in strings if s) # set globally
  if verb>=2:
    print(">>> setCMSLumi: cmsText=%r, extraText=%r, lumiText=%r"%(cmsText,extraText,lumiText))
  return lumiText
  

def getCMSLumiText(era=None,showEra=True,showYear=False,**kwargs):
  """Help function to create lumiText (string containing integrated luminosity)
  and center-of-mass energy for top right corner of CMS plots.
  E.g. UL2016_preVFP, 19.5 fb^{#minus1} (13 TeV)"""
  text = "" # return value
  year = None
  lumi = None
  cme  = None
  verb = kwargs.get('verb', 0 ) # verbosity level
  if era:
    era  = str(era) # ensure string
    year = getyear(era) # get year from e.g. 'UL2016_preVFP' -> '2016', '2018' -> '2018'
    if showYear: # print year in lumiText, e.g. "2016, 19.5 fb^{#minus1} (13 TeV)"
      text = era_dict.get(year,year)
    elif showEra: # print era in lumiText, e.g. "UL2016_preVFP, 19.5 fb^{#minus1} (13 TeV)"
      text = era_dict.get(era,era)
  if 'lumi' in kwargs: # allow override by user, incl. lumi=None/False to suppress
    lumi = kwargs['lumi']
  else: # lookup given era/year in global dictionary
    lumi = lumi_dict[era] if era in lumi_dict else lumi_dict.get(year,None)
  if 'cme' in kwargs: # allow override by user, incl. lumi=None/False to suppress
    cme  = kwargs['cme'] # center-of-mass energy in TeV, e.g. 13
  else: # lookup given era/year in global dictionary
    cme  = cme_dict[era] if era in cme_dict else cme_dict.get(year,None)
  if lumi: # print if defined
    if text: # add comma after era/year
      text += ", "
    lumi3sd = ("%#.3g"%lumi) if lumi<1000 else ("%d"%float("%.3g"%lumi)) # three significant digits
    text += lumi3sd.rstrip('.') + " fb^{#minus1}"
  if cme: # print if defined
    if text:
      text += " "
    text += "(%s TeV)"%(cme)
  text = text.strip() # remove empty spaces in front/back
  if verb>=4:
    print(">>> getCMSLumiText: era=%r, lumi=%r, cme=%r, lumiText=%r"%(era,lumi,lumiText,cme))
  return text
  

def setCMSLumiStyle(pad, iPosX=0, **kwargs):
  """Set CMS style for a given TPad."""
  global outOfFrame, lumiTextSize, lumiText, extraText
  if 'era' in kwargs: # one era
    era = kwargs.get('era')
    setCMSEra(era,**kwargs)
  elif 'eras' in kwargs:  # list of multiple eras
    eras = kwargs.get('eras')
    setCMSEra(*eras,**kwargs)
  if iPosX/10==0:
    outOfFrame  = True
  lumiTextSize_ = lumiTextSize
  relPosX_      = kwargs.get('relPosX',    relPosX    ) # relative position between 'CMS' and extra text
  lumiText_     = kwargs.get('lumiText',   lumiText   ) # luminosity text, e.g. '138 fb^{#minus1} (13 TeV)'
  extraText_    = kwargs.get('extraText',  extraText  ) # 'Preliminary', 'Simulation', ...
  outOfFrame    = kwargs.get('outOfFrame', outOfFrame ) # print CMS text outside frame
  verbosity     = kwargs.get('verb',       0          ) # verbosity level
  if outOfFrame:
    lumiTextSize_ *= 0.90
  if verbosity>=2:
    print(">>> setCMSLumiStyle: cmsText=%r, extraText=%r, lumiText=%r"%(cmsText,extraText_,lumiText))
  
  # https://root.cern.ch/doc/master/classTAttText.html#ATTTEXT1
  alignY_ = 3 # align top
  alignX_ = 2 # align center
  if   iPosX==0:     alignY_ = 1 # align bottom
  if   iPosX//10==0: alignX_ = 1 # align left
  elif iPosX//10==1: alignX_ = 1 # align left
  elif iPosX//10==2: alignX_ = 2 # align center
  elif iPosX//10==3: alignX_ = 3 # align right
  align = 10*alignX_ + alignY_
  extraTextSize = extraOverCmsTextSize*cmsTextSize
  
  H = pad.GetWh()*pad.GetHNDC()
  W = pad.GetWw()*pad.GetWNDC()
  l = pad.GetLeftMargin()
  t = pad.GetTopMargin()
  r = pad.GetRightMargin()
  b = pad.GetBottomMargin()
  e = 0.025
  scale = float(H)/W if W>H else 1 # float(W)/H
  pad.cd()
  
  latex = TLatex()
  latex.SetNDC()
  latex.SetTextAngle(0)
  latex.SetTextColor(kBlack)
  latex.SetTextFont(42)
  latex.SetTextAlign(31)
  latex.SetTextSize(lumiTextSize_*t)
  
  if lumiText_:
    latex.DrawLatex(1-r,1-t+lumiTextOffset*t,lumiText_)
  
  if iPosX==0:
    relPosX_ = relPosX_*(42*t*scale)*(cmsTextSize/0.84) # scale
    posX = l + relPosX_ #*(1-l-r)
    posY = 1 - t + lumiTextOffset*t
  else:
    posX = 0
    posY = 1 - t - relPosY*(1-t-b)
    if iPosX%10<=1:
      posX = l + relPosX_*(1-l-r)     # left aligned
    elif iPosX%10==2:
      posX = l + 0.5*(1-l-r)          # centered
    elif iPosX%10==3:
      posX = 1 - r - relPosX_*(1-l-r) # right aligned
  
  if outOfFrame:
    TGaxis.SetExponentOffset(-0.12*float(H)/W,0.015,'y')
    latex.SetTextFont(cmsTextFont)
    latex.SetTextAlign(11)
    latex.SetTextSize(cmsTextSize*t)
    latex.DrawLatex(l,1-t+lumiTextOffset*t,cmsText)
    if extraText_:
      latex.SetTextFont(extraTextFont)
      latex.SetTextSize(extraTextSize*t)
      latex.SetTextAlign(align)
      latex.DrawLatex(posX,posY,extraText_)
  elif drawLogo:
    posX =     l + 0.045*(1-l-r)*W/H
    posY = 1 - t - 0.045*(1-t-b)
    xl_0 = posX
    yl_0 = posY - 0.15
    xl_1 = posX + 0.15*H/W
    yl_1 = posY
    CMS_logo = TASImage("CMS-BW-label.png")
    pad_logo = TPad("logo","logo",xl_0,yl_0,xl_1,yl_1 )
    pad_logo.Draw()
    pad_logo.cd()
    CMS_logo.Draw('X')
    pad_logo.Modified()
    pad.cd()
  else: # inside frame
    latex.SetTextFont(cmsTextFont)
    latex.SetTextSize(cmsTextSize*t)
    latex.SetTextAlign(align)
    latex.DrawLatex(posX,posY,cmsText)
    if extraText_:
      lines = extraText_.split('\n') if '\n' in extraText_ else [extraText_]
      latex.SetTextFont(extraTextFont)
      latex.SetTextAlign(align)
      latex.SetTextSize(extraTextSize*t)
      for i, line in enumerate(lines):
        latex.DrawLatex(posX,posY-(relExtraDY+i)*cmsTextSize*t,line)
  
  if verbosity>=2:
    print(">>> setCMSLumiStyle: outOfFrame=%r, iPosX=%s, alignX_=%s, align=%s"%(outOfFrame,iPosX,alignX_,align))
    print(">>> setCMSLumiStyle: extraTextSize=%s, extraOverCmsTextSize=%s, cmsTextSize=%s"%(extraTextSize,extraOverCmsTextSize,cmsTextSize))
    print(">>> setCMSLumiStyle: posX=%s, posY=%s, relPosX_=%s"%(posX,posY,relPosX_))
  
  pad.SetTicks(1,1) # ticks on all four sides
  pad.Update()
  

def tdrGrid(gridOn):
  tdrStyle.SetPadGridX(gridOn)
  tdrStyle.SetPadGridY(gridOn)
  

def fixOverlay():
  gPad.RedrawAxis()
  

def setTDRStyle(**kwargs):
  global outOfFrame, extraText
  if 'outOfFrame' in kwargs:
    outOfFrame = kwargs['outOfFrame']
  if 'extra' in kwargs:
    extraText = kwargs['extra']
  
  tdrStyle = TStyle("tdrStyle","Style for P-TDR")
  
  # For the canvas:
  tdrStyle.SetCanvasBorderMode(0)
  tdrStyle.SetCanvasColor(kWhite)
  tdrStyle.SetCanvasDefH(600) # height of canvas
  tdrStyle.SetCanvasDefW(600) # width of canvas
  tdrStyle.SetCanvasDefX(0)   # position on screen
  tdrStyle.SetCanvasDefY(0)
  
  tdrStyle.SetPadBorderMode(0)
  #tdrStyle.SetPadBorderSize(Width_t size = 1)
  tdrStyle.SetPadColor(kWhite)
  tdrStyle.SetPadGridX(False)
  tdrStyle.SetPadGridY(False)
  tdrStyle.SetGridColor(0)
  tdrStyle.SetGridStyle(3)
  tdrStyle.SetGridWidth(1)
  
  # For the frame:
  tdrStyle.SetFrameBorderMode(0)
  tdrStyle.SetFrameBorderSize(1)
  tdrStyle.SetFrameFillColor(0)
  tdrStyle.SetFrameFillStyle(0)
  tdrStyle.SetFrameLineColor(1)
  tdrStyle.SetFrameLineStyle(1)
  tdrStyle.SetFrameLineWidth(1)
  
  # For the histo:
  #tdrStyle.SetHistFillColor(1)
  #tdrStyle.SetHistFillStyle(0)
  tdrStyle.SetHistLineColor(1)
  tdrStyle.SetHistLineStyle(1)
  tdrStyle.SetHistLineWidth(1)
  #tdrStyle.SetLegoInnerR(Float_t rad = 0.5)
  #tdrStyle.SetNumberContours(Int_t number = 20)
  
  tdrStyle.SetEndErrorSize(2)
  #tdrStyle.SetErrorMarker(20)
  tdrStyle.SetErrorX(0)
  tdrStyle.SetMarkerStyle(20)
  
  # For the fit/function:
  tdrStyle.SetOptFit(1)
  tdrStyle.SetFitFormat("5.4g")
  tdrStyle.SetFuncColor(2)
  tdrStyle.SetFuncStyle(1)
  tdrStyle.SetFuncWidth(1)
  
  # For the date:
  tdrStyle.SetOptDate(0)
  #tdrStyle.SetDateX(Float_t x = 0.01)
  #tdrStyle.SetDateY(Float_t y = 0.01)
  
  # For the statistics box:
  tdrStyle.SetOptFile(0)
  tdrStyle.SetOptStat(0) # to display the mean and RMS:   SetOptStat("mr")
  tdrStyle.SetStatColor(kWhite)
  tdrStyle.SetStatFont(42)
  tdrStyle.SetStatFontSize(0.025)
  tdrStyle.SetStatTextColor(1)
  tdrStyle.SetStatFormat("6.4g")
  tdrStyle.SetStatBorderSize(1)
  tdrStyle.SetStatH(0.1)
  tdrStyle.SetStatW(0.15)
  #tdrStyle.SetStatStyle(Style_t style = 1001)
  #tdrStyle.SetStatX(Float_t x = 0)
  #tdrStyle.SetStatY(Float_t y = 0)
  
  # For pad margins:
  tdrStyle.SetPadTopMargin(0.05)
  tdrStyle.SetPadBottomMargin(0.13)
  tdrStyle.SetPadLeftMargin(0.16)
  tdrStyle.SetPadRightMargin(0.02)
  
  # For the Global title:
  tdrStyle.SetOptTitle(0)
  tdrStyle.SetTitleFont(42)
  tdrStyle.SetTitleColor(1)
  tdrStyle.SetTitleTextColor(1)
  tdrStyle.SetTitleFillColor(10)
  tdrStyle.SetTitleFontSize(0.05)
  #tdrStyle.SetTitleH(0) # set the height of the title box
  #tdrStyle.SetTitleW(0) # set the width of the title box
  #tdrStyle.SetTitleX(0) # set the position of the title box
  #tdrStyle.SetTitleY(0.985) # set the position of the title box
  #tdrStyle.SetTitleStyle(Style_t style = 1001)
  #tdrStyle.SetTitleBorderSize(2)
  
  # For the axis titles:
  tdrStyle.SetTitleColor(1, 'XYZ')
  tdrStyle.SetTitleFont(42, 'XYZ')
  tdrStyle.SetTitleSize(0.06, 'XYZ')
  # tdrStyle.SetTitleXSize(Float_t size = 0.02) # another way to set the size?
  # tdrStyle.SetTitleYSize(Float_t size = 0.02)
  tdrStyle.SetTitleXOffset(0.9)
  tdrStyle.SetTitleYOffset(1.25)
  # tdrStyle.SetTitleOffset(1.1, 'Y') # another way to set the Offset
  
  # For the axis labels:
  tdrStyle.SetLabelColor(1, 'XYZ')
  tdrStyle.SetLabelFont(42, 'XYZ')
  tdrStyle.SetLabelOffset(0.007, 'XYZ')
  tdrStyle.SetLabelSize(0.05, 'XYZ')
  
  # For the axis:
  tdrStyle.SetAxisColor(1, 'XYZ')
  tdrStyle.SetStripDecimals(True)
  tdrStyle.SetTickLength(0.03, 'XYZ')
  tdrStyle.SetNdivisions(510, 'XYZ')
  tdrStyle.SetPadTickX(1) # to get tick marks on the opposite side of the frame
  tdrStyle.SetPadTickY(1)
  
  # Change for log plots:
  tdrStyle.SetOptLogx(0)
  tdrStyle.SetOptLogy(0)
  tdrStyle.SetOptLogz(0)
  
  # Postscript options:
  tdrStyle.SetPaperSize(20.,20.)
  #tdrStyle.SetLineScalePS(Float_t scale = 3)
  #tdrStyle.SetLineStyleString(Int_t i, const char* text)
  #tdrStyle.SetHeaderPS(const char* header)
  #tdrStyle.SetTitlePS(const char* pstitle)
  
  #tdrStyle.SetBarOffset(Float_t baroff = 0.5)
  #tdrStyle.SetBarWidth(Float_t barwidth = 0.5)
  #tdrStyle.SetPaintTextFormat(const char* format = "g")
  #tdrStyle.SetPalette(Int_t ncolors = 0, Int_t* colors = 0)
  #tdrStyle.SetTimeOffset(Double_t toffset)
  #tdrStyle.SetHistMinimumZero(True)
  
  tdrStyle.SetHatchesLineWidth(5)
  tdrStyle.SetHatchesSpacing(0.05)
  
  tdrStyle.cd()
  
