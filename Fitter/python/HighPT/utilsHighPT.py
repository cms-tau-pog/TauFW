import ROOT 
import math
from array import array
import numpy as np

#############################
##### General settings ######
#############################

#########################
# folder for picotuples #
#########################
picoFolder='/eos/user/r/rasp/output/HighPT'

#######################
# folders for figures #
#######################
figuresFolderFF = '/afs/cern.ch/user/r/rasp/public/HighPT_v2/FF'
figuresFolderMetTrigger = '/afs/cern.ch/user/r/rasp/public/HighPT_v2/MetTrigger'
figuresFolderSys = '/afs/cern.ch/user/r/rasp/public/HighPT_v2/Sys'
figuresFolderWMuNu = '/afs/cern.ch/user/r/rasp/public/HighPT_v2/WMuNu'
figuresFolderWTauNu = '/afs/cern.ch/user/r/rasp/public/HighPT_v2/WTauNu_eta'

########################
# folder for datacards #
########################
datacardsFolder = '/afs/cern.ch/work/r/rasp/public/HighPT_v2/datacards_eta'

###################
# Cross sections  #
###################

sampleXSec_2016 = { 
"DYJetsToLL_M-50" : 6077.22,
"TTTo2L2Nu" : 88.29,
"TTToSemiLeptonic" : 365.35,
"TTToHadronic" : 377.96,  
"WJetsToLNu_HT-100To200" : 1395.0*1.166,
"WJetsToLNu_HT-200To400" : 407.9*1.166,
"WJetsToLNu_HT-400To600" : 57.48*1.166,
"WJetsToLNu_HT-600To800" : 12.87*1.166,
"WJetsToLNu_HT-800To1200" : 5.366*1.166,
"WJetsToLNu_HT-1200To2500" : 1.074*1.166,
"WJetsToLNu" : 61526.7 ,  
"ST_tW_antitop_5f_NoFullyHadronicDecays" : 19.47,
"ST_tW_top_5f_NoFullyHadronicDecays" : 19.47,
"ST_t-channel_antitop_4f_InclusiveDecays" : 80.95,
"ST_t-channel_top_4f_InclusiveDecays" : 136.02,
"WW" : 118.7,
"WZ" : 27.68,
"ZZ" : 12.19,
"ZJetsToNuNu_HT-100To200"   : 304.5,
"ZJetsToNuNu_HT-200To400"   : 91.82,
"ZJetsToNuNu_HT-400To600"   : 13.11,
"ZJetsToNuNu_HT-600To800"   : 3.260,
"ZJetsToNuNu_HT-800To1200"  : 1.499,
"ZJetsToNuNu_HT-1200To2500" : 0.3430,
"WToMuNu_M-200" : 6.238,
"WToTauNu_M-200" : 6.206
}

sampleXSec_2017 = {
"DYJetsToLL_M-50" : 6077.22,
"TTTo2L2Nu" : 88.29,
"TTToSemiLeptonic" : 365.35,
"TTToHadronic" : 377.96,  
"WJetsToLNu_HT-100To200" : 1395.0*1.166,
"WJetsToLNu_HT-200To400" : 407.9*1.166,
"WJetsToLNu_HT-400To600" : 57.48*1.166,
"WJetsToLNu_HT-600To800" : 12.87*1.166,
"WJetsToLNu_HT-800To1200" : 5.366*1.166,
"WJetsToLNu_HT-1200To2500" : 1.074*1.166,
"WJetsToLNu" : 61526.7 ,  
"ST_tW_antitop_5f_NoFullyHadronicDecays" : 19.47,
"ST_tW_top_5f_NoFullyHadronicDecays" : 19.47,
"ST_t-channel_antitop_4f_InclusiveDecays" : 80.95,
"ST_t-channel_top_4f_InclusiveDecays" : 136.02,
"WW" : 118.7,
"WZ" : 27.68,
"ZZ" : 12.19,
"ZJetsToNuNu_HT-100To200"   : 304.5,
"ZJetsToNuNu_HT-200To400"   : 91.82,
"ZJetsToNuNu_HT-400To600"   : 13.11,
"ZJetsToNuNu_HT-600To800"   : 3.260,
"ZJetsToNuNu_HT-800To1200"  : 1.499,
"ZJetsToNuNu_HT-1200To2500" : 0.3430,
"WToMuNu_M-200" : 6.990,
"WToTauNu_M-200" : 7.246
}

sampleXSec_2018 = {
"DYJetsToLL_M-50" : 6077.22,
"TTTo2L2Nu" : 88.29,
"TTToSemiLeptonic" : 365.35,
"TTToHadronic" : 377.96,  
"WJetsToLNu_HT-100To200" : 1395.0*1.166,
"WJetsToLNu_HT-200To400" : 407.9*1.166,
"WJetsToLNu_HT-400To600" : 57.48*1.166,
"WJetsToLNu_HT-600To800" : 12.87*1.166,
"WJetsToLNu_HT-800To1200" : 5.366*1.166,
"WJetsToLNu_HT-1200To2500" : 1.074*1.166,
"WJetsToLNu" : 61526.7 ,  
"ST_tW_antitop_5f_NoFullyHadronicDecays" : 19.47,
"ST_tW_top_5f_NoFullyHadronicDecays" : 19.47,
"ST_t-channel_antitop_4f_InclusiveDecays" : 80.95,
"ST_t-channel_top_4f_InclusiveDecays" : 136.02,
"WW" : 118.7,
"WZ" : 27.68,
"ZZ" : 12.19,
"ZJetsToNuNu_HT-100To200"   : 304.5,
"ZJetsToNuNu_HT-200To400"   : 91.82,
"ZJetsToNuNu_HT-400To600"   : 13.11,
"ZJetsToNuNu_HT-600To800"   : 3.260,
"ZJetsToNuNu_HT-800To1200"  : 1.499,
"ZJetsToNuNu_HT-1200To2500" : 0.3430,
"WToMuNu_M-200" : 6.990,
"WToTauNu_M-200" : 7.246
}

eraSamples = {
"UL2016_postVFP" : sampleXSec_2016,
"UL2016_preVFP" : sampleXSec_2016,
"UL2017" : sampleXSec_2017,    
"UL2018" : sampleXSec_2018
}

eraLumi = {
    "UL2016" : 36300,
    "UL2016_postVFP" : 16800,
    "UL2016_preVFP"  : 19500,
    "UL2017" : 41480,    
    "UL2018" : 59830
}


################
# Data samples #
################

singlemu_2018 = ['SingleMuon_Run2018A','SingleMuon_Run2018B','SingleMuon_Run2018C','SingleMuon_Run2018D']
singlemu_2017 = ['SingleMuon_Run2017B','SingleMuon_Run2017C','SingleMuon_Run2017D','SingleMuon_Run2017E','SingleMuon_Run2017F']

jetht_2018 = ['JetHT_Run2018A','JetHT_Run2018B','JetHT_Run2018C','JetHT_Run2018D']
jetht_2017 = ['JetHT_Run2017B','JetHT_Run2017C','JetHT_Run2017D','JetHT_Run2017E','JetHT_Run2017F']

met_2018 = ['MET_Run2018A','MET_Run2018B','MET_Run2018C','MET_Run2018D']
met_2017 = ['MET_Run2017B','MET_Run2017C','MET_Run2017D','MET_Run2017E','MET_Run2017F']

singlemu = {
    "UL2017": singlemu_2017,
    "UL2018": singlemu_2018
}

jetht = {
    "UL2017": jetht_2017,
    "UL2018": jetht_2018
}

met = {
    "UL2017": met_2017,
    "UL2018": met_2018
}

tauWPs = {
    'Loose': "4",
    'Medium': "5",
    'Tight': "6",
    'VTight': "7",
    'VVTight': "8"
}

tauIntWPs = {
    'Loose': 4,
    'Medium': 5,
    'Tight': 6,
    'VTight': 7,
    'VVTight': 8    
}

#############################
# Shape uncertainties (JME) #
#############################
unc_jme = ['JES','Unclustered']

###############################
# Shape uncertainties (taues) #
###############################
unc_taues = ['taues','taues_1pr','taues_1pr1pi0','taues_3pr','taues_3pr1pi0'] 

##################################
### Settings for FF measurements #
##################################

xbinsPt2D = [100, 125, 150, 200, 2000] 
xbinsPt =   [100, 125, 150, 175, 200, 2000]
ptUncThreshold = 200. # split pt region for stat. uncertainties (<200, >=200.)

ptratio2DCuts = {
    'ptratioLow'   : 'jpt_ratio_2<0.85',
    'ptratioHigh'  : 'jpt_ratio_2>=0.85'
}
ptratio2DThreshold = 0.85

#ptratioCuts = {
#    'ptratioLow'   : 'jpt_ratio_2<0.8',
#    'ptratioMedium': 'jpt_ratio_2>=0.8&&jpt_ratio_2<0.9',
#    'ptratioHigh'  : 'jpt_ratio_2>=0.9'
#}
#ptratioThresholds = [0.8, 0.9]

ptratioCuts = {
    'ptratioLow'   : 'jpt_ratio_2<0.85',
#    'ptratioMedium': 'jpt_ratio_2>=0.8&&jpt_ratio_2<0.9',
    'ptratioHigh'  : 'jpt_ratio_2>=0.85'
}
ptratioThreshold = 0.85

decaymode2DCuts = {
    '1prong'    : 'dm_2==0',
    '1prongPi0' : '(dm_2==1||dm_2==2)',
    '3prong'    : 'dm_2==10',
    '3prongPi0' : 'dm_2==11'
}

decaymodeCuts = {
    '1prongPi0' : '(dm_2==1||dm_2==2)',
    '3prong'    : 'dm_2==10',
    '3prongPi0' : 'dm_2==11'}

xbinsMass = {
    '1prongPi0': [0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8],
    '3prong'   : [0.9, 1.0, 1.1, 1.2, 1.3, 1.4],
    '3prongPi0': [1.0, 1.1, 1.2, 1.3, 1.4, 1.5]
}

# histogram labels (W*->tau+v selection)
histLabels = ['','_SB','_mc_wjets','_data_wjets','_data_dijets']
histSysLabels = ['_mc_wjets','_data_wjets','_data_dijets']
ptratioLabels = ['_ptratioLow','_ptratioMedium','_ptratioHigh']
statUncLabels = ['_unc1','_unc2']

XTitle = {
    'mt_1'  : "m_{T} (GeV)",
    'pt_1'  : "p_{T} (GeV)",
    'eta_1' : "#eta",
    'met'   : "E_{T}^{mis} (GeV)",
    'm_1'   : "mass (GeV)"
}

#######################################
# Creating shape systematic templates #
#######################################
def ComputeSystematics(h_central, h_sys, name):
    h_up = h_central.Clone(name+"Up")
    h_down = h_central.Clone(name+"Down")
    nbins = h_central.GetNbinsX()
    for i in range(1,nbins+1):
        x_up = h_sys.GetBinContent(i)
        x_central = h_central.GetBinContent(i)
        x_down = x_central
        if x_up>0:
            x_down = x_central*x_central/x_up
        h_up.SetBinContent(i,x_up)
        h_down.SetBinContent(i,x_down)

    return h_up, h_down

def extractBinLabels(pt,ptratio):
    ratLabel = '_ptratioLow'
    #    if ptratio>=ptratioThresholds[0] and ptratio<ptratioThresholds[1]: ratLabel = '_ptratioMedium'
    #    if ptratio>=ptratioThresholds[1]: ratLabel = '_ptratioHigh'
    if ptratio>=ptratioThreshold: ratLabel = '_ptratioHigh'
    uncLabel = '_unc1'
    if pt>ptUncThreshold: uncLabel = '_unc2'
    return ratLabel, uncLabel

# Run over set of samples and create histogram
def RunSamples(samples,var,weight,cut,xbins,name):
    print
    print("Running",name,var,weight,cut)
    nbins = len(xbins)-1
    hist = ROOT.TH1D(name,"",nbins,array('d',list(xbins)))
    for sampleName in samples:
        sample = samples[sampleName]
        histsample = sample.CreateHisto(var,weight,cut,xbins,name+"_"+sampleName)
        hist.Add(hist,histsample,1.,1.)
    return hist

# Run over set of samples and create histograms for W*->tau+v channel
# for each sample loop over Tree entries is performed
def RunSamplesTauNu(samples,var,unc,xbins,selection,name):
    print
    print("Running",name,var,unc,selection)
    nbins = len(xbins)-1
    hists = {} # discionary of histograms
    for label in histLabels:
        histname = name + selection + unc + label
        hists[histname] = ROOT.TH1D(histname,"",nbins,array('d',list(xbins)))
    for label in histSysLabels:
        for ptratioLabel in ptratioLabels:
            for uncLabel in statUncLabels:
                histname = name + selection + unc + label + ptratioLabel + uncLabel
                hists[histname] = ROOT.TH1D(histname,"",nbins,array('d',list(xbins)))

    for sampleName in samples:        
        sample = samples[sampleName]
        histsample = sample.CreateHistosTauNu(var,unc,xbins,selection)
        
        for label in histLabels:
            histname = name + selection + unc + label
            histsamplename = sample.sampleName + selection + unc + label
            hists[histname].Add(hists[histname],histsample[histsamplename],1.,1.)
        for label in histSysLabels:
            for ptratioLabel in ptratioLabels:
                for uncLabel in statUncLabels:
                    histname = name + selection + unc + label + ptratioLabel + uncLabel
                    histsamplename = sample.sampleName + selection + unc + label + ptratioLabel + uncLabel
                    hists[histname].Add(hists[histname],histsample[histsamplename],1.,1.)

    return hists

def createBins(nbins,xmin,xmax):
    binwidth = (xmax-xmin)/float(nbins)
    bins = []
    for i in range(0,nbins+1):
        xb = xmin + float(i)*binwidth
        bins.append(xb)
    return bins

def zeroBinErrors(hist):
    nbins = hist.GetNbinsX()
    for i in range(1,nbins+1):
        hist.SetBinError(i,0.)

def createUnitHisto(hist,histName):
    nbins = hist.GetNbinsX()
    unitHist = hist.Clone(histName)
    for i in range(1,nbins+1):
        x = hist.GetBinContent(i)
        e = hist.GetBinError(i)
        if x>0:
            rat = e/x
            unitHist.SetBinContent(i,1.)
            unitHist.SetBinError(i,rat)

    return unitHist

def dividePassProbe(passHist,failHist,histName):
    nbins = passHist.GetNbinsX()
    hist = passHist.Clone(histName)
    for i in range(1,nbins+1):
        xpass = passHist.GetBinContent(i)
        epass = passHist.GetBinError(i)
        xfail = failHist.GetBinContent(i)
        efail = failHist.GetBinError(i)
        xprobe = xpass+xfail
        ratio = 1
        eratio = 0
        if xprobe>1e-4:
            ratio = xpass/xprobe
            dpass = xfail*epass/(xprobe*xprobe)
            dfail = xpass*efail/(xprobe*xprobe)
            eratio = math.sqrt(dpass*dpass+dfail*dfail)
        hist.SetBinContent(i,ratio)
        hist.SetBinError(i,eratio)

    return hist

def divideHistos(numHist,denHist,histName):
    nbins = numHist.GetNbinsX()
    hist = numHist.Clone(histName)
    for i in range(1,nbins+1):
        xNum = numHist.GetBinContent(i)
        eNum = numHist.GetBinError(i)
        xDen = denHist.GetBinContent(i)
        eDen = denHist.GetBinError(i)
        ratio = 1
        eratio = 0
        if xNum>1e-7 and xDen>1e-7:
            ratio = xNum/xDen
            rNum = eNum/xNum
            rDen = eDen/xDen
            rratio = math.sqrt(rNum*rNum+rDen*rDen)
            eratio = rratio * ratio
        hist.SetBinContent(i,ratio)
        hist.SetBinError(i,eratio)

    return hist

def histoRatio(numHist,denHist,histName):
    nbins = numHist.GetNbinsX()
    hist = numHist.Clone(histName)
    for i in range(1,nbins+1):
        xNum = numHist.GetBinContent(i)
        eNum = numHist.GetBinError(i)
        xDen = denHist.GetBinContent(i)
        ratio = 1
        eratio = 0
        if xNum>1e-7 and xDen>1e-7:
            ratio = xNum/xDen
            eratio = eNum/xDen
        hist.SetBinContent(i,ratio)
        hist.SetBinError(i,eratio)

    return hist

  
class TauNuCuts:
    def __init__(self,**kwargs):
        self.metCut = kwargs.get('metCut',120.)
        self.mtLowerCut = kwargs.get('mtLowerCut',200.)
        self.mtUpperCut = kwargs.get('mtUpperCut',99999999.)
        self.etaCut = kwargs.get('etaCut',2.3)
        self.ptLowerCut = kwargs.get('ptLowerCut',100.)
        self.ptUpperCut = kwargs.get('ptUpperCut',99999999.)
        self.metdphiCut = kwargs.get('metdphiCut',2.8)

class FakeFactorHighPt:

    def __init__(self,filename):
        print
        print('Loading fake factors from file',filename," >>>>>")
        self.fileName = filename
        self.fileFF = ROOT.TFile(self.fileName,"READ")
        self.hists = {}
        self.labels = ['dijets','wjets']
        #self.ptbins = ['ptratioLow','ptratioMedium','ptratioHigh']
        self.ptbins = ['ptratioLow','ptratioHigh']
        for ptbin in self.ptbins:
            for label in self.labels:                
                name = 'data_' + label + "_" + ptbin
                self.hists[name] = self.fileFF.Get(name)
                print(name,self.hists[name])
            name = 'mc_wjets_' + ptbin
            self.hists[name] = self.fileFF.Get(name)
            print(name,self.hists[name])

    def getWeight(self,pttau,ptratio,label):
        ptlabel = 'ptratioLow'
        #        if ptratio>=ptratioThresholds[0] and ptratio<ptratioThresholds[1]: ptlabel = 'ptratioMedium'
        #        if ptratio>=ptratioThresholds[1]: ptlabel = 'ptratioHigh'
        if ptratio>=ptratioThreshold: ptlabel = 'ptratioHigh'
        name = label + "_" + ptlabel
        x = pttau
        nbins = self.hists[name].GetNbinsX()
        lowerEdge = self.hists[name].GetBinLowEdge(1)
        upperEdge = self.hists[name].GetBinLowEdge(nbins+1)
        if pttau<lowerEdge: x = lowerEdge+0.001
        if pttau>upperEdge: x = upperEdge-0.001
        weight = self.hists[name].GetBinContent(self.hists[name].FindBin(x))
        error = self.hists[name].GetBinError(self.hists[name].FindBin(x))
        return weight,error

class sampleHighPt:

    def __init__(self,basefolder,era,channel,samplename,isdata,**kwargs):
        filename = basefolder + "/" + era + "/" + channel + "/" + samplename + ".root"
        self.additionalCut = kwargs.get('additionalCut', '')
        self.sampleName = samplename
        self.sampleFile = ROOT.TFile(filename,"READ")
        #self.sampleTree = self.sampleFile.Get("tree")
        self.norm = 1.0
        self.isdata = isdata
        if isdata:
            self.norm = 1.0
        else:
            xsecSamples = eraSamples[era]
            xsec = xsecSamples[samplename]
            histsumw = self.sampleFile.Get("weightedEvents")
            sumw = histsumw.GetSumOfWeights()
            lumi = eraLumi[era]
            self.norm = xsec*lumi/sumw
        print('sample >>> ',self.sampleName,self.norm,self.additionalCut)

    def CreateHisto(self,var,weight,cut,bins,name):

        nbins = len(bins)-1
        histname = self.sampleName+"_"+name
        hist = ROOT.TH1D(histname,"",nbins,array('d',list(bins)))
        cutstring = weight+"*("+cut+")"
        tree = self.sampleFile.Get("tree")
        if (self.additionalCut!=''):
            cutstring = weight+"*("+cut+"&&"+self.additionalCut+")"
        tree.Draw(var+">>"+histname,cutstring)
        hist.Scale(self.norm)
        return hist

    def SetTauNuConfig(self,fakeFactorHighPt,WP,tauNuCuts):
        self.fakeFactorHighPt = fakeFactorHighPt
        self.WP_index = tauIntWPs[WP]
        self.tauNuCuts = tauNuCuts

    def CreateHistosTauNu(self,var,unc,bins,selection):

        print("Running over",self.sampleName)
        tree = self.sampleFile.Get("tree")

        # initialization
        nbins = len(bins)-1
        wp_index = self.WP_index
        cuts = self.tauNuCuts
        fakeFactor = self.fakeFactorHighPt

        # creating histograms 
        hists = {}
        for label in histLabels:
            name = self.sampleName + selection + unc + label
            hists[name] = ROOT.TH1D(name,"",nbins,array('d',list(bins)))
        for label in histSysLabels:
            for ptratioLabel in ptratioLabels:
                for uncLabel in statUncLabels:
                    name = self.sampleName + selection + unc + label + ptratioLabel + uncLabel
                    hists[name] = ROOT.TH1D(name,"",nbins,array('d',list(bins)))

        # floats
        weight      = np.zeros(1,dtype='f')
        pt_1        = np.zeros(1,dtype='f')
        eta_1       = np.zeros(1,dtype='f')
        metdphi_1   = np.zeros(1,dtype='f')
        mt_1        = np.zeros(1,dtype='f')
        met         = np.zeros(1,dtype='f')
        jpt_ratio_1 = np.zeros(1,dtype='f')
        m_1         = np.zeros(1,dtype='f')

        # booleans
        mettrigger     = np.zeros(1,dtype='?')
        metfilter      = np.zeros(1,dtype='?')
        extramuon_veto = np.zeros(1,dtype='?')
        extraelec_veto = np.zeros(1,dtype='?')
        extratau_veto  = np.zeros(1,dtype='?')
        
        # integers
        njets                    = np.zeros(1,dtype='i')
        idDeepTau2017v2p1VSe_1   = np.zeros(1,dtype='i')
        idDeepTau2017v2p1VSmu_1  = np.zeros(1,dtype='i')
        idDeepTau2017v2p1VSjet_1 = np.zeros(1,dtype='i')
        genmatch_1               = np.zeros(1,dtype='i')

        # branches -> 
        # floats 
        tree.SetBranchAddress('met',met)
        tree.SetBranchAddress('metdphi_1',metdphi_1)
        tree.SetBranchAddress('mt_1',mt_1)
        tree.SetBranchAddress('pt_1',pt_1)
        tree.SetBranchAddress('m_1',m_1)
        tree.SetBranchAddress('weight',weight)
        tree.SetBranchAddress('eta_1',eta_1)
        tree.SetBranchAddress('jpt_ratio_1',jpt_ratio_1)

        # booleans
        tree.SetBranchAddress('mettrigger',mettrigger)
        tree.SetBranchAddress('metfilter',metfilter)
        tree.SetBranchAddress('extramuon_veto',extramuon_veto)
        tree.SetBranchAddress('extraelec_veto',extraelec_veto)
        tree.SetBranchAddress('extratau_veto',extratau_veto)

        # integers
        tree.SetBranchAddress('njets',njets)
        tree.SetBranchAddress('idDeepTau2017v2p1VSe_1',idDeepTau2017v2p1VSe_1)
        tree.SetBranchAddress('idDeepTau2017v2p1VSmu_1',idDeepTau2017v2p1VSmu_1)
        tree.SetBranchAddress('idDeepTau2017v2p1VSjet_1',idDeepTau2017v2p1VSjet_1)
        if not self.isdata: tree.SetBranchAddress("genmatch_1",genmatch_1)

        nentries = tree.GetEntries()

        # run over entries
        for entry in range(0,nentries):
            tree.GetEntry(entry)

            # mc selection
            # 0 - select genuine taus
            # 1 - select jet->tau fakes
            # 2 - select not jet->tau fakes
            if not self.isdata:
                if selection=='_tau' and genmatch_1[0]!=5: continue # genuine taus
                if selection=='_fake' and genmatch_1[0]!=0: continue # jet->tau fakes
                if selection=='_notFake' and genmatch_1[0]==0: continue # not jet->tau fakes

            # met filters, trigger, vetos
            if not metfilter[0]: continue
            if not mettrigger[0]: continue
            if extraelec_veto[0]: continue
            if extramuon_veto[0]: continue
            if extratau_veto[0]: continue
            if njets[0]!=0: continue

            # kinematic cuts
            if pt_1[0]<cuts.ptLowerCut: continue
            if pt_1[0]>cuts.ptUpperCut: continue
            if math.fabs(eta_1[0])>cuts.etaCut: continue
            if mt_1[0]<cuts.mtLowerCut: continue
            if mt_1[0]>cuts.mtUpperCut: continue
            if metdphi_1[0]<cuts.metdphiCut: continue
            if met[0]<cuts.metCut: continue

            # tau discriminator against e and mu and jet
            if idDeepTau2017v2p1VSe_1[0]<4: continue
            if idDeepTau2017v2p1VSmu_1[0]<1: continue
            if idDeepTau2017v2p1VSjet_1[0]<1: continue

            variable = mt_1[0]
            if var=='pt_1': variable = pt_1[0]
            if var=='eta_1': variable = eta_1[0]
            if var=='met': variable = met[0]
            if var=='m_1': variable = m_1[0]

            # signal region
            if idDeepTau2017v2p1VSjet_1[0]>=wp_index:
                name = self.sampleName + selection + unc
                hists[name].Fill(variable,weight[0])

            # Sideband region (VVVLoose and not Loose)
            if idDeepTau2017v2p1VSjet_1[0]<4:
                name = self.sampleName + selection + unc + "_SB"
                hists[name].Fill(variable,weight[0])
                
                # find label
                refRatioLabel, refUncLabel = extractBinLabels(pt_1[0],jpt_ratio_1[0])
                refLabel = refRatioLabel+refUncLabel

                # applying FF and systematics
                for label in ['mc_wjets','data_wjets','data_dijets']:
                    weightFF,errorFF = fakeFactor.getWeight(pt_1[0],jpt_ratio_1[0],label)
                    name = self.sampleName + selection + unc + '_' + label
                    hists[name].Fill(variable,weight[0]*weightFF)
                    for ptratioLabel in ptratioLabels:
                        for uncLabel in statUncLabels:
                            currentLabel = ptratioLabel+uncLabel
                            name = self.sampleName + selection + unc + "_" + label + currentLabel
                            if currentLabel==refLabel: 
                                hists[name].Fill(variable,weight[0]*(weightFF+errorFF))
                            else:
                                hists[name].Fill(variable,weight[0]*weightFF)

        for hist in hists:
            hists[hist].Scale(self.norm)

        return hists
