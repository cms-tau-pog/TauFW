# Author: Izaak Neutelings (November 2018)
# 2016: https://github.com/rmanzoni/triggerSF/tree/moriond17
# 2017: https://github.com/truggles/TauTriggerSFs/tree/final_2017_MCv2
# Run2: https://github.com/cms-tau-pog/TauTriggerSFs/blob/run2_SFs/python/getTauTriggerSFs.py
import os
from TauFW.PicoProducer import datadir
from TauFW.common.tools.file import ensureTFile, gethist
datadir = os.path.join(datadir,"trigger")


class TauTriggerSFs(object):
        
    def __init__(self, trigger, wp='Medium', id='DeepTau2017v2p1', year=2016):
        """Load tau trigger histograms from files."""
        print "Loading %s trigger SFs for  %s WP of %s ID for year %d..."%(trigger,wp,id,year)
        
        # CHECKS
        dms      = [0,1,10,11]
        triggers = ['ditau','mutau','etau']
        years    = [2016,2017,2018]
        ids      = ['DeepTau2017v2p1']
        wps      = ['VVVLoose','VVLoose','VLoose','Loose','Medium','Tight','VTight','VVTight']
        trigger  = trigger.replace('tautau','ditau').replace('eletau','etau')
        assert trigger in triggers, "Did not recognize '%s' trigger! Choose from: '%s' triggers."%(trigger,"', '".join(triggers))
        assert wp in wps, "Did not recognize '%s' WP! Choose from: '%s'"%(wp,"', '".join(wps))
        assert id in ids, "Did not recognize '%s' ID! Choose  from: '%s'."%(id,"', '".join(ids))
        assert year in years, "Did not recognize '%s' year! Choose from: %s."%(year,"', '".join(str(y) for y in years))
        
        # GET DATA
        file = ensureTFile('%s/%d_tauTriggerEff_%s.root'%(datadir,year,id), 'r')
        hists_data, hists_mc, hists_sf = { }, { }, { }
        for dm in dms:
          for histtype, histdict in [('data',hists_data),('mc',hists_mc),('sf',hists_sf)]:
            histname = "%s_%s_%s_dm%d_fitted"%(histtype,trigger,wp,dm)
            histdict[dm] = gethist(file,histname)
        file.Close()
        
        self.hists_data = hists_data
        self.hists_mc   = hists_mc
        self.hists_sf   = hists_sf
        self.trigger    = trigger
        self.year       = year
        self.wp         = wp
        self.id         = id
        self.dms        = dms
        
    def checkDM(self, dm):
        """Make sure to have valid DMs."""
        # Note: DM=2 was originally included in oldDM, but with the dynamic strip clustering
        # the second strip was reconstructed together with the first one. So it ends up to DM=1.
        # But, there are still some cases where DM=2 survives.
        if dm==2:  return 1
        if dm==11: return 10
        assert dm in self.dms, "Efficiencies only provided for DMs %s. You provided DM %i"%(', '.join(str(d) for d in self.dms),dm)
        return dm
        
    def getValueFromHist(self, histdict, pt, dm, unc=None):
        dm   = self.checkDM(dm)
        hist = histdict[dm]
        bin  = hist.FindFixBin(pt)
        bin  = min(hist.GetNbinsX(),max(1,bin))
        val  = hist.GetBinContent(bin)
        if unc=='Up':
          val += hist.GetBinError(bin)
        elif unc=='Down':
          val -= hist.GetBinError(bin)
        elif unc=='All':
          return val-hist.GetBinError(bin), val, val+hist.GetBinError(bin)
        return val
        
    def getEff_data(self, pt, dm, unc=None):
        """Return the data efficiency."""
        return self.getValueFromHist(self.hists_data,pt,dm,unc)
        
    def getEff_mc(self, pt, dm, unc=None):
        """Return the MC efficiency."""
        return self.getValueFromHist(self.hists_mc,pt,dm,unc)
        
    def getSF(self, pt, dm, unc=None):
        """Return the data/MC scale factor."""
        eff_data = self.getEff_data(pt,dm,unc)
        eff_mc   = self.getEff_mc(pt,dm,unc)
        if unc=='All':
          for eff in eff_mc:
            if eff < 1e-5:
              print "MC eff. is suspiciously low! MC eff=%s, trigger=%s, ID=%s, WP=%s, pt=%s"%(eff,self.trigger,self.id,self.wp,pt)
              return 0.0, 0.0, 0.0
          return eff_data[0]/eff_mc[0], eff_data[1]/eff_mc[1], eff_data[2]/eff_mc[2]
        else:
          if eff_mc < 1e-5:
            print "MC eff. is suspiciously low! MC eff=%s, trigger=%s, ID=%s, WP=%s, pt=%s"%(eff_mc,self.trigger,self.id,self.wp,pt)
            return 0.0
        sf = eff_data / eff_mc
        return sf
        
    def getSFPair(self, tau1, tau2, unc=None):
        """Return the data/MC scale factor for two tau legs."""
        if unc=='All':
          sf1_down, sf1, sf1_up = self.getSF(tau1.pt,tau1.decayMode,unc=unc)
          sf2_down, sf2, sf2_up = self.getSF(tau2.pt,tau2.decayMode,unc=unc)
          return sf1_down*sf2_down, sf1*sf2, sf1_up*sf1_up
        else:
          return self.getSF(tau1.pt,tau1.decayMode,unc=unc)*self.getSF(tau2.pt,tau2.decayMode,unc=unc)
    
