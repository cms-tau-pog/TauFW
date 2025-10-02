# Inspired by HiggsAnalysis-CombinedLimit/python/TagAndProbeModel.py
# https://github.com/cms-analysis/HiggsAnalysis-CombinedLimit/blob/102x/python/TagAndProbeModel.py
from HiggsAnalysis.CombinedLimit.PhysicsModel import *
import re

class TagAndProbe(PhysicsModelBase):
    """Class that build a model for double tag an probe.
       - Two regions:
           pass = WP pass
           fail = WP fail
       - Use as
           text2workspace.py datacard.txt -o workspace.root -m 90 -P TagAndProbeModel:tagAndProbe --PO verbose=2 --PO pass=M --PO fail=VLnM
           combine -M FitDiagnostics workspace.root --redefineSignalPOIs SF
           combine -M MultiDimFit workspace.root --algo=cross --cl 0.6827 -P SF --saveSpecifiedFunc SF_fail
    """
    
    def __init__(self):
        self.verbose = 0
        self.passbin = 'pass' # name of pass region
        self.failbin = 'fail' # name of fail region
        
    def setPhysicsOptions(self,physOptions):
        """Process physics options."""
        physOptions.sort(key=lambda x: x.startswith('verbose'), reverse=True) # put verbose first
        for option in physOptions:
          if option=='verbose':
            self.verbose = 1
          else:
            match = re.match(r"([^=]*)=(.*)",option)
            assert match, "Unknown physics option '%s'"%(option)
            param = match.group(1)
            value = match.group(2)
            if param=='verbose' and value.isdigit():
              self.verbose = int(value)
            elif param=='pass':
              self.passbin = value # rename
            elif param=='fail':
              self.failbin = value # rename
            else:
              raise "Unknown physics option '%s'"%(option)
        
    def doParametersOfInterest(self):
        """Create POI and other parameters, and define the POI set.
           - pass region: SF * A
           - fail region: SF_fail * B = B - (1-SF)*A
        """
        
        # FIX MASS
        if self.options.mass!=0:
          if self.modelBuilder.out.var('MH'):
            self.modelBuilder.out.var('MH').removeRange()
            self.modelBuilder.out.var('MH').setVal(self.options.mass)
          else:
            self.modelBuilder.doVar("MH[%g]"%self.options.mass)
        
        # EXPECTED YIELDS for fail region
        exp_pass = 0.
        exp_fail = 0.
        for bin in self.DC.bins:
          for param in self.DC.exp[bin].keys():
           if self.DC.isSignal[param]:
             if self.failbin in bin:
               exp_fail += self.DC.exp[bin][param]
             elif self.passbin in bin:
               exp_pass += self.DC.exp[bin][param]
             if self.verbose>=3:
               print(">>> Expected number of %s events in %s bin: %9.1f"%(param,bin,self.DC.exp[bin][param]))
        if self.verbose>=2:
          print(">>> Expected number of signal events in pass region: %9.1f"%(exp_pass))
          print(">>> Expected number of signal events in fail region: %9.1f"%(exp_fail))
          print(">>> SF_fail = (%.2f+(1.-SF)*%.2f)/%.2f"%(exp_fail,exp_pass,exp_fail))
        assert exp_fail, "Fail region has no signal events!"
        
        # DEFINE PARAMETERS
        self.modelBuilder.doVar("SF[1.,0.2,1.8]")
        self.modelBuilder.doSet('POI','SF')
        # Assume:
        #   exp_pass + exp_fail = SF*exp_pass + SF_fail*exp_fail
        self.modelBuilder.factory_('expr::SF_fail("(%.5f+(1.-SF)*%.5f)/%.5f",SF)'%(exp_fail,exp_pass,exp_fail))
        
    def getYieldScale(self,bin,process):
        """Return the name of a RooAbsReal to scale this yield by or the
        two special values 1 and 0 (don't scale, and set to zero)."""
        if self.DC.isSignal[process]:
          scale = 1
          if self.failbin in bin:
            scale = 'SF_fail'
          elif self.passbin in bin:
            scale = 'SF'
          if self.verbose>=1:
            print(">>> Scaling %3s in %s bin by '%s'"%(process,bin,scale))
          return scale
        return 1
    
tagAndProbe = TagAndProbe()
