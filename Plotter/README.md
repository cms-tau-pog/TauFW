# TauFW Plotter

### Table of Contents  
* [Installation](#Installation)<br>
* [Basic plots](#Basic-plots)<br>
* [CMS style](#CMS-style)<br>
* [Variable](#Variable)<br>
* [Sample](#Sample)<br>

## Installation
See [the README.md in the parent directory](../../../#taufw).


## Basic plots

### Histogram comparisons
Some classes are provided to facilitate making plots in CMS style.
If you have a list of histograms, `hists`, you want to compare with a ratio plot,
use the [`Plot`](python/plot/Plot.py) class, e.g.
```
from TauFW.Plotter.plot.Plot import Plot, CMSStyle
CMSStyle.setCMSEra(2018)
plot = Plot("x",hists)
plot.draw(ratio=True,grid=True,logy=True)
plot.drawlegend()
plot.saveas("plot.png")
plots.close
```

<p align="center" vertical-align: middle>
  <img src="../docs/testHists.png" alt="Gaussians with Plot class" width="420" hspace="20"/>
  <img src="../docs/testHists_ratio_logy.png" alt="Gaussians with Plot class and ratio plot" width="420"/>
</p>

### Data-MC comparisons
If you want to make a data-MC comparison between a data histogram `datahist` and
a list of expected SM processes, `exphists`,
you can use the [`Stack`](python/plot/Stack.py) class, with something like
```
from TauFW.Plotter.plot.Stack import Stack, CMSStyle
CMSStyle.setCMSEra(2018)
plot = Stack("p_{T} [GeV]",datahist,exphists)
plot.draw(ratio=True,logy=False)
plot.drawlegend()
plot.drawtext("#mu#tau_{h} baseline")
plot.saveas("stack.png")
plot.saveas("stack.pdf")
plots.close
```

More examples of usage of `Plot` and `Stack` are provided in [`test/`](test/), run as
```
test/plotHists.py -v 2
test/plotStacks.py -v 2
```

<p align="center">
  <img src="../docs/testStacks_m_vis_ratio.png" alt="Data-MC with Stack class" width="420" hspace="20"/>
  <img src="../docs/testStacks_njets_ratio_logy.png" alt="Data-MC comparison with Stack class" width="420"/>
</p>


## CMS style
[CMSStyle.py](python/plot/CMSStyle.py) provides tools to make a plot have the CMS style.
The luminosity and center-of-mass energy are automatically set for a given year,
```
CMSStyle.setCMSEra(2018)
```
but can be manually set as
```
CMSStyle.setCMSEra(2018,lumi=59.7,cme=13,extra="Preliminary")
```


## Variable
A [`Variable`](python/plot/Variable.py) class is provided to contain variable name (e.g. `pt_1`),
title (e.g. `Leading p_{T} [GeV]`) and the binning (`(nbins,xmin,xmax)` or a list for variable binning), for example:
```
from TauFW.Plotter.plot.Variable import Variable
variables = [
  Variable('pt_1',  "p_{T} [GeV]",   40, 0,200),
  Variable('m_vis', "m_{vis} [GeV]", [0,20,40,50,60,65,70,75,80,85,90,100,120,150]),
  Variable('njets', "Number of jets", 8, 0,  8),
]
```
A `Variable` object can contain a lot of information, passed as key-word arguments that are
useful when making plots (e.g. `ymin`, `ymax`, `logx`, `logy`, `ymargin`, ...)
or selection strings (e.g. `cut`, `blind`, `weight`, ...).
It also has several handy functions that provide shortcuts for common routines.
For example, `Variable.gethist` can create a histogram for you:
```
hist = var.gethist()
```
and `Variable.drawcmd` can parse a draw command for [`TTree::Draw`](https://root.cern.ch/doc/master/classTTree.html#a73450649dc6e54b5b94516c468523e45):
```
var  = Variable('pt_1',40,0,200)
hist = var.gethist('hist') # returns a TH1D
dcmd = var.drawcmd('hist') # returns a string, e.g. "pt_1 >> hist"
tree.Draw(dcmd)            # loops over tree events and fills the histogram 'hist'
```
It can also be used to initialize a `Plot` or `Stack` object, e.g.
```
var  = Variable('pt_1',40,0,200,logy=True,ymargin=1.4)
plot = Plot(var,hists)
```
Examples are provided in [`test/testVariables.py`](test/testVariables.py).


## Sample
A [`Sample`](python/sample/Sample.py) class is provided to contain a sample' information,
like title (for legends), filename, cross section, normalization, etc.
```
sample = Sample("TT,"t#bar{t}","TT.root",831.76)
```
It provides a useful method that can draw many histograms in parallel for you,
using [`MultiDraw`](python/plot/MultiDraw.py):
```
hists  = sample.gethist(variables,"pt_1>30 && pt_2>30")
```
where `variables` is a list of variables as above, and the returned `hists` is a list of `TH1D`s.

You can also split samples into subsamples based on some cut, e.g.
```
sample.split([
  ('ZTT',"real tau","genmatch_2==5"),
  ('ZJ', "fake tau","genmatch_2!=5"),
])
hists = { }
for subsample in sample.splitsamples:
  hists[subsample] = subsample.gethist(variables,"pt_1>50")
```
Examples are provided in [`test/testSamples.py`](test/testSamples.py).
