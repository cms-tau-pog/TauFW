#! /usr/bin/env python
# Author: Konstantinos Christoforou (Feb 2022)
# Description: Simple script to read and plot jet-to-tau FakeRates
# ./readAndPlotFR.py --yMin 0.0 --yMax 0.5 --saveDir plots/UL2018/FakeRates --ratio --bandValue 30 --dirs plots/UL2018/TauFakeRate_UL2018_mumutau,plots/UL2018/TauFakeRate_UL2018_mumutau

#import os
import ROOT
import math
import ctypes 
import array
import os
import getpass
import sys
import glob
import json
import array
import copy
import re
from optparse import OptionParser

ROOT.gROOT.SetBatch(True)
ROOT.PyConfig.IgnoreCommandLineOptions = True

import TauFW.Plotter.corrections.JetToTauFR.tools.tdrstyle as tdrstyle
import TauFW.Plotter.corrections.JetToTauFR.tools.styles as styles
import TauFW.Plotter.corrections.JetToTauFR.tools.histograms as histograms
import TauFW.Plotter.corrections.JetToTauFR.tools.plots as plots
import TauFW.Plotter.corrections.JetToTauFR.tools.fakeFactors as fakeFactors
import TauFW.Plotter.corrections.JetToTauFR.tools.ShellStyles as ShellStyles

#================================================================================================
# Variable definition
#================================================================================================
ss = ShellStyles.SuccessStyle()
ns = ShellStyles.NormalStyle()
ts = ShellStyles.NoteStyle()
hs = ShellStyles.HighlightAltStyle()
ls = ShellStyles.HighlightStyle()
es = ShellStyles.ErrorStyle()
cs = ShellStyles.CaptionStyle()

#================================================================================================
# Custo colours
#================================================================================================
kDarkBlack = ROOT.TColor.GetColor("#000000")
kLightBlack= ROOT.TColor.GetColor("#b2b2b2")
kDarkGold  = ROOT.TColor.GetColor("#DAA520")
kLightGold = ROOT.TColor.GetColor("#EEE8AA")
kDarkGreen = ROOT.TColor.GetColor("#008000")
kLightGreen= ROOT.TColor.GetColor("#006400")
kDarkRed   = ROOT.TColor.GetColor("#e7153f")
kLightRed  = ROOT.TColor.GetColor("#f38a9f")
kLightBlue = ROOT.TColor.GetColor("#89ace7")
kDarkBlue  = ROOT.TColor.GetColor("#1359d0")

# https://root.cern.ch/doc/master/classTAttMarker.html
colourList = [ROOT.kBlack     , ROOT.kAzure, ROOT.kOrange-3, ROOT.kGreen+1, ROOT.kPink, ROOT.kTeal+2, ROOT.kViolet+1, ROOT.kAzure+2, ROOT.kGray+2, ROOT.kTeal+2]
markerList = [ROOT.kFullCircle, ROOT.kFullTriangleDown, ROOT.kFullTriangleUp, ROOT.kFullSquare, ROOT.kFullCross, ROOT.kOpenCircle, ROOT.kOpenTriangleDown, ROOT.kOpenTriangleUp, ROOT.kOpenSquare]
#styleList  = [styles.Style(ROOT.kFullCircle, kDarkGreen)] +  [styles.Style(ROOT.kFullTriangleDown, kDarkBlue)]
styleList  = [styles.Style(ROOT.kFullCircle, kDarkBlack)] +  [styles.Style(ROOT.kFullTriangleDown, kDarkBlue)]
styleList += [styles.Style(ROOT.kFullTriangleUp, kDarkRed)] + [styles.Style(ROOT.kFullCross, kLightGreen)]
styleList += [styles.Style(ROOT.kFullSquare, ROOT.kMagenta+1)]+ styles.getStyles()

#================================================================================================
# Function definition
#================================================================================================
def Verbose(msg, printHeader=False):
    '''
    Calls Print() only if verbose options is set to true.
    '''
    if not opts.verbose:
        return
    Print(msg, printHeader)
    return

def Print(msg, printHeader=True):
    '''
    Simple print function. If verbose option is enabled prints, otherwise does nothing.
    '''
    fName = __file__.split("/")[-1]
    if printHeader:
        print("=== ", fName)
    print("\t", msg)
    return

def getLumiByYear(year):
    yrList = ["2016", "2017", "2018", "UL2016_preVFP", "UL2016_postVFP", "UL2017", "UL2018"]
    yrDict = {}
    yrDict["2016"] = 36.3*1e3
    yrDict["2017"] = 41.5*1e3
    yrDict["2018"] = 59.0*1e3
    yrDict["UL2016_preVFP"]  = 19.5*1e3
    yrDict["UL2016_postVFP"] = 16.8*1e3
    yrDict["UL2017"] = 41.5*1e3
    yrDict["UL2018"] = 59.0*1e3
    
    if year not in yrList:
        msg = "Invalid year \"%s\". Please select one of: %s" % (year, ", ".join(yrList) ) 
        #raise Exception(es + msg + ns)
        return ""
    else:
        return yrDict[year]

def doCompareJson(dirList, name, **kwargs):

    # Provide these as options in the future
    graphDict = {}
    prongList = [""]#["1prong", "3prong"]
    etaList   = ["Barrel", "Endcap"]#["Barrel", "Endcap"] #[""]

    # For-loop: All nProngs
    for i, nProng in enumerate(prongList, 0):

        # For-loop: All eta regions
        for j, eta in enumerate(etaList, 0):
                    
            Verbose("Creating the fakeFactors objects using the directory list:\n\t%s" % ("\n\t".join([d for d in dirList])), True)
            myFakeFactorsData       = fakeFactors.FakeFactors(dirList, "Data"      , nProng, eta, None, opts.analysisType, opts.verbose)
            myFakeFactorsSimulation = fakeFactors.FakeFactors(dirList, "Simulation", nProng, eta, None, opts.analysisType, opts.verbose)
            #myFakeFactors = fakeFactors.FakeFactors(dirList, opts.dataType, eta, nProng, None, "mumutau", opts.verbose)
            #print("nProng = ", nProng)
            #print("eta = ", eta)
            #print("myFakeFactorsData ="      , myFakeFactorsData)
            #print("myFakeFactorsSimulation =", myFakeFactorsSimulation)
            
            Verbose("Creating the comparison plot (%s, %s)" % (nProng, eta), True)
            jsonToGraphDict = doPlots(myFakeFactorsData, myFakeFactorsSimulation, nProng, eta, opts.name, opts) 
                
            #for jsonDir in jsonToGraphDict.keys():
            #    graphDict["%s-%s_%s_%s" % (nProng, eta, None, jsonDir)] = jsonToGraphDict[jsonDir]

    # Put everythin on single plot
    #Print("Producting %d summary fake rate plots" % ( len(dirList) ), True)
    #doSummaryPlots(dirList, graphDict)
    return 


def doPlots(fakeFactorsData, fakeFactorsSimulation, decayMode, etaRegion, saveName, _opts={}):

    saveExt   = "%s_%s" % (decayMode, etaRegion)
    saveName  = opts.name + "_" + saveExt
    graphs    = []    
    styleGen  = styles.Generator(styleList) #styleGen  = styles.Generator(styles.styles)
    legDict   = {}
    graphDict = {}


    # Simulation-----------------------------------------------------------
    grMC = fakeFactorsSimulation.getGraphs()[0]
    grNameMC  = saveExt+"Simulation"
    jsonDirMC = os.path.dirname(fakeFactorsData.GetJsonList()[0])
    legNameMC = GetLabel(jsonDirMC+"Simulation")
            
    legDict[grNameMC] = legNameMC
    Verbose("jsonDirMC = %s" % (jsonDirMC), True)
    
    #hgMC = histograms.HistoGraph(grMC, grNameMC, legendStyle="FLP", drawStyle="P2")
    hgMC = histograms.HistoGraph(grMC, grNameMC, legendStyle="LP", drawStyle="P2")
    #hgMC = histograms.HistoGraph(grMC, grNameMC, legendStyle="FLP", drawStyle="P")
    styleGen(hgMC)
    hgMC.getRootHisto().SetMarkerColor(kDarkRed)
    hgMC.getRootHisto().SetFillColor(kDarkRed)
    hgMC.getRootHisto().SetLineColor(kDarkRed)
    hgMC.getRootHisto().SetFillStyle(3354)
    graphs.append(hgMC)     
    graphDict[jsonDirMC+"Simulation"] = hgMC
    #----------------------------------------------------------------------
    # Data ---------------------------------------------------------------
    gr = fakeFactorsData.getGraphs()[0]
    grName  = saveExt+"_Data"
    jsonDir = os.path.dirname(fakeFactorsData.GetJsonList()[0])
    legName = GetLabel(jsonDir+"Data")
            
    legDict[grName] = legName        
    Verbose("jsonDir = %s" % (jsonDir), True)
    
    #hg = histograms.HistoGraph(gr, grName, legendStyle="FLP", drawStyle="P2")
    #hg = histograms.HistoGraph(gr, grName, legendStyle="FLP", drawStyle="P")
    hg = histograms.HistoGraph(gr, grName, legendStyle="LP", drawStyle="P")
    styleGen(hg)
    hg.getRootHisto().SetMarkerColor(kDarkBlack)
    hg.getRootHisto().SetFillColor(kLightBlack)
    hg.getRootHisto().SetLineColor(kDarkBlack)
    hg.getRootHisto().SetFillStyle(3354)
    graphs.append(hg)     
    graphDict[jsonDir+"_Data"] = hg
    #----------------------------------------------------------------------

    # Set line style
    #graphs[0].getRootHisto().SetLineStyle(ROOT.kSolid)

    # Create plot base object
    if not opts.ratio:
        plot = plots.PlotBase(graphs)
    else:
        plot = plots.ComparisonManyPlot(graphs[0], graphs[1:], saveFormats=[])

    # Set luminosity?
    #kc
    opts.intLumi = getLumiByYear(opts.year)
    ###

    if opts.intLumi > 0.0:
        plot.setLuminosity(opts.intLumi)
    #    for k in legDict.keys():
    #        legDict[k] = legDict[k].replace(" (%s)" % (opts.dataEra), "")
        
    # Set legend labels
    plot.histoMgr.setHistoLegendLabelMany(legDict)

    # Create & set legend
    legend = getLegend()
    header = fakeFactorsData.GetLegendHeader().replace("1p", "1-p").replace("3p", "3-p")
    plot.setLegend(legend) 
    #plot.setLegendHeader("%s (%s)" % (header, opts.dataType))
    #plot.setLegendHeader("%s: %s" % ("Data", header.lower()))
    plot.setLegendHeader("%s" % (header.lower()))
    #moveLegend(legend, "NW", len(graphs))

    # Determine options
    ymin = 0.0
    ymax = 1.0
    opts1 = {"xmin": _opts.xMin, "xmax": _opts.xMax, "ymin": _opts.yMin, "ymax": _opts.yMax}
    if _opts.yMin == -1:
        _opts.yMin = ymin
    if opts.yMax == -1:
        _opts.yMax = ymax

    if opts.xMin == None:
        del opts1["xmin"]
    if opts.xMax == None:
        del opts1["xmax"]

    # Create the frame and set axes titles
    if opts.ratio:
        plot.createFrame(saveName, createRatio=opts.ratio, opts=opts1, opts2={"ymin": 0.0, "ymax": 2.05})
    else:
        plot.createFrame(saveName, opts=opts1)

    # Add cut lines?
    for x in opts.cutLinesX:
        kwargs = {"greaterThan": True}
        plot.addCutBoxAndLine(cutValue=int(x), fillColor=ROOT.kRed, box=False, line=True, **kwargs)

    for y in opts.cutLinesY:
        kwargs = {"greaterThan": True, "mainCanvas": True, "ratioCanvas": False}
        plot.addCutBoxAndLineY(cutValue=int(y), fillColor=ROOT.kRed, box=False, line=True, **kwargs)

    if opts.bandValue != 0 and opts.ratio==True:
        # https://root.cern.ch/doc/master/classTAttFill.html
        kwargs = {"cutValue": 1.0 + float(opts.bandValue)/100.0, "fillColor": kLightBlack, "fillStyle": 3354, "box": True, "line": False, "greaterThan": True, "mainCanvas": False, "ratioCanvas": opts.ratio, "mirror": True}
        #kwargs = {"cutValue": 1.0 + float(opts.bandValue)/100.0, "fillColor": ROOT.kGray+1, "fillStyle": 3001, "box": True, "line": False, "greaterThan": True, "mainCanvas": False, "ratioCanvas": opts.ratio, "mirror": True}
        #kwargs = {"cutValue": 1.0 + float(opts.bandValue)/100.0, "fillColor": ROOT.kGray+1, "fillStyle": 3003, "box": True, "line": False, "greaterThan": True, "mainCanvas": False, "ratioCanvas": opts.ratio, "mirror": True}
        plot.addCutBoxAndLineY(**kwargs)

    # Set axes titles
    plot.frame.GetXaxis().SetTitle("#tau_{h} p_{T} (GeV)")
    #plot.frame.GetYaxis().SetTitle("fake factors (j #rightarrow #tau_{h})")
    plot.frame.GetYaxis().SetTitle("Fake Rate (jet #rightarrow #tau_{h})")
    #plot.frame.GetYaxis().SetTitle("misidentification probability")

    # Enable/Disable logscale for axes 
    ROOT.gPad.SetLogy(_opts.logY)
    ROOT.gPad.SetLogx(_opts.logX)
    ROOT.gPad.SetGridy(_opts.gridY) #fixme ratio pad does not get the grid lines
    ROOT.gPad.SetGridx(_opts.gridX)

    # Draw the plot with standard texts
    plot.draw()
    #kc
    opts.intLumi = getLumiByYear(opts.year)
    ###
    plot.addStandardTexts(addLuminosityText=(opts.intLumi > 0.0))
    #plot.addStandardTexts(addLuminosityText=getLumiByYear(era))
    plot.addStandardTexts(addLuminosityText=getLumiByYear("2018"))

    # Additional text?    
    if 0:
        histograms.addText(0.20, 0.86, fakeFactors.getHardProcessText(), size=22, bold=opts.boldText)
        histograms.addText(0.20, 0.82, fakeFactors.getFinalStateText() , size=22, bold=opts.boldText)

    # Save the plots & return
    SavePlot(plot, opts.saveDir, saveName, opts.saveFormats)
    return graphDict 

def GetLabel(dirName):
    #Predefined labels for datacard directories
    #\S+ means 1 or more non-white-space chars, covering multicrab-Hplus2hwAnalysis-CMSSW10_6_17- part
    #TauFakeRate_(?P<analysis>\S+?)_" takes the string between first and second _
    #"Run(?P<year>\d+?)\S*_"
    #\d means a digit, + means one or more, ? not greedy, actually not needed here
    #\S means non-white-space character, * means 0 or more times
    #in the first regex you need the non-greedy, because with greedy it will take greedly up to the last underscore
    fakesRegion = ""
    if "fakesRegion" in dirName:
        fakesRegion = os.path.split(dirName)[1].replace("fakesRegion", "") + ", "
        dirName     = os.path.split(dirName)[0]
    dirName = os.path.basename(dirName)
    Verbose("dirName = %s" % (dirName), True)
    
    finalState = ""
    # FIXME with better code!
    if "Simulation" in dirName:
        finalState = "Simulation"
    elif opts.analysisType+"Data" in dirName:
        finalState = "Data"

    dirToLabelDict = {}
    #dirToLabelDict["DYJets2016"]  = "ee#tau_{h} + #mu#mu#tau_{h} (2016)" #"Z/\\gamma\,\, 2016"
    dirToLabelDict["Simulation"] = "Simulation"
    dirToLabelDict["Data"] = "Data"

    dName  = os.path.basename(dirName)
    Verbose("dName  = %s" % (dName), True)
    if dName in dirToLabelDict.keys():
        return dirToLabelDict[dName]
    elif "_".join(dName.split("_")[:-1]) in dirToLabelDict.keys(): # remove the date
        return dirToLabelDict["_".join(dName.split("_")[:-1])]
    elif dName.split("_")[1] in dirToLabelDict.keys(): # usecase: Plots_TTbar2016_Created26Nov2020
        return dirToLabelDict[dName.split("_")[1]]
    elif finalState in dirName:
        return dirToLabelDict[finalState]
    else:
        return os.path.basename(dName)
        
def getLegend(_x1=0.73-0.06, _y1=0.62, _x2 = 0.93-0.06, _y2=0.92):
    legend = histograms.createLegend(x1=_x1, y1=_y1, x2=_x2, y2=_y2)
    # legend.SetMargin(0.17)
    # legend.SetFillStyle(1001) #for opaque legend
    return legend

def SavePlot(plot, saveDir, plotName, saveFormats = [".png", ".pdf"]):
    # Check that path exists
    if not os.path.exists(saveDir):
        os.makedirs(saveDir)

    # Create the name under which plot will be saved
    saveName = os.path.join(saveDir, plotName.replace("/", "_"))

    if opts.logY == True:
        saveName += "_logy"
    if opts.logX == True:
        saveName += "_logx"

    # For-loop: All save formats
    for i, ext in enumerate(saveFormats, 1):
        saveNameURL = saveName + ext
        #saveNameURL = saveNameURL.replace("/afs/cern.ch/user/a/attikis/public/html", "https://cmsdoc.cern.ch/~%s" % getpass.getuser())
        #if opts.url:
        #    Verbose(saveNameURL, i==0)
        #else:
        #    Verbose(saveName + ext, i==0)
        plot.saveAs(saveName, formats=saveFormats)
    return


def main():

    # Apply TDR style # fixme - does nothing
    style = tdrstyle.TDRStyle()
    style.setGridX(opts.gridX)
    style.setGridY(opts.gridY)
    style.setGridX(opts.logX)
    style.setGridY(opts.logY)

   # Set x-axis divisions
    n1 = 8 # primary divisions (8)
    n2 = 5  # second order divisions (5)
    n3 = 0  # third order divisions (@)
    nDivs = n1 + 100*n2 + 10000*n3
    ROOT.gStyle.SetNdivisions(nDivs, "X")

    # Enable OpenGL (for opaque legend)
    if 0: 
        ROOT.gEnv.SetValue("OpenGL.CanvasPreferGL", 1)

    # here
    # Set text mode
    if opts.paper:
        histograms.cmsTextMode = histograms.CMSMode.PAPER
    else:
        histograms.cmsTextMode = histograms.CMSMode.UNPUBLISHED
        #histograms.cmsTextMode = histograms.CMSMode.PRELIMINARY

    # Definitions
    savePath = opts.saveDir
    # here
    #if opts.url:
    #    savePath = opts.saveDir.replace("/afs/cern.ch/user/a/attikis/public/html", "https://cmsdoc.cern.ch/~%s" % getpass.getuser())

    # Do comparison plot for different json files
    #msg  = "Creating comparison plots (%d) using the following directories:%s\n\t%s" % (len(opts.dirList), hs, "\n\t".join([os.path.basename(d) for d in opts.dirList]) )
    msg  = "Creating comparison plots (%d) using the following directories:%s\n\t%s" % (len(opts.dirList), hs, "\n\t".join([d for d in opts.dirList]) )
    Print(msg + ns, True)
    doCompareJson(opts.dirList, opts.name) 
    
    # inform user of output location
    # here
    #Print("Plots saved under directory %s"% (hs + aux.convertToURL(opts.saveDir, opts.url) + ns), True)
    return

if __name__ == "__main__":

    # Default options
    BATCHMODE    = True    
    VERBOSE      = False
    ANALYSISTYPE = "mumutau"
    INTLUMI      = -1
    YEAR         = None
    BANDVALUE    = 0
    CUTLINE      = 999.9
    CUTLINEX     = ""
    CUTLINEY     = ""
    GRIDX        = False
    GRIDY        = False
    LOGX         = False
    LOGY         = False
    MAXX         = None
    MAXY         = None
    MINX         = None
    MINY         = None
    NAME         = "fakeFactors"
    PAPER        = False
    SAVEDIR      = None
    SAVEFORMATS  = "pdf,png"#,C"
    URL          = False
    BOLDTEXT     = False
    DIRS         = None
    RATIO        = False
    DATATYPE     = "Data"
    RATIOREF     = None

    parser = OptionParser(usage="Usage: %prog [options]", add_help_option=True, conflict_handler="resolve")

    parser.add_option("-b", "--batchMode", dest="batchMode", action="store_false", default=BATCHMODE,
                      help="Enables batch mode (canvas creation does NOT generate a window) [default: %s]" % BATCHMODE)

    parser.add_option("-v", "--verbose", dest="verbose", default=VERBOSE, action="store_true",
                      help="Verbose mode for debugging purposes [default: %s]" % (VERBOSE) )
    
    parser.add_option("--boldText", dest="boldText", default=BOLDTEXT, action="store_true",
                      help="Use bold text printed on canvas? [default: %s]" % (BOLDTEXT))

    parser.add_option("--dirs", dest="dirs", default=DIRS,
                      help="List for datacard directories draw in comparison (comma separated WITHOUT space) [default: %s]" % (DIRS))
    
    parser.add_option("--analysisType", dest="analysisType", default=ANALYSISTYPE,
                      help="Flag to indicate the analysis type (e.g. \"HToTauNu\", \"HToTB\", \"HToHW\") [default: %s]" % (ANALYSISTYPE) )
 
    parser.add_option("--paper", dest="paper", default=PAPER, action="store_true",
                      help="Paper mode [default: %s]" % (PAPER) )

    parser.add_option("--ratio", dest="ratio", default=RATIO, action="store_true",
                      help="Enable ratio pad where possible [default: %s]" % (RATIO) )
    
    parser.add_option("--name", dest="name", type="string", default=NAME,
                      help="Name of the output plot [default = %s]" % (NAME))

    parser.add_option("--url", dest="url", action="store_true", default=URL,
                      help="Don't print the actual save path the plots are saved, but print the URL instead [default: %s]" % URL)

    parser.add_option("--saveDir", dest="saveDir", type="string", default=SAVEDIR,
                      help="Directory where all plots will be saved [default: %s]" % SAVEDIR)

    parser.add_option("--logX", dest="logX", action="store_true", default=LOGX,
                      help="Plot x-axis (mass) as logarithmic [default: %s]" % (LOGX) )
    
    parser.add_option("--logY", dest="logY", action="store_true", default=LOGY,
                      help="Plot y-axis (exlusion limit) as logarithmic [default: %s]" % (LOGY) )
    
    parser.add_option("--gridX", dest="gridX", default=GRIDX, action="store_true",
                      help="Enable the grid for the x-axis [default: %s]" % (GRIDX) )

    parser.add_option("--gridY", dest="gridY", default=GRIDY, action="store_true",
                      help="Enable the grid for the y-axis [default: %s]" % (GRIDY) )

    parser.add_option("--yMin", dest="yMin", default=MINY, type="float",
                      help="Overwrite automaticly calculated minimum value of y-axis [default: %s]" % (MINY) )
    
    parser.add_option("--yMax", dest="yMax", default=MAXY, type="float",
                      help="Overwrite automaticly calculated maximum value of y-axis [default: %s]" % (MAXY) )

    parser.add_option("--xMin", dest="xMin", default=MINX, type="float",
                      help="Overwrite minimum value of x-axis [default: %s]" % (MINX) )
    
    parser.add_option("--xMax", dest="xMax", default=MAXX, type="float",
                      help="Overwrite maximum value of x-axis [default: %s]" % (MAXX) )

    parser.add_option("-s", "--saveFormats", dest="saveFormats", default = SAVEFORMATS,
                      help="Save formats for all plots [default: %s]" % SAVEFORMATS)

    #parser.add_option("--dataType", dest="dataType", default = DATATYPE,
    #                  help="Data type to use when plotting the fake factors [default: %s]" % DATATYPE)

    parser.add_option("--ratioReference", dest="ratioReference", default = RATIOREF,
                      help="Name or keyword for the input directory that will be used as reference in the ratio pad [default: %s]" % RATIOREF)

    parser.add_option("--intLumi", dest="intLumi", default=INTLUMI,
                      help="Value of integrated luminosity (in fb) to display on canvas [default: %s]" % (INTLUMI))

    parser.add_option("--year", dest="year", default=YEAR,
                      help="The collision data era  [default: %s]" % (YEAR))

    parser.add_option("--cutLineX", dest="cutLineX", default=CUTLINEX,
                      help="List for values for x-axis lines to be drawn on canvas (comma separated WITHOUT space) [default: %s]" % (CUTLINEX))

    parser.add_option("--cutLineY", dest="cutLineY", default=CUTLINEY,
                      help="List for values for y-axis lines to be drawn on canvas (comma separated WITHOUT space) [default: %s]" % (CUTLINEY))

    parser.add_option("--bandValue", dest="bandValue", type="int", default=BANDVALUE,
                      help="Add a symmetric band around 1.0. Value passed should be the percentage (e.g 10 or 5)  [default: %s]" % (BANDVALUE) )

    (opts, args) = parser.parse_args()


    # Sanity checks
    opts.dirList = []
    if opts.dirs == None:
        msg = "No fake-factor directories provided!"
        raise Exception(es + msg + ns)

    if "," in opts.dirs:
        opts.dirList = opts.dirs.split(",")
    else:
        opts.dirList = [os.path.join(opts.dirs,f) for f in os.listdir(opts.dirs) if os.path.isdir(os.path.join(opts.dirs, f))]
    opts.dirList = [d.rstrip("/") for d in opts.dirList]

    # Sanity check
    #if len(opts.dirList) < 2:
    #    print(opts.dirList)
    #    msg = "Only %d directories provided. Need at least 2 for comparison plots:\n\t%s" % (len(opts.dirList), "\n\t".join(opts.dirList))
    #    raise Exception(es + msg + ns)

    # Sanity check
    #if opts.dataType not in ["Data", "Simulation"]:
    #    msg = "Unsupported data types \"%s\"" % (opts.dataType)
    #    raise Exception(es + msg + ns)
        
    #if len(opts.dirList) > 1:
    #    msg = "Datacard directories considered:%s\n\t%s" % (hs, "\n\t".join(opts.dirList))
    #    Verbose(msg + ns, True)
    #else:
    #    msg = "At least 2 directories required. Only %d passed with --dirs argument!" % len(opts.dirList)
    #    #raise Exception(es + msg + ns)
    #    pass
    
    #kc
    opts.intLumi = getLumiByYear(opts.year)
    ###

    # Save in current working directory?
    if opts.saveDir =="":
        opts.saveDir = os.getcwd()
    else:
        #opts.saveDir = os.path.join(opts.saveDir, opts.dataType)
        opts.saveDir = os.path.join(opts.saveDir)

    # Sanity check (analysis type)
    myAnalyses = ["mumutau", "eetau", "mumettau"]
    if opts.analysisType not in myAnalyses:
        msg = "Invalid analysis type \"%s\". Please selected one of the following: \"%s" % (opts.analysisType, "\", \"".join(myAnalyses) + "\"")
        raise Exception(es + msg + ns)
    else:
        msg = "Analysis type is %s" % (hs + opts.analysisType + ns)
        Print(msg, True)        

    # Cut lines
    opts.cutLinesX = []
    if len(opts.cutLineX) > 0:
        opts.cutLinesX = opts.cutLineX.split(",")
    if len(opts.cutLinesX) > 0:
        msg = "Adding x-axis lines \"%s\"" % (", ".join(opts.cutLinesX))
        Print(hs +  msg + ns, True)
    else:
        pass
    opts.cutLinesY = []
    if len(opts.cutLineY) > 0:
        opts.cutLinesY = opts.cutLineY.split(",")
    if len(opts.cutLinesY) > 0:
        msg = "Adding y-axis lines \"%s\"" % (", ".join(opts.cutLinesY))
        Print(hs +  msg + ns, True)
    else:
        pass

    # Sanity check
    for i, d in enumerate(opts.dirList, 0):
        if not os.path.isdir(d):
            msg = "Directory \"%s\" does not exist" % (d)
            raise Exception(es + msg + ns)
        else:
            d2 = os.path.join(os.path.join(os.getcwd(), d))
            if os.path.isdir(d2):
                opts.dirList[i] = d2
            else:
                msg = "Directory \"%s\" does not exist" % (os.path.join(d))
                raise Exception(es + msg + ns)
                               
    if opts.saveDir == None:
        opts.saveDir = opts.dirList[0]

    # Create save formats
    if "," in opts.saveFormats:
        opts.saveFormats = opts.saveFormats.split(",")
    else:
        opts.saveFormats = [opts.saveFormats]
    opts.saveFormats = ["." + s for s in opts.saveFormats]


    # Re-sort directory list to put the reference histo first
    #if opts.ratioReference != None:
    #    for i, d in enumerate(opts.dirList, 0):
    #        if opts.ratioReference in d:
    #            opts.dirList.insert(0, opts.dirList.pop(i))
    #            break
    #Print("The reference histo for the ratio pad will be %s" % (ls + opts.dirList[0] + ns), True)

    # Call the main function
    main()
    
    if not opts.batchMode:
        raw_input("=== plotFakeFactors.py: Press any key to quit ROOT ...")
