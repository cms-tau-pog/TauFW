# TauFW Plotter

## Installation

See [the README.md in the parent directory](../../../#taufw).


## Simple plots

Some classes are provided to facilitate making plots in CMS style.
If you have a list of histograms, `hists`, you want to compare with a ratio plot,
use the [`Plot`](python/plot/Plot.py) class, e.g.
```
from TauFW.Plotter.plot.Plot import Plot, CMSStyle
CMSStyle.setCMSEra(2018)
plot = Plot("x",hists)
plot.plot(ratio=True,grid=True)
plot.setlegend()
plot.saveas("plot.png")
plots.close
```
If you want to make a data-MC comparison between a data histogram `datahist` and
a list of expected SM processes, `exphists`,
you can use the [`Stack`](python/plot/Stack.py) class, with something like
```
from TauFW.Plotter.plot.Stack import Stack, CMSStyle
CMSStyle.setCMSEra(2018)
plot = Stack("p_{T}",datahist,exphists)
plot.plot(ratio=True)
plot.setlegend()
plot.saveas("stack.png")
plots.close
```
More examples of usage are provided in [`test/`](test/).
