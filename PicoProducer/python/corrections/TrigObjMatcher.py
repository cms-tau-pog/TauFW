# Author: Izaak Neutelings (November, 2019)
# Description: Tools to match reco objects to trigger objects in nanoAOD,
#              and to read JSON file containing trigger information
# Sources:
#   https://github.com/cms-sw/cmssw/blob/master/PhysicsTools/NanoAOD/python/triggerObjects_cff.py
#   https://cms-nanoaod-integration.web.cern.ch/integration/master-106X/mc106X_doc.html#TrigObj
import os, sys, yaml #, json
from collections import namedtuple
from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection
TriggerData = namedtuple('TriggerData',['trigdict','combdict']) # simple container class
objectTypes = { 1: 'Jet', 6: 'FatJet', 2: 'MET', 3: 'HT', 4: 'MHT',
                11: 'Electron', 13: 'Muon', 15: 'Tau', 22: 'Photon', } 
objectIds   = { t: i for i,t in objectTypes.iteritems() }
objects     = [ 'Electron', 'Muon', 'Tau', 'Photon', 'Jet', 'FatJet', 'MET', 'HT', 'MHT' ]


def loadTriggerDataFromJSON(filename,channel=None,isdata=True,verbose=False):
    """Help function to load trigger path and object information from a JSON file.
    
    The JSON format is as follows:
      'year'
         -> year
      'filterbits'
         -> object type ('Electron', 'Muon', 'Tau', ...)
           -> shorthand for filters patterns in nanoAOD
             -> bits (powers of 2)
      'hltcombs'
         -> data type ('data' or 'mc')
           -> tau trigger type (e.g. 'etau', 'mutau', 'ditau', 'SingleMuon', ...)
             -> list of recommended HLT paths
      'hltpaths'
         -> HLT path ("HLT_*")
           -> 'runrange':     in case this path was only available in some data runs (optional)
           -> 'filter':       last filter associated with this trigger path ("hlt*")
           -> object type ('Electron', 'Muon', 'Tau', ...)
             -> 'ptmin':      offline cut on pt 
             -> 'etamax':     offline cut on eta (optional)
             -> 'filterbits': list of shorthands for filter patterns
    
    Returns a named tuple 'TriggerData' with attributes
      trigdict = dict of trigger path -> 'Trigger' object
      combdict = dict of channel -> list of combined triggers ('Trigger' object)
    """
    if verbose:
      print ">>> loadTriggerDataFromJSON: loading '%s'"%(filename)
    datatype = 'data' if isdata else 'mc'
    channel_ = channel
    triggers = [ ]
    combdict = { }
    trigdict = { }
    
    # OPEN JSON
    with open(filename,'r') as file:
      data = yaml.safe_load(file)
    for key in ['filterbits','hltpaths']:
      assert key in data, "Did not find '%s' key in JSON file '%s'"%(key,filename)
    
    # FILTER BIT DICTIONARY: object type -> filterbit shortname -> bit
    bitdict = data['filterbits']
    
    # HLT PATHS with corresponding filter bits, pt, eta cut
    for path, trigobjdict in data['hltpaths'].iteritems():
      runrange     = trigobjdict.get('runrange',None) if isdata else None
      filters      = [ ]
      for obj in objects: # ensure order
        if obj not in trigobjdict: continue
        if obj not in bitdict:
          raise KeyError("Did not find '%s' in filter bit dictionary! Please check the JSON file '%s' with bitdict = %s"%(obj,filename,bitdict))
        ptmin      = trigobjdict[obj].get('ptmin', 0.0)
        etamax     = trigobjdict[obj].get('etamax',6.0)
        filterbits = trigobjdict[obj]['filterbits']
        filter     = TriggerFilter(obj,filterbits,ptmin,etamax)
        filter.setbits(bitdict[obj])
        filters.append(filter)
      assert len(filters)>0, "Did not find any valid filters for '%s' in %s"%(path,trigobjdict)
      filters.sort(key=lambda f: (objects.index(f.type),-f.ptmin)) # order by 1) object type, 2) ptmin
      trigger = Trigger(path,filters,runrange=runrange)
      triggers.append(trigger)
      trigdict[path] = trigger
    
    # COMBINATIONS OF HLT PATHS
    if 'hltcombs' in data:
      if channel_:
        assert channel_ in data['hltcombs'][datatype], "Did not find channel '%s' in JSON file! Available: '%s'"%(channel_,"', '".join(data['hltcombs'][datatype].keys()))
      for channel, paths in data['hltcombs'][datatype].iteritems():
        if channel_ and channel!=channel_: continue
        #combtrigs = [trigdict[p] for p in paths]
        combdict[channel] = [trigdict[p] for p in paths] #TriggerCombination(combtrigs)
    
    # PRINT
    triggers.sort(key=lambda t: t.path)
    if verbose:
      print ">>> triggers & filters:"
      for trigger in triggers:
        if channel_ and trigger not in combdict[channel_]: continue
        print ">>>   %s"%(trigger.path)
        for filter in trigger.filters:
          print ">>>     %-9s %r"%(filter.type+':',filter.name) #,"bits=%s"%filter.bits
      print ">>> trigger combinations for %s:"%datatype
      for channel, triglist in combdict.iteritems():
        if channel_ and channel!=channel_: continue
        print ">>>   %s"%(channel)
        for trigger in triglist:
          path     = "'%s'"%trigger.path
          if trigger.runrange:
            path += ", %d <= run <= %d"%(trigger.runrange[0],trigger.runrange[1])
          print ">>>     "+path
    
    return TriggerData(trigdict,combdict)
  

class Trigger:
  """Class to contain a single trigger and its trigger object(s)."""
  def __init__(self,path,filters,runrange=None,**kwargs):
    assert path, "No paths value given!"
    if not isinstance(filters,list): filters = [filters]
    assert path and isinstance(path,str),\
      "No valid trigger path given! Received: %r."%(path)
    assert all(isinstance(f,TriggerFilter) for f in filters),\
      "Trigger filter should be instances of the TriggerFilter class! Received: %r."%(filters)
    assert not runrange or type(runrange) in [list,tuple] and len(runrange)==2,\
      "Trigger run range should be a tuple of length two! Received: %r."%(runrange)
    patheval      =  "e."+path
    if runrange:
      patheval    = "e.run>=%d and e.run<=%d and %s"%(runrange[0],runrange[1],patheval)
    self.filters  = filters                             # list of trigger filters, one per leg
    self.runrange = runrange                            # range of run for this trigger formatted as (first,last); for data only
    self.path     = path                                # human readable trigger combination
    self.patheval = patheval                            # trigger evaluation per event 'e'
    self.fireddef = "self.fired = lambda e: "+patheval  # exact definition of 'fired' function
    exec self.fireddef in locals()                      # method to check if trigger was fired for a given event
    #self.fired = lambda e: any(e.p for p in self.paths)
  
  def __repr__(self):
    """Returns string representation of Trigger object."""
    return "<%s('%s') at %s>"%(self.__class__.__name__,self.path,hex(id(self)))
  
  def __str__(self):
    """String representation of trigger."""
    trigstr = "'%s'"%self.path
    if self.runrange:
      trigstr += ", %d <= run <= %d"%(self.runrange[0],self.runrange[1])
    print trigstr
  

###class TriggerCombination:
###    """Container class for a combination of triggers."""
###    def __init__(self,triggers,**kwargs):
###        assert triggers and isinstance(triggers,list) and all(isinstance(t,Trigger) for t in triggers),\
###          "Triggers argument should be a list of 'Trigger' objects! Received: %r."%(triggers)
###        patheval = ""
###        for trigger in triggers:
###          if patheval!="":
###            patheval += " || "
###          if '&&' in trigger.patheval or '||' in trigger.patheval:
###            patheval += '('+trigger.patheval+')'
###          else:
###            patheval += trigger.patheval
###        self.patheval = patheval
###        self.path     = patheval.replace("e.",'')
###        self.fireddef = "self.fired = lambda e: "+patheval
###        exec self.fireddef in locals() # method to check if any of the triggers was fired for a given event
###        
###    def __repr__(self):
###        """Returns string representation of TriggerCombination object."""
###        return "<%s('%s') at %s>"%(self.__class__.__name__,self.path,hex(id(self)))


class TriggerFilter:
  """Class to contain trigger filter and allow easy matching to trigger objects."""
  
  def __init__(self,obj,filters,ptmin=0.0,etamax=6.0,**kwargs):
    if not isinstance(filters,list):
      filters = [filters]
    assert all(isinstance(f,str) for f in filters), "Filter bits should be a list of strings! Received: %r."%(filters)
    if isinstance(obj,int): id_, type_ = obj, objectTypes[obj]
    else:                   id_, type_ = objectIds[obj], obj
    self.id      = id_                   # nanoAOD object ID (e.g. 11, 13, 15, ...)
    self.type    = type_                 # nanoAOD object type (e.g. 'Muon', 'Tau', ...)
    self.name    = '_'.join(filters)     # name of this object
    self.filters = filters               # list of filters
    self.bits    = kwargs.get('bits',0)  # sum of filter bits
    self.ptmin   = ptmin                 # offline min pT cut
    self.etamax  = etamax                # offline max eta cut
    if 'bitdict' in kwargs:
      self.setbits(kwargs['bitdict'])
  
  def __repr__(self):
    """Returns string representation of TriggerFilter object."""
    return "<%s('%s','%s',%s) at %s>"%(self.__class__.__name__,self.objtype,self.name,self.bits,hex(id(self)))
  
  def isSame(ofilt):
    """Compare to other filter object based on values."""
    return sorted(self.filters)==sorted(ofilt.filters) and self.bits==ofilt.bits and self.ptmin==ofilt.ptmin and self.etamin==ofilt.etamin
  
  def setbits(self,bitdict):
    """Compute bits for all filters using a given filter bit dictionary."""
    self.bits = 0
    for filter in self.filters:
      assert filter in bitdict, "Could not find filter '%s' in bitdict = %s"%(filter,bitdict)
      self.bits += bitdict[filter] #.get(filter,0)
    return self.bits
  
  def hasbits(self,bits):
    """Check if a given set of bits contain this filter's set of bits,
    using the bitwise 'and' operator, '&'."""
    return self.bits & bits == self.bits
  
  def matchbits(self,trigObj):
    """Check if trigger object has the same bits."""
    return self.hasbits(trigObj.filterBits)
  
  def match(self,trigObj,recoObj,dR=0.2):
    """Match trigger object (first argument) to reconstructed object (second argument).
    Also check if the reconstructed object passes the offline pT and eta cut."""
    #if isinstance(recoObj,'TrigObj'): trigObj, recoObj = recoObj, trigObj
    return trigObj.DeltaR(recoObj)<dR and recoObj.pt>self.ptmin and abs(recoObj.eta)<self.etamax
  

class TrigObjMatcher:
  """Class to contain trigger filter(s)."""
  
  def __init__(self,triggers,**kwargs):
    
    # TRIGGERS
    trigger = kwargs.get('trigger',None) # type of trigger: 'ditau', 'SingleMuon', ...
    if isinstance(triggers,str) and trigger: # JSON file
      trigdata = loadTriggerDataFromJSON(triggers,isdata=kwargs.get('isdata',True))
      triggers = trigdata.combdict[trigger]
    if not isinstance(triggers,list):
      triggers = [triggers]
    assert triggers and all(isinstance(t,Trigger) for t in triggers),\
      "Triggers should be a list of instances of the 'Trigger' class! Received: %r."%(triggers)
    
    # SET BITS & SANITY CHECKS
    nlegs    = len(triggers[0].filters) # one filter per leg
    ids      = [ ]
    types    = [ ]
    ptmins   = [ ]
    bits     = 0
    for itrig, trigger in enumerate(triggers):
      if itrig!=0 and len(trigger.filters)!=nlegs:
        raise IOError("Triggers '%s' and '%s' do not have the same number of filters; %d and %d, resp."%(
                      triggers[0].path,trigger.path,nlegs,len(trigger.filters)))
      for ifilt, filter in enumerate(trigger.filters):
        if itrig==0:
          ids.append(filter.id)
          types.append(filter.type)
          ptmins.append(filter.ptmin)
          bits = bits | filter.bits # bitwise 'OR' combination
        else:
          if filter.ptmin<ptmins[ifilt]:
            ptmins[ifilt] = filter.ptmin
          if filter.id!=ids[ifilt]:
            raise IOError("Filter ID does not correspond between triggers '%s' (%d) and '%s' (%d)"%(
                          triggers[0].path,ids[ifilt],trigger.path,filter.id))
    
    # TRIGGER COMBINATION
    patheval = ""
    for trigger in triggers:
      if patheval!="":
        patheval += " or "
      if ' and ' in trigger.patheval or ' or ' in trigger.patheval:
        patheval += '('+trigger.patheval+')'
      else:
        patheval += trigger.patheval
    path    = patheval.replace("e.",'').replace(" or "," || ").replace(" and "," && ")
    firedef = "self.fired = lambda e: "+patheval
    
    self.triggers = triggers       # list of triggers
    self.nlegs    = nlegs          # number of legs = number of filters
    self.ids      = ids            # list of nanoAOD object ID, one per leg
    self.types    = types          # list of nanoAOD object type, one per leg
    self.ptmins   = ptmins         # list of smallest minimum pT, one per legs
    self.bits     = bits           # bitwise 'OR'-combination of all filter bits
    self.path     = path           # human readable trigger combination
    self.patheval = patheval       # trigger evaluation per event 'e'
    self.fireddef = firedef        # exact definition of 'fired' function
    exec self.fireddef in locals() # method to check if any of the triggers was fired for a given event
  
  def __repr__(self):
    """Returns string representation of TriggerFilter object."""
    return "<%s('%s') at %s>"%(self.__class__.__name__,self.path,hex(id(self)))
  
  def printTriggersAndFilters(self,indent=">>> "):
    """Print triggers & their respective filters."""
    for trigger in self.triggers:
      trigstr = indent + "'%s'"%trigger.path
      if trigger.runrange:
        trigstr += ", %d <= run <= %d"%(trigger.runrange[0],trigger.runrange[1])
      print trigstr
      for i, filter in enumerate(trigger.filters,1):
        print "%s  leg %d: %s, %r"%(indent,i,filter.type,filter.name)
  
  def match(self,event,recoObj,leg=1,dR=0.2):
    """Match given reconstructed object to trigger objects."""
    leg     -= 1 # index starting at 0
    trigObjs = [o for o in Collection(event,'TrigObj') if o.id==self.ids[leg]] # and (o.filterBits&self.bits)>0
    for trigger in self.triggers:
      if not trigger.fired(event): continue
      for trigObj in trigObjs:
        if trigger.filters[leg].matchbits(trigObj) and trigger.filters[leg].match(trigObj,recoObj,dR=dR):
          return trigObj
    return None
  
