from array import array
import numpy as np
import ROOT

class Histogram:
    def __init__(self, th1_hist):
        n_bins = th1_hist.GetNbinsX()
        self.values = np.zeros(n_bins)
        self.errors = np.zeros(n_bins)
        self.edges = np.zeros(n_bins + 1)
        for n in range(n_bins):
            self.values[n] = th1_hist.GetBinContent(n + 1)
            self.edges[n] = th1_hist.GetBinLowEdge(n + 1)
            self.errors[n] = th1_hist.GetBinError(n + 1)
        self.edges[n_bins] = th1_hist.GetBinLowEdge(n_bins + 1)

    @staticmethod
    def CreateTH1(values, edges, errors, fixed_step=False):
        if fixed_step:
            th1_hist = ROOT.TH1F('', '', len(values), edges[0], edges[-1])
        else:
            th1_hist = ROOT.TH1F('', '', len(edges) - 1, array('f', edges))
        for n in range(len(values)):
            th1_hist.SetBinContent(n + 1, values[n])
            th1_hist.SetBinError(n + 1, errors[n])
        return th1_hist

class Graph:
    def __init__(self, **kwargs):
        if 'root_graph' in kwargs:
            graph = kwargs['root_graph']
            print(type(graph))
            n_points = graph.GetN()
        elif 'n_points' in kwargs:
            graph = None
            n_points = kwargs['n_points']
        else:
            raise RuntimeError("Invalid arguments for Graph init")

        self.x = np.zeros(n_points)
        self.x_error_low = np.zeros(n_points)
        self.x_error_high = np.zeros(n_points)
        self.y = np.zeros(n_points)
        self.y_error_low = np.zeros(n_points)
        self.y_error_high = np.zeros(n_points)

        if graph is not None:
            for n in range(n_points):
                self.x[n] = graph.GetX()[n]
                self.x_error_low[n] = graph.GetErrorXlow(n)
                self.x_error_high[n] = graph.GetErrorXhigh(n)
                self.y[n] = graph.GetY()[n]
                self.y_error_low[n] = graph.GetErrorYlow(n)
                self.y_error_high[n] = graph.GetErrorYhigh(n)

    def ToRootGraph(self, n_active_points=None):
        n_points = n_active_points if n_active_points is not None else len(self.x)
        return ROOT.TGraphAsymmErrors(n_points, array('d', self.x), array('d', self.y),
                                      array('d', self.x_error_low), array('d', self.x_error_high),
                                      array('d', self.y_error_low), array('d', self.y_error_high))

class MultiGraph:
    def __init__(self, n_graphs, n_points):
        self.x = np.zeros(n_points)
        self.x_error_low = np.zeros(n_points)
        self.x_error_high = np.zeros(n_points)
        self.y = np.zeros((n_graphs, n_points))
        self.y_error_low = np.zeros((n_graphs, n_points))
        self.y_error_high = np.zeros((n_graphs, n_points))

    def ToRootGraphs(self, n_active_points=None):
        n_points = n_active_points if n_active_points is not None else self.x.shape[0]
        root_graphs = []
        for n in range(self.y.shape[0]):
            graph = ROOT.TGraphAsymmErrors(n_points, array('d', self.x), array('d', self.y[n, :]),
                                           array('d', self.x_error_low), array('d', self.x_error_high),
                                           array('d', self.y_error_low[n, :]), array('d', self.y_error_high[n, :]))
            root_graphs.append(graph)
        return root_graphs
