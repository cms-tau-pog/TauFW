#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Izaak Neutelings (2017)
from TauFW.Plotter.plot.utils import LOG


class Context(object):
  """
  Context class to save different objects that depend on a certain context 
  TODO: point to specific attribute ?
  TODO: allow to set context for pattern (e.g. selection string)
  """
  
  def __init__(self, context_dict, *args, **kwargs):
    if not isinstance(context_dict,dict):
      LOG.warning("Context.Context: No dictionary given!")
    self.context = context_dict
    self.default = args[0] if len(args)>0 else context_dict.get('default',None)
    self.regex   = kwargs.get('regex',False)
  
  def __iter__(self):
    """Start iteration over selection information."""
    for i in self.context:
      yield i
  
  def getContext(self,*args,**kwargs):
    """Get the contextual object for a set of ordered arguments. If it is not available, return Default."""
    
    regex = kwargs.get('regex', self.regex)
    
    # CHECK
    if len(args)==0:
      LOG.warning("Context.getContext: No arguments given!")
      return self.default
    if not self.context:
      LOG.warning("Context.getContext: No context dictionary!")
      return None
    
    # MATCH
    ckey   = args[0]
    if ckey.__class__.__name__=='Selection':
      ckey = ckey.selection
    result = None
    if regex:
      for key in sorted(self.context,key=lambda x: len(x) if isinstance(x,str) else 1,reverse=True):
        #LOG.verbose('Context.getContext: Matching "%s" to "%s"'%(key,ckey),True)
        if key==ckey or (isinstance(key,str) and isinstance(ckey,str) and re.search(key,ckey)):
          #LOG.verbose('Context.getContext: Regex match of key "%s" to "%s"'%(key,ckey),True)
          ckey = key
          result = self.context[ckey]
          break
      else:
        result = self.default # TODO: check for multiple args !
    elif ckey not in self.context:
      result = self.default
    else:
      result = self.context[ckey]
    
    # RESULT
    if isinstance(result,Context):
      return result.getContext(*args[1:],**kwargs) # recursive
    elif len(args)>1 and result==self.default:
      return self.getContext(*args[1:],**kwargs) # recursive
    return result
  

def getContextFromDict(contextdict,*default,**kwargs):
  """Check for context in contextdict. If a dictionary is given, make a Context object. Else return None."""
  ckey    = kwargs.get('key',     'context')
  regex   = kwargs.get('regex',   False    )
  context = contextdict.get(ckey, None     ) # context-dependent
  if isinstance(context,Context):
    return context
  if isinstance(context,dict):
    if len(default)==0: default = context.get('default', None)
    else: default = default[0]
    context = Context(context,default,regex=regex)
    return context
  elif not context:
    return None
  LOG.error('No valid arguments "%s"'%(args))
  return None

