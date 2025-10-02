'''
\package tdrstyle

Provides pythonized version of CMS TDR style
'''
# Author: Konstantinos Christoforou (Feb 2022)
#================================================================================================    
# Imports
#================================================================================================    
import ROOT
from array import array

#================================================================================================    
# Class definition
#================================================================================================    
class TDRStyle:
    '''
    TDR style class
    
    Translated from C++
    '''
    def __init__(self):
        '''
        Apply the default tdr style in the constructor
        '''
        self.tdrStyle = ROOT.TStyle("self.tdrStyle", "Style for P-TDR")
        self.defaultStat = ""
        self.mode = ""

        self.canvasH = 600
        self.canvasW = 600

        #absoluteSize = False
        absoluteSize = True

        if absoluteSize:
            # helvetica, size absolute
            self.font = 43
            self.titleSize = 33
            self.labelSize = 27
            self.statSize = 14
        else:
            # helvetica, size w.r.t. pad size
            self.font = 42
            self.titleSize = 0.06
            self.labelSize = 0.05
            self.statSize = 0.025

        # for the canvas
        self.tdrStyle.SetCanvasBorderMode(0)
        self.tdrStyle.SetCanvasColor(ROOT.kWhite)
        self.tdrStyle.SetCanvasDefH(self.canvasH) # Height of canvas
        self.tdrStyle.SetCanvasDefW(self.canvasW) # Width of canvas
        # These modifications are in order to get the frame area square
        # Cf. SetPad*Margin
        #self.tdrStyle.SetCanvasDefH(740) # Height of canvas
        #self.tdrStyle.SetCanvasDefW(820) # Width of canvas
        self.tdrStyle.SetCanvasDefX(0)   # POsition on screen
        self.tdrStyle.SetCanvasDefY(0)

        # For the Pad:
        self.tdrStyle.SetPadBorderMode(0)
        self.tdrStyle.SetPadColor(ROOT.kWhite)
        self.tdrStyle.SetPadGridX(False)
        self.tdrStyle.SetPadGridY(False)
        self.tdrStyle.SetGridColor(0)
        self.tdrStyle.SetGridStyle(3)
        self.tdrStyle.SetGridWidth(1)

        # For the frame:
        self.tdrStyle.SetFrameBorderMode(0)
        self.tdrStyle.SetFrameBorderSize(1)
        self.tdrStyle.SetFrameFillColor(0)
        self.tdrStyle.SetFrameFillStyle(0)
        self.tdrStyle.SetFrameLineColor(1)
        self.tdrStyle.SetFrameLineStyle(1)
        self.tdrStyle.SetFrameLineWidth(1)

        # For the histo:
        # self.tdrStyle.SetHistFillColor(1)
        # self.tdrStyle.SetHistFillStyle(0)
        self.tdrStyle.SetHistLineColor(1)
        self.tdrStyle.SetHistLineStyle(0)
        self.tdrStyle.SetHistLineWidth(1)
        # self.tdrStyle.SetLegoInnerR(Float_t rad = 0.5)
        # self.tdrStyle.SetNumberContours(Int_t number = 20)

        self.tdrStyle.SetEndErrorSize(2)
        # self.tdrStyle.SetErrorMarker(20)
        self.tdrStyle.SetErrorX(0.)

        self.tdrStyle.SetMarkerStyle(20)

        # For the fit/function:
        self.tdrStyle.SetOptFit(1)
        #self.tdrStyle.SetOptFit(0)
        self.tdrStyle.SetFitFormat("5.4g")
        self.tdrStyle.SetFuncColor(2)
        self.tdrStyle.SetFuncStyle(1)
        self.tdrStyle.SetFuncWidth(1)

        # For the date:
        self.tdrStyle.SetOptDate(0);
        # self.tdrStyle.SetDateX(Float_t x = 0.01);
        # self.tdrStyle.SetDateY(Float_t y = 0.01);

        # For the statistics box:
        self.tdrStyle.SetOptFile(0)
        self.tdrStyle.SetOptStat(0) # To display the mean and RMS:   SetOptStat("mr");
        self.tdrStyle.SetStatColor(ROOT.kWhite)
        self.tdrStyle.SetStatFont(self.font)
        self.tdrStyle.SetStatFontSize(self.statSize)
        self.tdrStyle.SetStatTextColor(1)
        self.tdrStyle.SetStatFormat("6.4g")
        self.tdrStyle.SetStatBorderSize(1)
        self.tdrStyle.SetStatH(0.1)
        self.tdrStyle.SetStatW(0.15)
        # self.tdrStyle.SetStatStyle(Style_t style = 1001)
        # self.tdrStyle.SetStatX(Float_t x = 0)
        # self.tdrStyle.SetStatY(Float_t y = 0)

        # Margins:
        self.rightMargin = 0.05
        self.tdrStyle.SetPadTopMargin(0.05) # default
        #self.tdrStyle.SetPadTopMargin(0.13)
        self.tdrStyle.SetPadBottomMargin(0.13)
        #self.tdrStyle.SetPadLeftMargin(0.13)
        self.tdrStyle.SetPadLeftMargin(0.16)
        self.tdrStyle.SetPadRightMargin(self.rightMargin) # default    

        # Based on the new example myMacro.C, increase top margin
        # slightly
        # https://ghm.web.cern.ch/ghm/plots/
        self.tdrStyle.SetPadTopMargin(0.06)
        #self.tdrStyle.SetPadBottomMargin(0.12)
        #self.tdrStyle.SetPadLeftMargin(0.12)
        #self.tdrStyle.SetPadRightMargin(0.04)

        # For the Global title:

        self.tdrStyle.SetOptTitle(0)
        self.tdrStyle.SetTitleFont(self.font)
        self.tdrStyle.SetTitleColor(1)
        self.tdrStyle.SetTitleTextColor(1)
        self.tdrStyle.SetTitleFillColor(10)
        self.tdrStyle.SetTitleFontSize(self.labelSize)
        # self.tdrStyle.SetTitleH(0); // Set the height of the title box
        # self.tdrStyle.SetTitleW(0); // Set the width of the title box
        # self.tdrStyle.SetTitleX(0); // Set the position of the title box
        # self.tdrStyle.SetTitleY(0.985); // Set the position of the title box
        # self.tdrStyle.SetTitleStyle(Style_t style = 1001);
        # self.tdrStyle.SetTitleBorderSize(2);

        # For the axis titles:
        self.tdrStyle.SetTitleColor(1, "XYZ")
        self.tdrStyle.SetTitleFont(self.font, "XYZ")
        self.tdrStyle.SetTitleSize(self.titleSize, "XYZ")
        # self.tdrStyle.SetTitleXSize(Float_t size = 0.02); // Another way to set the size?
        # self.tdrStyle.SetTitleYSize(Float_t size = 0.02);
        self.tdrStyle.SetTitleXOffset(0.9)
        self.tdrStyle.SetTitleYOffset(1.25)
        # self.tdrStyle.SetTitleOffset(1.1, "Y"); // Another way to set the Offset

        # For the axis labels:
        self.tdrStyle.SetLabelColor(1, "XYZ")
        self.tdrStyle.SetLabelFont(self.font, "XYZ")
        self.tdrStyle.SetLabelOffset(0.007, "XYZ")
        self.tdrStyle.SetLabelSize(self.labelSize, "XYZ")

        # For the axis:
        self.tdrStyle.SetAxisColor(1, "XYZ")
        self.tdrStyle.SetStripDecimals(True)
        self.tdrStyle.SetTickLength(0.03, "XYZ")
        self.tdrStyle.SetNdivisions(510, "XYZ")
        self.tdrStyle.SetPadTickX(1)  # To get tick marks on the opposite side of the frame
        self.tdrStyle.SetPadTickY(1)

        # For the text boxes
        self.tdrStyle.SetTextFont(self.font+20) # Bold
        self.tdrStyle.SetTextSize(self.labelSize)

        # Change for log plots:
        self.tdrStyle.SetOptLogx(0)
        self.tdrStyle.SetOptLogy(0)
        self.tdrStyle.SetOptLogz(0)

        # Postscript options:
        self.tdrStyle.SetPaperSize(20,20)
        # self.tdrStyle.SetLineScalePS(Float_t scale = 3);
        # self.tdrStyle.SetLineStyleString(Int_t i, const char* text);
        # self.tdrStyle.SetHeaderPS(const char* header);
        # self.tdrStyle.SetTitlePS(const char* pstitle);
        
        # self.tdrStyle.SetBarOffset(Float_t baroff = 0.5);
        # self.tdrStyle.SetBarWidth(Float_t barwidth = 0.5);
        # self.tdrStyle.SetPaintTextFormat(const char* format = "g");
        # self.tdrStyle.SetPalette(Int_t ncolors = 0, Int_t* colors = 0);
        self.tdrStyle.SetPalette(1); # Set pre-defined palette ranging from blue to red
        # self.tdrStyle.SetTimeOffset(Double_t toffset);
        # self.tdrStyle.SetHistMinimumZero(kTRUE);
        self.tdrStyle.cd()
        return

    def setGrid(self, onoff):
        '''
        Set grid on or off
        
        \param onoff  If True (False), set the grid on (off)
        '''
        self.tdrStyle.SetPadGridX(onoff)
        self.tdrStyle.SetPadGridY(onoff)
        return

    def setGridX(self, onoff):
        self.tdrStyle.SetPadGridX(onoff)
        return

    def setGridY(self, onoff):
        self.tdrStyle.SetPadGridY(onoff)
        return

    def setLogX(self, onoff):
        self.tdrStyle.SetOptLogx(onoff)
        return

    def setLogY(self, onoff):
        self.tdrStyle.SetOptLogy(onoff)
        return

    def setLogZ(self, onoff):
        self.tdrStyle.SetOptLogz(onoff)
        return

    def setPalettePretty(self):
        '''
        Set pretty palette style
        '''
        self.tdrStyle.SetPalette(1)
        return

    def setPaletteMy(self):
        '''
        Set a custom palette style
        '''
        mycolors = [51, 60, 65, 70, 80, 90, 95, 100]
        self.tdrStyle.SetPalette(len(mycolors), array("i", mycolors))
        return

    def setPalettePastel(self):
        '''
        Set a custom palette style
        '''
        kDarkBlue = ROOT.TColor.GetColor("#0048Ba")
        kBlue     = ROOT.TColor.GetColor("#608DD4")
        kNavyBlue = ROOT.TColor.GetColor("#DFE8F6")
        kWhite    = ROOT.TColor.GetColor("FFFFFFF")
        kGreen    = ROOT.TColor.GetColor("#9DBDAB")
        kRed      = ROOT.TColor.GetColor("#e23222")
        kOrange   = ROOT.TColor.GetColor("#FF7E00")
        kYellow   = ROOT.TColor.GetColor("#FFBF00")
        
        #mycolors = [kDarkBlue, kBlue, kNavyBlue, kGreen, kYellow, kOrange, kRed]
        mycolors = [kDarkBlue, kBlue, kNavyBlue, kWhite, kYellow, kOrange, kRed]
        self.tdrStyle.SetPalette(len(mycolors), array("i", mycolors))
        return

    def setWide(self, onoff, percIncrease=0.08):
        '''
        Widen the default canvas and pad widths to be able to draw with "*Z" draw styles
        
        \param onoff  If True (False), make the canvas and pad wider (normal)     
        '''
        factor = 1+percIncrease
        if onoff:
            self.tdrStyle.SetCanvasDefW(int(factor*self.canvasW))
            self.tdrStyle.SetPadRightMargin(percIncrease+self.rightMargin)
        else:
            self.tdrStyle.SetCanvasDefW(self.canvasW)
            self.tdrStyle.SetPadRightMargin(self.rightMargin)
        return

    def setPadRightMargin(newMargin=0.05):
        '''
        Decrease the canvas right margin (use-case: TH2)
        '''
        self.tdrStyle.SetPadRightMargin(newMargin)
        return

    def setOptStat(self, stat):
        '''
        Set OptStat
        '''
        self.tdrStyle.SetOptStat(stat)
        return
        
def setGrid(onoff):
    '''
    Set grid on or off
    
    \param onoff  If True (False), set the grid on (off)
    '''
    ROOT.gStyle.SetPadGridX(onoff)
    ROOT.gStyle.SetPadGridX(onoff)
    return

def setOptStat(stat):
    '''
    Set OptStat
    '''
    ROOT.gStyle.SetOptStat(stat)
    return

def setDeepSeaPalette():
    '''
    Set "Deep Sea" palette (51)
    '''
    ROOT.gStyle.SetPalette(51)
    return

def setRainBowPalette():
    '''
    Set "Rainbow" palette (55)
    '''
    ROOT.gStyle.SetPalette(1)
    return

def setDarkBodyRadiatorPalette():
    '''
    Set "Dark Body Radiator" palette (53)
    '''
    # Copied from TColor::SetPalette(53) of a recent ROOT
    stops = [0.00, 0.25, 0.50, 0.75, 1.00]
    red   = [0.00, 0.50, 1.00, 1.00, 1.00]
    green = [0.00, 0.00, 0.55, 1.00, 1.00]
    blue  = [0.00, 0.00, 0.00, 0.00, 1.00]
    ret   = ROOT.TColor.CreateGradientColorTable(len(stops), array("d", stops), array("d", red), array("d", green), array("d", blue), 255)
    return

def setGreyScalePalette():
    '''
    Set "Grey Scale" palette (52)
    '''
    stops = [0.00, 0.50, 1.00]
    red   = [0.00, 0.50, 1.00];
    green = [0.00, 0.50, 1.00];
    blue  = [0.00, 0.50, 1.00];
    ret   = ROOT.TColor.CreateGradientColorTable(len(stops), array("d", stops), array("d", red), array("d", green), array("d", blue), 255)
    return

def setTwoColorHuePalette():
    '''
    Set "Two Color Hue" palette(54)
    '''
    stops = [0.00, 0.50, 1.00];
    red   = [ 0.00, 0.50, 1.00];
    green = [0.00, 0.50, 1.00];
    blue  = [0.50, 0.50, 0.00];
    ret   = ROOT.TColor.CreateGradientColorTable(len(stops), array("d", stops), array("d", red), array("d", green), array("d", blue), 255)
    return
