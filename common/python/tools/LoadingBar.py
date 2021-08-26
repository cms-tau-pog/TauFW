# -*- coding: utf-8 -*-
# Author: Izaak Neutelings (2017)
import sys
from math import log10


class LoadingBar(object):
  """Class to make a simple, custom loading bar."""
  # TODO: move cursor to end (to prevent breaks)
  
  def __init__(self, *args, **kwargs):
    '''Constructor for LoadingBar object.'''
    self.steps    = 10
    if len(args)>0 and isinstance(args[0],int) and args[0]>0: self.steps = args[0]
    self.tally    = 0
    self.position = 0
    self.steps    = max(kwargs.get('steps',   self.steps      ),1)
    self.width    = max(kwargs.get('width',   self.steps      ),1)
    self.counter  = kwargs.get('counter',     False           )
    self.counterformat = "%%%ii"%(log10(self.steps)+1)
    self.remove   = kwargs.get('remove',      False           )
    self.symbol   = kwargs.get('symbol',      "="             )
    self.prepend  = kwargs.get('pre',         ">>> "          )
    self.append   = kwargs.get('append',      ""              )
    self.message_ = kwargs.get('message',     ""              )
    self.done     = False
    if self.counter: self.counter = " %s/%i" % (self.counterformat%self.tally,self.steps)
    else:            self.counter = ""
    sys.stdout.write("%s[%s]" % (self.prepend," "*self.width))
    sys.stdout.flush()
    sys.stdout.write("\b"*(self.width+1)) # return to start of line, after '['
    if self.counter: self.update()
    if self.message_: self.message(self.message_)
  
  def count(self,*args,**kwargs):
    """Count one step."""
    if self.done: return
    i = 1.0
    message = ""
    if len(args)>0 and isinstance(args[0],int) and args[0]>0:
      i = args[0]
      args.remove(i)
    if len(args)>0 and isinstance(args[0],str):
      message = args[0]
    i = max(min(i,self.steps-self.tally),0)
    newposition = int(round(float(self.tally+i)*self.width/self.steps))
    step = newposition-self.position
    self.position = newposition
    sys.stdout.write(self.symbol*step)
    sys.stdout.flush()
    self.tally += i
    if self.counter: self.update()
    if message: self.message(message)
    if self.tally>=self.steps:
      if self.append:
        self.message(self.append,moveback=self.remove)
      if self.remove:
        sys.stdout.write("\b"*(self.width+1+len(self.prepend)))
        sys.stdout.write(' '*(len(self.prepend)+self.width+len(self.counter)+len(self.message_)+4))
        sys.stdout.write("\b"*(len(self.prepend)+self.width+len(self.counter)+len(self.message_)+4))
        sys.stdout.flush()
      elif not self.append:
        self.message("\n")
      self.done = True
  
  def update(self,**kwargs):
    """Update the counter."""
    self.counter = " %s/%i" % (self.counterformat%self.tally,self.steps)
    sys.stdout.write("%s]%s" % (' '*(self.width-self.position), self.counter))
    sys.stdout.flush()
    sys.stdout.write("\b"*(self.width+1-self.position+len(self.counter)))
  
  def message(self,newmessage,moveback=True):
    """Append the counter with some progress message."""
    end_ = ""
    if "\n" in newmessage:
      end_ = newmessage[newmessage.index("\n"):]
      newmessage = newmessage[:newmessage.index("\n")]
    self.message_ = newmessage.ljust(len(self.message_))+end_
    sys.stdout.write("%s]%s %s" % (' '*(self.width-self.position), self.counter, self.message_))
    sys.stdout.flush()
    if moveback: sys.stdout.write("\b"*(self.width+2-self.position+len(self.counter)+len(self.message_)))
  
