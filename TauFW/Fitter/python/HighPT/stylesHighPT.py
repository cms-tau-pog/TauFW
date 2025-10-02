import ROOT

#############################################
# ROOT styles (High tau pT analysis)        #
# Author : Alexei Raspereza (December 2022) #
#############################################

eraLumiLabel = {
    "UL2016" : "2016, 36.3 fb^{-1} (13TeV)",
    "UL2016_postVFP" : "2016 postVFP, 16.8 fb^{-1} (13 TeV)",
    "UL2016_preVFP"  : "2016 preVFP, 19.5 fb^{-1} (13TeV)",
    "UL2017" : "2017, 41.5 fb^{-1} (13TeV)",
    "UL2018" : "2018, 59.8 fb^{-1} (13TeV)"
}

def InitROOT():

    ROOT.TH1.SetDefaultSumw2(True)
    ROOT.TH2.SetDefaultSumw2(True)
    ROOT.gROOT.SetBatch(True)


def SetStyle():

    HttStyle = ROOT.TStyle("HttStyle","High pT analysis : ROOT Styles -)")
    ROOT.gStyle = HttStyle
    HttStyle.SetOptStat(0000)
    HttStyle.SetOptFit(0000)    

    # Canvas
    HttStyle.SetCanvasColor     (0)
    HttStyle.SetCanvasBorderSize(10)
    HttStyle.SetCanvasBorderMode(0)
    HttStyle.SetCanvasDefH      (700)
    HttStyle.SetCanvasDefW      (700)
    HttStyle.SetCanvasDefX      (100)
    HttStyle.SetCanvasDefY      (100)

    # pads
    HttStyle.SetPadColor       (0)
    HttStyle.SetPadBorderSize  (10)
    HttStyle.SetPadBorderMode  (0)
    HttStyle.SetPadBottomMargin(0.15)
    HttStyle.SetPadTopMargin   (0.08)
    HttStyle.SetPadLeftMargin  (0.18)
    HttStyle.SetPadRightMargin (0.05)
    HttStyle.SetPadGridX       (0)
    HttStyle.SetPadGridY       (0)
    HttStyle.SetPadTickX       (1)
    HttStyle.SetPadTickY       (1)

    # Frames
    HttStyle.SetLineWidth(3)
    HttStyle.SetFrameFillStyle ( 0)
    HttStyle.SetFrameFillColor ( 0)
    HttStyle.SetFrameLineColor ( 1)
    HttStyle.SetFrameLineStyle ( 0)
    HttStyle.SetFrameLineWidth ( 2)
    HttStyle.SetFrameBorderSize(10)
    HttStyle.SetFrameBorderMode( 0)

    # Histograms
    HttStyle.SetHistFillColor(2)
    HttStyle.SetHistFillStyle(0)
    HttStyle.SetHistLineColor(1)
    HttStyle.SetHistLineStyle(0)
    HttStyle.SetHistLineWidth(3)
    HttStyle.SetNdivisions(505)

    # Functions
    HttStyle.SetFuncColor(1)
    HttStyle.SetFuncStyle(0)
    HttStyle.SetFuncWidth(2)

    # Various
    HttStyle.SetMarkerStyle(20)
    HttStyle.SetMarkerColor(ROOT.kBlack)
    HttStyle.SetMarkerSize (1.4)

    HttStyle.SetTitleBorderSize(0)
    HttStyle.SetTitleFillColor (0)
    HttStyle.SetTitleX         (0.2)

    HttStyle.SetTitleSize  (0.055,"X")
    HttStyle.SetTitleOffset(1.200,"X")
    HttStyle.SetLabelOffset(0.005,"X")
    HttStyle.SetLabelSize  (0.050,"X")
    HttStyle.SetLabelFont  (42   ,"X")

    HttStyle.SetStripDecimals(False)
    HttStyle.SetLineStyleString(11,"20 10")

    HttStyle.SetTitleSize  (0.055,"Y")
    HttStyle.SetTitleOffset(1.600,"Y")
    HttStyle.SetLabelOffset(0.010,"Y")
    HttStyle.SetLabelSize  (0.050,"Y")
    HttStyle.SetLabelFont  (42   ,"Y")

    HttStyle.SetTextSize   (0.055)
    HttStyle.SetTextFont   (42)

    HttStyle.SetStatFont   (42)
    HttStyle.SetTitleFont  (42)
    HttStyle.SetTitleFont  (42,"X")
    HttStyle.SetTitleFont  (42,"Y")

    HttStyle.SetOptStat    (0)

    ROOT.gStyle = HttStyle

def MakeCanvas(name,title,dX,dY):

    # Create canvas
    canvas = ROOT.TCanvas(name,title,dX,dY)
    canvas.SetFillColor      (0)
    canvas.SetBorderMode     (0)
    canvas.SetBorderSize     (10)

    # Set margins to reasonable defaults
    canvas.SetLeftMargin     (0.18)
    canvas.SetRightMargin    (0.05)
    canvas.SetTopMargin      (0.08)
    canvas.SetBottomMargin   (0.15)

    # Setup a frame which makes sense
    canvas.SetFrameFillStyle (0)
    canvas.SetFrameLineStyle (0)
    canvas.SetFrameBorderMode(0)
    canvas.SetFrameBorderSize(10)
    canvas.SetFrameFillStyle (0)
    canvas.SetFrameLineStyle (0)
    canvas.SetFrameBorderMode(0)
    canvas.SetFrameBorderSize(10)
  
    return canvas

def InitModel(hist,color):
    hist.SetFillStyle(0)
    hist.SetLineStyle(1)
    hist.SetLineWidth(2)
    hist.SetLineColor(color)
    hist.SetMarkerStyle(0)
    hist.SetMarkerSize(0)
    hist.SetMarkerColor(0)
    

def InitHist(hist, xtit, ytit, color, style):
    hist.SetXTitle(xtit)
    hist.SetYTitle(ytit)
    hist.SetLineColor(ROOT.kBlack)
    hist.SetLineWidth(    2)
    hist.SetFillColor(color )
    hist.SetFillStyle(style )
    hist.SetTitleSize  (0.055,"Y")
    hist.SetTitleOffset(1.200,"Y")
    hist.SetLabelOffset(0.014,"Y")
    hist.SetLabelSize  (0.040,"Y")
    hist.SetLabelFont  (42   ,"Y")
    hist.SetTitleSize  (0.055,"X")
    hist.SetTitleOffset(1.300,"X")
    hist.SetLabelOffset(0.014,"X")
    hist.SetLabelSize  (0.050,"X")
    hist.SetLabelFont  (42   ,"X")
    hist.SetMarkerStyle(20)
    hist.SetMarkerColor(color)
    hist.SetMarkerSize (0.6)
    hist.GetYaxis().SetTitleFont(42)
    hist.GetXaxis().SetTitleFont(42)
    hist.SetTitle("")  

def InitTotalHist(hist):
    hist.SetFillStyle(3013);
    hist.SetFillColor(1);
    hist.SetMarkerStyle(21);
    hist.SetMarkerSize(0);

def InitData(hist):
    hist.SetMarkerStyle(20)
    hist.SetMarkerSize(1.3)
    hist.SetLineWidth(2)

def InitRatioHist(hist):
    hist.GetXaxis().SetLabelOffset(0.04)
    hist.GetXaxis().SetLabelSize(0.14)
    hist.GetXaxis().SetTitleSize(0.13)
    hist.GetXaxis().SetTitleOffset(1.2)
    hist.GetYaxis().SetLabelFont(42)
    hist.GetYaxis().SetLabelOffset(0.015)
    hist.GetYaxis().SetLabelSize(0.13)
    hist.GetYaxis().SetTitleSize(0.14)
    hist.GetYaxis().SetTitleOffset(0.5)
    hist.GetXaxis().SetTickLength(0.07)
    hist.GetYaxis().SetTickLength(0.04)
    hist.GetYaxis().SetLabelOffset(0.01)
    hist.GetYaxis().SetNdivisions(505)

def SetLegendStyle(leg): 
    leg.SetFillStyle (0)
    leg.SetFillColor (0)
    leg.SetBorderSize(0)

def InitUpperPad(pad):
    pad.SetFillColor(0)
    pad.SetBorderMode(0)
    pad.SetBorderSize(10)
    pad.SetTickx(1)
    pad.SetTicky(1)
    pad.SetLeftMargin(0.17)
    pad.SetRightMargin(0.05)
    pad.SetBottomMargin(0.02)
    pad.SetFrameFillStyle(0)
    pad.SetFrameLineStyle(0)
    pad.SetFrameLineWidth(2)
    pad.SetFrameBorderMode(0)
    pad.SetFrameBorderSize(10)
    pad.SetFrameFillStyle(0)
    pad.SetFrameLineStyle(0)
    pad.SetFrameLineWidth(2)
    pad.SetFrameBorderMode(0)
    pad.SetFrameBorderSize(10)

def InitLowerPad(pad):
    pad.SetFillColor(0)
    pad.SetBorderMode(0)
    pad.SetBorderSize(10)
    pad.SetGridy()
    pad.SetTickx(1)
    pad.SetTicky(1)
    pad.SetLeftMargin(0.17)
    pad.SetRightMargin(0.05)
    pad.SetTopMargin(0.026)
    pad.SetBottomMargin(0.35)
    pad.SetFrameFillStyle(0)
    pad.SetFrameLineStyle(0)
    pad.SetFrameLineWidth(2)
    pad.SetFrameBorderMode(0)
    pad.SetFrameBorderSize(10)
    pad.SetFrameFillStyle(0)
    pad.SetFrameLineStyle(0)
    pad.SetFrameLineWidth(2)
    pad.SetFrameBorderMode(0)
    pad.SetFrameBorderSize(10)

def CMS_label(pad,**kwargs):

    iPeriod = kwargs.get('Period',4)
    iPosX = kwargs.get('PosX',33)
    writeExtraText = kwargs.get('writeExtraText',True)
    era = kwargs.get('era',"UL2018")
    extraText = kwargs.get('extraText',"Internal")

    lumiText = eraLumiLabel[era]

    extraTextFont = 52  #

    cmsText = "CMS"
    cmsTextFont = 61  # default is helvetic-bold

    # text sizes and text offsets with respect to the top frame
    # in unit of the top margin size
    lumiTextSize     = 0.6
    lumiTextOffset   = 0.2
    cmsTextSize      = 0.75
    cmsTextOffset    = 0.1 # only used in outOfFrame version
    
    relPosX    = 0.045
    relPosY    = 0.035
    relExtraDY = 1.2

    # ratio of "CMS" and extra text size
    extraOverCmsTextSize  = 0.76

    outOfFrame    = False
    alignY_=3
    alignX_=2
    if iPosX/10==0: 
        alignX_=1
    if iPosX==0:
        alignX_=1
    if iPosX/10==1: 
        alignX_=1
    if iPosX/10==2: 
        alignX_=2
    if iPosX/10==3: 
        alignX_=3
    if iPosX == 0: 
        relPosX = 0.12
  
    align_ = 10*alignX_ + alignY_

    H = pad.GetWh()
    W = pad.GetWw()
    l = pad.GetLeftMargin()
    t = pad.GetTopMargin()
    r = pad.GetRightMargin()
    b = pad.GetBottomMargin()

    pad.cd()

    latex = ROOT.TLatex()
    latex.SetNDC()
    latex.SetTextAngle(0)
    latex.SetTextColor(ROOT.kBlack)    

    extraTextSize = extraOverCmsTextSize*cmsTextSize

    latex.SetTextFont(42)
    latex.SetTextAlign(31) 
    latex.SetTextSize(lumiTextSize*t)    
    latex.DrawLatex(1-r,1-t+lumiTextOffset*t,lumiText)
  
    if outOfFrame:
        latex.SetTextFont(cmsTextFont)
        latex.SetTextAlign(11) 
        latex.SetTextSize(cmsTextSize*t)    
        latex.DrawLatex(l,1-t+lumiTextOffset*t,cmsText)
  
    pad.cd()

    posX_=0.
    if iPosX%10<=1:
        posX_ =   l + relPosX*(1-l-r)
    if iPosX%10==2:
        posX_ =  l + 0.5*(1-l-r)
    if iPosX%10==3:
        posX_ =  1-r - relPosX*(1-l-r)

    posY_ = 1-t - relPosY*(1-t-b)

    if not outOfFrame:
        latex.SetTextFont(cmsTextFont)
        latex.SetTextSize(cmsTextSize*t)
        latex.SetTextAlign(align_)
        latex.DrawLatex(posX_, posY_, cmsText)
        if  writeExtraText:
            latex.SetTextFont(extraTextFont)
            latex.SetTextAlign(align_)
            latex.SetTextSize(extraTextSize*t)
            latex.DrawLatex(posX_, posY_- relExtraDY*cmsTextSize*t + 0.01, extraText)
    elif writeExtraText:
        if iPosX==0: 
            posX_ =   l +  relPosX*(1-l-r)
            posY_ =   1-t+lumiTextOffset*t
        latex.SetTextFont(extraTextFont)
        latex.SetTextSize(extraTextSize*t)
        latex.SetTextAlign(align_)
        latex.DrawLatex(posX_, posY_+0.7, extraText)      
