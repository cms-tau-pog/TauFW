'''
\package limit
Various tools for plotting BR/tanbeta limits

Some of the settings depend on the \a forPaper boolean flag. All of
these are functions, so user can override the flag in a script.
'''
# Author: Konstantinos Christoforou (Feb 2022)

#================================================================================================ 
# Import modules
#================================================================================================ 
import os
import math
import json
import array
import sys
import re

import ROOT
ROOT.gROOT.SetBatch(True)

import TauFW.Plotter.tools.ShellStyles as ShellStyles


#================================================================================================ 
# Shell Type
#================================================================================================ 
ss = ShellStyles.SuccessStyle()
ns = ShellStyles.NormalStyle()
ts = ShellStyles.NoteStyle()
hs = ShellStyles.HighlightAltStyle()
ls = ShellStyles.HighlightStyle()
es = ShellStyles.ErrorStyle()
cs = ShellStyles.CaptionStyle()


#================================================================================================ 
# Global Definitions
#================================================================================================ 
verbose = False


#================================================================================================ 
# Function Definitions
#================================================================================================ 
def Verbose(msg, printHeader=False):
    '''
    Calls Print() only if verbose options is set to true.
    '''
    if not verbose:
        return
    Print(msg, printHeader)
    return


def Print(msg, printHeader=True):
    '''
    Simple print function. If verbose option is enabled prints, otherwise does nothing.
    '''
    fName = __file__.split("/")[-1]
    if printHeader:
        print "=== ", fName
    print "\t", msg
    return

def setStyle(graph):
    '''
    Changes made using
    https://twiki.cern.ch/twiki/bin/viewauth/CMS/Internal/FigGuidelines
    as guideline
    '''
    graph.SetMarkerStyle(ROOT.kFullCircle) #21
    graph.SetMarkerSize(1.3)
    graph.SetMarkerColor(ROOT.kBlack)
    graph.SetLineWidth(3)
    graph.SetLineColor(ROOT.kBlack)
    return

#================================================================================================ 
# Class Definition
#================================================================================================ 
class FakeFactors:
    '''
    Class for reading the BR limits from the JSON file produced by
    landsMergeHistograms.py
    '''
    #def __init__(self, dirList, dataType="Data", decayMode=10, etaRegion="Barrel", ptRatio=None, analysisType="HToTauNu", verbose=False):
    def __init__(self, dirList, dataType="Data", nProng="1prong", etaRegion="Barrel", ptRatio=None, analysisType="HToTauNu", verbose=False):
        #self.lumi = float(jsonData["luminosity"]) #fixme 
        self.verbose         = verbose
        self.dirList         = dirList
        self.dataType        = dataType
        #self.decayMode       = decayMode
        self.nProng          = nProng
        self.etaRegion       = etaRegion
        self.ptRatio         = ptRatio
        self.analysisType    = self.GetAnalysisType(analysisType)
        self.jsonList        = self.FindJsonFiles(dirList)
        self.eraList         = self.GetDataErasFromJson()
        if self.verbose:
            self.PrintJsonPaths(dirDepth=2)
        self.jsonDataDict    = self.GetJsonDataDictionary()
        self.ptRangeDict     = self.GetPtRangeDictionary()
        self.valuesDict      = {} # jsonFile => fake factors
        self.errorsPlusDict  = {} # jsonFile => fake factors
        self.errorsMinusDict = {} # jsonFile => fake factors
        self.StoreValuesAndErrorsInDictionaries()
        if verbose:
            self.PrintValuesAndErrors()
        return

    def _GetFName(self):
        fName = __file__.split("/")[-1].replace("pyc", "py")
        return fName

    def Verbose(self, msg, printHeader=True):
        if not self.verbose:
            return
        self.Print(msg, printHeader)
        return

    def Print(self, msg, printHeader=False):
        if printHeader==True:
            print "=== ", self._GetFName()
            print "\t", msg
        else:
            print "\t", msg
        return

    def PrintFlushed(self, msg, printHeader=True):
        msg = "\r\t" + msg
        if printHeader:
            print "=== ", self._GetFName()
        sys.stdout.write(msg)
        sys.stdout.flush()
        sys.stdout.write("\033[K") #clear line
        return

    def GetAnalysisType(self, analysisType):
        myAnalyses = ["HToTauNu", "HToTB", "HToHW", "HToHW_2ta", "HToHW_lt", "mumutau","eetau"]

        if analysisType in myAnalyses:
           return analysisType
        else:
            msg = "Invalid analysis type \"%s\". Please selected one of the following: \"%s" % (self.analysisType, "\", \"".join(myAnalyses) + "\"")
            raise Exception(es + msg + ns)

    def GetJsonList(self):
        return self.jsonList

    def GetPtRangeDictionary(self):
        ptRangeDict = {}
        # For-loop: All json files
        for f in self.jsonList:
            # Make pair: jsonFile <-> jsonData
            ptRangeDict[f] = self.GetPtRangeFromJson(f)
        return ptRangeDict

    def GetJsonDataDictionary(self):

        jsonDataDict = {}
        # For-loop: All json files
        for f in self.jsonList:
            # Make pair: jsonFile <-> jsonData
            jsonDataDict[f] =  self.GetJsonData(f)
        return jsonDataDict
            
    def PrintJsonPaths(self, dirDepth=2):

        self.Print("Found the following %d JSON files: " % (len(self.jsonList)), True)
        for i, f in enumerate(self.jsonList, 1):       
            filePath = "/".join(f.split("/")[-dirDepth:])
            self.Print("%d) %s" % (i, filePath), False)
        return    
    
    def FindJsonFiles(self, dirList, keyword=".json"):
        jsonPathList = []
        for i,d in enumerate(dirList, 1):
            jsonPathList.extend( self.FindJsonFile(d) )

        #if len(jsonPathList) < 1:
        #    msg = "Could not find any JSON file in any of the following directories:\n\t" % ("\n\t".join(dirList)) #iro
        #    raise Exception(es + msg + ns)        
        return jsonPathList

    def FindJsonFile(self, myDir, fileType=".json"):
        jsonList = []
        
        for o in os.listdir(myDir):
            path = os.path.join(myDir, o)
            if not os.path.isfile(path):
                continue
            if not path.endswith(fileType):
                continue
            jsonList.append(path)

        if len(jsonList) > 1:
            msg = "Multiple matches for fileType \"%s\" found in path \"%s\":\n%s" % (fileType, os.path.basename(myDir), "\n".join(jsonList))
            self.Verbose(es + msg + ns)

        if len(jsonList) < 1:
            msg = "No matches for fileType \"%s\" found in path \"%s\":" % (fileType, os.path.basename(myDir))
            raise Exception(es + msg + ns)
        return jsonList
    

    def GetDataErasFromJson(self):
        eraList = []
        for jsonPath in self.jsonList:
            jsonName   = os.path.basename(jsonPath) # format: TauFakeRate_Run2016_350to3000.json
            eraList.append(self.GetDataEraFromJson(jsonName))
        return eraList

    def GetDataEraFromJson(self, jsonName):
        '''
        Assuming that the jsonName is with the following format:
        jsonName = "TauFakeRate_<dataEra>_<searchMode>.json"
        e.g. "TauFakeRate_Run2016_350to3000.json{
        '''
        dataEra    = jsonName.split("_")[1]
        #searchMode = jsonName.split("_")[2]
        return dataEra

    def GetJsonData(self, jsonFilePath):
        if os.path.isfile(jsonFilePath):
            #self.Print("Reading the json file %s" % (ls + jsonFilePath + ns), True)
            self.Verbose("Reading the json file %s" % (ls + jsonFilePath + ns), True)
            jsonData = json.loads( open(jsonFilePath).read() )
            return jsonData
        else:
            msg = "The json file %s does not exist!" % (jsonFilePath)
            raise Exception(es + msg + ns)

    def GetPtRangeFromJson(self, jsonFile):
        if not hasattr(self, "jsonDataDict"):
            msg = "Cannot determine pt range before the jsonDataDict variable is assigned!"
            raise Exception(es + msg + ns)
        if not hasattr(self, "nProng"):
            msg = "Cannot determine pt range before the nProng variable is assigned!"
            raise Exception(es + msg + ns)
            #        if not hasattr(self, "decayMode"):
            #            msg = "Cannot determine pt range before the decayMode variable is assigned!"
            #            raise Exception(es + msg + ns)
        if not hasattr(self, "etaRegion"):
            msg = "Cannot determine pt range before the etaRegion variable is assigned!"
            raise Exception(es + msg + ns)
        if not hasattr(self, "dataType"):
            msg = "Cannot determine pt range before the dataType variable is assigned!"
            raise Exception(es + msg + ns)

        ptRange  = []
        ptRatios = self.GetPtRatios(jsonFile) # fixme

        # For-loop: All pt ranges and append to list
        if self.ptRatio != None:
            if self.nProng == "":
                key = "%s_%s_%s" % (self.analysisType, self.etaRegion, self.ptRatio)
            else:
                key = "%s_%s_%s_%s" % (self.analysisType, self.nProng, self.etaRegion, self.ptRatio)
            #key = "merged_%s_%s_%s" % (self.decayMode, self.etaRegion, self.ptRatio)
        else:
            if self.nProng == "":
                key = "%s_%s" % (self.analysisType, self.etaRegion)
            else:
                key = "%s_%s_%s" % (self.analysisType, self.nProng, self.etaRegion)
            #key = "merged_%s_%s" % (self.decayMode, self.etaRegion)

        dataList = self.jsonDataDict[jsonFile][key][self.dataType]
        for pt in sorted(dataList):
            pt = re.findall(r'\[(.*?)\]', pt)[0]
            ptRange.append(str(pt)) # convert unicode to string

        self.Verbose("The pt range in json file %s is: %s" % (jsonFile, ptRange), True)
        return ptRange

    def GetPtRatios(self, jsonFile):
        keyList = list(filter(lambda x: "merged" in x and "inclusive" not in x.lower(), self.jsonDataDict[jsonFile]))
        ptRatios = []

        # For-loop: All json file keys
        for key in keyList:
            ptRatio = "R" + "".join(key).split("_R")[-1]
            if ptRatio not in ptRatios:
                ptRatios.append(ptRatio)
                
        if self.verbose:
            for i, R in enumerate(ptRatios, 0):
                self.Print("GetPtRatios(): R=%s" % (R), i==0)
        return ptRatios

    def StoreValuesAndErrorsInDictionaries(self):
        # For-loop: All json files
        for f in self.jsonList:
            ptRange = self.ptRangeDict[f]

            if self.ptRatio != None:
                if self.nProng == "":
                    key = "%s_%s_%s" % (self.analysisType, self.etaRegion, self.ptRatio)
                else:
                    key = "%s_%s_%s_%s" % (self.analysisType, self.nProng, self.etaRegion, self.ptRatio)
                #key = "merged_%s_%s_%s" % (self.decayMode, self.etaRegion, self.ptRatio)
            else:
                if self.nProng == "":
                    key = "%s_%s" % (self.analysisType, self.etaRegion)
                else:
                    key = "%s_%s_%s" % (self.analysisType, self.nProng, self.etaRegion)
                #key = "merged_%s_%s" % (self.decayMode, self.etaRegion)

            try:
                self.valuesDict[f]      = [self.jsonDataDict[f][key][self.dataType]["pt:[%s]" % pt]["value"] for pt in ptRange]
                self.errorsPlusDict[f]  = [self.jsonDataDict[f][key][self.dataType]["pt:[%s]" % pt]["error"] for pt in ptRange]
                self.errorsMinusDict[f] = [self.jsonDataDict[f][key][self.dataType]["pt:[%s]" % pt]["error"] for pt in ptRange]
            except:
                msg  = "Failed retrieving fake factors from file \"%s\"" % (f)
                msg += "\nfile = %s" % (f)
                msg += "\nkey = %s" % (key)
                msg += "\ndataType = %s" % (self.dataType)
                msg += "\npt = %s" % (pt)
                #Print(es + msg + ns, True)
                raise Exception(es + msg + ns)
        return

    def PrintValuesAndErrors(self):        

        # For-loop: All json files
        for f in self.jsonList:
            self.Print("Printing fake factor values and errors from file %s" % (f), True)

            # For-loop: All values/errors
            for i in range(0, len(self.valuesDict[f])):
                self.Print("pt: [%s]) %.3f +/- %.3f" % (self.ptRangeDict[f][i], self.valuesDict[f][i], self.errorsPlusDict[f][i]), False)
        return

    def getFinalStateText(self, analysisType=None):
        
        finalStates = {}
        finalStates["HToTauNu"] = "#tau_{h}+jets final state"
        finalStates["HToHW"]    = "#mu#tau_{h}#tau_{h} and e#tau_{h}#tau_{h} final states"
        finalStates["HToHW_2ta"]= "#mu#tau_{h}#tau_{h} and e#tau_{h}#tau_{h} final states"
        finalStates["HToHW_lt"] = "#mu#tau_{h} and e#tau_{h} final states"
        finalStates["HToTB"]    = "fully hadronic final state"
        finalStates["mumutau"]    = "#mu#mu#tau_{h}"
        finalStates["eetau"]    = "ee#tau_{h}"
        if analysisType==None:
            return finalStates[self.analysisType]
        else:
            return finalStates[analysisType]            

    def getHardProcessText(self):
        
        processes = {}
        processes["HToTauNu"] = "pp #rightarrow t(b)H^{#pm} #rightarrow #tau^{#pm}#nu_{#tau}"
        processes["HToHW"]    = "pp #rightarrow t(b)H^{#pm}, H^{#pm} #rightarrow H W^{#pm}"
        processes["HToHW_2ta"]= "pp #rightarrow t(b)H^{#pm}, H^{#pm} #rightarrow H W^{#pm}"
        processes["HToHW_lt"] = "pp #rightarrow t(b)H^{#pm}, H^{#pm} #rightarrow H W^{#pm}"
        processes["HToTB"]    = "pp #rightarrow t(b)H^{#pm} #rightarrow t(b)"
        processes["mumutauHToTB"]    = "#mu#mu#tau_{h}"
        return processes[self.analysisType]

    def getBRassumptionText(self):

        assumptions = {}
        assumptions["HToTauNu"] = "#bf{#it{#Beta}}(H^{#pm} #rightarrow #tau^{#pm}#nu_{#tau}) = 1"
        assumptions["HToHW"]    = ""
        assumptions["HToHW_2ta"]= ""
        assumptions["HToHW_lt"] = ""
        assumptions["HToTB"]    = ""
        return assumptions[self.analysisType]

    def getLuminosity(self):
        '''
        Get the integrated luminosity in 1/pb
        '''
        return self.lumi

    def getTable(self, nDigits=5):
        '''
        Returns a table (list) with the BR limits
        '''
        # fixme
        width  = nDigits + 6
        align  = "{:<8} {:>%s} {:>%s} {:>%s} {:>%s} {:>%s} {:>%s}" % (width, width, width, width, width, width)
        header = align.format("Mass", "Observed", "Median", "-2sigma", "-1sigma", "+1sigma", "+2sigma")
        hLine  = "="*len(header)

        # Define precision
        precision = "%%.%df" % nDigits

        # Create the results table
        table  = []
        table.append(hLine)
        table.append(header)
        table.append(hLine)
        for i in xrange(len(self.mass_string)):
            mass = self.mass_string[i]
            observed = precision % (self.observed_string[i])
            median       = precision % (self.expectedMedian_string[i])
            sigma2minus  = precision % (self.expectedMinus2_string[i])
            sigma1minus  = precision % (self.expectedMinus1_string[i])
            sigma1plus   = precision % (self.expectedPlus1_string[i])
            sigma2plus   = precision % (self.expectedPlus2_string[i])

            # Append results
            row = align.format(mass, observed, median, sigma2minus, sigma1minus, sigma1plus, sigma2plus)
            table.append(row)
        table.append(hLine)
        return table

    def printTable(self, nDigits=5):
        '''
        Print the BR limits table
        '''
        table = self.getTable(nDigits)
        # Print limits (row by row)
        for i, row in enumerate(table,1):
            Print(row, i==1)
        return
        
    def saveAsLatexTable(self, unblindedStatus=False, nDigits=3, savePath=None, HToTB=False):
        '''
        Save the table as tex format
        '''        
        myDigits = nDigits
        isLightHplus  = self.isLightHPlus(self.mass[0])
        if isLightHplus and nDigits==3:
                myDigits += 1

        # Define precision of results
        precision = "%%.%df" % myDigits
        format    = "%3s "

        # Five columns (+/-2sigma, +/-1sigma, median)
        for i in range(0,5):
                format += "& %s "%precision 
                
        # Blinded column
        if not unblindedStatus:
            format += "& Blinded "
        else:
            format += "& %s " % precision 

        # End-line character (\\)
        format += "\\\\ \n"

        # Add the LaTeX table contents
        s  = "% Table autocreated by HiggsAnalysis.LimitCalc.limit.saveAsLatexTable() \n"
        s += "\\begin{tabular}{ c c c c c c c } \n"
        s += "\\hline \n"
        if HToTB:
                s += "\\multicolumn{7}{ c }{95\\% CL upper limit on $\\BRtH\\times\\BRHtb$}\\\\ \n"
        else:
            if isLightHplus:
                s += "\\multicolumn{7}{ c }{95\\% CL upper limit on $\\BRtH\\times\\BRHtau$}\\\\ \n"
            else:
                s += "\\multicolumn{7}{ c }{95\\% CL upper limit on $\\sigmaHplus\\times\\BRHtau$}\\\\ \n"

                s += "\\hline \n"
                s += "\\mHpm & \\multicolumn{5}{ c }{Expected limit} & Observed \\\\ \\cline{2-6} \n"
                s += "(GeV)   & $-2\\sigma$  & $-1\\sigma$ & median & +1$\\sigma$ & +2$\\sigma$  & limit \\\\ \n"
                s += "\\hline \n"

        # Get the limit values
        for i in xrange(len(self.mass_string)):
            mass     = self.mass_string[i]
            eMinus2  = float( precision % (self.expectedMinus2_string[i]) )
            eMinus1  = float( precision % (self.expectedMinus1_string[i]) )
            eMedian  = float( precision % (self.expectedMedian_string[i]) )
            ePlus1   = float( precision % (self.expectedPlus1_string[i]) )
            ePlus2   = float( precision % (self.expectedPlus2_string[i]) )
            observed = float( self.observed_string[i]) 
            if unblindedStatus:
                s += format % (mass, eMinus2, eMinus1, eMedian, ePlus1, ePlus2, observed)
            else:
                s += format % (mass, eMinus2, eMinus1, eMedian, ePlus1, ePlus2)
                s += "\\hline \n"
        s += "\\end{tabular} \n"

        fileName = "limitsTable.tex"
        openMode = "w"  
        Verbose("Opening file '%s' in mode '%s'" % (fileName, openMode), True)
        if savePath == None:
            f = open(fileName, openMode)
        else:
            if not os.path.isdir(savePath):
                raise Exception("Cannot save LaTeX table! The path provided (%s) is not a directory!" % (savePath))
            f = open(os.path.join(savePath, fileName), openMode)
        f.write(s)
        f.close()
        Print("Wrote LaTeX table in file '%s'" % (fileName), True)
        return

    def GetLegendHeader(self):
        header = "%s %s" % (self.nProng, self.etaRegion)
        #header = "%s %s" % (self.decayMode, self.etaRegion)
        return header

    def GetPtAsFloat(self, pt):
        
        ptLow  = float(pt.split(", ")[0])
        if pt.split(", ")[1] == "infty": # g-man
            self.Print("The tau pt bin of \"infty\" will be taken to be 300.0 GeV", True)
            ptHigh = 300.0 
        else:
            ptHigh = float(pt.split(", ")[1])
        ptAv   = 0.5*(ptLow + ptHigh)
        return ptLow, ptAv, ptHigh

    def GetPtRangeAsFloat(self, ptRange):
        
        ptLowList  = []
        ptAvList   = []
        ptHighList = []
                
        for pt in ptRange:
            ptLow, ptAv, ptHigh = self.GetPtAsFloat(pt)
            # print "%s, %s, %s" % (ptLow, ptAv, ptHigh)
            ptLowList.append(ptAv-ptLow)
            ptAvList.append(ptAv)
            ptHighList.append(ptHigh-ptAv)
        return ptLowList, ptAvList, ptHighList

    def _getGraph(self, jsonFile, postfix, sigma):
        '''
        Helper function for the fake factors
        
        \param postfix   Postfix string for the record names in the JSON file
        \param sigma     Number for the sigma (0 for median, 1,-1, 2,-2)
        '''
        
        ptLowList, ptAvList, ptHighList = self.GetPtRangeAsFloat(self.ptRangeDict[jsonFile])
        ptArray        = array.array("d", ptAvList)
        ptErrLowArray  = array.array("d", ptLowList)
        ptErrHighArray = array.array("d", ptHighList)
        valuesArray    = array.array("d", self.valuesDict[jsonFile])
        ePlusArray     = array.array("d", self.errorsPlusDict[jsonFile])
        eMinusArray    = array.array("d", self.errorsMinusDict[jsonFile])

        # Create TGraphAsymmErrors(Int_t n, const Double_t* x, const Double_t* y, const Double_t* exl = 0, const Double_t* exh = 0, const Double_t* eyl = 0, const Double_t* eyh = 0)
        gr = ROOT.TGraphAsymmErrors(len(ptArray), ptArray, valuesArray, ptErrLowArray, ptErrHighArray, eMinusArray, ePlusArray)
        #gr.SetName("FakeFactors_%s" % (jsonFile) )
        #gr.SetTitle("FakeFactors_%s" % (os.path.join(jsonFile.split("/")[-2] , os.path.basename(jsonFile) )) )
        gr.SetTitle("%s" % (os.path.join(jsonFile.split("/")[-2] , os.path.basename(jsonFile) )) )
        if self.GetNprong() == "":
            gr.SetName("%s_%s_%s" % (self.dataType, self.GetDataEraFromJson(os.path.basename(jsonFile)), self.GetEtaRegion()) )
        else:
            gr.SetName("%s_%s_%s_%s" % (self.dataType, self.GetDataEraFromJson(os.path.basename(jsonFile)), self.GetNprong(), self.GetEtaRegion()) )
        setStyle(gr)
        return gr

    def getGraphs(self, sigma=0):
        '''
        Construct TGraph for the fake factors
        
        \param sigma   Integer for the sigma band (0 for median, 1,-1, 2,-2)
        
        \return TGraph of the expexted limit
        '''
        #kc, temporary hack to take graphs for len(jsonList) = 1
        #graphs = [] #fixme
        #for f in self.jsonList:
        #    graphs.append( self._getGraph(f, "", sigma))
        #return graphs
        graphs = [] #fixme
        f = self.jsonList[0]
        graphs.append( self._getGraph(f, "", sigma))
        return graphs
        #########################################

    def GetDataType(self):
        return self.dataType

    def GetNprong(self):
        return self.nProng

    def GetEtaRegion(self):
        return self.etaRegion
                                            

def divideGraph(num, denom):
    '''
    Divide two TGraphs
    
     \param num    Numerator TGraph
     \param denom  Denominator TGraph
     
     \return new TGraph as the ratio of the two TGraphs
     '''
    gr = ROOT.TGraph(num)
    for i in xrange(gr.GetN()):
        y = denom.GetY()[i]
        val = 0
        if y != 0:
            val = gr.GetY()[i]/y
        gr.SetPoint(i, gr.GetX()[i], val)
    return gr

def subtractGraph(minuend, subtrahend):
    '''
    Subtract two TGraphs
    
    \param minuend     Minuend TGraph
    \param subtrahend  Subtrahend TGraph
    
    \return new TGraph as the difference of the two TGraphs
    '''
    gr = ROOT.TGraph(minuend)
    for i in xrange(gr.GetN()):
        val = gr.GetY() - subtrahend.GetY()[i]
        gr.SetPoint(i, gr.GetX()[i], val)
    return gr
