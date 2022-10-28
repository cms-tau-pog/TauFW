'''
\package styles

Histogram/graph (line/marker/fill) style classes and objects

\todo This package would benefit from a major overhaul...
'''
# Author: Konstantinos Christoforou (Feb 2022)
#================================================================================================  
# Import Modules
#================================================================================================  
import ROOT


#================================================================================================  
# Class Definition
#================================================================================================  
class StyleBase:
    '''
    Base class for styles
    
    The only abstraction it provides is forwarding the function call to
    apply() method call.
    
    Deribing classes should implement the \a apply() method.
    '''
    def __call__(self, h):
        '''
        Function call syntax
        
        \param h   histograms.Histo object
        
        Call apply() method with the ROOT histogram/graph object.
        '''
        self.apply(h.getRootHisto())
        
        try:
            gr = h.getSystematicUncertaintyGraph()
            if gr is not None:
                self.applyUncertainty(gr)
        except:
            pass

    def applyUncertainty(self, gr):
        pass

class Style(StyleBase):
    '''
    Basic style (marker style, marker and line color)
    '''
    def __init__(self, marker, color):
        '''
        Constructor
        
        \param marker   Marker style
        \param color    Marker and line color
        '''    
        self.marker = marker
        self.color = color
        return

    def apply(self, h):
        '''
        Apply the style
        
        \param h ROOT object
        '''
        h.SetLineWidth(2)
        h.SetLineColor(self.color)
        h.SetMarkerColor(self.color)
        h.SetMarkerStyle(self.marker)
        h.SetMarkerSize(1.2)
        h.SetFillColor(0)
        h.SetFillStyle(3001)
        return

    def clone(self):
        return Style(self.marker, self.color)

class StyleCompound(StyleBase):
    '''
    Compound style

    Applies are contained styles
    '''
    def __init__(self, styles=[]):
        ''' 
        Constructor
    
        \param styles   List of style objects
        '''
        self.styles = styles
        return

    def append(self, style):
        '''
        Append a style object
        '''
        self.styles.append(style)
        return

    def extend(self, styles):
        '''
        Extend style objects
        '''
        self.styles.extend(styles)
        return

    def apply(self, h):
        '''
        Apply the style
        
        \param h ROOT object
        '''
        for s in self.styles:
            s.apply(h)
        return

    def applyUncertainty(self, gr):
        for s in self.styles:
            s.applyUncertainty(gr)
        return

    def clone(self):
        '''
        Clone the compound style
        '''
        return StyleCompound(self.styles[:])

class StyleFill(StyleBase):
    '''
    Fill style
    
    Contains a base style, and applies fill style and color on top of
    that.
    
    \todo Remove the holding of the style, this is done with
    styles.StyleCompound in much cleaner way
    '''
    def __init__(self, style=None, fillStyle=1001, fillColor=None):
        '''
        Constructor
        
        \param style      Other style object
        \param fillStyle  Fill style
        \param fillColor  Fill color (if not given, line color is used as fill color)
        '''
        self.style     = style
        self.fillStyle = fillStyle
        self.fillColor = fillColor
        return

    def apply(self, h):
        '''
        Apply the style
        
        \param h ROOT object
        '''
        if self.style != None:
            self.style.apply(h)
            if self.fillColor != None:
                h.SetFillColor(self.fillColor)
            else:
                h.SetFillColor(h.GetLineColor())
        h.SetFillStyle(self.fillStyle)
        return

class StyleLine(StyleBase):
    '''
    Line style
    '''
    def __init__(self, lineStyle=None, lineWidth=None, lineColor=None):
        self.lineStyle = lineStyle
        self.lineWidth = lineWidth
        self.lineColor = lineColor
        return

    def apply(self, h):
        '''
        Apply the style
        
        \param h ROOT object
        '''
        if self.lineStyle != None:
            h.SetLineStyle(self.lineStyle)
        if self.lineWidth != None:
            h.SetLineWidth(self.lineWidth)
        if self.lineColor != None:
            h.SetLineColor(self.lineColor)
        return

class StyleMarker(StyleBase):
    '''
    Marker style

    \todo markerSizes should be handled in a cleaner way
    '''
    def __init__(self, markerSize=1.2, markerColor=None, markerSizes=None, markerStyle=None):
        '''
        Constructor
        
        \param markerSize   Marker size
        \param markerColor  Marker color
        \param markerStyle  Marker style
        \param markerSizes  List of marker sizes. If given, marker sizes are drawn from this list succesively.
        '''
        self.markerSize = markerSize
        self.markerColor = markerColor
        self.markerSizes = markerSizes
        self.markerStyle = markerStyle
        self.markerSizeIndex = 0
        return

    def apply(self, h):
        '''
        Apply the style
    
        \param h ROOT object
        '''
        if self.markerSizes == None:
            h.SetMarkerSize(self.markerSize)
        else:
            h.SetMarkerSize(self.markerSizes[self.markerSizeIndex])
            self.markerSizeIndex = (self.markerSizeIndex+1)%len(self.markerSizes)
        if self.markerColor != None:
            h.SetMarkerColor(self.markerColor)
            if self.markerStyle != None:
                    h.SetMarkerStyle(self.markerStyle)
        return

class StyleError(StyleBase):
    '''
    Error style
    '''
    def __init__(self, color, style=3004, linecolor=None, styleSyst=3005):
        '''
        Constructor
        
        \param color      Fill color
        \param style      Fill style
        \param linecolor  Line color
        '''
        self.color = color
        self.style = style
        self.linecolor = linecolor
        self.styleSyst = styleSyst
        return

    def apply(self, h):
        '''
        Apply the style
        
        \param h ROOT object
        '''
        h.SetFillStyle(self.style)
        h.SetFillColor(self.color)
        h.SetMarkerStyle(0)
        if self.linecolor != None:
            h.SetLineColor(self.color)
        else:
            h.SetLineStyle(0)
            h.SetLineWidth(0)
            h.SetLineColor(ROOT.kWhite)
        return

    def applyUncertainty(self, gr):
        self.apply(gr)
        gr.SetFillStyle(self.styleSyst)
        return


#================================================================================================  
# Custom Colours (https://www.color-hex.com/color/161f75)
#================================================================================================  
# https://www.color-hex.com/color/161f75
kBrazilGold  = ROOT.TColor.GetColor("#f8e31c") #"#ffcc00  # 95% confidence interval
kBrazilGoldL = ROOT.TColor.GetColor("#fcf6ba") # 95% confidence interval (ligh)
kBrazilGreen = ROOT.TColor.GetColor("#1d9e3a") #"#00cc00" # 68% confidence interval
kBrazilGreenL= ROOT.TColor.GetColor("#a4d8b0") # 68% confidence interval (light)
kBrazilBlue  = ROOT.TColor.GetColor("#161f75")
kBrazilBlueL = ROOT.TColor.GetColor("#d0d2e3")

cDict  = {}
cDict["TT"]        = ROOT.TColor.GetColor("#6495ED") #3d4494")
cDict["FakeTau"]   = ROOT.TColor.GetColor("#948d3d")
cDict["SingleTop"] = ROOT.TColor.GetColor("#800000") #6B8E23 #228B22") #9ACD32") #00FA9A") #44943d")
cDict["EW"]        = ROOT.TColor.GetColor("#FF7F50") #673136")
cDict["ttX"]       = ROOT.TColor.GetColor("#9370DB") #F7CFFC") ##8d3d94") #F7CFFC

#================================================================================================  
# Definitions
#================================================================================================  
dataStyle = StyleCompound([Style(ROOT.kFullCircle, ROOT.kBlack)])
simStyle  = StyleCompound([Style(ROOT.kOpenCircle, ROOT.kPink)])
dataMcStyle = dataStyle.clone()
errorStyle = StyleCompound([StyleError(ROOT.kBlack, 3345, styleSyst=3354)])
errorStyle2 = StyleCompound([StyleError(ROOT.kGray+2, 3354)])
#errorStylePaper = StyleCompound([StyleError(ROOT.kBlack, 3345, styleSyst=3345)]) # stat #oplus syst (not individually) => same style
errorStyle3 = StyleCompound([StyleError(ROOT.kRed-10, 1001, linecolor=ROOT.kRed-10)])
errorRatioStatStyle = StyleCompound([StyleError(ROOT.kGray, 1001, linecolor=ROOT.kGray)])
errorRatioSystStyle = StyleCompound([StyleError(ROOT.kGray+1, 1001, linecolor=ROOT.kGray+1)])

ratioStyle = dataStyle.clone()
ratioLineStyle = StyleCompound([StyleLine(lineColor=ROOT.kRed, lineWidth=2, lineStyle=3)])

#mcStyle = Style(ROOT.kFullSquare, ROOT.kGreen-2)
mcStyle = StyleCompound([Style(ROOT.kFullSquare, ROOT.kRed+1)])
mcStyle2 = StyleCompound([Style(33, ROOT.kBlue-4)])
signalStyle = StyleCompound([Style(34, ROOT.kAzure+9), 
                             StyleLine(lineStyle=ROOT.kSolid, lineWidth=4)
                             ])
signalHHStyle = StyleCompound([Style(34, ROOT.kRed-8), 
                             StyleLine(lineStyle=8, lineWidth=6)
                             ])
signal80Style =  signalStyle.clone()
signal90Style =  signalStyle.clone()
signal100Style = signalStyle.clone()
signal120Style = signalStyle.clone()
signal140Style = signalStyle.clone()
signal150Style = signalStyle.clone()
signal155Style = signalStyle.clone()
signal160Style = signalStyle.clone()

signalHH80Style =  signalHHStyle.clone()
signalHH90Style =  signalHHStyle.clone()
signalHH100Style = signalHHStyle.clone()
signalHH120Style = signalHHStyle.clone()
signalHH140Style = signalHHStyle.clone()
signalHH150Style = signalHHStyle.clone()
signalHH155Style = signalHHStyle.clone()
signalHH160Style = signalHHStyle.clone()

signal145Style = signalStyle.clone()
signal150Style = signalStyle.clone()
signal155Style = signalStyle.clone()
signal160Style = signalStyle.clone()
signal165Style = signalStyle.clone()
signal170Style = signalStyle.clone()
signal175Style = signalStyle.clone()
signal180Style = signalStyle.clone()
signal190Style = signalStyle.clone()
signal200Style = signalStyle.clone()

"""
# Problem with StyleCompound: solid signal histo in control plots. 13122016/SL
signal200Style = StyleCompound([
        Style(ROOT.kFullCross, ROOT.kBlue), 
        StyleMarker(markerSize=1.2, markerColor=ROOT.kBlue, markerSizes=None, markerStyle=ROOT.kFullCross),
        StyleFill(fillStyle=1001, fillColor=ROOT.kBlue), 
        StyleLine(lineStyle=ROOT.kDashed, lineWidth=3, lineColor=ROOT.kBlue) ])
signal220Style = signalStyle.clone()
signal250Style = signalStyle.clone()
signal300Style = StyleCompound([
        Style(ROOT.kFullTriangleUp, ROOT.kRed), 
        StyleMarker(markerSize=1.2, markerColor=ROOT.kRed, markerSizes=None, markerStyle=ROOT.kFullTriangleUp),
        StyleFill(fillStyle=1001, fillColor=ROOT.kRed), 
        StyleLine(lineStyle=ROOT.kSolid, lineWidth=3, lineColor=ROOT.kRed) ])
signal350Style = signalStyle.clone()
signal400Style = StyleCompound([
        Style(ROOT.kFullTriangleDown, ROOT.kSpring+5), 
        StyleMarker(markerSize=1.2, markerColor=ROOT.kSpring+5, markerSizes=None, markerStyle=ROOT.kFullTriangleDown),
        StyleFill(fillStyle=1001, fillColor=ROOT.kSpring+5), 
        StyleLine(lineStyle=ROOT.kSolid, lineWidth=3, lineColor=ROOT.kSpring+5) ])
signal500Style = StyleCompound([
        Style(ROOT.kFullCircle, ROOT.kBlue+3), 
        StyleMarker(markerSize=1.2, markerColor=ROOT.kBlue+3, markerSizes=None, markerStyle=ROOT.kFullCircle),
        StyleFill(fillStyle=1001, fillColor=ROOT.kBlue+3), 
        StyleLine(lineStyle=ROOT.kDashed, lineWidth=3, lineColor=ROOT.kBlue+3) ])
"""
signal180Style  = signalStyle.clone()
signal200Style  = signalStyle.clone()
signal220Style  = signalStyle.clone()
signal250Style  = signalStyle.clone()
signal300Style  = signalStyle.clone()   
signal350Style  = signalStyle.clone()   
signal400Style  = signalStyle.clone()   
signal500Style  = signalStyle.clone()   
signal600Style  = signalStyle.clone()
signal650Style  = signalStyle.clone()
signal700Style  = signalStyle.clone()
signal750Style  = signalStyle.clone()
signal800Style  = signalStyle.clone()
signal1000Style = signalStyle.clone()
signal1250Style = signalStyle.clone()
signal1500Style = signalStyle.clone()
signal1750Style = signalStyle.clone()
signal2000Style = signalStyle.clone()
signal2500Style = signalStyle.clone()
signal3000Style = signalStyle.clone()
signal5000Style = signalStyle.clone()
signal7000Style = signalStyle.clone()
signal10000Style= signalStyle.clone()

dibStyle          = Style(ROOT.kMultiply, ROOT.kBlue-4)
dyAltStyle        = Style(ROOT.kStar, ROOT.kMagenta-3) #ROOT.kBlue-7)
dyStyle           = Style(ROOT.kStar, ROOT.kTeal-9)
dyM10to50Style    = Style(ROOT.kStar, ROOT.kTeal-1)
ewkFillStyle      = StyleCompound([StyleFill(fillColor=ROOT.kMagenta-2)])
ewkStyle          = Style(ROOT.kFullTriangleDown, ROOT.kRed-4)
ewkfakeFillStyle  = StyleCompound([StyleFill(fillColor=ROOT.kGreen+2)])
qcdBEnrichedStyle = Style(ROOT.kOpenTriangleUp, ROOT.kOrange-3)
qcdFillStyle      = StyleCompound([StyleFill(fillColor=ROOT.kOrange-2)])
qcdStyle          = Style(ROOT.kFullTriangleUp, ROOT.kOrange-2)
qcdStyleF         = Style(ROOT.kFullTriangleUp, ROOT.kOrange-2)
qcdStyleG         = Style(ROOT.kFullTriangleUp, ROOT.kOrange-3)
fakeTauStyle      = Style(ROOT.kFullTriangleUp, ROOT.kOrange-4) #ROOT.kOrange-2)
genuineTauStyle   = Style(ROOT.kOpenDiamond, ROOT.kAzure+2)
genTauFillStyle   = StyleCompound([StyleFill(fillColor=ROOT.kAzure+2)])
singleTopStyle    = Style(ROOT.kOpenDiamond, ROOT.kTeal+9)
stStyle           = Style(ROOT.kPlus, ROOT.kSpring+4)     # from HIG-11-019 to HIG-18-014 ad HIG-18-015
#stStyle           = Style(ROOT.kPlus, cDict["SingleTop"]) # from HIG-21-010
stsStyle          = Style(ROOT.kPlus, ROOT.kSpring-9)
sttStyle          = Style(ROOT.kPlus, ROOT.kSpring-7)
sttwStyle         = stStyle
ttStyle           = Style(ROOT.kFullSquare, ROOT.kMagenta-2) # from HIG-11-019 to HIG-18-014 ad HIG-18-015
#ttStyle           = Style(ROOT.kFullSquare, cDict["TT"])     # from HIG-21-010
ttbbStyle         = Style(ROOT.kOpenCross, ROOT.kPink-9)
ttjetsStyle       = Style(ROOT.kPlus, ROOT.kMagenta-4)
ttttStyle         = Style(ROOT.kFullStar, ROOT.kYellow-9)
ttHStyle          = Style(ROOT.kFullSquare, ROOT.kSpring)
ttHToGGStyle      = Style(ROOT.kFullSquare, ROOT.kViolet-5)
ttHToTTStyle      = Style(ROOT.kFullSquare, ROOT.kViolet-7)
ttHTobbStyle      = Style(ROOT.kFullSquare, ROOT.kSpring-5)
ttHToNonbbStyle   = Style(ROOT.kFullSquare, ROOT.kSpring-7)
ttwStyle          = Style(ROOT.kOpenSquare, ROOT.kSpring+9)
ttzStyle          = Style(ROOT.kFullDiamond, ROOT.kAzure-4)
wStyle            = Style(ROOT.kFullTriangleDown, ROOT.kRed+1)
ewStyle           = Style(ROOT.kFullTriangleDown, ROOT.kOrange+1) # from HIG-11-019 to HIG-18-014 ad HIG-18-015
#ewStyle           = Style(ROOT.kFullTriangleDown, cDict["EW"]) # from HIG-21-010
ewStyleG          = Style(ROOT.kFullTriangleDown, ROOT.kOrange+1)
ewStyleF          = Style(ROOT.kFullTriangleDown, ROOT.kOrange+2)
wjetsStyle        = Style(ROOT.kStar, ROOT.kRed+1) #ROOT.kOrange+9)
wwStyle           = Style(ROOT.kMultiply, ROOT.kPink-9)
wzStyle           = Style(ROOT.kMultiply, ROOT.kPink-7)
zjetsStyle        = Style(ROOT.kFullCross, ROOT.kRed-7)
zzStyle           = Style(ROOT.kMultiply, ROOT.kPink-5)
ttXStyle          = Style(ROOT.kOpenSquare, ROOT.kAzure-4) # from HIG-11-019 to HIG-18-014 ad HIG-18-015
#ttXStyle          = Style(ROOT.kOpenSquare, cDict["ttX"]) # from HIG-21-010
vvStyle           = Style(ROOT.kOpenSquare, ROOT.kYellow-7)
noTopStyle        = Style(ROOT.kOpenSquare, ROOT.kRed+1) # ROOT.kRed-9)
raresStyle        = Style(ROOT.kOpenSquare, ROOT.kViolet+10)  # ROOT.kAzure+8) 
#StyleCompound([StyleMarker(markerSize=1.2, markerColor=ROOT.kBlue-3, markerSizes=None, markerStyle=4),
#                                   StyleLine(lineColor=ROOT.kBlue-3, lineStyle=ROOT.kSolid, lineWidth=4), 
#                                   StyleFill(fillColor=ROOT.kBlue-3, fillStyle=3001)])


ttStyleG  = Style(ROOT.kFullSquare, ROOT.kMagenta)
stStyleG  = Style(ROOT.kPlus, ROOT.kSpring+2)
dyStyleG  = Style(ROOT.kStar, ROOT.kAzure+10)
dyM10to50StyleG = Style(ROOT.kStar, ROOT.kGray+2)
wStyleG   = Style(ROOT.kFullTriangleDown, ROOT.kRed)
ttXStyleG = Style(ROOT.kOpenSquare, ROOT.kYellow-10)
dibStyleG = Style(ROOT.kMultiply, ROOT.kBlue-7)
ttStyleF  = Style(ROOT.kFullSquare, ROOT.kMagenta-2)
stStyleF  = Style(ROOT.kPlus, ROOT.kSpring+4)
dyStyleF  = Style(ROOT.kStar, ROOT.kAzure+7)
dyM10to50StyleF = Style(ROOT.kStar, ROOT.kGray)
wStyleF   = Style(ROOT.kFullTriangleDown, ROOT.kRed+2)
ttXStyleF = Style(ROOT.kOpenSquare, ROOT.kYellow-8)
dibStyleF = Style(ROOT.kMultiply, ROOT.kBlue-4)


# stat #oplus syst (not individually) => same style
errorStylePaper = StyleCompound([StyleError(ROOT.kBlack, 3345, styleSyst=3345), 
                                 StyleLine(lineColor=ROOT.kBlack, lineStyle=ROOT.kSolid, lineWidth=3)])

baselineStyle     = StyleCompound([StyleMarker(markerSize=1.2, markerColor=ROOT.kBlue, markerSizes=None, markerStyle=ROOT.kFullTriangleUp),
                                   StyleLine(lineColor=ROOT.kBlue, lineStyle=ROOT.kSolid, lineWidth=3), 
                                   StyleFill(fillColor=ROOT.kBlue, fillStyle=1001)])
baselineLineStyle = StyleCompound([StyleMarker(markerSize=1.2, markerColor=ROOT.kAzure+2, markerSizes=None, markerStyle=ROOT.kFullTriangleUp),
                                   StyleLine(lineColor=ROOT.kAzure+2, lineStyle=ROOT.kSolid, lineWidth=3), 
                                   StyleFill(fillColor=ROOT.kAzure+2, fillStyle=0)])
invertedStyle     = StyleCompound([StyleMarker(markerSize=1.2, markerColor=ROOT.kRed-4, markerSizes=None, markerStyle=ROOT.kFullTriangleDown),
                                   StyleLine(lineColor=ROOT.kRed-4, lineStyle=ROOT.kSolid, lineWidth=3), 
                                   StyleFill(fillColor=ROOT.kRed-4, fillStyle=1001)])
altEwkStyle       = StyleCompound([StyleMarker(markerSize=1.2, markerColor=ROOT.kMagenta-2, markerSizes=None, markerStyle=ROOT.kFullTriangleDown),
                                   StyleLine(lineColor=ROOT.kMagenta-2, lineStyle=ROOT.kSolid, lineWidth=3),
                                   StyleFill(fillColor=ROOT.kMagenta-2, fillStyle=1001)])
altEwkLineStyle   = StyleCompound([StyleMarker(markerSize=1.2, markerColor=ROOT.kMagenta-2, markerSizes=None, markerStyle=ROOT.kFullTriangleDown),
                                   StyleLine(lineColor=ROOT.kMagenta-2, lineStyle=ROOT.kSolid, lineWidth=3),
                                   StyleFill(fillColor=ROOT.kMagenta-2, fillStyle=0)])
invertedLineStyle = StyleCompound([StyleMarker(markerSize=1.2, markerColor=ROOT.kRed, markerSizes=None, markerStyle=ROOT.kFullTriangleDown),
                                   StyleLine(lineColor=ROOT.kRed, lineStyle=ROOT.kSolid, lineWidth=3), 
                                   StyleFill(fillColor=ROOT.kRed, fillStyle=0)])
altQCDStyle       = StyleCompound([StyleMarker(markerSize=1.2, markerColor=ROOT.kOrange-2, markerSizes=None, markerStyle=ROOT.kFullDiamond),
                                   StyleLine(lineColor=ROOT.kOrange-2, lineStyle=ROOT.kSolid, lineWidth=3), 
                                   StyleFill(fillColor=ROOT.kOrange-2, fillStyle=1001)])
genuineBAltStyle   = StyleCompound([StyleMarker(markerSize=1.2, markerColor=ROOT.kAzure-3, markerSizes=None, markerStyle=ROOT.kOpenCircle),
                                   StyleLine(lineColor=ROOT.kAzure-3, lineStyle=ROOT.kSolid, lineWidth=3), 
                                   StyleFill(fillColor=ROOT.kAzure-3, fillStyle=1001)])
genuineBStyle     = StyleCompound([StyleMarker(markerSize=1.2, markerColor=ROOT.kAzure-2, markerSizes=None, markerStyle=ROOT.kFullCircle),
                                   StyleLine(lineColor=ROOT.kAzure-2, lineStyle=ROOT.kSolid, lineWidth=3), 
                                   StyleFill(fillColor=ROOT.kAzure-2, fillStyle=1001)])
genuineBLineStyle = StyleCompound([StyleMarker(markerSize=1.2, markerColor=ROOT.kGreen+2, markerSizes=None, markerStyle=ROOT.kFullCircle),
                                   StyleLine(lineColor=ROOT.kGreen+2, lineStyle=ROOT.kSolid, lineWidth=3), 
                                   StyleFill(fillColor=ROOT.kGreen+2, fillStyle=0)])
fakeBStyle        = StyleCompound([StyleMarker(markerSize=1.2, markerColor=ROOT.kOrange-3, markerSizes=None, markerStyle=ROOT.kFullTriangleDown),
                                   StyleLine(lineColor=ROOT.kOrange-3, lineStyle=ROOT.kSolid, lineWidth=3), 
                                   StyleFill(fillColor=ROOT.kOrange-3, fillStyle=1001)]) #fillStyle=3005)])
fakeBLineStyle    = StyleCompound([StyleMarker(markerSize=1.2, markerColor=ROOT.kOrange-3, markerSizes=None, markerStyle=ROOT.kFullTriangleDown),
                                   StyleLine(lineColor=ROOT.kOrange-3, lineStyle=ROOT.kSolid, lineWidth=3), 
                                   StyleFill(fillColor=ROOT.kOrange-3, fillStyle=0)])
fakeBLineStyle1   = StyleCompound([StyleMarker(markerSize=1.2, markerColor=ROOT.kRed, markerSizes=None, markerStyle=ROOT.kFullTriangleDown),
                                   StyleLine(lineColor=ROOT.kRed, lineStyle=ROOT.kSolid, lineWidth=3), 
                                   StyleFill(fillColor=ROOT.kRed, fillStyle=0)])
signalStyleHToTB = StyleCompound([StyleMarker(markerSize=0.0, markerColor=ROOT.kSpring-3, markerSizes=None, markerStyle=ROOT.kFullTriangleUp),
                                   StyleLine(lineColor=ROOT.kSpring-3, lineStyle=ROOT.kDashed, lineWidth=3), 
                                   StyleFill(fillColor=ROOT.kSpring-3, fillStyle=0)])

signalStyleHToHW300  = StyleCompound([StyleMarker(markerSize=0.0, markerColor=ROOT.kPink+6, markerSizes=None, markerStyle=ROOT.kFullTriangleUp),
                                      StyleLine(lineColor=ROOT.kPink+6, lineStyle=ROOT.kDashed, lineWidth=3), 
                                      StyleFill(fillColor=ROOT.kPink+6, fillStyle=0)])

signalStyleHToHW400  = signalStyleHToHW300
signalStyleHToHW500  = signalStyleHToHW300
signalStyleHToHW600  = signalStyleHToHW300
signalStyleHToHW700  = signalStyleHToHW300
signalStyleHToHW800  = signalStyleHToHW300
signalStyleHToHW1000 = signalStyleHToHW300

signalFillStyleHToTB  = StyleCompound([StyleMarker(markerSize=0, markerColor=ROOT.kYellow-7, markerSizes=None, markerStyle=4),
                                   StyleLine(lineColor=ROOT.kYellow-7, lineStyle=ROOT.kSolid, lineWidth=1), 
                                   StyleFill(fillColor=ROOT.kYellow-7, fillStyle=10001)])
signalStyleHToTB180 = StyleCompound([StyleMarker(markerSize=0.0, markerColor=ROOT.kGray+1, markerSizes=None, markerStyle=ROOT.kFullTriangleUp),
                                   StyleLine(lineColor=ROOT.kGray+1, lineStyle=ROOT.kDashed, lineWidth=3), 
                                   StyleFill(fillColor=ROOT.kGray+1, fillStyle=0)])
signalStyleHToTB200 = StyleCompound([StyleMarker(markerSize=0.0, markerColor=ROOT.kPink-2, markerSizes=None, markerStyle=ROOT.kFullTriangleUp),
                                   StyleLine(lineColor=ROOT.kPink-2, lineStyle=ROOT.kDashed, lineWidth=3), 
                                   StyleFill(fillColor=ROOT.kPink-2, fillStyle=0)])
signalStyleHToTB220 = StyleCompound([StyleMarker(markerSize=0.0, markerColor=ROOT.kSpring-2, markerSizes=None, markerStyle=ROOT.kFullTriangleUp),
                                   StyleLine(lineColor=ROOT.kSpring-2, lineStyle=ROOT.kDashed, lineWidth=3), 
                                   StyleFill(fillColor=ROOT.kSpring-2, fillStyle=0)])
signalStyleHToTB250 = StyleCompound([StyleMarker(markerSize=0.0, markerColor=ROOT.kAzure+6, markerSizes=None, markerStyle=ROOT.kFullTriangleUp),
                                   StyleLine(lineColor=ROOT.kAzure+6, lineStyle=ROOT.kDashed, lineWidth=3), 
                                   StyleFill(fillColor=ROOT.kAzure+6, fillStyle=0)])
signalStyleHToTB300 = StyleCompound([StyleMarker(markerSize=0.0, markerColor=ROOT.kOrange-3, markerSizes=None, markerStyle=ROOT.kFullTriangleUp),
                                   StyleLine(lineColor=ROOT.kOrange-3, lineStyle=ROOT.kDashed, lineWidth=3), 
                                   StyleFill(fillColor=ROOT.kOrange-3, fillStyle=0)])
signalStyleHToTB350 = StyleCompound([StyleMarker(markerSize=0.0, markerColor=ROOT.kOrange+7, markerSizes=None, markerStyle=ROOT.kFullTriangleUp),
                                   StyleLine(lineColor=ROOT.kOrange+7, lineStyle=ROOT.kSolid, lineWidth=3), 
                                   StyleFill(fillColor=ROOT.kOrange+7, fillStyle=0)])
signalStyleHToTB400 = StyleCompound([StyleMarker(markerSize=0.0, markerColor=ROOT.kOrange-2, markerSizes=None, markerStyle=ROOT.kFullTriangleUp),
                                   StyleLine(lineColor=ROOT.kOrange-2, lineStyle=ROOT.kSolid, lineWidth=3), 
                                   StyleFill(fillColor=ROOT.kOrange-2, fillStyle=0)])
signalStyleHToTB500 = StyleCompound([StyleMarker(markerSize=0.0, markerColor=ROOT.kRed, markerSizes=None, markerStyle=ROOT.kFullTriangleUp),
                                   StyleLine(lineColor=ROOT.kRed, lineStyle=ROOT.kSolid, lineWidth=3), 
                                   StyleFill(fillColor=ROOT.kRed, fillStyle=0)])
signalStyleHToTB600 = StyleCompound([StyleMarker(markerSize=0.0, markerColor=ROOT.kAzure-6, markerSizes=None, markerStyle=ROOT.kFullTriangleDown),
                                     StyleLine(lineColor=ROOT.kAzure-6, lineStyle=ROOT.kSolid, lineWidth=3),
                                     StyleFill(fillColor=ROOT.kAzure-6, fillStyle=0)])
signalStyleHToTB650 = StyleCompound([StyleMarker(markerSize=0.0, markerColor=ROOT.kAzure-6, markerSizes=None, markerStyle=ROOT.kFullTriangleDown),
                                   StyleLine(lineColor=ROOT.kAzure-6, lineStyle=ROOT.kSolid, lineWidth=3), 
                                   StyleFill(fillColor=ROOT.kAzure-6, fillStyle=0)])
signalStyleHToTB700 = StyleCompound([StyleMarker(markerSize=0.0, markerColor=ROOT.kOrange+9, markerSizes=None, markerStyle=ROOT.kFullTriangleDown),
                                     StyleLine(lineColor=ROOT.kOrange+9, lineStyle=ROOT.kSolid, lineWidth=3),
                                     StyleFill(fillColor=ROOT.kOrange+9, fillStyle=0)])
signalStyleHToTB800 = StyleCompound([StyleMarker(markerSize=0.0, markerColor=ROOT.kSpring-1, markerSizes=None, markerStyle=ROOT.kFullTriangleUp),
                                   StyleLine(lineColor=ROOT.kSpring-1, lineStyle=ROOT.kSolid, lineWidth=3), 
                                   StyleFill(fillColor=ROOT.kSpring-1, fillStyle=0)])
signalStyleHToTB1000 = StyleCompound([StyleMarker(markerSize=0.0, markerColor=ROOT.kGreen+3, markerSizes=None, markerStyle=ROOT.kFullTriangleUp),
                                   StyleLine(lineColor=ROOT.kGreen+3, lineStyle=ROOT.kSolid, lineWidth=3), 
                                   StyleFill(fillColor=ROOT.kGreen+3, fillStyle=0)])
signalStyleHToTB1250 = StyleCompound([StyleMarker(markerSize=0.0, markerColor=ROOT.kRed-6, markerSizes=None, markerStyle=ROOT.kFullTriangleUp),
                                      StyleLine(lineColor=ROOT.kRed-6, lineStyle=ROOT.kDotted, lineWidth=3),
                                      StyleFill(fillColor=ROOT.kRed-6, fillStyle=0)])
signalStyleHToTB1500 = StyleCompound([StyleMarker(markerSize=0.0, markerColor=ROOT.kCyan+1, markerSizes=None, markerStyle=ROOT.kFullTriangleUp),
                                   StyleLine(lineColor=ROOT.kCyan+1, lineStyle=ROOT.kDashed, lineWidth=3), 
                                   StyleFill(fillColor=ROOT.kCyan+1, fillStyle=0)])
signalStyleHToTB1750 = StyleCompound([StyleMarker(markerSize=0.0, markerColor=ROOT.kBlue-6, markerSizes=None, markerStyle=ROOT.kFullTriangleUp),
                                      StyleLine(lineColor=ROOT.kBlue-6, lineStyle=ROOT.kDashed, lineWidth=3),
                                      StyleFill(fillColor=ROOT.kBlue-6, fillStyle=0)])
signalStyleHToTB2000 = StyleCompound([StyleMarker(markerSize=0.0, markerColor=ROOT.kViolet-9, markerSizes=None, markerStyle=ROOT.kFullTriangleUp),
                                   StyleLine(lineColor=ROOT.kViolet-9, lineStyle=ROOT.kDashed, lineWidth=3), 
                                   StyleFill(fillColor=ROOT.kViolet-9, fillStyle=0)])
signalStyleHToTB2500 = StyleCompound([StyleMarker(markerSize=0.0, markerColor=ROOT.kRed-9, markerSizes=None, markerStyle=ROOT.kFullTriangleUp),
                                   StyleLine(lineColor=ROOT.kRed-9, lineStyle=ROOT.kDashed, lineWidth=3), 
                                   StyleFill(fillColor=ROOT.kRed-9, fillStyle=0)])
signalStyleHToTB3000 = StyleCompound([StyleMarker(markerSize=0.0, markerColor=ROOT.kRed+2, markerSizes=None, markerStyle=ROOT.kFullTriangleUp),
                                   StyleLine(lineColor=ROOT.kRed+2, lineStyle=ROOT.kDashed, lineWidth=3), 
                                   StyleFill(fillColor=ROOT.kRed+2, fillStyle=0)])

# FakeB Style
FakeBStyle1 = StyleCompound([StyleMarker(markerSize=1.2, markerColor=ROOT.kRed, markerSizes=None, markerStyle=ROOT.kFullTriangleUp),
                                   StyleLine(lineColor=ROOT.kRed, lineStyle=ROOT.kSolid, lineWidth=3), 
                                   StyleFill(fillColor=ROOT.kRed, fillStyle=1001)])
FakeBStyle2 = StyleCompound([StyleMarker(markerSize=1.2, markerColor=ROOT.kOrange-3, markerSizes=None, markerStyle=34),
                                   StyleLine(lineColor=ROOT.kOrange-3, lineStyle=ROOT.kSolid, lineWidth=3), 
                                   StyleFill(fillColor=ROOT.kOrange-3, fillStyle=1001)])
FakeBStyle3 = StyleCompound([StyleMarker(markerSize=1.2, markerColor=ROOT.kBlue, markerSizes=None, markerStyle=ROOT.kFullCircle),
                                   StyleLine(lineColor=ROOT.kBlue, lineStyle=ROOT.kSolid, lineWidth=3), 
                                   StyleFill(fillColor=ROOT.kBlue, fillStyle=1001)])
FakeBStyle4 = StyleCompound([StyleMarker(markerSize=1.2, markerColor=ROOT.kAzure+1, markerSizes=None, markerStyle=ROOT.kFullSquare),
                                   StyleLine(lineColor=ROOT.kAzure+1, lineStyle=ROOT.kSolid, lineWidth=3), 
                                   StyleFill(fillColor=ROOT.kAzure+1, fillStyle=1001)])
FakeBStyle5 = StyleCompound([StyleMarker(markerSize=1.2, markerColor=ROOT.kPink-2, markerSizes=None, markerStyle=ROOT.kFullTriangleUp),
                                   StyleLine(lineColor=ROOT.kPink-2, lineStyle=ROOT.kSolid, lineWidth=3), 
                                   StyleFill(fillColor=ROOT.kPink-2, fillStyle=1001)])
FakeBStyle6 = StyleCompound([StyleMarker(markerSize=1.2, markerColor=ROOT.kViolet-5, markerSizes=None, markerStyle=ROOT.kFullTriangleDown),
                                   StyleLine(lineColor=ROOT.kViolet-5, lineStyle=ROOT.kSolid, lineWidth=3), 
                                   StyleFill(fillColor=ROOT.kViolet-5, fillStyle=1001)])

markerStyles = [ 
    baselineStyle, 
    invertedStyle,
    altQCDStyle,
    genuineBAltStyle,
    genuineBStyle,
    fakeBStyle,
    FakeBStyle1,
    FakeBStyle4,
    FakeBStyle5,
    FakeBStyle6,
    FakeBStyle2,
    FakeBStyle3,
    ]


styles = [ 
    Style(26, ROOT.kBlue),
    Style(27, ROOT.kRed),
    Style(23, ROOT.kGreen+2),
    Style(24, ROOT.kMagenta),
    Style(28, ROOT.kCyan),
    Style(35, ROOT.kGray),
    Style(25, ROOT.kBlack),
    Style(29, ROOT.kYellow-2),
    Style(31, ROOT.kOrange+3),
    Style(32, ROOT.kMagenta+3),
    Style(33, ROOT.kGray+2),
    Style(34, ROOT.kBlue+3),
    Style(35, ROOT.kOrange+1),
    Style(35, ROOT.kGray),
    Style(35, ROOT.kTeal),
    Style(35, ROOT.kViolet),
    Style(35, ROOT.kSpring-1),
    Style(41, ROOT.kCyan-5),
    Style(37, ROOT.kYellow-8),
    Style(22, ROOT.kViolet-9),
    Style(ROOT.kFullTriangleDown, ROOT.kOrange-2),
    Style(ROOT.kFullSquare, ROOT.kGreen+2),
    Style(ROOT.kFullTriangleUp, ROOT.kPink),
    Style(ROOT.kFullCircle, ROOT.kAzure+2),
    ]

stylesCompound = [ 
    StyleCompound([
            StyleMarker(markerSize=1.2, markerColor=ROOT.kBlack, markerSizes=None, markerStyle=ROOT.kFullCircle),
            StyleLine(lineColor=ROOT.kBlack, lineStyle=ROOT.kSolid, lineWidth=3), 
            StyleFill(fillColor=ROOT.kBlack, fillStyle=1001)]),
    StyleCompound([
            StyleMarker(markerSize=1.2, markerColor=ROOT.kOrange-2, markerSizes=None, markerStyle=ROOT.kFullTriangleUp),
            StyleLine(lineColor=ROOT.kOrange-2, lineStyle=ROOT.kDashed, lineWidth=3), 
            StyleFill(fillColor=ROOT.kOrange-2, fillStyle=1001)]),
    StyleCompound([
            StyleMarker(markerSize=1.2, markerColor=ROOT.kMagenta-2, markerSizes=None, markerStyle=ROOT.kFullTriangleDown),
            StyleLine(lineColor=ROOT.kMagenta-2, lineStyle=ROOT.kSolid, lineWidth=3),  #ROOT.kDashDotted
            StyleFill(fillColor=ROOT.kMagenta-2, fillStyle=3001)]),
    StyleCompound([
            StyleMarker(markerSize=1.2, markerColor=ROOT.kGreen+2, markerSizes=None, markerStyle=ROOT.kFullCross),
            StyleLine(lineColor=ROOT.kGreen+2, lineStyle=ROOT.kDotted, lineWidth=3), 
            StyleFill(fillColor=ROOT.kGreen+2, fillStyle=1001)]),
    StyleCompound([
            StyleMarker(markerSize=1.2, markerColor=ROOT.kAzure-1, markerSizes=None, markerStyle=ROOT.kFullTriangleDown),
            StyleLine(lineColor=ROOT.kAzure-1, lineStyle=ROOT.kSolid, lineWidth=3),  #ROOT.kDashDotted
            StyleFill(fillColor=ROOT.kAzure-1, fillStyle=3005)]),
            #StyleFill(fillColor=ROOT.kAzure-1, fillStyle=3003)]),
    ]


def applyStyle(h, ind):
    styles[ind].apply(h)

def applyCompoudStyle(h, baseColour):
    #Style(26, ROOT.kBlue).apply(h)
    StyleCompound([
            StyleMarker(markerSize=1.2, markerColor=baseColour, markerSizes=None, markerStyle=None),
            StyleLine(lineColor=baseColour, lineStyle=ROOT.kSolid, lineWidth=3), 
            StyleFill(fillColor=baseColour, fillStyle=1001)]).apply(h)

def getDataStyle():
    return dataStyle

def getEWKStyle():
    return ewkFillStyle

def getAltEWKStyle():
    return altEwkStyle

def getAltEWKLineStyle():
    return altEwkLineStyle

def getEWKFillStyle():
    return ewkFillStyle

def getEWKLineStyle():
    return ewkStyle

def getEWKFakeStyle():
    return ewkfakeFillStyle

def getAltQCDStyle():
    return altQCDStyle

def getFakeTauStyle():
    return qcdFillStyle

def getGenuineTauStyle():
    return genTauFillStyle
    #return genuineTauStyle

def getQCDStyle():
    return qcdFillStyle

def getQCDFillStyle():
    return qcdFillStyle

def getQCDLineStyle():
    return qcdStyle

def getABCDStyle(region):
    if region == "SR":
        return FakeBStyle1
    elif region == "CR1" or region == "CRone" or region == "R1":
        return FakeBStyle2
    elif region == "VR" or region == "AR":
        return FakeBStyle3
    elif region == "CR2" or region == "CRtwo" or region == "R2":
        return FakeBStyle4
    elif region == "CR3" or region == "CRthree" or region == "R3":
        return FakeBStyle5
    elif region == "CR4" or region == "CRfour":
        return FakeBStyle6
    else:
        print "Invalid region \"%s\". Returning qcd style" % (region)
        return qcdStyle

def getBaselineStyle():
    return baselineStyle

def getBaselineLineStyle():
    return baselineLineStyle

def getGenuineBStyle():
    return genuineBStyle

def getGenuineBLineStyle():
    return genuineBLineStyle

def getFakeBStyle():
    return fakeBStyle

def getFakeBLineStyle():
    return fakeBLineStyle

def getInvertedStyle():
    return invertedStyle

def getInvertedLineStyle():
    return invertedLineStyle

def getSignalStyle():
    return signalStyle

def getSignalStyleHToTB():
    return signalStyleHToTB

def getSignalStyleHToTB():
    return signalFillStyleHToTB

def getSignalStyleHToTB_M(myMass):

    mass = str(myMass)
    if mass == "180":
        return signalStyleHToTB180
    elif mass == "200":
        return signalStyleHToTB200
    elif mass == "220":
        return signalStyleHToTB220
    elif mass == "250":
        return signalStyleHToTB250
    elif mass == "300":
        return signalStyleHToTB300
    elif mass == "350":
        return signalStyleHToTB350
    elif mass == "400":
        return signalStyleHToTB400
    elif mass == "500":
        return signalStyleHToTB500
    elif mass == "600":
        return signalStyleHToTB600
    elif mass == "650":
        return signalStyleHToTB650
    elif mass == "700":
        return signalStyleHToTB700
    elif mass == "800":
          return signalStyleHToTB800
    elif mass == "1000":
        return signalStyleHToTB1000
    elif mass == "1250":
        return signalStyleHToTB1250
    elif mass == "1500":
        return signalStyleHToTB1500
    elif mass == "1750":
        return signalStyleHToTB1750
    elif mass == "2000":
        return signalStyleHToTB2000
    elif mass == "2500":
        return signalStyleHToTB2500
    elif mass == "3000":
        return signalStyleHToTB3000
    elif mass == "5000":
        return signalStyleHToTB3000
    elif mass == "10000":
        return signalStyleHToTB3000
    else:
        print "Invalid mass point \"%s\". Returning default style" % (mass)
    return signalStyleHToTB500        

def getErrorStyle():
    return errorStyle

def getErrorStylePaper():
    return errorStylePaper

def getStyles():
    return styles

def getStylesFill(**kwargs):
    return [StyleFill(s, **kwargs) for s in styles]

class Generator:
    def __init__(self, styles):
        self.styles = styles
        self.index = 0

    def reset(self, index=0):
        self.index = index

    def reorder(self, indices):
        self.styles = [self.styles[i] for i in indices]

    def next(self):
        self.index = (self.index+1) % len(self.styles)

    def __call__(self, h):
        self.styles[self.index](h)
        self.next()

def generator(fill=False, **kwargs):
    if fill:
        return Generator(getStylesFill(**kwargs))
    else:
        return Generator(getStyles(**kwargs))

def generator2(styleCustomisations, styles=styles):
    if not isinstance(styleCustomisations, list):
        styleCustomisations = [styleCustomisations]
    return Generator([StyleCompound([s]+styleCustomisations) for s in styles])
