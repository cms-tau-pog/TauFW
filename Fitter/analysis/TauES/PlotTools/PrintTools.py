#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Izaak Neutelings (2017)

import sys, re
from math import log
from cStringIO import StringIO # for stdout capturing
# TODO http://stackoverflow.com/questions/16571150/how-to-capture-stdout-output-from-a-python-function-call



text_color_dict = {
    'black'     : 30,   'red'       : 31,
    'green'     : 32,   'yellow'    : 33,   'orange' : 33,
    'blue'      : 34,   'purple'    : 35,
    'magenta'   : 36,   'grey'      : 37,
}


background_color_dict = {
    'black'     : 40,   'red'       : 41,
    'green'     : 42,   'yellow'    : 43,   'orange' : 43,
    'blue'      : 44,   'purple'    : 45,
    'magenta'   : 46,   'grey'      : 47,
}



def color(string,color0='red',**kwargs):
    """Color"""
    color0     = kwargs.get('color',color0)
    # http://stackoverflow.com/questions/287871/print-in-terminal-with-colors-using-python
    bold_code  = kwargs.get('bold',False)
    color_code = "%d;%d;%d"%( bold_code, text_color_dict[color0], background_color_dict[kwargs.get('background',"black")])
    return kwargs.get('pre',"") + "\x1b[%sm%s\033[0m"%(color_code, string )
    


def warning(string,*trigger,**kwargs):
    if len(trigger)==0 or trigger[0]:
        return color(kwargs.get('exclamation',"Warning! ")+string, 'yellow', bold=True, pre=">>> "+kwargs.get('pre',""))
    


def error(string,*trigger,**kwargs):
    if len(trigger)==0 or trigger[0]:
        return color(kwargs.get('exclamation',"ERROR! ")+string, 'red', bold=True, pre=">>> "+kwargs.get('pre',""))
    


def printVerbose(string,verbosity,level=False,**kwargs):
    """Print string if verbosity is true or verbosity int is lager than given level."""
    if level:
      if verbosity>=level:
        print kwargs.get('pre',"") + string
    elif verbosity:
      print kwargs.get('pre',"") + string
    


def printSameLine(string):
    """Print string without making new line. (Write to stdout and flush.)"""
    #http://stackoverflow.com/questions/3249524/print-in-one-line-dynamically
    if string: string = string+" "
    sys.stdout.write(string)
    sys.stdout.flush()
    


def header(header0):
    """Returns formatted header"""
    
    return ( ">>>\n>>>\n" +
             ">>>   ###%s\n"    % ('#'*(len(header0)+3)) +
             ">>>   #  %s  #\n" % (header0) +
             ">>>   ###%s\n"    % ('#'*(len(header0)+3)) +
             ">>>" )
    




class capturing(object):
    """Capture standard output"""

    def __init__(self,**kwargs):
        self.old_stdout = sys.stdout
        self.old_stderr = sys.stderr
        self.captured0 = StringIO()
        sys.stdout = self.captured0
        sys.stderr = self.captured0

    def stop(self):
        sys.stdout = self.old_stdout
        sys.stderr = self.old_stderr
        self.captured0.close()

    def captured(self):
        sys.stdout = self.old_stdout
        sys.stderr = self.old_stderr
        out = self.captured0.getvalue()
        if '\n' in out[-2:]: out = out[:-1]
        self.captured0.close()
        return out
    




class LoadingBar(object):
    """Class to make a simple, custom loading bar."""
    # from math import log, import sys
    # TODO: move cursor to end (to prevent breaks)

    def __init__(self, *args, **kwargs):
        '''Constructor for LoadingBar object.'''
        self.steps      = 10
        if len(args)>0 and isinstance(args[0],int) and args[0]>0: self.steps = args[0]
        self.tally      = 0
        self.position   = 0
        self.steps      = max(kwargs.get('steps',   self.steps      ),1)
        self.width      = max(kwargs.get('width',   self.steps      ),1)
        self.counter    = kwargs.get('counter',     False           )
        self.counterformat = "%%%ii"%(log(self.steps,10)+1)
        self.remove     = kwargs.get('remove',      False           )
        self.symbol     = kwargs.get('symbol',      "="             )
        self.prepend    = kwargs.get('pre',         ">>> "          )
        self.append     = kwargs.get('append',      ""              )
        self.message_   = kwargs.get('message',     ""              )
        self.done       = False
        if self.counter: self.counter = " %s/%i" % (self.counterformat%self.tally,self.steps)
        else:            self.counter = ""
        sys.stdout.write("%s[%s]" % (self.prepend," "*self.width))
        sys.stdout.flush()
        sys.stdout.write("\b"*(self.width+1)) # return to start of line, after '['
        if self.counter: self.updateCounter()
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
        if self.counter: self.updateCounter()
        if message: self.message(message)
        if self.tally >= self.steps:
            if self.append: self.message(self.append,moveback=self.remove)
            if self.remove:
                sys.stdout.write("\b"*(self.width+1+len(self.prepend)))
                sys.stdout.write(' '*(len(self.prepend)+self.width+len(self.counter)+len(self.message_)+4))
                sys.stdout.write("\b"*(len(self.prepend)+self.width+len(self.counter)+len(self.message_)+4))
            elif not self.append: self.message("\n")
            self.done = True

    def updateCounter(self,**kwargs):
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
    


def makeThreshold(n,**kwargs):
    """Help function to find a good stepsize for read out when looping over a large number N.
       In a for loop with index i, you could do a print out like:
         if i % threshold == 0: print "some progress message" """
    max_digits = kwargs.get('max',6)
    #                      floor(log(N/10.0,10))        stepsize = (number of digits in N) - 2
    #              max(0.0,floor(log(N/10.0,10)))       make sure it is at least 0
    #        min(6,max(0.0,floor(log(N/10.0,10))))      set maximum step size to 10^6 (otherwise one has to wait too long for an update)
    # pow(10,min(6,max(0.0,floor(log(N/10.0,10)))))     make treshold a power of 10
    return pow(10,min(max_digits,max(0.0,floor(log(n/10.0,10)))))
    


def printRow(*values,**kwargs):
    '''Help function to print bin errors'''
    widths          = kwargs.get('widths',[14])
    width           = kwargs.get('width',widths[0])
    precision       = kwargs.get('precision',3)
    prefix          = kwargs.get('prepend',"  ")
    appendix        = kwargs.get('append',"  ")
    line            = kwargs.get('line',"")
    row             = ">>> "+prefix
    pattern_float   = "%%%d.%df"%(width,precision)
    pattern_int     = "%%%dd"   %(width)
    pattern_string  = "%%%ds"   %(width)
    for i, value in enumerate(values):
        if len(widths)>1:
            index = min(i,len(widths)-1)
            pattern_float   = "%%%d.%df"%(widths[index],precision)
            pattern_int     = "%%%dd"   %(widths[index])
            pattern_string  = "%%%ds"   %(widths[index])
        if   isinstance(value,str):   row += pattern_string%(value)
        elif isinstance(value,int):   row += pattern_int%(value)
        elif isinstance(value,float): row += pattern_float%(value)
    if "above" in line: print ">>> "+'-'*(len(row+appendix)+int(width/4))
    print row + appendix
    if "below" in line: print ">>> "+'-'*(len(row+appendix)+int(width/4))
    


def printBinError(hist,**kwargs):
    '''Help function to print bin errors'''
    N       = hist.GetNbinsX()
    mini    = max(kwargs.get('mini',1),0)
    maxi    = min(kwargs.get('maxi',N),N+1)
    #mina    = kwargs.get('min',hist.FindBin(mini))
    #maxb    = kwargs.get('max',hist.FindBin(maxi))
    print ">>>   %4s  %8s  %8s  %8s" % ("bin","content","error",hist.GetName())
    for i in range(mini,maxi):
        print ">>>   %4s  %8.4f  %8.4f" % (i,hist.GetBinContent(i),hist.GetBinError(i))


class Table(object):
    """Class to print a simple table. Initialize as
         - Table(str rowformat)
         - Table(int nColumns)
         - Table(int nColumns, int width)
    """
    
    def __init__(self, *args, **kwargs):
        self.rowformat    = ""
        if len(args)==1 and isinstance(args[0],str):
          self.rowformat  = args[0]
        elif len(args)==1 and isinstance(args[0],int):
          self.rowformat  = " %11s"*args[0]
        elif len(args)==2 and isinstance(args[0],int) and isinstance(args[1],int):
          self.rowformat  = (" %%%ds"%args[1])*args[0]
        else:
          print warning("Table: unrecognized initialization %s"%(args))
        self.headerformat = re.sub(r"%(-?\d+)\.?\d*[fgdi]",r"%\1s",self.rowformat).replace('%0','%')
        self.nColums      = self.rowformat.replace('%%','').count('%')
        self.rows         = [ ]
    
    def __str__(self):
        return '\n'.join(self.rows)
        
    def printTable(self):
        for r in self.rows: print r
        
    def header(self,*args,**kwargs):
        """Header for table which is assumed to be all strings."""
        if len(args)!=self.nColums:
          print error("Table::header: number of argument (%d) != nColumns (%d)"%(len(args),self.nColums))
          exit(1)
        if kwargs.get('save',True):
          self.rows.append(self.headerformat%args)
        else:
          print self.headerformat%args
        
    def row(self,*args,**kwargs):
        """Row for table which is assumed to be of the datatype corresponding to the given row format."""
        if len(args)!=self.nColums:
          print warning("Table::header: number of argument (%d) != nColumns (%d)"%(len(args),self.nColums))
          exit(1)
        if kwargs.get('save',True):
          self.rows.append(self.headerformat%args)
        else:
          print self.headerformat%args
    


class Logger(object):
    """Class to customly log program."""
    
    def __init__(self, *args, **kwargs):
        self.name   = args[0] if args else "unnamed logger"
        self.pre    = ">>> "
        self._table  = None
        
    def info(self,string,**kwargs):
        """Info"""
        print self.pre+string
        
    def color(self,*args,**kwargs):
        """Color"""
        print self.pre+color(*args,**kwargs)
        
    def warning(self,string,*args,**kwargs):
        """Warning"""
        if len(args)==0 or args[0]:
          print color(kwargs.get('exclamation',"Warning! ")+string,'yellow', bold=True, pre=self.pre+kwargs.get('pre',""))
        
    def title(self,*args,**kwargs):
        print header(*args,**kwargs)
        
    def header(self,*args,**kwargs):
        print header(*args,**kwargs)
        
    def error(self,string,*args,**kwargs):
        """Error"""
        if len(args)==0 or args[0]:
          print color(kwargs.get('exclamation',"ERROR! ")+string,'red', bold=True, pre=self.pre+kwargs.get('pre',""))
        
    def fatal(self,*args,**kwargs):
        """Fatalerror"""
        self.error(*args,**kwargs)
        exit(1)
        
    def verbose(self,*args,**kwargs):
        """Verbose"""
        kwargs['pre'] = pre=self.pre+kwargs.get('pre',"")
        printVerbose(*args,**kwargs)
        
    def table(self,format,**kwargs):
        """Initiate new table."""
        self._table = Table(format)
        
    def theader(self,*args):
        """Print header of table."""
        self._table.header(*args)
        
    def row(self,*args):
        """Print row of table."""
        self._table.row(*args)
        
    # TODO table with memorized column sizes from header




