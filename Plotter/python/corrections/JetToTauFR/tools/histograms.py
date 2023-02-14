'''
## \package histograms
# Histogram utilities and classes
#
# The package contains classes and utilities for histogram management.
'''
# Author: Konstantinos Christoforou (Feb 2022)
#================================================================================================   
# Import modules
#================================================================================================   
import os, sys
import glob
import array
import math
import copy
import inspect

from optparse import OptionParser

import ROOT

import dataset

#================================================================================================   
# Class definition
#================================================================================================   
class CMSMode:
    '''
    Enumeration class for CMS text mode
    '''
    class NONE: pass
    class PRELIMINARY: pass
    class PAPER: pass
    class UNPUBLISHED: pass
    class SIMULATION: pass
    class SIMULATION_PRELIMINARY: pass
    class SIMULATION_UNPUBLISHED: pass


## Global variable to hold CMS text mode
cmsTextMode = CMSMode.PRELIMINARY

## Global dictionary to hold the CMS text labels
cmsText = {
    CMSMode.NONE: None,
    CMSMode.PRELIMINARY: "Preliminary",
    CMSMode.PAPER: "",
    CMSMode.UNPUBLISHED: "Preliminary",
    CMSMode.SIMULATION : "Simulation",
    CMSMode.SIMULATION_PRELIMINARY : "Preliminary simulation",
    CMSMode.SIMULATION_UNPUBLISHED: "Simulation unpublished",
    }

#================================================================================================   
# Class definition
#================================================================================================   
class Uncertainty:
    '''
    Global uncertainty mode
    
     Python treats classes as singletons, slitghly more safe than
      hand-made enumeration
    '''
    ## Statistical uncertainties only
    class StatOnly:
        pass
    ## Systematic uncertainties only
    class SystOnly:
        pass
    ## Stat+syst uncertainty only
    class StatPlusSyst:
        pass
    # Stat and stat+syst uncertainties
    class StatAndSyst:
        pass

    def __init__(self, mode=StatAndSyst):
        self._mode = mode

    def set(self, mode):
        self._mode = mode

    def get(self):
        return self._mode

    def getName(self):
        return self._mode.__name__

    def equal(self, mode):
        return self._mode == mode

    def showStatOnly(self):
        return not (self.equal(self.SystOnly) or self.equal(self.StatPlusSyst))

    def addStatToSyst(self):
        return not self.equal(self.SystOnly)
## Global uncertainty mode
uncertaintyMode = Uncertainty()

## Default energy text
energyText = "13 TeV"


#================================================================================================   
# Class definition
#================================================================================================   
class TextDefaults:
    '''
    Class to provide default positions of the various texts.
    
     The attributes which can be set are the x and y coordinates and the
     text size.
    '''
    def __init__(self):
        self._setDefaults("cmsPreliminary", x=0.62, y=0.96)
        self._setDefaults("energy", x=0.19, y=0.96)
        self._setDefaults("lumi", x=0.43, y=0.96)
        return

    def _setDefaults(self, name, **kwargs):
        '''
        Modify the default values
        
         \param name   Name of the property ('cmsPreliminary', 'energy', 'lumi')
         \param kwargs Keyword arguments
         
         <b>Keyword arguments</b>
         \li \a x     X coordinate
         \li \a y     Y coordinate
         \li \a size  Font size
        '''
        for x, value in kwargs.iteritems():
            setattr(self, name+"_"+x, value)
            
    ## Modify the default position of "CMS Preliminary" text
    #
    # \param kwargs  Keyword arguments (forwarded to _setDefaults())
    def setCmsPreliminaryDefaults(self, **kwargs):
        self._setDefaults("cmsPreliminary", **kwargs)

    ## Modify the default position of center-of-mass energy text
    #
    # \param kwargs  Keyword arguments (forwarded to _setDefaults())
    def setEnergyDefaults(self, **kwargs):
        self._setDefaults("energy", **kwargs)
        
    ## Modify the default position of integrated luminosity text
    #
    # \param kwargs  Keyword arguments (forwarded to _setDefaults())
    def setLuminosityDefaults(self, **kwargs):
        self._setDefaults("lumi", **kwargs)

    ## Get the (x, y) values for property
    #
    # \param name  Name of property
    # \param x     X coordinate, if None, use the default
    # \param y     Y coordinate, if None, use the default
    def getValues(self, name, x, y):
        if x == None:
            x = getattr(self, name+"_x")
        if y == None:
            y = getattr(self, name+"_y")
        return (x, y)

    ## Get the size for property
    #
    # \param name  Name of property
    #
    # \return The text size, taken from ROOT.gStyle if no value has been set
    def getSize(self, name):
        try:
            return getattr(self, name+"_size")
        except AttributeError:
            return ROOT.gStyle.GetTextSize()

## Provides default text positions and sizes
#
# In order to modify the global defaults, modify this object.
#
# Used by histograms.addCmsPreliminaryText(),
# histograms.addEnergyText(), histograms.addLuminosityText().
textDefaults = TextDefaults()

def addText(x, y, text, *args, **kwargs):
    '''
    Draw text to current TCanvas/TPad with TLaTeX
    
    \param x       X coordinate of the text (in NDC)
    \param y       Y coordinate of the text (in NDC)
    \param text    String to draw
    \param args    Other positional arguments (forwarded to histograms.PlotText.__init__())
    \param kwargs  Other keyword arguments (forwarded to histograms.PlotText.__init__())    
    '''
    t = PlotText(x, y, text, *args, **kwargs)
    t.Draw()
    return


#================================================================================================   
# Class definition
#=====================1===========================================================================   
class PlotText:
    '''
    Class for drawing text to current TPad with TLaTeX
    
    Text can be added to plots in object-oriented way. Mainly intended
    to be used with plots.PlotBase.appendPlotObject etc.
    '''
    def __init__(self, x, y, text, size=None, bold=False, align="left", color=ROOT.kBlack, font=None):
        '''
        Constructor
        
        \param x       X coordinate of the text (in NDC)
        \param y       Y coordinate of the text (in NDC)
        \param text    String to draw
        \param size    Size of text (None for the default value, taken from gStyle)
        \param bold    Should the text be bold?
        \param align   Alignment of text (left, center, right)
        \param color   Color of the text
        \param font    Specify font explicitly        
        '''
        self.x = x
        self.y = y
        self.text = text
        self.l = ROOT.TLatex()
        self.l.SetNDC()
        if not bold:
            self.l.SetTextFont(self.l.GetTextFont()-20) # bold -> normal
        if font is not None:
            self.l.SetTextFont(font)
        if size is not None:
            self.l.SetTextSize(size)
        if isinstance(align, basestring):
            if align.lower() == "left":
                self.l.SetTextAlign(11)
            elif align.lower() == "center":
                self.l.SetTextAlign(21)
            elif align.lower() == "right":
                self.l.SetTextAlign(31)
            else:
                raise Exception("Error: Invalid option '%s' for text alignment! Options are: 'left', 'center', 'right'."%align)
        else:
            self.l.SetTextAlign(align)
        self.l.SetTextColor(color)
        return

    def Draw(self, options=None):
        '''
        Draw the text to the current TPad
        
        \param options   For interface compatibility, ignored
        
        Provides interface compatible with ROOT's drawable objects.
        '''
        self.l.DrawLatex(self.x, self.y, self.text)        
        return

class PlotTextBox:
    '''
    Class for drawing text and a background box
    '''
    def __init__(self, xmin, ymin, xmax, ymax, lineheight=0.04, fillColor=ROOT.kWhite, transparent=True, **kwargs):
        '''
        Constructor
        
        \param xmin       X min coordinate of the box (NDC)
        \param ymin       Y min coordinate of the box (NDC) (if None, deduced automatically)
        \param xmax       X max coordinate of the box (NDC)
        \param ymax       Y max coordinate of the box (NDC)
        \param lineheight Line height
        \param fillColor  Fill color of the box
        \param transparent  Should the box be transparent? (in practive the TPave is not created)
        \param kwargs       Forwarded to histograms.PlotText.__init__()
        '''

        # ROOT.TPave Set/GetX1NDC() etc don't seem to work as expected.
        self.xmin = xmin
        self.xmax = xmax
        self.ymin = ymin
        self.ymax = ymax
        self.lineheight = lineheight
        self.fillColor = fillColor
        self.transparent = transparent
        self.texts = []
        self.textArgs = {}
        self.textArgs.update(kwargs)

        self.currenty = ymax
        return

    def addText(self, text):
        '''
        Add text to current position
        '''
        self.currenty -= self.lineheight
        self.addPlotObject(PlotText(self.xmin+0.01, self.currenty, text, **self.textArgs))
        return

    def addPlotObject(self, obj):
        '''
        Add PlotText object
        '''
        self.texts.append(obj)
        return

    def move(self, dx=0, dy=0, dw=0, dh=0):
        '''
        Move the box and the contained text objects
        
        \param dx  Movement in x (positive is to right)
        \param dy  Movement in y (positive is to up)
        \param dw  Increment of width (negative to decrease width)
        \param dh  Increment of height (negative to decrease height)
        
        \a dx and \a dy affect to both box and text objects, \a dw and
        \dh affect the box only.
        '''
        self.xmin += dx
        self.xmax += dx
        if self.ymin is not None:
            self.ymin += dy
        self.ymax += dy

        self.xmax += dw
        if self.ymin is not None:
            self.ymin -= dh

        for t in self.texts:
            t.x += dx
            t.y += dy
        return

    def Draw(self, options=""):
        '''
        Draw the box and the text to the current TPad
        
        \param options  Forwarded to ROOT.TPave.Draw(), and the Draw() of the contained objects
        '''
        if not self.transparent:
            ymin = self.ymin
            if ymin is None:
                ymin = self.currenty - 0.01
            self.pave = ROOT.TPave(self.xmin, self.ymin, self.xmax, self.ymax, 0, "NDC")
            self.pave.SetFillColor(self.fillColor)
            self.pave.Draw(options)
        for t in self.texts:
            t.Draw(options)
        return

def _printTextDeprecationWarning(oldFunctionName, newFunctionName="histograms.addStandardTexts()"):
    import traceback
    print "#################### WARNING ####################"
    print
    print "%s is deprecated, please use %s instead" % (oldFunctionName, newFunctionName)
    print "Traceback (most recent call last):"
    stack = traceback.extract_stack()[:-2] # take out calls to this and the caller
    print "".join(traceback.format_list(stack))
    print "#################################################"
    return

def addCmsPreliminaryText(x=None, y=None, text=None):
    '''
    Draw the "CMS Preliminary" text to the current TPad
    
    \param x   X coordinate of the text (None for default value)
    \param y   Y coordinate of the text (None for default value)    
    '''
    _printTextDeprecationWarning("histograms.addCmsPreliminaryText()")
    (x, y) = textDefaults.getValues("cmsPreliminary", x, y)
    if text == None:
        txt  = cmsText[cmsTextMode]
    else:
        txt = text
    addText(x, y, txt, textDefaults.getSize("cmsPreliminary"), bold=False)

def addEnergyText(x=None, y=None, s=None):
    '''
    Draw the center-of-mass energy text to the current TPad
    
    \param x   X coordinate of the text (None for default value)
    \param y   Y coordinate of the text (None for default value)
    \param s   Center-of-mass energy text with the unit (None for the default value, dataset.energyText
    '''
    _printTextDeprecationWarning("histograms.addEnergyText()")
    (x, y) = textDefaults.getValues("energy", x, y)
    text = energyText
    if s != None:
        text = s
    addText(x, y, "#sqrt{s} = "+text, textDefaults.getSize("energy"), bold=False)
    return

def formatLuminosityInFb(lumi):
    '''
    Format luminosity number to fb
    
    \param lumi  Luminosity in pb^-1
    '''
    lumiInFb = lumi/1000.
    log = 0
    ndigis = 0
    if lumi > 0:
        log = math.log10(lumiInFb)
        ndigis = int(log)
    format = "%.1f" # ndigis >= 1, 10 <= lumiInFb
    if ndigis == 0: 
        if log >= 0: # 1 <= lumiInFb < 10
            format = "%.1f"
        else: # 0.1 < lumiInFb < 1
            format = "%.2f"
    elif ndigis <= -1:
        format = ".%df" % (abs(ndigis)+1)
        format = "%"+format
    return format % lumiInFb

def addLuminosityText(x, y, lumi, unit="fb^{-1}"):
    '''
    Draw the integrated luminosity text to the current TPad
    
    \param x     X coordinate of the text (None for default value)
    \param y     Y coordinate of the text (None for default value)
    \param lumi  Value of the integrated luminosity in pb^-1
    \param unit  Unit of the integrated luminosity value (should be fb^-1)
    '''
    _printTextDeprecationWarning("histograms.addLuminosityText()")
    (x, y) = textDefaults.getValues("lumi", x, y)
    lumiStr = "L="
    if isinstance(lumi, basestring):
        lumiStr += lumi
    else:
        lumiStr += formatLuminosityInFb(lumi)

    lumiStr += " "+unit

    addText(x, y, lumiStr, textDefaults.getSize("lumi"), bold=False)
    return

def addStandardTexts(lumi=None, sqrts=None, addCmsText=True, cmsTextPosition=None, cmsExtraTextPosition=None, cmsText=None, cmsExtraText=None):
    '''
    ## Draw the CMS standard texts
    #
    # Updated version of addCmsPreliminaryText(), addEnergyText() and
    # addLuminosityText() following the new guidelines at
    # https://ghm.web.cern.ch/ghm/plots/
    #
    # \param lumi        Luminosity as float in pb^-1 (or as string in fb^1), None to ignore completely
    # \param sqrts       Centre-of-mass energy text with the unit
    # \param addCmsText  If True, add the CMS text
    # \param cmsTextPosition Position of CMS text ("left", "right", "outframe", pair of (x, y) in NDC
    # \param cmsExtraTextPosition Position of CMS extra text (None for default, pair of (x, y) for explicit)
    # \param cmsText         If not None, override the "CMS" text
    # \param cmsExtraText    If not None, override the CMS extra text (e.g. "Preliminary")
    '''
    cmsTextPosition  = "outframe"
    lumiTextSize     = 40*0.6
    cmsTextFrac      = 0.75
    cmsTextSize      = 40*cmsTextFrac
    cmsExtraTextSize = cmsTextSize * 0.76

    # Lumi + energy text
    lumiText = ""
    if lumi is not None:
        if isinstance(lumi, basestring):
            lumiText = lumi
        else:
            lumiText = formatLuminosityInFb(lumi)
        lumiText += " fb^{-1} ("
    if sqrts is not None:
        lumiText += sqrts
    else:
        lumiText += energyText
    if lumi is not None:
        lumiText += ")"

    lumiTextOffset = 0.2
    l = ROOT.gPad.GetLeftMargin()
    t = ROOT.gPad.GetTopMargin()
    r = ROOT.gPad.GetRightMargin()
    b = ROOT.gPad.GetBottomMargin()

    addText(1-r, 1-t+lumiTextOffset*t, lumiText, size=lumiTextSize, bold=False, align="right")

    if not addCmsText:
        return

    cmsExtraTextDefault = globals()["cmsText"][cmsTextMode]
    if cmsExtraTextDefault is None:
        return

    # CMS + extratext
    relPosX = 0.045
    relPosY = 0.035
    relExtraDY = 1.2

    posY = 1-t - relPosY*(1-t-b)
    if isinstance(cmsTextPosition, basestring):
        p = cmsTextPosition.lower()
        if p == "left":
            posX = l + relPosX*(1-l-r)
            align = 13 # left, top
            posXe = posX
            posYe = posY - relExtraDY*cmsTextFrac*t
        elif p == "right":
            posX = 1-r - relPosX*(1-l-r)
            align = 33 # right, top
            posXe = posX
            posYe = posY - relExtraDY*cmsTextFrac*t
        elif cmsTextPosition.lower() == "outframe":
            posX = l
            posY = 1-t+lumiTextOffset*t
            align = 11 # left, bottom
            posXe = l + 0.14*(1-l-r)
            posYe = posY
        else:
            raise Exception("Invalid value for cmsTextPosition '%s', valid are left, right, outframe" % (cmsTextPosition))
    else:
        posX = cmsTextPosition[0]
        posY = cmsTextPosition[1]
        align = 13 # left, top
        posXe = posX
        posYe = posY - relExtraDY*cmsTextFrac*t

    cms = "CMS"
    if cmsText is not None:
        cms = cmsText

    if cms != "":
        addText(posX, posY, cms, size=cmsTextSize, font=63, align=align)

    extraText = cmsExtraText
    if extraText is None:
        extraText = cmsExtraTextDefault
    if extraText is not None and extraText != "":
        if cmsExtraTextPosition is not None:
            posXe = cmsExtraTextPosition[0]
            posYe = cmsExtraTextPosition[1]
        addText(posXe, posYe, extraText, size=cmsExtraTextSize, font=53, align=align)
    return


class SignalTextCreator:
    '''
    Class to create signal information box on plots
    '''
    def __init__(self, xmin=0.6, ymax=0.9, size=20, lineheight=0.04, width=0.3, **kwargs):
        '''
        Constructor
        
        \param xmin       xmin coordinate of the box (NDC)
        \param ymax       ymax coordinate of the box (NDC)
        \param size       Text size
        \param lineheight Height of one line
        \param width      Width of the box
        \param kwargs     Keyword arguments, forwarded to histograms.PlotTextBox.__init__()
        '''
        self.settings = dataset.Settings(xmin=xmin, ymax=ymax, size=size, lineheight=lineheight, width=width,
                                 mass=None, tanbeta=None, mu=None,
                                 br_tH=None,
                                 sigma_H=None, br_Htaunu=None)
        self.boxArgs = {}
        self.boxArgs.update(kwargs)

    ## Set the signal information
    def set(self, **kwargs):
        self.settings.set(**kwargs)

    ## Function call syntax to create histograms.PlotTextBox
    def __call__(self, **kwargs):
        xmin = self.settings.get("xmin", kwargs)
        ymax = self.settings.get("ymax", kwargs)
        size = self.settings.get("size", kwargs)
        lineheight = self.settings.get("lineheight", kwargs)
        width = self.settings.get("width", kwargs)

        box = PlotTextBox(xmin, None, xmin+width, ymax, lineheight=lineheight, size=size, **self.boxArgs)

        for attr, text in [
            ("mass", "m_{H^{+}}=%d GeV/c^{2}"),
            ("br_tH", "#it{B}(t #rightarrow bH^{+})=%.2f"),
            ("sigma_H", "#sigma(H^{+})=%.1f pb"),
            ("br_Htaunu", "#it{B}(H^{+} #rightarrow #tau#nu_{#tau})=%.2f"),
            ("tanbeta", "tan#beta=%d"),
            ("mu", "#mu=%d")]:

            value = self.settings.get(attr, kwargs)
            if value is not None:
                box.addText(text % value)

        return box

createSignalText = SignalTextCreator()


## Class for generating legend creation functions with default positions.
#
# The intended usage is demonstrated in histograms.py below, i.e.
# \code
# createLegend = LegendCreator(x1, y1, x2, y2)
# createLegend.setDefaults(x1=0.4, y2=0.5)
# createLegend.moveDefaults(dx=0.2, dh=0.1)
# legend = createLegend()
# \endcode
#
# All coordinates are in NDC
class LegendCreator:
    ## Constructor
    #
    # \param x1          Default x1 (left x)
    # \param y1          Default y1 (lower y)
    # \param x2          Default x2 (right x)
    # \param y2          Default y2 (upper y)
    # \param textSize    Default text size
    # \param borderSize  Default border size
    # \param fillStyle   Default fill style
    # \param fillColor   Default fill color
    def __init__(self, x1=0.73, y1=0.62, x2=0.93, y2=0.92, textSize=0.035, borderSize=0, fillStyle=4000, fillColor=ROOT.kWhite, ncolumns=1, columnSeparation=None):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.textSize = textSize
        self.borderSize = borderSize
        self.fillStyle = fillStyle
        self.fillColor = fillColor
        self.ncolumns = ncolumns
        self.columnSeparation = columnSeparation
        self._keys = ["x1", "y1", "x2", "y2"]

    ## Create a copy of the object
    def copy(self):
        return LegendCreator(self.x1, self.y1, self.x2, self.y2)

    ## Set new default positions
    #
    # \param kwargs   Keyword arguments
    #
    # <b>Keyword arguments</b>
    # \li \a x1          X1 coordinate
    # \li \a y1          Y1 coordinate
    # \li \a x2          X2 coordinate
    # \li \a y2          Y2 coordinate
    # \li \a textSize    Text size
    # \li \a borderSize  Border size
    # \li \a fillStyle   Fill style
    # \li \a fillColor   Fill color
    def setDefaults(self, **kwargs):
        for x, value in kwargs.iteritems():
            setattr(self, x, value)

    ## Move the default position/width/height
    #
    # \param dx  Movement in x (positive is to right)
    # \param dy  Movement in y (positive is to up)
    # \param dw  Increment of width (negative to decrease width)
    # \param dh  Increment of height (negative to decrease height)
    #
    # Typically one want's to only move the legend, but keep it with
    # the same size, or increase/decrease width/height for some plots
    # only from the default
    def moveDefaults(self, dx=0, dy=0, dw=0, dh=0):
        self.x1 += dx
        self.x2 += dx

        self.y1 += dy
        self.y2 += dy

        self.x2 += dw
        self.y1 -= dh # we want to move the lower edge, and negative dh should shrink the legend

    ## Create a new TLegend object (function call syntax)
    #
    # \param args    Positional arguments (must get 0 or 4, see below)
    # \param kwargs  Keyword arguments
    # 
    # <b>Arguments can be either</b>
    # \li Four numbers for the coordinates (\a x1, \a y1, \a x2, \a y2) as positional arguments
    # \li Keyword arguments (\a x1, \a y1, \a x2, \a y2)
    #
    # If all 4 coordinates are specified, they are used. In the
    # keyword argument case, the coordinates which are not given are
    # taken from the default values.
    def __call__(self, *args, **kwargs):
        if len(args) == 4:
            if len(kwargs) != 0:
                raise Exception("Got 4 positional arguments, no keyword arguments allowed")
            for i, k in enumerate(self._keys):
                kwargs[k] = args[i]
        elif len(args) != 0:
            raise Exception("If positional arguments given, must give 4")
        else:
            for i in self._keys:
                if not i in kwargs:
                    kwargs[i] = getattr(self, i)

        legend = ROOT.TLegend(kwargs["x1"], kwargs["y1"], kwargs["x2"], kwargs["y2"])
        legend.SetFillStyle(self.fillStyle)
        if self.fillStyle != 0:
            legend.SetFillColor(self.fillColor)
        legend.SetBorderSize(self.borderSize)
        if legend.GetTextFont() % 10 == 3:
            legend.SetTextFont(legend.GetTextFont()-1) # From x3 to x2
        legend.SetTextSize(self.textSize)
        #legend.SetMargin(0.1)

        if self.ncolumns > 1:
            legend.SetNColumns(self.ncolumns)
            if self.columnSeparation is not None:
                legend.SetColumnSeparation(self.columnSeparation)

        return legend

    ## \var x1
    # X1 coordinate
    ## \var y1
    # Y1 coordinate
    ## \var x2
    # X2 coordinate
    ## \var y2
    # Y2 coordinate
    ## \var textSize
    # Text size
    ## \var borderSize
    # Border size
    ## \var fillStyle
    # Fill style
    ## \var fillColor
    # Fill color
    ## \var _keys
    # List of valid coordinate names for __call__() function


## Default legend creator object
createLegend = LegendCreator()

## Default legend creator object for ratio plots
createLegendRatio = LegendCreator(x1=0.7, y1=0.7, x2=0.93, y2=0.95, textSize=0.07)

## Move TLegend
# 
# \param legend   TLegend object to modify
# \param dx  Movement in x (positive is to right)
# \param dy  Movement in y (positive is to up)
# \param dw  Increment of width (negative to decrease width)
# \param dh  Increment of height (negative to decrease height)
#
# \return Modified TLegend (which is the same object as given as input)
#
# Typically one want's to only move the legend, but keep it with
# the same size, or increase/decrease width/height for some plots
# only from the default
def moveLegend(legend, dx=0, dy=0, dw=0, dh=0):
    legend.SetX1(legend.GetX1() + dx)
    legend.SetX2(legend.GetX2() + dx)
    legend.SetY1(legend.GetY1() + dy)
    legend.SetY2(legend.GetY2() + dy)

    legend.SetX2(legend.GetX2() + dw)
    legend.SetY1(legend.GetY1() - dh) # negative dh should shrink the legend
    
    return legend
    

## Update the style of palette Z axis according to ROOT.gStyle.
#
# \return TPalatteAxis object, or None if it doesn't exist
#
# This function is needed because the style is not propageted to the Z
# axis automatically. It is recommended to call this every time
# something is drawn with an option "Z"
def updatePaletteStyle(histo):
    if not hasattr(histo, "GetListOfFunctions"):
        # Applies at least to THStack, which is not applicable for Z axis
        return None

    ROOT.gPad.Update()
    paletteAxis = histo.GetListOfFunctions().FindObject("palette")
    if paletteAxis == None:
        return None
    paletteAxis.SetLabelColor(ROOT.gStyle.GetLabelColor("Z"))
    paletteAxis.SetLabelFont(ROOT.gStyle.GetLabelFont("Z"))
    paletteAxis.SetLabelOffset(ROOT.gStyle.GetLabelOffset("Z"))
    paletteAxis.SetLabelSize(ROOT.gStyle.GetLabelSize("Z"))

    axis = paletteAxis.GetAxis()
    axis.SetTitleColor(ROOT.gStyle.GetTitleColor("Z"))
    axis.SetTitleFont(ROOT.gStyle.GetTitleFont("Z"))
    axis.SetTitleOffset(ROOT.gStyle.GetTitleOffset("Z"))
    axis.SetTitleSize(ROOT.gStyle.GetTitleSize("Z"))

    return paletteAxis

## Sum TH1 histograms
#
# \param rootHistos  List of TH1 objects
# \param postfix     Postfix for the sum histo name
def sumRootHistos(rootHistos, postfix="_sum"):
    h = rootHistos[0].Clone()
    h.SetDirectory(0)
    h.SetName(h.GetName()+"_sum")
    for a in rootHistos[1:]:
        h.Add(a)
    return h

def drawNonVisibleErrorsTH1(th1):
    if isinstance(th1, ROOT.TH2):
        raise Exception("This function supports only 1D TH1, got %s" % th1.__class__.__name__)

    # Get the Y-axis min/max from pad
    pad_ymin = ROOT.gPad.GetUymin()
    pad_ymax = ROOT.gPad.GetUymax()

    ret = []
    for i in xrange(1, th1.GetNbinsX()+1):
        x = th1.GetBinCenter(i)
        y = th1.GetBinContent(i)
        ymin = y - th1.GetBinError(i)
        ymax = y + th1.GetBinError(i)

        line = None
        if y < pad_ymin and ymax > pad_ymin:
            line = ROOT.TLine(x, pad_ymin, x, min(pad_ymax, ymax))
            copyStyle(th1, line)
            line.Draw("same")
            ret.append(line)
        elif y > pad_ymax and ymin < pad_ymax:
            line = ROOT.TLine(x, max(pad_ymin, ymin), x, pad_ymax)
            copyStyle(th1, line)
            line.Draw("same")
            ret.append(line)
    return ret

def drawNonVisibleErrorsTGraph(tgraph):
    # Get the Y-axis min/max from pad
    pad_ymin = ROOT.gPad.GetYmin()
    pad_ymax = ROOT.gPad.GetYmax()
#    print "FOO", ROOT.gPad.GetUxmin(), ROOT.gPad.GetUxmax(),ROOT.gPad.GetUymin(), ROOT.gPad.GetUymax()
    for i in xrange(0, tgraph.GetN()):
        ymin = tgraph.GetY()[i]-tgraph.GetErrorYhigh(i)
        ymax = tgraph.GetErrorYhigh(i)+tgraph.GetY()[i]
        print ymin, tgraph.GetY()[i], ymax
    raise Exception("This function is not finished because of lack of need")

## Helper function for lessThan/greaterThan argument handling
#
# \param kwargs  Keyword arguments
#
# <b>Keyword arguments</b>
# \li \a lessThan     True for lessThan, False for greaterThan
# \li \a greaterThan  False for lessThan, True for greaterThan
#
# \return True for lessThan, False for greaterThan
#
# Provides the ability to have 'lessThan=True' and 'greaterThan=True'
# keyword arguments, as I believe they enhance the readability of the
# function calls.
def isLessThan(**kwargs):
    if len(kwargs) != 1:
        raise Exception("Should give only either 'lessThan' or 'greaterThan' as a keyword argument")
    elif "lessThan" in kwargs:
        return kwargs["lessThan"]
    elif "greaterThan" in kwargs:
        return not kwargs["greaterThan"]
    else:
        raise Exception("Must give either 'lessThan' or 'greaterThan' as a keyword argument")

## Convert TH1 distribution to TH1 of number of passed events as a function of cut value
#
# \param hdist   TH1 distribution
# \param kwargs  Keyword arguments (forwarded to histograms.isLessThan)
def dist2pass(hdist, **kwargs):
    lessThan = isLessThan(**kwargs)

    # for less than
    integral = None
    if lessThan:
        integral = lambda h, bin: h.Integral(0, bin)
    else:    
        integral = lambda h, bin: h.Integral(bin, h.GetNbinsX()+1)
        
    # bin 0             underflow bin
    # bin 1             first bin
    # bin GetNbinsX()   last bin
    # bin GetNbinsX()+1 overflow bin

    # Here we assume that all the bins in hdist have equal widths. If
    # this doesn't hold, the output must be TGraph
    bw = hdist.GetBinWidth(1);
    for bin in xrange(2, hdist.GetNbinsX()+1):
        if abs(bw - hdist.GetBinWidth(bin))/bw > 0.01:
            raise Exception("Input histogram with variable bin width is not supported (yet). The bin width of bin1 was %f, and bin width of bin %d was %f" % (bw, bin, hdist.GetBinWidth(bin)))

    # Construct the low edges of the passed histogram. Set the low
    # edges such that the bin centers correspond to the edges of the
    # distribution histogram. This makes sense because the only
    # sensible cut points in the distribution histogram are the bin
    # edges, and if one draws the passed histogram with points, the
    # points are placed to bin centers.
    nbins = hdist.GetNbinsX()+1
    firstLowEdge = hdist.GetXaxis().GetBinLowEdge(1) - bw/2
    lastUpEdge = hdist.GetXaxis().GetBinUpEdge(hdist.GetNbinsX()) + bw/2
    name = "passed_"+hdist.GetName()
    hpass = ROOT.TH1F("cumulative_"+hdist.GetName(), "Cumulative "+hdist.GetTitle(),
                      nbins, firstLowEdge, lastUpEdge)

    if lessThan:
        passedCumulative = 0
        passedCumulativeErrSq = 0
        for bin in xrange(0, hdist.GetNbinsX()+2):
            passedCumulative += hdist.GetBinContent(bin)
            err = hdist.GetBinError(bin)
            passedCumulativeErrSq += err*err

            hpass.SetBinContent(bin+1, passedCumulative)
            hpass.SetBinError(bin+1, math.sqrt(passedCumulativeErrSq))
    else:
        passedCumulative = 0
        passedCumulativeErrSq = 0
        for bin in xrange(hdist.GetNbinsX()+1, -1, -1):
            passedCumulative += hdist.GetBinContent(bin)
            err = hdist.GetBinError(bin)
            passedCumulativeErrSq += err*err

            hpass.SetBinContent(bin, passedCumulative)
            hpass.SetBinError(bin, math.sqrt(passedCumulativeErrSq))

    return hpass

## Helper function for applying a function for each bin of TH1
#
# \param th1       TH1 object
# \param function  Function taking a number as an input, and returning a number
def th1ApplyBin(th1, function):
    for bin in xrange(0, th1.GetNbinsX()+2):
        th1.SetBinContent(bin, function(th1.GetBinContent(bin)))

def th1ApplyBinError(th1, function):
    for bin in xrange(0, th1.GetNbinsX()+2):
        th1.SetBinError(bin, function(th1.GetBinError(bin)))
                
## Convert TH1 distribution to TH1 of efficiency as a function of cut value
#
# \param hdist  TH1 distribution
# \param kwargs  Keyword arguments (forwarded to histograms.isLessThan)
def dist2eff(hdist, **kwargs):
    hpass = dist2pass(hdist, **kwargs)
    total = hdist.Integral(0, hdist.GetNbinsX()+1)
    th1ApplyBin(hpass, lambda value: value/total)
    th1ApplyBinError(hpass, lambda value: math.sqrt(value)/total)
    return hpass

## Convert TH1 distribution to TH1 of 1-efficiency as a function of cut value
#
# \param hdist  TH1 distribution
# \param kwargs  Keyword arguments (forwarded to histograms.isLessThan)
def dist2rej(hdist, **kwargs):
    hpass = dist2pass(hdist, **kwargs)
    total = hdist.Integral(0, hdist.GetNbinsX()+1)
    th1ApplyBin(hpass, lambda value: 1-value/total)
    return hpass


## Infer the frame bounds from the histograms and keyword arguments
#
# \param histos  List of histograms.Histo objects
# \param kwargs  Dictionary of keyword arguments to parse
#
# <b>Keyword arguments</b>
# \li\a ymin        Minimum value of Y axis
# \li\a ymax        Maximum value of Y axis
# \li\a xmin        Minimum value of X axis
# \li\a xmax        Maximum value of X axis
# \li\a xmaxlist    List of possible maximum values of X axis. The
#                   smallest value larger than the xmax in list of
#                   histograms is picked. If all values are smaller
#                   than the xmax of histograms, the xmax of
#                   histograms is used.
# \li\a ymaxfactor  Maximum value of Y is \a ymax*\a ymaxfactor (default 1.1)
# \li\a yminfactor  Minimum value of Y is \a ymax*\a yminfactor (yes, calculated from \a ymax )
#
# By default \a ymin, \a ymax, \a xmin and \a xmax are taken as
# the maximum/minimums of the histogram objects such that frame
# contains all histograms. The \a ymax is then multiplied with \a
# ymaxfactor
#
# The \a yminfactor/\a ymaxfactor are used only if \a ymin/\a ymax
# is taken from the histograms, i.e. \a ymax keyword argument is
# \b not given.
#
# Used e.g. in histograms.CanvasFrame and histograms.CanvasFrameTwo
def _boundsArgs(histos, kwargs):
    ymaxfactor = kwargs.get("ymaxfactor", 1.1)

    if not "ymax" in kwargs:
        kwargs["ymax"] = ymaxfactor * max([h.getYmax() for h in histos])
    if not "ymin" in kwargs:
        if "yminfactor" in kwargs:
            kwargs["ymin"] = kwargs["yminfactor"]*kwargs["ymax"]
        else:
            kwargs["ymin"] = min([h.getYmin() for h in histos])

    if not "xmin" in kwargs:
        kwargs["xmin"] = min([h.getXmin() for h in histos])
    if not "xmax" in kwargs:
        kwargs["xmax"] = max([h.getXmax() for h in histos])
        if "xmaxlist" in kwargs:
            largerThanMax = filter(lambda n: n > kwargs["xmax"], kwargs["xmaxlist"])
            if len(largerThanMax) > 0:
                kwargs["xmax"] = min(largerThanMax)


def _drawFrame(pad, xmin, ymin, xmax, ymax, nbins=None, nbinsx=None, nbinsy=None):
    '''
    Draw a frame

    \param pad   TPad to draw the frame to
    \param xmin  Minimum X axis value
    \param ymin  Minimum Y axis value
    \param xmax  Maximum X axis value
    \param ymax  Maximum Y axis value
    \param nbins Number of x axis bins
    \param nbinsx Number of x axis bins
    \param nbinsy Number of y axis bins
    
    If nbins is None, TPad.DrawFrame is used. Otherwise a custom TH1 is
    created for the frame with nbins bins in x axis.
    
    Use case: selection flow histogram (or whatever having custom x axis
    lables).
    '''
    if nbins is not None and nbinsx is not None:
        raise Exception("Both 'nbins' and 'nbinsx' should not be set, please use the latter only")
    if nbins is None:
        nbins = nbinsx

    if nbinsx is None and nbinsy is None:
        return pad.DrawFrame(xmin, ymin, xmax, ymax)
    else:
        pad.cd()
        # From TPad.cc
        frame = pad.FindObject("hframe")
        if frame is not None:
            # frame.Delete()
            frame = None
        if nbinsx is not None and nbinsy is None:
            frame = ROOT.TH1F("hframe", "hframe", nbinsx, xmin, xmax)
        elif nbinsx is None and nbinsy is not None:
            frame = ROOT.TH2F("hframe", "hframe", 100,xmin,xmax, nbinsy,ymin,ymax)
        else: # neither is None
            frame = ROOT.TH2F("hframe", "hframe", nbinsx,xmin,xmax, nbinsy,ymin,ymax)

        frame.SetBit(ROOT.TH1.kNoStats)
        frame.SetBit(ROOT.kCanDelete)
        frame.SetMinimum(ymin)
        frame.SetMaximum(ymax)
        frame.GetYaxis().SetLimits(ymin, ymax)
        frame.SetDirectory(0)
        frame.Draw(" ")
        return frame

class CanvasFrame:
    '''
    Create TCanvas and frame for one TPad.
    
    Used mainly from plots.PlotBase (based) class(es), although it can
    be also used directly if one really wants.
    '''
    def __init__(self, histoManager, name, canvasOpts={}, **kwargs):
        '''
        Create TCanvas and TH1 for the frame.
        
        \param histoManager  histograms.HistoManager object to take the histograms for automatic axis ranges
        \param name          Name for TCanvas (will be the file name, if TCanvas.SaveAs(".png") is used)
        \param canvasOpts    Dictionary for modifying the canvas/pad properties (see below)
        \param kwargs        Keyword arguments for frame bounds (forwarded to histograms._boundsArgs())
        
        <b>Keyword arguments</b>
        \li\a opts   If given, give \a opts to histograms._boundsArgs() instead of kwargs. No other keyword arguments are allowed (except opts2, see below).
        \li\a opts2  Ignored, existence allowed only for compatibility with histograms.CanvasFrameTwo
        
        <b>Canvas modification parameters</b>
        \li\a addWidth   Add this to the width of the canvas (e.g. for
                         COLZ). If COLZ exists in any the drawing
                         options of any input histogram, a default value
                         of 0.13 is used (this can be disabled with
                         explicit value None).
        \li\a addHeight  Add this to the height of the canvas
        '''
        histos = []
        if isinstance(histoManager, list):
            histos = histoManager[:]
        else:
            histos = histoManager.getHistos()
        if len(histos) == 0:
            raise Exception("Empty set of histograms!")

        # Infer the default based on the existence of COLZ drawing option
        canvasAddWidth = None
        for h in histos:
            drawStyle = h.getDrawStyle()
            if drawStyle is not None and "colz" in drawStyle.lower():
                canvasAddWidth = 0.13

        canvasAddWidth = canvasOpts.get("addWidth", canvasAddWidth)
        canvasAddHeight = canvasOpts.get("addHeight", None)

        if canvasAddWidth is not None:
            cw = ROOT.gStyle.GetCanvasDefW()
            prm = ROOT.gStyle.GetPadRightMargin()

            ROOT.gStyle.SetCanvasDefW(int((1+canvasAddWidth)*cw))
            ROOT.gStyle.SetPadRightMargin(canvasAddWidth+prm)
        if canvasAddHeight is not None:
            ch = ROOT.gStyle.GetCanvasDefH()
            ROOT.gStyle.SetCanvasDefH(int((1+canvasAddHeight)*ch))

        self.canvas = ROOT.TCanvas(name)
        self.pad = self.canvas.GetPad(0)

        if canvasAddWidth is not None:
            ROOT.gStyle.SetCanvasDefW(cw)
            ROOT.gStyle.SetPadRightMargin(prm)
        if canvasAddHeight is not None:
            ROOT.gStyle.SetCanvasDefH(ch)

        opts = kwargs
        if "opts" in kwargs:
            tmp = {}
            tmp.update(kwargs)
            if "opts2" in tmp:
                del tmp["opts2"]
            if len(tmp) != 1:
                raise Exception("If giving 'opts' as keyword argument, no other keyword arguments can be given (except opts2, which is ignored), got %s" % ",".join(tmp.keys()))
            opts = kwargs["opts"]
        tmp = opts
        opts = {}
        opts.update(tmp)

        if "yfactor" in opts:
            if "ymaxfactor" in opts:
                raise Exception("Only one of ymaxfactor, yfactor can be given")
            opts["ymaxfactor"] = opts["yfactor"]

        _boundsArgs(histos, opts)

        # Check if the first histogram has x axis bin labels
        rootHisto = histos[0].getRootHisto()
        hasBinLabels = isinstance(rootHisto, ROOT.TH1) and len(rootHisto.GetXaxis().GetBinLabel(1)) > 0
        if hasBinLabels and "TH2" not in str(type(rootHisto)): # added 23-Mar-2021 (to allow use plotBase with TH2)
            try:
                binWidth = histos[0].getBinWidth(1)
                opts["nbinsx"] = int((opts["xmax"]-opts["xmin"])/binWidth +0.5)
            except:
                # Added to allow for use with TH2 (for some reason 'hasBinLabels' does not get the instancec right
                # print type(rootHisto)
                binWidth = None
                opts["nbinsx"] = None

        self.frame = _drawFrame(self.canvas, opts["xmin"], opts["ymin"], opts["xmax"], opts["ymax"], opts.get("nbins", None), opts.get("nbinsx", None), opts.get("nbinsy", None))
        self.frame.GetXaxis().SetTitle(histos[0].getXtitle())
        self.frame.GetYaxis().SetTitle(histos[0].getYtitle())

        # Copy the bin labels
        if hasBinLabels:
            try:
                firstBin = rootHisto.FindFixBin(opts["xmin"])
                for i in xrange(0, opts["nbinsx"]):
                    self.frame.GetXaxis().SetBinLabel(i+1, rootHisto.GetXaxis().GetBinLabel(firstBin+i))
            except:
                # Added to allow for use with TH2 (for some reason 'hasBinLabels' does not get the instancec right
                # print type(rootHisto)
                pass
        return

class CanvasFrameTwo:
    '''
    Create TCanvas and frames for two TPads.
    '''
    def __init__(self, histoManager1, histoManager2, name, **kwargs):
        '''
        Create TCanvas and TH1 for the frame.
        
        \param histoManager1 HistoManager object to take the histograms for automatic axis ranges for upper pad
        \param histoManager2 HistoManager object to take the histograms for automatic axis ranges for lower pad
        \param name          Name for TCanvas (will be the file name, if TCanvas.SaveAs(".png") is used)
        \param kwargs        Keyword arguments (see below)
        
        <b>Keyword arguments</b>
        \li\a opts   Dictionary for frame bounds (forwarded to histograms._boundsArgs())
        \li\a opts1  Same as \a opts (can not coexist with \a opts, only either one can be given)
        \li\a opts2  Dictionary for ratio pad bounds (forwarded to histograms._boundsArgs()) Only Y axis values are allowed, for X axis values are taken from \a opts/\a opts1
        '''
        class FrameWrapper:
            '''
            Wrapper to provide the CanvasFrameTwo.frame member.
            
            The GetXaxis() is forwarded to the frame of the lower pad,
            and the GetYaxis() is forwared to the frame of the upper pad.
            '''
            def __init__(self, pad1, frame1, pad2, frame2):
                self.pad1 = pad1
                self.frame1 = frame1
                self.pad2 = pad2
                self.frame2 = frame2

            def GetXaxis(self):
                return self.frame2.GetXaxis()

            def GetYaxis(self):
                return self.frame1.GetYaxis()

            def getXmin(self):
                return th1Xmin(self.frame2)

            def getXmax(self):
                return th1Xmax(self.frame2)

            def Draw(self, *args):
                self.pad1.cd()
                self.frame1.Draw(*args)
                self.pad2.cd()
                self.frame2.Draw(*args)
                self.pad1.cd()

        class HistoWrapper:
            '''
            Wrapper to provide the getXmin/getXmax functions for _boundsArgs function.
            '''
            def __init__(self, histo):
                self.histo = histo

            def getRootHisto(self):
                return self.histo

            def getXmin(self):
                return th1Xmin(self.histo)

            def getXmax(self):
                return th1Xmax(self.histo)

            def getYmin(self):
                return self.histo.GetMinimum()

            def getYmax(self):
                return self.histo.GetMaximum()

        histos1 = []
        if isinstance(histoManager1, list):
            histos1 = histoManager1[:]
        else:
            histos1 = histoManager1.getHistos()
        if len(histos1) == 0:
            raise Exception("Empty set of histograms for first pad!")
        histos2 = []
        if isinstance(histoManager2, list):
            histos2 = histoManager2[:]
        else:
            histos2 = histoManager2.getHistos()
        if len(histos2) == 0:
            raise Exception("Empty set of histograms for second pad!")

        canvasFactor = kwargs.get("canvasFactor", 1.25)
        divisionPoint = 1-1/canvasFactor

        # Do it like this (create empty, update from kwargs) in order
        # to make a copy and NOT modify the dictionary in the caller
        opts1 = {}
        opts1.update(kwargs.get("opts", {}))
        if "opts1" in kwargs:
            if "opts" in kwargs:
                raise Exception("Can not give both 'opts' and 'opts1' as keyword arguments")
            opts1 = kwargs["opts1"]
        opts2 = {}
        opts2.update(kwargs.get("opts2", {}))

        if "xmin" in opts2 or "xmax" in opts2 or "nbins" in opts2 or "nbinsx" in opts2:
            raise Exception("No 'xmin', 'xmax', 'nbins', or 'nbinsy' allowed in opts2, values are taken from opts/opts1")

        _boundsArgs(histos1, opts1)
        opts2["xmin"] = opts1["xmin"]
        opts2["xmax"] = opts1["xmax"]
        opts2["nbins"] = opts1.get("nbins", None)
        opts2["nbinsx"] = opts1.get("nbinsx", None)
#        _boundsArgs([HistoWrapper(h) for h in histos2], opts2)
        _boundsArgs(histos2, opts2) # HistoWrapper not needed anymore? Ratio is Histo

        # Create the canvas, divide it to two
        self.canvas = ROOT.TCanvas(name, name, ROOT.gStyle.GetCanvasDefW(), int(ROOT.gStyle.GetCanvasDefH()*canvasFactor))
        self.canvas.Divide(1, 2)

        topMargin = ROOT.gStyle.GetPadTopMargin()
        bottomMargin = ROOT.gStyle.GetPadBottomMargin()
        divisionPoint += (1-divisionPoint)*bottomMargin # correct for (almost-)zeroing bottom margin of pad1
        divisionPointForPad1 = 1-( (1-divisionPoint) / (1-0.02) ) # then correct for the non-zero bottom margin, but for pad1 only

        # Set the lower point of the upper pad to divisionPoint
        self.pad1 = self.canvas.cd(1)
        yup = 1.0
        ylow = divisionPointForPad1
        xup = 1.0
        xlow = 0.0
        self.pad1.SetPad(xlow, ylow, xup, yup)
        self.pad1.SetFillStyle(4000) # transparent
        self.pad1.SetBottomMargin(0.02) # need some bottom margin here for eps/pdf output (at least in ROOT 5.34)

        # Set the upper point of the lower pad to divisionPoint
        self.pad2 = self.canvas.cd(2)
        yup = divisionPoint
        ylow = 0.0
        self.pad2.SetPad(xlow, ylow, xup, yup)
        self.pad2.SetFillStyle(4000) # transparent
        self.pad2.SetTopMargin(0.0)
        self.pad2.SetBottomMargin(bottomMargin/(canvasFactor*divisionPoint))

        self.canvas.cd(1)

        yoffsetFactor = canvasFactor#*1.15
        #xoffsetFactor = canvasFactor*1.6
        #xoffsetFactor = canvasFactor*2
        #xoffsetFactor = 0.5*canvasFactor/(canvasFactor-1) * 1.3
        #xoffsetFactor = 1/(canvasFactor*divisionPoint)
        xoffsetFactor = 1/divisionPoint

        # Check if the first histogram has x axis bin labels
        rootHisto = histos1[0].getRootHisto()
        hasBinLabels = isinstance(rootHisto, ROOT.TH1) and len(rootHisto.GetXaxis().GetBinLabel(1)) > 0
        if hasBinLabels:
            binWidth = histos1[0].getBinWidth(1)
            opts1["nbinsx"] = int((opts1["xmax"]-opts1["xmin"])/binWidth +0.5)
            opts2["nbinsx"] = opts1["nbinsx"]

        self.frame1 = _drawFrame(self.pad1, opts1["xmin"], opts1["ymin"], opts1["xmax"], opts1["ymax"], opts1.get("nbins", None), opts1.get("nbinsx", None), opts1.get("nbinsy", None))
        (labelSize, titleSize) = (self.frame1.GetXaxis().GetLabelSize(), self.frame1.GetXaxis().GetTitleSize())
        self.frame1.GetXaxis().SetLabelSize(0)
        self.frame1.GetXaxis().SetTitleSize(0)
        self.frame1.GetYaxis().SetTitle(histos1[0].getRootHisto().GetYaxis().GetTitle())
        self.frame1.GetYaxis().SetTitleOffset(self.frame1.GetYaxis().GetTitleOffset()*yoffsetFactor)

        self.canvas.cd(2)
        self.frame2 = _drawFrame(self.pad2, opts2["xmin"], opts2["ymin"], opts2["xmax"], opts2["ymax"], opts2.get("nbins", None), opts2.get("nbinsx", None))
        self.frame2.GetXaxis().SetTitle(histos1[0].getXtitle())
        self.frame2.GetYaxis().SetTitle(histos2[0].getYtitle())
        self.frame2.GetYaxis().SetTitleOffset(self.frame2.GetYaxis().GetTitleOffset()*yoffsetFactor)
        self.frame2.GetXaxis().SetTitleOffset(self.frame2.GetXaxis().GetTitleOffset()*xoffsetFactor)
        self.frame2.GetYaxis().SetLabelSize(int(self.frame2.GetYaxis().GetLabelSize()*0.8))

        self.canvas.cd(1)
        self.frame = FrameWrapper(self.pad1, self.frame1, self.pad2, self.frame2)
        self.pad = self.pad1

        # Copy the bin labels
        if hasBinLabels:
            firstBin = rootHisto.FindFixBin(opts1["xmin"])
            for i in xrange(0, opts1["nbinsx"]):
                self.frame.GetXaxis().SetBinLabel(i+1, rootHisto.GetXaxis().GetBinLabel(firstBin+i))

    ## \var frame1
    # TH1 for the upper frame
    ## \var frame2
    # TH2 for the lower frame
    ## \var canvas
    # TCanvas for the canvas
    ## \var pad
    # TPad for the upper pad
    ## \var pad1
    # TPad for the upper pad
    ## \var pad2
    # TPad for the lower pad
    ## \var frame
    # Wrapper for the two frames
    #
    # The y axis of the wrapper is taken from the upper frame, and the
    # xa xis from the lower frame.

## Base class for all Histo classes.
#
# Histo classes are wrappers for ROOT TH1/TH2/TGraph objects,
# providing one layer of customisation options between the end user
# and ROOT. The classes contain all necessary information to draw the
# histograms without the need for drawing code to know anything about
# the objects to be drawn (i.e. in addition of TH1, these contain the
# draw and legend styles).


## Base class for all Histo classes.
#
# Histo classes are wrappers for ROOT TH1/TH2/TGraph objects,
# providing one layer of customisation options between the end user
# and ROOT. The classes contain all necessary information to draw the
# histograms without the need for drawing code to know anything about
# the objects to be drawn (i.e. in addition of TH1, these contain the
# draw and legend styles).
class Histo:
    ## Constructor
    #
    # \todo test draw style "9"
    #
    # \param rootHisto    ROOT histogram object (TH1) or dataset.RootHistoWithUncertainties
    # \param name         Name of the histogram
    # \param legendStyle  Style string for TLegend (third parameter for TLegend.AddEntry())
    # \param drawStyle    Style string for Draw (string parameter for
    #                     TH1.Draw()). None to not to draw the histogram.
    # \param uncertaintyLegendStyle Style string for TLegend of the
    #                               uncertainty graph (if None, use \a legendStyle)
    # \param uncertaintyDrawStyle   Style string for Draw of the
    #                               uncertainty graph
    #                               (TGraphAsymmErrors.Draw()). None
    #                               to not to draw the systematic
    #                               uncertainty graph
    # \param uncertaintyLegendLabel Legend label of the uncertainty
    #                               graph (if None, graph is not added to legend)
    # \param kwargs       Keyword arguments (see below)
    #
    # <b>Keyword arguments</b>
    # \li\a legendLabel  Legend label (if None, histo is ignored for legend; if doesn't exist, use name)
    def __init__(self, rootHisto, name, legendStyle="l", drawStyle="HIST",
                 uncertaintyLegendStyle=None, uncertaintyDrawStyle=None, uncertaintyLegendLabel=None,
                 **kwargs):
        if isinstance(rootHisto, dataset.RootHistoWithUncertainties):
            self._histo = rootHisto
        else:
            self._histo = dataset.RootHistoWithUncertainties(rootHisto)
        self.name = name
        self.legendLabel = name
        if "legendLabel" in kwargs:
            self.legendLabel = kwargs["legendLabel"]
        self.legendStyle = legendStyle
        self.drawStyle = drawStyle

        self._uncertaintyLegendStyle = uncertaintyLegendStyle
        if self._uncertaintyLegendStyle is None:
            self._uncertaintyLegendStyle = self.legendStyle
        self._uncertaintyDrawStyle = uncertaintyDrawStyle
        self._uncertaintyLegendLabel = uncertaintyLegendLabel
        self._uncertaintyGraph = None
        self._uncertaintyGraphValid = False

    ## Get the ROOT histogram object (TH1)
    def getRootHisto(self):
        return self._histo.getRootHisto()

    ## (Re)set the ROOT histogram object (TH1)
    def setRootHisto(self, rootHisto):
        self._histo.setRootHisto(rootHisto)

    ## Get RootHistoWithUncertainties object
    def getRootHistoWithUncertainties(self):
        return self._histo

    ## Construct the systematic uncertainty graph
    #
    # \return TGraphAsymmErrors, or None if there are no systematic
    # uncertainties associated to the histogram.
    def getSystematicUncertaintyGraph(self):
        if not self._uncertaintyGraphValid and self._histo.hasSystematicUncertainties() and not uncertaintyMode.equal(Uncertainty.StatOnly):
            update = self.getRootHistoWithUncertainties().getSystematicUncertaintyGraph(uncertaintyMode.addStatToSyst())
            if self._uncertaintyGraph is not None:
                copyStyle(self._uncertaintyGraph, update)
            self._uncertaintyGraph = update

            self._uncertaintyGraphValid = True
        return self._uncertaintyGraph

    ## Add shape systematics variations
    #
    # \param name     Name of the uncertainty
    # \param th1plus  TH1 for plus variation
    # \param th1minus TH1 for minus variation
    def addShapeUncertaintyFromVariation(self, name, th1Plus, th1Minus):
        self._uncertaintyGraphValid = False
        self._histo.addShapeUncertaintyFromVariation(name, th1Plus, th1Minus)

    ## Add shape systematics as bin-wise relative uncertainties
    #
    # \param name  Name of the uncertainty
    # \param th1   TH1 containing the bin-wise relative uncertainties
    def addShapeUncertaintyRelative(self, name, th1):
        self._uncertaintyGraphValid = False
        self._histo.addShapeUncertaintyRelative(name, th1)

    ## Add normalization systematic uncertainty
    #
    # \param name         Name of the uncertainty
    # \param uncertainty  Uncertainty (e.g. 0.2 for 20 %)
    def addNormalizationUncertaintyRelative(self, name, uncertainty):
        self._uncertaintyGraphValid = False
        self._histo.addNormalizationUncertaintyRelative(name, uncertainty)

    ## Get the histogram name
    def getName(self):
        return self.name

    ## Set the histogram name
    #
    # \param name  New histogram name
    def setName(self, name):
        self.name = name

    ## Allow the Data/MC status of the Histo to be changed
    #
    # \param isData   True for data, false for MC
    # \param isMC     True for MC, false for data
    #
    # Some plotting defaults depend on whether histograms are data or
    # MC. This provides an ability to circumvent those.
    def setIsDataMC(self, isData, isMC):
        self._isData = isData
        self._isMC = isMC

    ## Is the histogram from MC?
    def isMC(self):
        if not hasattr(self, "_isMC"):
            raise Exception("setIsDataMC() has not been called, don't know if the histogram is from data or MC")
        return self._isMC

    ## Is the histogram from collision data?
    def isData(self):
        if not hasattr(self, "_isData"):
            raise Exception("setIsDataMC() has not been called, don't know if the histogram is from data or MC")
        return self._isData

    ## Set the histogram draw style
    #
    # \param drawStyle  new draw style
    def setDrawStyle(self, drawStyle):
        self.drawStyle = drawStyle

    ## Get the histogram draw style
    def getDrawStyle(self):
        return self.drawStyle

    ## Set the draw style for the uncertainty graph
    #
    # \param drawStyle  new draw style
    def setUncertaintyDrawStyle(self, drawStyle):
        self._uncertaintyDrawStyle = drawStyle

    ## Get the drawstyle of the uncertainty graph
    def getUncertaintyDrawStyle(self):
        return self._uncertaintyDrawStyle

    ## Set the legend label
    #
    # If the legend label is set to None, this Histo is not added to
    # TLegend in addToLegend()
    #
    # \param label  New histogram label for TLegend
    def setLegendLabel(self, label):
        self.legendLabel = label

    ## Set the legend label for the uncertainty graph
    #
    # If the legend label is set to None, the uncertainty graph is not
    # added to TLegend in addToLegend()
    #
    # \param label  New histogram label for TLegend
    def setUncertaintyLegendLabel(self, label):
        self._uncertaintyLegendLabel = label

    def getLegendStyle(self):
        return self.legendStyle

    ## Set the legend style
    #
    # \param style  New histogram style for TLegend
    def setLegendStyle(self, style):
        self.legendStyle = style

    ## Set the legend style for uncertainty graph
    #
    # \param style  New histogram style for TLegend
    def setUncertaintyLegendStyle(self, style):
        self._uncertaintyLegendStyle = style

    def _addToLegendHisto(self, legend):
        if self.legendLabel is None or self.legendStyle is None:
            return
        h = self.getRootHisto()
        if h is None:
            print >>sys.stderr, "WARNING: Trying to add Histo %s to the legend, but rootHisto is None" % self.getName()
            return

        cloned = False
        gr = self.getSystematicUncertaintyGraph()
        if gr is not None and self._uncertaintyLegendLabel is not None and \
                self.legendStyle.lower() == "f" and self._uncertaintyLegendStyle.lower() == "f":
            h = h.Clone("_forLegend")
            cloned = True
            fillStyles = [h.GetFillStyle(), self._uncertaintyGraph.GetFillStyle()]
            if 3345 in fillStyles and 3354 in fillStyles:
                h.SetFillStyle(3344)
            elif 3345 in fillStyles:
                h.SetFillStyle(3345)
            else:
                info = inspect.getframeinfo(inspect.currentframe())
                print >>sys.stderr, 'WARNING: encountered fill styles %d and %d for stat and syst uncertainties, and there is no support yet for "combining" them for stat. Consider adding your case to %s near line %d' % (fillStyles[0], fillStyles[1], info.filename, info.lineno)

        # Keep reference to avoid segfault
        self.rootHistoForLegend = addToLegend(legend, h, self.legendLabel, self.legendStyle, canModify=cloned)

    def _addToLegendUncertainty(self, legend):
        gr = self.getSystematicUncertaintyGraph()
        if gr is None or self._uncertaintyLegendLabel is None:
            return
        self._rootHistoForLegendUncertainty = addToLegend(legend, gr, self._uncertaintyLegendLabel, self._uncertaintyLegendStyle)

    ## Add the histogram to a TLegend
    #
    # If the legend label or draw style is None, do not add this Histo to TLegend
    #
    # \param legend   TLegend object
    def addToLegend(self, legend):
        self._addToLegendHisto(legend)
        self._addToLegendUncertainty(legend)

    ## Call a function with self as an argument.
    #
    # \param func  Function with one parameter
    #
    # \todo This resembles the Visitor pattern, perhaps this should be
    # renamed to visit()?
    def call(self, func):
        func(self)

    ## Draw the histogram
    #
    # \param opt  Drawing options (in addition to the draw style)
    def draw(self, opt):
        h = self.getRootHisto()
        if h is None:
            print >>sys.stderr, "WARNING: Trying to draw Histo %s, but rootHisto is None" % self.getName()
            return
        if self._uncertaintyDrawStyle is not None:
            unc = self.getSystematicUncertaintyGraph()
            if unc is not None:
                unc.Draw(self._uncertaintyDrawStyle+" "+opt)
        if self.drawStyle is not None:
            drawStyle = self.drawStyle+" "+opt
            h.Draw(drawStyle)
            tmp = drawStyle.lower()
            if "e" in tmp and "p" in tmp:
                if isinstance(h, ROOT.TH1):
                    self._nonVisibleErrorLinesTH1 = drawNonVisibleErrorsTH1(h)
#                elif isinstance(h, ROOT.TGraphErrors):
#                    drawNonVisibleErrorsTGraph(h)

    def Draw(self, *args):
        self.draw(*args)

    ## Get the minimum value of the X axis
    def getXmin(self):
        return self._histo.getXmin()

    ## Get the maximum value of the X axis
    def getXmax(self):
        return self._histo.getXmax()

    ## Get the minimum value of the Y axis
    def getYmin(self):
        return self._histo.getYmin()

    ## Get the maximum value of the Y axis
    def getYmax(self):
        return self._histo.getYmax()

    ## Get the X axis title
    def getXtitle(self):
        return self._histo.getXtitle()

    ## Get the Y axis title
    def getYtitle(self):
        return self._histo.getYtitle()

    ## Get the width of a bin
    #
    # \param bin  Bin number
    def getBinWidth(self, bin):
        return self._histo.getBinWidth(bin)

    ## Get list of bin widths
    def getBinWidths(self):
        return self._histo.getBinWidths()

    ## \var _histo
    # dataset.RootHistoWithUncertainties object
    ## \var name
    # Histogram name
    ## \var legendLabel
    # Label for TLegend
    ## \var legendStyle
    # Style string for TLegend
    ## \var drawStyle
    # Style string for Draw()
    ## \var _uncertaintyLegendStyle
    # Legend style for the uncertainty graph
    ## \var _uncertaintyDrawStyle
    # Draw style for the uncertainty graph
    ## \var _uncertaintyLegendLabel
    # Legend label for the uncertainty graph
    ## \var _uncertaintyGraph
    # Cached uncertainty graph
    ## \var _uncertaintyGraphValid
    # True, if _uncertaintyGraph cache is still valid (i.e. systematic uncertainties have not been modified)
    ## \var _isData
    # Is the histogram from data?
    ## \var _isMC
    # Is the histogram from MC?

class HistoWithDataset(Histo):
    '''
    Represents one (TH1/TH2) histogram associated with a dataset.Dataset object
    
    Treats pseudo-datasets as MC-datasets.
    '''
    def __init__(self, *args, **kwargs):
        '''
        Constructor
        
        \param args    Position arguments (see below)
        \param kwargs  Keyword arguments (see below)
        
        Either positional or keyword arguments are allowed
        
        <b>Positional arguments</b>
        \li\a dataset    dataset.Dataset object
        \li\a rootHisto  TH1 or RootHistoWithUncertainties object
        \li\a name       Name of the Histo
        
        <b>Keyword arguments</b>
        \li\a datasetRootHisto  dataset.DatasetRootHisto object
        
        The default legend label is the dataset name
        '''
        if len(kwargs) == 0 and len(args) != 3:
            raise Exception("In absence of keyword arguments, I expect 3 positional arguments (dataset, rootHisto, name). Now I got %d." % len(args))
        if len(args) == 0 and len(kwargs) != 1 and not "datasetRootHisto" in kwargs:
            raise Exception("In absence of positional arguments, I expect 1 keyword argument 'datasetRootHisto. Now I got %s" % ",".join(kwargs.keys()))

        if len(args) > 0:
            Histo.__init__(self, args[1], args[2])
            self.dataset = args[0]
        else:
            drh = kwargs["datasetRootHisto"]
            Histo.__init__(self, drh.getHistogramWithUncertainties(), drh.getName())
            self.dataset = drh.getDataset()

        self.setIsDataMC(self.dataset.isData(), self.dataset.isMC() or self.dataset.isPseudo())

    def getDataset(self):
        '''
        Get the dataset.Dataset object
        '''
        return self.dataset

    ## \var dataset
    # The histogram is from this dataset.Dataset object

class HistoWithDatasetFakeMC(HistoWithDataset):
    def __init__(self, dataset, rootHisto, name, **kwargs):
        HistoWithDataset.__init__(self, dataset, rootHisto, name, **kwargs)
        self.setIsDataMC(False, True)

class HistoStacked(Histo):
    '''
    Represents stacked TH1 histograms
    
    Stacking is done with the help of THStack object
    '''
    def __init__(self, histos, name, **kwargs):
        '''
        Constructor.
        
        \param histos  List of Histo objects to stack
        \param name    Name of the stacked histogram
        \param kwargs  Keyword arguments (forwarded to Histo.__init__())
        '''
        Histo.__init__(self, ROOT.THStack(name+"stackHist", name+"stackHist"), name, None, "HIST", **kwargs)
        self.histos = histos

        histos = filter(lambda h: h.getRootHisto() is not None, [d.getRootHistoWithUncertainties() for d in self.histos])
        if len(histos) == 0:
            raise Exception("Got 0 histograms, or all input histograms are None")
        histos.reverse()
        thStack = self.getRootHisto()
        for h in histos:
            # Addition of uncertainties is done on the fly in getSumRootHistoWithUncertainties()
            thStack.Add(h.getRootHisto())

        self.setIsDataMC(self.histos[0].isData(), self.histos[0].isMC())

    def setRootHisto(self, rootHisto):
        raise NotImplementedError("HistoStacked.setRootHisto() would be ill-defined")

    def getAllRootHistos(self):
        '''
        Get the list of original TH1 histograms.
        '''
        return [x.getRootHisto() for x in self.histos]

    def getSumRootHisto(self):
        '''
        Get the sum of the original histograms.
        '''
        return sumRootHistos([d.getRootHisto() for d in self.histos])

    def getAllRootHistoWithUncertainties(self):
        return [x.getRootHistoWithUncertainties() for x in self.histos]

    def getSumRootHistoWithUncertainties(self):
        return sumRootHistos(self.getAllRootHistoWithUncertainties())

    def getSumSystematicUncertaintyGraph(self):
        if not self._uncertaintyGraphValid and self._histo.hasSystematicUncertainties() and not uncertaintyMode.equal(Uncertainty.StatOnly):
            update = self.getSumRootHistoWithUncertainties().getSystematicUncertaintyGraph(uncertaintyMode.addStatToSyst())
            if self._uncertaintyGraph is not None:
                copyStyle(self._uncertaintyGraph, update)
            self._uncertaintyGraph = update
            self._uncertaintyGraphValid = True
        return self._uncertaintyGraph

    def getSystematicUncertaintyGraph(self):
        return None

    def setLegendLabel(self, label):
        for h in self.histos:
            h.setLegendLabel(label)

    def setLegendStyle(self, style):
        for h in self.histos:
            h.setLegendStyle(style)

    def addToLegend(self, legend):
        for h in self.histos:
            h.addToLegend(legend)

    ## Call a function for each Histo in the stack.
    #
    # \param function  Function with one parameter
    #
    # \todo This resembles the Visitor pattern, perhaps this should be
    # renamed to visit()?
    def call(self, function):
        for h in self.histos:
            h.call(function)

    def getXmin(self):
        return min(filter(lambda x: x is not None, [h.getXmin() for h in self.histos]))

    def getXmax(self):
        return max(filter(lambda x: x is not None, [h.getXmax() for h in self.histos]))

    def getBinWidth(self, bin):
        for h in self.histos:
            w = h.getBinWidth(bin)
            if w is not None:
                return w
        return None

    ## \var histos
    # List of histograms.Histo objects which are stacked

## Represents TGraph objects
#
# \todo The way to detect TGraph from TGraphErrors or TGraphAsymmErrors is really ugly
class HistoGraph(Histo):
    ## Constructor
    #
    # \param rootGraph    TGraph object
    # \param name         Name of the histogram
    # \param legendStyle  Style string for TLegend (third parameter for TLegend.AddEntry())
    # \param drawStyle    Style string for Draw (string parameter for TH1.Draw())
    # \param kwargs       Keyword arguments (forwarded for Histo.__init__())
    def __init__(self, rootGraph, name, legendStyle="l", drawStyle="L", **kwargs):
        Histo.__init__(self, rootGraph, name, legendStyle, drawStyle, **kwargs)

    def getRootGraph(self):
        return self.getRootHisto()

    def setRootGraph(self, rootGraph):
        self.setRootHisto(rootGraph)

    def _values(self, values, func):
        return [func(values[i], i) for i in xrange(0, self.getRootGraph().GetN())]

    def getXmin(self):
        if isinstance(self.getRootGraph(), ROOT.TGraphErrors) or isinstance(self.getRootGraph(), ROOT.TGraphAsymmErrors):
            function = lambda val, i: val-self.getRootGraph().GetErrorXlow(i)
        else:
            # TGraph.GetError[XY]{low,high} return -1 ...
            function = lambda val, i: val
        return min(self._values(self.getRootGraph().GetX(), function))

    def getXmax(self):
        if isinstance(self.getRootGraph(), ROOT.TGraphErrors) or isinstance(self.getRootGraph(), ROOT.TGraphAsymmErrors):
            function = lambda val, i: val+self.getRootGraph().GetErrorXhigh(i)
        else:
            # TGraph.GetError[XY]{low,high} return -1 ...
            function = lambda val, i: val
        return max(self._values(self.getRootGraph().GetX(), function))

    def getYmin(self):
        if isinstance(self.getRootGraph(), ROOT.TGraphErrors) or isinstance(self.getRootGraph(), ROOT.TGraphAsymmErrors):
            function = lambda val, i: val-self.getRootGraph().GetErrorYlow(i)
        else:
            # TGraph.GetError[XY]{low,high} return -1 ...
            function = lambda val, i: val
        return min(self._values(self.getRootGraph().GetY(), function))

    def getYmax(self):
        if isinstance(self.getRootGraph(), ROOT.TGraphErrors) or isinstance(self.getRootGraph(), ROOT.TGraphAsymmErrors):
            function = lambda val, i: val+self.getRootGraph().GetErrorYhigh(i)
        else:
            # TGraph.GetError[XY]{low,high} return -1 ...
            function = lambda val, i: val
        return max(self._values(self.getRootGraph().GetY(), function))

    def getBinWidth(self, bin):
        raise Exception("getBinWidth() is meaningless for HistoGraph (name %s)" % self.getName())

## Represents TGraph objects with associated dataset.Dataset object
class HistoGraphWithDataset(HistoGraph):
    ## Constructor
    #
    # \param dataset  dataset.Dataset object
    # \param args     Positional arguments (forwarded to histograms.HistoGraph.__init__())
    # \param kwargs   Keyword arguments (forwarded to histograms.HistoGraph.__init__())
    def __init__(self, dataset, *args, **kwargs):
        HistoGraph.__init__(self, *args, **kwargs)
        self.dataset = dataset
        self.setIsDataMC(self.dataset.isData(), self.dataset.isMC())

    def getDataset(self):
        return self.dataset

## Represents combined (statistical) uncertainties of multiple histograms.
class HistoTotalUncertainty(HistoGraph):
    ## Constructor
    #
    # \param histos  List of histograms.Histo objects
    # \param name    Name of the uncertainty histogram
    def __init__(self, histos, name):
        rootHistosWithUnc = []
        for h in histos:
            if hasattr(h, "getSumRootHistoWithUncertainties"):
                ret = h.getSumRootHistoWithUncertainties()
            else:
                ret = h.getRootHistoWithUncertainties()
            if ret is not None:
                rootHistosWithUnc.append(ret)
        if len(rootHistosWithUnc) == 0:
            raise Exception("Got 0 histograms, or all input histograms are None")

        tmp = rootHistosWithUnc[0].Clone()
        tmp.SetDirectory(0)
        for h in rootHistosWithUnc[1:]:
            tmp.Add(h)
        if uncertaintyMode.equal(Uncertainty.SystOnly):
            tmpgr = tmp.getSystematicUncertaintyGraph()
        else:
            tmpgr = tmp.getSystematicUncertaintyGraph(addStatistical=True, addSystematic=False)
        HistoGraph.__init__(self, dataset.RootHistoWithUncertainties(tmpgr), name, "F", "E2")
        self._histo.SetName(rootHistosWithUnc[0].GetName()+"_errors")
        self.histos = histos
        self.setIsDataMC(self.histos[0].isData(), self.histos[0].isMC())

        if tmp.hasSystematicUncertainties() and not uncertaintyMode.equal(Uncertainty.StatOnly):
            self._uncertaintyGraph = tmp.getSystematicUncertaintyGraph(uncertaintyMode.addStatToSyst())
            self._uncertaintyGraphValid = True
            self.setUncertaintyDrawStyle("E2")

        if not uncertaintyMode.showStatOnly():
            self.setDrawStyle(None)

    ## \var histos
    # List of histograms.Histo objects from which the total uncertaincy is calculated

## Represents TEfficiency objects
class HistoEfficiency(Histo):
    ## Constructor
    #
    # \param rootEfficiency TEfficiency object
    # \param name         Name of the histogram
    # \param legendStyle  Style string for TLegend (third parameter for TLegend.AddEntry())
    # \param drawStyle    Style string for Draw (string parameter for TH1.Draw())
    # \param kwargs       Keyword arguments (forwarded to Histo.__init__())
    def __init__(self, rootEfficiency, name, legendStyle="l", drawStyle="L", **kwargs):
        Histo.__init__(self, rootEfficiency, name, legendStyle, drawStyle, **kwargs)

    def _values(self, function):
        ret = []
        for bin in xrange(1, self.getRootPassedHisto().GetNbinsX()+1):
            ret.append(function(self.getRootEfficiency(), bin))
        return ret

    def getRootEfficiency(self):
        return self.getRootHisto()

    def setRootEfficiency(self, rootEfficiency):
        self.setRootEfficiency(rootEfficiency)

    def getRootPassedHisto(self):
        return self.getRootEfficiency().GetPassedHistogram()

    def getXmin(self):
        return th1Xmin(self.getRootPassedHisto())

    def getXmax(self):
        return th1Xmax(self.getRootPassedHisto())

    def getYmin(self):
        return min(self._values(lambda eff, bin: eff.GetEfficiency(bin)-eff.GetEfficiencyErrorLow(bin)))

    def getYmax(self):
        return max(self._values(lambda eff, bin: eff.GetEfficiency(bin)+eff.GetEfficiencyErrorUp(bin)))

    def getYmin(self):
        return self.getRootPassedHisto().GetMinimum()

    def getYmax(self):
        return 1.0

    def getXtitle(self):
        return self.getRootPassedHisto().GetXaxis().GetTitle()

    def getYtitle(self):
        return "Efficiency"

    def getBinWidth(self, bin):
        return self.getRootPassedHisto().GetBinWidth(bin)


## Implementation of HistoManager.
#
# Intended to be used only from histograms.HistoManager. This class contains all
# the methods which require the Histo objects (and only them).
#
# Contains two lists for histograms, one for the drawing order, and
# other for the legend insertion order. By default, the histogram
# which is first in the legend, is drawn last such that it is in the
# top of all drawn histograms. Both lists can be reordered if user
# wants.
class HistoManagerImpl:
    ## Constructor.
    #
    # \param histos    List of histograms.Histo objects
    def __init__(self, histos=[]):

        # List for the Draw() order, keep it reversed in order to draw
        # the last histogram in the list first. i.e. to the bottom
        self.drawList = histos[:]

        # List for the legend order, first histogram is also first in
        # the legend
        self.legendList = histos[:]

        # Dictionary for accessing the histograms by name
        self._populateMap()

    ## Get the number of managed histograms.Histo objects
    def __len__(self):
        return len(self.drawList)

    ## Populate the name -> histograms.Histo map
    def _populateMap(self):
        self.nameHistoMap = {}
        for h in self.drawList:
            self.nameHistoMap[h.getName()] = h

    ## Append a histograms.Histo object.
    #
    # \param histo   histograms.Histo object to be added
    def appendHisto(self, histo):
        self.drawList.append(histo)
        self.legendList.append(histo)
        self._populateMap()

    ## Extend with a list of histograms.Histo objects.
    #
    # \param histos  List of histograms.Histo objects to be added
    def extendHistos(self, histos):
        self.drawList.extend(histos)
        self.legendList.extend(histos)
        self._populateMap()

    ## Insert histograms.Histo to position i.
    #
    # \param i      Index of the position to insert the histogram
    # \param histo  histograms.Histo object to insert
    # \param kwargs Keyword arguments
    # 
    # <b>Keyword arguments</b>
    # \li \a legendIndex  Index of the position to insert the histogram in
    #                     the legend list (default is the same as i). Can
    #                     be useful for e.g. separate uncertainty histogram.
    def insertHisto(self, i, histo, **kwargs):
        drawIndex = i
        legendIndex = i

        if "legendIndex" in kwargs:
            legendIndex = kwargs["legendIndex"]

        self.drawList.insert(drawIndex, histo)
        self.legendList.insert(legendIndex, histo)
        self._populateMap()

    ## Remove histograms.Histo object
    #
    # \param name  Name of the histograms.Histo object to be removed
    def removeHisto(self, name):
        del self.nameHistoMap[name]
        for i, h in enumerate(self.drawList):
            if h.getName() == name:
                del self.drawList[i]
                break
        for i, h in enumerate(self.legendList):
            if h.getName() == name:
                del self.legendList[i]
                break

    def removeAllHistos(self):
        self.drawList = []
        self.legendList = []
        self._populateMap()

    ## Replace histograms.Histo object
    #
    # \param name   Name of the histograms.Histo object to be replaced
    # \param histo  New histograms.Histo object
    def replaceHisto(self, name, histo):
        if not name in self.nameHistoMap:
            raise Exception("Histogram %s doesn't exist" % name)
        self.nameHistoMap[name] = histo
        for i, h in enumerate(self.drawList):
            if h.getName() == name:
                self.drawList[i] = histo
                break
        for i, h in enumerate(self.legendList):
            if h.getName() == name:
                self.legendList[i] = histo
                break

    ## Reverse draw and legend lists
    def reverse(self):
        self.drawList.reverse()
        self.legendList.reverse()

    ## Reorder both draw and legend lists
    #
    # \param histogNames   List of histogram names
    def reorder(self, histoNames):
        self.reorderDraw(histoNames)
        self.reorderLegend(histoNames)

    ## Reorder the legend
    #
    # \param histoNames  List of histogram names
    #
    # The legend list is reordered as specified by histoNames.
    # Histograms not mentioned in histoNames are kept in the original
    # order at the end of the legend.
    def reorderLegend(self, histoNames):
        def index_(list_, name_):
            for i, o in enumerate(list_):
                if o.getName() == name_:
                    return i
            raise Exception("No such histogram %s" % name_)

        src = self.legendList[:]
        dst = []
        for name in histoNames:
            dst.append(src.pop(index_(src, name)))
        dst.extend(src)
        self.legendList = dst

    ## Reorder the draw list
    #
    # \param histoNames  List of histogram names
    #
    # The draw list is reordered as specified by histoNames.
    # Histograms not mentioned in histoNames are kept in the original
    # order at the end of the draw list.
    def reorderDraw(self, histoNames):
        def index_(list_, name_):
            for i, o in enumerate(list_):
                if o.getName() == name_:
                    return i
            raise Exception("No such histogram %s" % name_)

        src = self.drawList[:]
        dst = []
        for name in histoNames:
            dst.append(src.pop(index_(src, name)))
        dst.extend(src)
        self.drawList = dst

    ## Call a function for a named histograms.Histo object.
    #
    # \param name   Name of histogram
    # \param func   Function taking one parameter (histograms.Histo), return value is not used
    def forHisto(self, name, func):
        try:
            self.nameHistoMap[name].call(func)
        except KeyError:
            print >> sys.stderr, "WARNING: Tried to call a function for histogram '%s', which doesn't exist." % name

    ## Call each MC histograms.Histo with a function.
    #
    # \param func   Function taking one parameter (histograms.Histo), return value is not used
    def forEachMCHisto(self, func):
        def forMC(histo):
            if histo.isMC():
                func(histo)

        self.forEachHisto(forMC)

    ## Call each collision data histograms.Histo with a function.
    #
    # \param func  Function taking one parameter (Histo, return value is not used
    def forEachDataHisto(self, func):
        def forData(histo):
            if histo.isData():
                func(histo)
        self.forEachHisto(forData)

    ## Call each histograms.Histo with a function.
    #
    # \param func  Function taking one parameter (Histo), return value is not used
    def forEachHisto(self, func):
        for d in self.drawList:
            d.call(func)

    ## Check if a histograms.Histo with a given name exists
    #
    # \param name   Name of histograms.Histo to check
    def hasHisto(self, name):
        return name in self.nameHistoMap

    def getHisto(self, name):
        '''
        Get histograms.Histo of a given name
        
        \param name  Name of histograms.Histo to get
        '''
        if name in self.nameHistoMap.keys():
            return self.nameHistoMap[name]
        else:
            msg = "Cannot find histogram with name \"%s\" in the nameHistoMap.Please choose one of the following: %s" % (name, ", ".join(self.nameHistoMap.keys()))
            raise Exception(msg)

    def getHistos(self):
        '''
         Get all histograms.Histo objects
         '''
        return self.drawList[:]

    ## Set legend names for given histograms.
    #
    # \param nameMap   Dictionary with name->label mappings
    def setHistoLegendLabelMany(self, nameMap):
        for name, label in nameMap.iteritems():
            try:
                self.nameHistoMap[name].setLegendLabel(label)
            except KeyError:
                print >> sys.stderr, "WARNING: Tried to set legend label for histogram '%s', which doesn't exist." % name

    ## Set the legend style for a given histogram.
    #
    # \param name   Name of the histogram
    # \param style  Style for the legend (given to TLegend as 3rd argument)
    def setHistoLegendStyle(self, name, style):
        try:
            self.nameHistoMap[name].setLegendStyle(style)
        except KeyError:
            print >> sys.stderr, "WARNING: Tried to set legend style for histogram '%s', which doesn't exist." % name

    ## Set the legend style for all histograms.
    #
    # \param style  Style for the legend (given to TLegend as 3rd argument)
    def setHistoLegendStyleAll(self, style):
        for d in self.legendList:
            d.setLegendStyle(style)

    ## Set histogram drawing style for a given histogram.
    #
    # \param name   Name of the histogram
    # \param style  Style for obj.Draw() call
    def setHistoDrawStyle(self, name, style):
        try:
            self.nameHistoMap[name].setDrawStyle(style)
        except KeyError:
            print >> sys.stderr, "WARNING: Tried to set draw style for histogram '%s', which doesn't exist." % name

    ## Set the histogram drawing style for all histograms.
    #
    # \param style  Style for obj.Draw() call
    def setHistoDrawStyleAll(self, style):
        for d in self.drawList:
            d.setDrawStyle(style)

    ## Add histograms to a given TLegend.
    #
    # \param legend  TLegend object
    def addToLegend(self, legend):
        for d in self.legendList:
            d.addToLegend(legend)

    ## Draw histograms.
    #
    # \param untilName  If not None, untilName is the last histogram to
    #                   be drawn. In this case, the current index is
    #                   returned.
    # \param fromIndex  If not None, fromIndex is the index of the
    #                   first histogram to be drawn.
    #
    # Use case for the two above ones is to draw stat and syst+stat
    # ratios on the "background" of the ratio pad, then draw the ratio
    # line, and finally continue with the rest of the ratio histograms.
    def draw(self, untilName=None, fromIndex=None):
        # Reverse the order of histograms so that the last histogram
        # is drawn first, i.e. on the bottom
        histos = self.drawList[:]
        histos.reverse()

        for i, h in enumerate(histos):
            if fromIndex is not None and i < fromIndex:
                continue
            h.draw("same")
            if untilName is not None and h.getName() == untilName:
                return i
        return None

    ## Stack histograms.
    #
    # \param newName   Name of the histogram stack
    # \param nameList  List of histogram names to stack
    def stackHistograms(self, newName, nameList):
        (selected, notSelected, firstIndex) = dataset._mergeStackHelper(self.drawList, nameList, "stack")
        if len(selected) == 0:
            return

        stacked = HistoStacked(selected, newName)
        notSelected.insert(firstIndex, stacked)
        self.drawList = notSelected

        self.legendList = filter(lambda x: x in notSelected, self.legendList)
        self.legendList.insert(firstIndex, stacked)

        self._populateMap()

    ## Add MC uncertainty band histogram
    #
    # \param style        Style function for the uncertainty histogram
    # \param name         Name of the unceratinty histogram
    # \param legendLabel  Legend label for the uncertainty histogram
    # \param uncertaintyLegendLabel  Legend label for the (stat+)syst uncertainty histogram
    # \param nameList     List of histogram names to include to the uncertainty band (\a None corresponds all MC)
    def addMCUncertainty(self, style, name="MCuncertainty", legendLabel="Sim. stat. unc.", uncertaintyLegendLabel=None, nameList=None):
        mcHistos = filter(lambda x: x.isMC(), self.drawList)
        if len(mcHistos) == 0:
            print >> sys.stderr, "WARNING: Tried to create MC uncertainty histogram, but there are not MC histograms!"
            return

        if nameList != None:
            mcHistos = filter(lambda x: x.getName() in nameList, mcHistos)
        if len(mcHistos) == 0:
            print >>sys.stderr, "WARNING: No MC histograms to use for uncertainty band"
            return

        hse = HistoTotalUncertainty(mcHistos, name)
        hse.setLegendLabel(legendLabel)
        hse.setUncertaintyLegendLabel(uncertaintyLegendLabel)
        hse.call(style)

        firstMcIndex = len(self.drawList)
        for i, h in enumerate(self.drawList):
            if h.isMC():
                firstMcIndex = i
                break
        self.insertHisto(firstMcIndex, hse, legendIndex=len(self.drawList))
        
    ## \var drawList
    # List of histograms.Histo objects for drawing
    # The histograms are drawn in the <i>reverse</i> order, i.e. the
    # first histogram is on the top, anbd the last histogram is on the
    # bottom.
    #
    ## \var legendList
    # List of histograms.Histo objects for TLegend
    # The histograms are added to the TLegend in the order they are in
    # the list.
    #
    ## \var nameHistoMap
    # Dictionary from histograms.Histo names to the objects


## Collection of histograms which are managed together.
#
# The histograms in a HistoManager are drawn to one plot.

# The implementation is divided to this and
# histograms.HistoManagerImpl class. The idea is that here are the
# methods, which don't require Histo objects (namely setting the
# normalization), and histograms.HistoManagerImpl has all the methods
# which require the histograms.Histo objects. User can set freely the
# normalization scheme as many times as (s)he wants, and at the first
# time some method not implemented in HistoManagerBase is called, the
# Histo objects are created and the calls are delegated to
# HistoManagerImpl class.
class HistoManager:
    ## Constructor.
    #
    # \param args   Positional arguments
    # \param kwargs Keyword arguments
    #
    # <b>Positional arguments</b>
    # \li \a datasetMgr   DatasetManager object to take the histograms from
    # \li \a name         Path to the TH1 objects in the DatasetManager ROOT files
    #
    # <b>Keyword arguments</b>
    # \li \a datasetRootHistos   Initial list of DatasetRootHisto objects
    #
    # Only either both positional arguments or the keyword argument
    # can be given.
    #
    # \todo The interface should be fixed to have only the keyword
    #       argument (also as the only positional argument). This is
    #       not done yet for backward compatibility.
    def __init__(self, *args, **kwargs):
        if len(args) == 0:
            if len(kwargs) == 0:
                self.datasetRootHistos = []
            elif len(kwargs) == 1:
                self.datasetRootHistos = kwargs["datasetRootHistos"]
            else:
                raise Exception("If positional arguments are not given, there must be ither 0 or 1 keyword argument (got %d)"%len(kwargs))
        else:
            if len(args) != 2:
                raise Exception("Must give exactly 2 positional arguments (got %d)" % len(args))
            if len(kwargs) != 0:
                raise Exception("If positional arguments are given, there must not be any keyword arguments")
            datasetMgr = args[0]
            name = args[1]

            self.datasetRootHistos = datasetMgr.getDatasetRootHistos(name)

        self.impl = None
        self.luminosity = None

    ## Delegate the calls which require the histograms.Histo objects to the implementation class.
    #
    # \param name  Name of the attribute to get
    def __getattr__(self, name):
        if self.impl == None:
            self._createImplementation()
        return getattr(self.impl, name)

    ## Append dataset.DatasetRootHistoBase object
    #
    # \param datasetRootHisto  dataset.DatasetRootHistoBase object
    def append(self, datasetRootHisto):
        if self.impl != None:
            raise Exception("Can't append after the histograms have been created!")
        if not isinstance(datasetRootHisto, dataset.DatasetRootHistoBase):
            raise Exception("Can append only DatasetRootHistoBase derived objects, got %s" % str(datasetRootHisto))
        self.datasetRootHistos.append(datasetRootHisto)

    ## Extend with another HistoManager or a list of dataset.DatasetRootHistoBase objects
    #
    # \param datasetRootHistos  HistoManager object, or a list of dataset.DatasetRootHistoBase objects
    def extend(self, datasetRootHistos):
        if self.impl != None:
            raise Exception("Can't extend after the histograms have been created!")
        if isinstance(datasetRootHistos, HistoManager):
            if datasetRootHistos.impl != None:
                raise Exception("Can't extend from HistoManagerBase whose histograms have been created!")
            datasetRootHistos = HistoManagerBase.datasetRootHistos
        for d in datasetRootHistos:
            if not isinstance(datasetRootHisto, dataset.DatasetRootHistoBase):
                raise Exception("Can extend only DatasetRootHistoBase derived objects, got %s" % str(d))
        self.datasetRootHistos.extend(datasetRootHistos)

    ## Set the histogram normalization scheme to <i>to one</i>.
    #
    # All histograms are normalized to unit area.
    def normalizeToOne(self):
        if self.impl != None:
            raise Exception("Can't normalize after the histograms have been created!")
        for h in self.datasetRootHistos:
            h.normalizeToOne()
        self.luminosity = None

    ## Set the MC histogram normalization scheme to <i>by cross section</i>.
    #
    # All histograms from MC datasets are normalized by their cross
    # section.
    def normalizeMCByCrossSection(self):
        if self.impl != None:
            raise Exception("Can't normalize after the histograms have been created!")
        for h in self.datasetRootHistos:
            if h.getDataset().isMC():
                h.normalizeByCrossSection()
        self.luminosity = None

    ## Set the MC histogram normalization <i>by luminosity</i>.
    #
    # The set of histograms is required to contain one, and only one
    # histogram from data dataset (if there are many data datasets,
    # they should be merged first). All histograms from MC datasets
    # are normalized to the integrated luminosity of the the data
    # dataset.
    def normalizeMCByLuminosity(self):
        if self.impl != None:
            raise Exception("Can't normalize after the histograms have been created!")
        lumi = None
        for h in self.datasetRootHistos:
            if h.getDataset().isData():
                if lumi != None:
                    raise Exception("Unable to normalize by luminosity, more than one data datasets (you might want to merge data datasets)")
                lumi = h.getDataset().getLuminosity()

        if lumi == None:
            raise Exception("Unable to normalize by luminosity, no data datasets")

        self.normalizeMCToLuminosity(lumi)

    ## Set the MC histogram normalization <i>to luminosity</i>.
    #
    # \param lumi   Integrated luminosity (pb^-1)
    #
    # All histograms from MC datasets are normalized to the given
    # integrated luminosity.
    def normalizeMCToLuminosity(self, lumi):
        if self.impl != None:
            raise Exception("Can't normalize after the histograms have been created!")
        for h in self.datasetRootHistos:
            if h.getDataset().isMC():
                h.normalizeToLuminosity(lumi)
        self.luminosity = lumi
        return

    def hasLuminosity(self):
        return self.luminosity is not None

    def getLuminosity(self):
        '''
        Get the integrated luminosity to which the MC datasets have been normalized to.
        '''
        if self.luminosity == None:
            raise Exception("No normalization by or to luminosity!")
        return self.luminosity

    def addLuminosityText(self, x=None, y=None):
        '''
        Draw the text for the integrated luminosity.
        
        \param x   X coordinate of the text (\a None for default)
        \param y   Y coordinate of the text (\a None for default)
        '''
        _printTextDeprecationWarning("histograms.HistoManager.addLuminosityText()", "histograms.addStandardTexts() with histograms.HistoManager.getLuminosity()")
        addLuminosityText(x, y, self.getLuminosity())
        return

    def _createImplementation(self):
        '''
        Create the HistoManagerImpl object.
        '''
        self.impl = HistoManagerImpl([HistoWithDataset(datasetRootHisto=drh) for drh in self.datasetRootHistos])

    ## Stack all MC histograms to one named <i>StackedMC</i>.
    def stackMCHistograms(self):
        histos = self.getHistos()

        self.stackHistograms("StackedMC", [h.getName() for h in filter(lambda h: h.isMC(), self.getHistos())])

    ## \var datasetRootHistos
    # List of dataset.DatasetRootHisto objects to manage
    ## \var impl
    # histograms.HistoManagerImpl object for the implementation
    ## \var luminosity
    # Total integrated luminosity ofthe managed collision data (None if not set)


def addSysError(histogram,syserror):
    # error in decimals
    for i in range(1,histogram.GetNbinsX()+1):
        error  = histogram.GetBinError(i)
        value  = histogram.GetBinContent(i)
        syserr = value*syserror    

        newError = math.sqrt(error*error + syserr*syserr)
        histogram.SetBinError(i,newError)
    return histogram

## added from H2HW, aux.py
def copyStyle(src, dst):
    properties = []
    if hasattr(src, "GetLineColor") and hasattr(dst, "SetLineColor"):
        properties.extend(["LineColor", "LineStyle", "LineWidth"])
    if hasattr(src, "GetFillColor") and hasattr(dst, "SetFillColor"):
        properties.extend(["FillColor", "FillStyle"])
    if hasattr(src, "GetMarkerColor") and hasattr(dst, "SetMarkerColor"):
        properties.extend(["MarkerColor", "MarkerSize", "MarkerStyle"])

    for prop in properties:
        getattr(dst, "Set"+prop)(getattr(src, "Get"+prop)())

def addToLegend(legend, rootObject, legendLabel, legendStyle, canModify=False):
    # Hack to get the black border to the legend, only if the legend style is fill
    h = rootObject
    ret = None
    if "f" == legendStyle.lower():
        if not canModify:
            h = rootObject.Clone(h.GetName()+"_forLegend")
            if hasattr(h, "SetDirectory"):
                h.SetDirectory(0)
        h.SetLineWidth(1)
        if h.GetLineColor() == h.GetFillColor():
            h.SetLineColor(ROOT.kBlack)
        ret = h

    labels = legendLabel.split("\n")
    legend.AddEntry(h, labels[0], legendStyle)
    for lab in labels[1:]:
        legend.AddEntry(None, lab, "")

    return ret

def th1Xmin(th1):
    if th1 is None:
        return None
    return th1.GetXaxis().GetBinLowEdge(th1.GetXaxis().GetFirst())

def th1Xmax(th1):
    if th1 is None:
        return None
    return th1.GetXaxis().GetBinUpEdge(th1.GetXaxis().GetLast())

def th2Ymin(th2):
    if th2 is None:
        return None
    return th2.GetYaxis().GetBinLowEdge(th2.GetYaxis().GetFirst())


