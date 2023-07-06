from plotfit import *

def LegendSettings(leg):
  leg.SetBorderSize(0)
  leg.SetTextSize(0.032)
  leg.SetLineColor(0)
  leg.SetLineStyle(1)
  leg.SetLineWidth(0)
  leg.SetFillColor(0)
  leg.SetFillStyle(0)

def makeLatex(string):
  for var in var_dict:
    string = string.replace(var,var_dict[var])
  for wp,Wp in [("vvlo","VVLo"),("vlo","VLo"),("lo","Lo"),("me","Me"),
                ("vvti","VVTi"),("vti","VTi"),("ti","Ti")]:
    if wp in string:
      string = string.replace(wp,Wp)
  #if '_' in string:
  #  string = re.sub(r"\b([^_]*)_([^_]*)\b",r"\1_{\2}",string,flags=re.IGNORECASE)
  return string

def returnsf(idx, graph):
  # print graph, idx
  _x_ = Double(0.)
  _y_ = Double(0.)
  graph.GetPoint(idx,_x_,_y_)
  return _y_

def returnsf_up(idx, graph):
  #print 'up', idx, graph.GetName(), graph.GetErrorYhigh(idx)
  return returnsf(idx, graph) + graph.GetErrorYhigh(idx)
  return graph.GetErrorYhigh(idx)

def returnsf_down(idx, graph):
  print 'down', idx, graph.GetName(), graph.GetErrorYhigh(idx)
  return returnsf(idx, graph) - graph.GetErrorYlow(idx)
  #return graph.GetErrorYlow(idx)

def returnsf_unc(idx, graph):
  return graph.GetErrorYhigh(idx)

def main(args):
  #file_new = open('log_dm_20210618')
  #file_prev = open('log_dm_20191114')
  graphs = {}
  #graphs_prev = {}
  cols = [1,2,4,6]
  wpdict = {
    '0': 0,
    '1': 1,
    '10':2,
    '11':3
  }
  yearshift={
    '2016':-0.1,
    '2016_preVFP':-0.12,
    '2016_postVFP':-0.08,
    '2017':0.,
    'UL2018':0.0,
  }
  year2draw = []
  pulldirs = {}
  jobdir='log/'
  #for year in ['2016_preVFP', '2016_postVFP', '2017', '2018']:
  for year in ['UL2018']:
    for dm in ['0', '1', '10', '11']:
      for wp in ['VVVLoose', 'VVLoose', 'VLoose', 'Loose', 'Medium', 'Tight', 'VTight', 'VVTight']:
        wplabel = year+'_'+wp
        binlabel = year+'_'+wp+'_dm'+dm
        #ex. ztt_Loose_UL2018_dm0.log
        file = open(jobdir+'/ztt_'+wp+'_'+year+'_dm'+dm+'.log')
        for line in file:
          line = line.rstrip()
          words = line.split()
          #if line.find('setting')!=-1:
          #  pulldirs[binlabel] = {'titles':[],
          #                        'vals':[],
          #                        'errs':[]}
          #  if year not in year2draw:
          #      year2draw.append(year)
          #  if not graphs.has_key(wplabel):
          #      graph = TGraphAsymmErrors()
          #      graphs[wplabel] = {'count':0, 'graph':graph}
          if line.find('ZTT_mu')!=-1:
            
            pulldirs[binlabel] = {'titles':[],
                                  'vals':[],
                                  'errs':[]}
            if year not in year2draw:
              year2draw.append(year)
            if not graphs.has_key(wplabel):
              graph = TGraphAsymmErrors()
              graphs[wplabel] = {'count':0, 'graph':graph}
            
            val = Double(words[2])
            errval_up = Double(words[4])
            errval_down = Double(words[4])
            if len(words)==6:
              errval_up = Double(words[4])
              errval_down = Double(words[5])
            #print year, wp, '(pT = ', wprange[pt]['low'], '-', wprange[pt]['up'], ')', '{0:.3f}'.format(val), '+{0:.3f}'.format(errval_up), ' / -{0:.3f}'.format(errval_down)
            #print 'SetPoint', graphs[year + '_' + wp]['count'], Double(wpdict[pt]), val
            graphs[wplabel]['graph'].SetPoint(graphs[wplabel]['count'], Double(wpdict[dm]) + Double(yearshift[year]), val)
            graphs[wplabel]['graph'].SetPointError(graphs[wplabel]['count'], 0, 0, abs(errval_up), abs(errval_down))
            graphs[wplabel]['count'] += 1
          elif line.find('CMS_')!=-1 or line.find('shape_')!=-1:
            pulldirs[binlabel]['titles'].append(words[0])
            pulldirs[binlabel]['vals'].append(words[2])
            pulldirs[binlabel]['errs'].append(words[4])
        
  ###for line in file_new:
  ###    line = line.rstrip()
  ###    words = line.split()
  ###    if line.find('setting')!=-1:
  ###        year = words[1].replace('2016_preVFP','2016')
  ###        wp = words[2]
  ###        dm = words[3]
  ###        if not graphs.has_key(year + '_' + wp):
  ###            graph = TGraphAsymmErrors()
  ###            graphs[year + '_' + wp] = {'count':0, 'graph':graph}
  ###        if year not in year2draw:
  ###            year2draw.append(year)
  ###    if line.find('ZTT_mu')!=-1:
  ###        val = Double(words[2])
  ###        errval_up = Double(words[4])
  ###        errval_down = Double(words[4])
  ###        if len(words)==6:
  ###            errval_up = Double(words[4])
  ###            errval_down = Double(words[5])
  ###        #print year, wp, '(pT = ', wprange[pt]['low'], '-', wprange[pt]['up'], ')', '{0:.3f}'.format(val), '+{0:.3f}'.format(errval_up), ' / -{0:.3f}'.format(errval_down)
  ###        #print 'count = ', graphs[year + '_' + wp]['count'], '(x,y) = ', Double(wpdict[wp]), val, '-', val_down, '+', val_up
  ###        print 'old ... SetPoint', graphs[year + '_' + wp]['count'], Double(wpdict[dm]), val
  ###        graphs[year + '_' + wp]['graph'].SetPoint(graphs[year + '_' + wp]['count'], Double(wpdict[dm]) + Double(yearshift[year]), val)
  ###        graphs[year + '_' + wp]['graph'].SetPointError(graphs[year + '_' + wp]['count'], 0, 0, abs(errval_up), abs(errval_down))
  ###        graphs[year + '_' + wp]['count'] += 1
  
 # for line in file_prev:
 #   line = line.rstrip()
 #   words = line.split()
 #   if line.find('setting')!=-1:
 #     year = words[1]
 #     wp = words[2]
 #     dm = words[3]
 #     if not graphs_prev.has_key(year + '_' + wp):
 #       graph_prev = TGraphAsymmErrors()
 #       graphs_prev[year + '_' + wp] = {'count':0, 'graph':graph_prev}
 #   if line.find('ZTT_mu')!=-1:
 #     val = Double(words[2])
 #     errval_up = Double(words[4])
 #     errval_down = Double(words[4])
 #     if len(words)==6:
 #         errval_up = Double(words[4])
 #         errval_down = Double(words[5])
 #     #print year, wp, '(pT = ', wprange[pt]['low'], '-', wprange[pt]['up'], ')', '{0:.3f}'.format(val), '+{0:.3f}'.format(errval_up), ' / -{0:.3f}'.format(errval_down)
 #     #print 'count = ', graphs[year + '_' + wp]['count'], '(x,y) = ', Double(wpdict[wp]), val, '-', val_down, '+', val_up
 #     print 'old ... SetPoint', graphs_prev[year + '_' + wp]['count'], Double(wpdict[dm]), val
 #     graphs_prev[year + '_' + wp]['graph'].SetPoint(graphs_prev[year + '_' + wp]['count'], Double(wpdict[dm]) + Double(yearshift[year]), val)
 #     graphs_prev[year + '_' + wp]['graph'].SetPointError(graphs_prev[year + '_' + wp]['count'], 0, 0, abs(errval_up), abs(errval_down))
 #     graphs_prev[year + '_' + wp]['count'] += 1
      
  
  wpdict_v2 = dict((v,k) for k,v in wpdict.iteritems())
  ensuredir('plots/dm/')
  for wp in ['VVVLoose', 'VVLoose', 'VLoose', 'Loose', 'Medium', 'Tight', 'VTight', 'VVTight']:
  #for wp in ['Medium', 'Tight']:
    canvas = TCanvas('canvas_' + wp)
    ROOT.gStyle.SetOptStat(0)
    legend = TLegend(0.6, 0.2, 0.9, 0.4)
    LegendSettings(legend)
    frame =  TH2F('frame_' + wp, 'DM dependence', len(wpdict),-0.5,-0.5 + len(wpdict),100,0.,1.5)
    frame.SetMinimum(0.5)
    frame.SetMaximum(1.)
    for ibin in range(1, frame.GetXaxis().GetNbins()+1):
      frame.GetXaxis().SetBinLabel(ibin, 'DM' + wpdict_v2[ibin-1])
      frame.GetXaxis().SetLabelSize(0.065)
    #frame.GetXaxis().SetBinLabel(1, 'VVLoose')
    frame.Draw()
    frame.GetYaxis().SetTitle('Scale Factor')
    frame.GetYaxis().SetNdivisions(505)
    frame.SetTitle(wp )#+ ' (p_{T} #geq 40 GeV inclusive)')
    for idx, year in enumerate(year2draw):
      if not graphs.has_key(year + '_' + wp): continue
      graphs[year + '_' + wp]['graph'].SetLineColor(1)
      graphs[year + '_' + wp]['graph'].SetLineWidth(2)
      graphs[year + '_' + wp]['graph'].SetMarkerColor(2) 
      graphs[year + '_' + wp]['graph'].SetMarkerStyle(73)  
      graphs[year + '_' + wp]['graph'].SetMarkerSize(1) 
      graphs[year + '_' + wp]['graph'].Draw('pe')
        #if options.overlay and year.find('postVFP')==-1:
        #  yearnew = year.replace('_preVFP', '').replace('_postVFP','')
        #  graphs_prev[yearnew + '_' + wp]['graph'].SetLineColor(cols[idx])
        #  graphs_prev[yearnew + '_' + wp]['graph'].SetMarkerColor(cols[idx])
        #  graphs_prev[yearnew + '_' + wp]['graph'].SetMarkerStyle(24)
        #  graphs_prev[yearnew + '_' + wp]['graph'].Draw('pzsame')
        #  legend.AddEntry(graphs_prev[yearnew + '_' + wp]['graph'], yearnew + '(prev)', 'lep')
      legend.AddEntry(graphs[year + '_' + wp]['graph'], year, 'lep')
    #idx += 1
    legend.Draw()
    canvas.Print('plots/dm/sf_' + wp + '.gif')
    canvas.Print('plots/dm/sf_' + wp + '.pdf')
  pullsVertical_noBonly(pulldirs,outdir="plots/pulls_dm")
  
  for idx, year in enumerate(year2draw):
    sfile = TFile('TauID_SF_dm_DeepTau2018v2p5VSjet_' + year + 'UL.root', 'recreate')
    for wp in ['VVVLoose', 'VVLoose', 'VLoose', 'Loose', 'Medium', 'Tight', 'VTight', 'VVTight']:
      hist_cent = ROOT.TH1F(wp, wp, 12,0.,12.)
      hist_cent.GetXaxis().SetTitle('dm')
      hist_cent.GetYaxis().SetTitle('SF (cent)')
      for idx, dm in enumerate(['0', '1', '10', '11']):
        print idx
        hist_cent.SetBinContent(int(dm)+1, returnsf(idx, graphs[year + '_' + wp]['graph']))
        hist_cent.SetBinError(int(dm)+1, returnsf_unc(idx, graphs[year + '_' + wp]['graph']))
      hist_cent.Write()
    sfile.Write()
    sfile.Close()
  

if __name__ == '__main__':
  from argparse import ArgumentParser
  description = '''This script creates plots and ROOT files of the fit results.'''
  parser = ArgumentParser(prog="plotfit_dm",description=description,epilog="Good luck!")
  #parser.add_option("-o", "--outName",  action="store", type="string", dest="outName",  default="pulls"    )
  #parser.add_option("-t", "--text",     action="store", type="string", dest="text",     default=""         )
  #parser.add_option('-f', '--fit', action="store_true", default=False, dest='fit')
  parser.add_argument('-o', '--overlay',  dest='overlay', action="store_true")
  parser.add_argument('-v', '--verbose',  dest='verbosity', type=int, nargs='?', const=1, default=0,
                                          help="set verbosity level" )
  args = parser.parse_args()
  main(args)
