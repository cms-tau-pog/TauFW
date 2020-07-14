# -*- coding: utf-8 -*-
# Author: Izaak Neutelings (2017)
import re

formatrexp = re.compile(r"(%(-?\d*)\.?\d*[sfgdir])")
class Table(object):
  """
  Class to print a simple table. Initialize as
    - Table(str rowformat)
    - Table(str headerformat, str rowformat)
    - Table(int ncols)
    - Table(int ncols, int colwidth)
  where rowformat is a string formatting the rows with `%`, e.g.
    ">>> %-20d %-10d %-10.3f"
  """
  
  def __init__(self, *args, **kwargs):
    self.rowformat      = ""
    self.headerformat   = ""
    self.ncols          = 0
    self.ncols_header   = 0
    self.colwidth       = 11
    self.pre            = kwargs.get('pre',  ">>> ")
    self.verbosity      = kwargs.get('verb', 0     )
    self.level          = kwargs.get('level',0     ) # verbosity threshold to print
    if len(args)==1 and isinstance(args[0],str):
      self.rowformat    = args[0]
    elif len(args)==2 and isinstance(args[0],str) and isinstance(args[1],str):
      self.headerformat = args[0]
      self.rowformat    = args[1]
    elif len(args)==1 and isinstance(args[0],int):
      self.ncols        = args[0]
    elif len(args)==2 and isinstance(args[0],int) and isinstance(args[1],int):
      self.ncols        = args[0]
      self.colwidth     = args[1]
    else:
      LOG.warning("Table.__init__: unrecognized arguments for initialization: %r"%(args))
    if not self.rowformat:
      self.rowformat    = (" %%%ds"%self.colwidth)*self.ncols
    if not self.headerformat:
      self.headerformat = formatrexp.sub(r"%\2s",self.rowformat).replace('%0','%')
    if not self.ncols:
      self.ncols        = self.rowformat.replace('%%','').count('%')
      self.ncols_header = self.headerformat.replace('%%','').count('%')
    else:
      self.ncols_header = self.ncols
    if kwargs.get('ul',True): # underline
      self.headerformat = "\033[4m%s\033[0m"%(self.headerformat)
    if self.pre: # underline
      self.headerformat = self.pre + self.headerformat
      self.rowformat    = self.pre + self.rowformat
    self.rows           = [ ]
    self.columnformats  = [ ]
    matches = formatrexp.findall(self.rowformat)
    assert len(matches)==self.ncols, "Number of recognized columns in the row pattern (%d) is not the same as the set number of columns (%d)"%(len(matches),self.ncols)
    ilast = len(self.rowformat)
    for i, match in reversed(list(enumerate(matches))): # remove last nlast columns from row format
      icol = self.rowformat[:ilast].rfind(match[0]) if i>0 else 0
      self.columnformats.insert(0,self.rowformat[icol:ilast])
      ilast = icol
    if self.verbosity>=self.level+3:
      print ">>> headerformat=%r, rowformat=%r"%(self.headerformat,self.rowformat)
      print ">>> columnformats=%s, ncols=%r"%(self.columnformats,self.ncols)
  
  def __str__(self):
    return '\n'.join(self.rows)
  
  def printtable(self):
    """Print full table."""
    for r in self.rows:
      print r
  
  def printheader(self,*args,**kwargs):
    """Print row."""
    if self.verbosity>=self.level:
      print self.header(*args,**kwargs)
  
  def printrow(self,*args,**kwargs):
    """Print row."""
    if self.verbosity>=self.level:
      print self.row(*args,**kwargs)
  
  def header(self,*args,**kwargs):
    """Header for table which is assumed to be all strings."""
    format = self.headerformat
    if len(args)!=self.ncols_header:
      LOG.warning("Table.header: number of argument (%d) != ncols_header (%d)"%(len(args),self.ncols_header))
    string = format%(args[:self.ncols_header]) + kwargs.get('post',"")
    if kwargs.get('save',False):
      self.rows.append(string)
    return string
  
  def row(self,*args,**kwargs):
    """Row for table which is assumed to be of the datatype corresponding to the given row format."""
    format = self.rowformat
    if len(args)<self.ncols:
      #LOG.warning("Table.row: number of argument (%d) != ncols (%d)"%(len(args),self.ncols))
      format = ''.join(self.columnformats[:len(args)])
    string = format%(args[:self.ncols])
    if len(args)>self.ncols:
      string += ' '+' '.join(str(a) for a in args[self.ncols:])
    if kwargs.get('save',False):
      self.rows.append(string)
    return string
  
from TauFW.common.tools.log import LOG