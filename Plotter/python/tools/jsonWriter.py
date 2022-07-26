# Author: Konstantinos Christoforou (Feb 2022)
#================================================================================================   
# Import modules
#================================================================================================   
import sys
import os
import ROOT

import TauFW.Plotter.tools.ShellStyles as ShellStyles

#================================================================================================   
# Shell Colour Aliases
#================================================================================================   
ss = ShellStyles.SuccessStyle()
ns = ShellStyles.NormalStyle()
ts = ShellStyles.NoteStyle()
hs = ShellStyles.HighlightAltStyle()
ls = ShellStyles.HighlightStyle()
es = ShellStyles.ErrorStyle()
cs = ShellStyles.CaptionStyle()

#================================================================================================   
# Class definition
#================================================================================================   
class JsonWriter:

    def __init__(self, saveDir="", verbose=False):
        self.graphs = {}
        self.parameters = {}
        self.verbose = verbose
        self.saveDir = saveDir
        if not os.path.exists(self.saveDir):
            os.makedirs(self.saveDir)
        return

    def Print(self, msg, printHeader=False):
        fName = __file__.split("/")[-1]
        if printHeader==True:
            print "=== ", fName
            print "\t", msg
        else:
            print "\t", msg
            return

    def Verbose(self, msg, printHeader=True, verbose=False):
        if not self.verbose:
            return
        self.Print(msg, printHeader)
        return

    def addParameter(self, name, value):
        if name in self.parameters.keys():
            self.parameters[name] += value
        else:
            self.parameters[name] = value
        return

    def addParameterList(self, name, value):
        if name in self.parameters.keys():
            self.parameters[name].append(value)
        else:
            self.parameters[name] = [value]
        return

    def addGraph(self, name, graph):
        self.graphs[name] = graph
        return

    def timeStamp(self):
        import datetime
        time = datetime.datetime.now().ctime()
        return time
    
    def write(self, fileName, fileMode="w"):
        
        filePath = os.path.join(self.saveDir, fileName)
        self.Verbose("Opening file %s in %s mode" % (filePath, fileMode), True)
        fOUT = open(filePath, fileMode)

        self.Verbose("Writing timestamp to file %s" % (filePath), True)
        fOUT.write("{\n")
        time = self.timeStamp()
        fOUT.write("  \"timestamp\": \"Generated on " + time + " by jsonWriter.py\",\n")

        self.Verbose("Writing all parameters (=%d) to file %s" % (len(self.parameters.keys()), filePath), True)
        # For-loop: All parameter keys-values
        for i, key in enumerate(self.parameters.keys(), 1):
            #fOUT.write("  \""+key+"\": \"%s\",\n" % self.parameters[key])
            #fOUT.write("  \""+key+"\": %s\n}" % self.parameters[key])
            if i==len(self.parameters.keys()):
                fOUT.write("  \""+key+"\": %s\n  }\n" % self.parameters[key])
            else:
                fOUT.write("  \""+key+"\": %s\n  },\n" % self.parameters[key])

        self.Verbose("Writing all graphs (=%d) to file %s" % (len(self.graphs.keys()), filePath), True)
        self.writeAllGraphs()

        # Write and close the file
        fOUT.write("}\n")
        fOUT.close()

        #self.Verbose("Created file %s" % (filePath), True)
        self.Print("Created file %s" % (ss + filePath + ns), True)
        return

    def writeAllGraphs(self):
        if len(self.graphs.keys()) < 1:
            return

        nkeys = 0
        # For-loop: All graphs
        for key in self.graphs.keys():
            fOUT.write("  \""+key+"\": [\n")
            # For-loop: All entries
            for i in range(self.graphs[key].GetN()):                
                x = self.graphs[key].GetX()
                y = self.graphs[key].GetY()
                if 0:
                    print "\t x = %s, y = %s" % (x[i], y[i])
                comma = ","
                if i == self.graphs[key].GetN() - 1:
                    comma = ""
                fOUT.write("      { \"x\": %s, \"y\": %s }%s\n"%(x[i],y[i],comma))
            nkeys+=1
            if nkeys < len(self.graphs.keys()):
                fOUT.write("  ],\n")
            else:
                fOUT.write("  ]\n")
                
