# CMS_lumi
#  Initiated by: Gautier Hamel de Monchenault (Saclay)
#  Translated in Python by: Joshua Hardenbrook (Princeton)
#  Edited: Izaak Neutelings (July 2018)
#  Sources:
#    https://ghm.web.cern.ch/ghm/plots/
#    https://twiki.cern.ch/twiki/bin/view/CMSPublic/LumiPublicResults#Multi_year_plots
from ROOT import TStyle, TPad, TLatex, TASImage, kBlack, kWhite, TGaxis

cmsText        = "CMS"
cmsTextFont    = 61
writeExtraText = True
extraText      = "Preliminary"
lumiText       = ""
extraTextFont  = 52
lumiTextSize   = 0.90
lumiTextOffset = 0.20
cmsTextSize    = 1.00
cmsTextOffset  = 0.15
extraOverCmsTextSize = 0.78
relPosX        = 0.045
relPosY        = 0.035
relExtraDY     = 1.2
drawLogo       = False
outOfFrame     = False
lumi_dict      = {
  '7':      5.1,    '2016': 35.9,
  '8':      19.7,   '2017': 41.5,
  '2012':   19.7,   '2018': 59.7,
  'Run2':   137.1,
  'Phase2': 3000,
}
cme_dict       = {
  '7':      7,   '2016': 13,
  '8':      8,   '2017': 13,
  '2012':   8,   '2018': 13,
  'Run2':   13,
  'Phase2': 14,
}
era_dict       = {
  '7':      "",         'Run1': "Run 1",
  '8':      "",         'Run2': "Run 2",
  '13':     "Run 2",    'Run3': "Run 3",
  'Phase1': "Phase I",
  'Phase2': "Phase II",
}

def setCMSEra(*eras,**kwargs):
  global cmsText, extraText, lumiText
  cmsText   = "CMS"
  extra     = kwargs.get('extra',None)
  if extra:
    extraText = extra
  strings   = [ ]
  for era in eras:
    era     = str(era)
    string  = era_dict.get(era,   era   )
    lumi    = lumi_dict.get(era,  False )
    cme     = cme_dict.get(era,   False )
    lumi    = kwargs.get('lumi',  lumi  )
    cme     = kwargs.get('cme',   cme   )
    if lumi:
      if string:
        string += ", "
      string += "%s fb^{-1}"%(lumi)
    if cme:
      string += " (%s TeV)"%(cme)
    strings.append(string)
  lumiText = ' + '.join(strings)
  return lumiText
  

def setCMSLumiStyle(pad, iPosX, **kwargs):
  global outOfFrame, lumiTextSize, lumiText
  if iPosX/10==0:
    outOfFrame  = True
  lumiTextSize_ = lumiTextSize
  relPosX_      = kwargs.get('relPosX',  relPosX)
  lumiText_     = kwargs.get('lumiText', lumiText)
  if outOfFrame:
    lumiTextSize_ *= 0.90
  
  if 'era' in kwargs: # one era
    era = kwargs.get('era')
    setCMSEra(era,**kwargs)
  elif 'eras' in kwargs:  # list of multiple eras
    eras = kwargs.get('eras')
    setCMSEra(*eras,**kwargs)
  
  #if lumiText=="":
  #  if iPeriod==1:
  #    lumiText += lumi_7TeV
  #    lumiText += " (7 TeV)"
  #  elif iPeriod==2:
  #    lumiText += lumi_8TeV
  #    lumiText += " (8 TeV)"
  #  elif iPeriod==3:
  #    lumiText = lumi_8TeV
  #    lumiText += " (8 TeV)"
  #    lumiText += " + "
  #    lumiText += lumi_7TeV
  #    lumiText += " (7 TeV)"
  #  elif iPeriod==4:
  #    lumiText += lumi_13TeV
  #    lumiText += " (13 TeV)"
  #  elif iPeriod==7:
  #    if outOfFrame: lumiTextSize_ *= 0.85
  #    lumiText += lumi_13TeV
  #    lumiText += " (13 TeV)"
  #    lumiText += " + "
  #    lumiText += lumi_8TeV
  #    lumiText += " (8 TeV)"
  #    lumiText += " + "
  #    lumiText += lumi_7TeV
  #    lumiText += " (7 TeV)"
  #  elif iPeriod==12:
  #    lumiText += "8 TeV"
  #  else:
  #    if outOfFrame: lumiTextSize_ *= 0.90
  #    if iPeriod==13:
  #      lumiText += lumi_13TeV
  #      lumiText += " (13 TeV)"
  #    elif iPeriod==2016:
  #      lumiText += lumi_2016
  #      lumiText += " (13 TeV)"
  #    elif iPeriod==2017:
  #      lumiText += lumi_2017
  #      lumiText += " (13 TeV)"
  #    elif iPeriod==2018:
  #      lumiText += lumi_2018
  #      lumiText += " (13 TeV)"
  #    elif iPeriod==14:
  #      lumiText += lumi_14TeV
  #      lumiText += " (14 TeV, 200 PU)"
  ##print lumiText
  
  alignY_ = 3
  alignX_ = 2
  if   iPosX==0:    alignY_ = 1
  if   iPosX/10==0: alignX_ = 1
  elif iPosX/10==1: alignX_ = 1
  elif iPosX/10==2: alignX_ = 2
  elif iPosX/10==3: alignX_ = 3
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
    relPosX_ = relPosX_*(50*t*scale)*(cmsTextSize/0.84)
    posX = l + relPosX_*(1-l-r)
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
    if writeExtraText:
      latex.SetTextFont(extraTextFont)
      latex.SetTextSize(extraTextSize*t)
      latex.SetTextAlign(align)
      latex.DrawLatex(posX,posY,extraText)
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
  else:
    latex.SetTextFont(cmsTextFont)
    latex.SetTextSize(cmsTextSize*t)
    latex.SetTextAlign(align)
    latex.DrawLatex(posX,posY,cmsText)
    if writeExtraText:
      latex.SetTextFont(extraTextFont)
      latex.SetTextAlign(align)
      latex.SetTextSize(extraTextSize*t)
      latex.DrawLatex(posX,posY-relExtraDY*cmsTextSize*t,extraText)
  
  pad.Update()
  

def tdrGrid(gridOn):
  tdrStyle.SetPadGridX(gridOn)
  tdrStyle.SetPadGridY(gridOn)
  

def fixOverlay():
  gPad.RedrawAxis()
  

def setTDRStyle():
  
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
  
