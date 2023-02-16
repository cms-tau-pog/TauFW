import os, numpy, math, copy, math, collections
import ROOT; ROOT.PyConfig.IgnoreCommandLineOptions = True
from ROOT import gStyle, TCanvas, TLegend, gROOT, TGraphAsymmErrors, Double, TH2F, kBlack, TBox, kGreen, kOrange, TFile, TF1, gMinuit, TColor
import optparse
gROOT.SetBatch(True)
#gROOT.SetBatch(False)
tt = TColor.GetColor(135,206,250)

def returnsf(idx, graph):
  _x_ = Double(0.)
  _y_ = Double(0.)
  graph.GetPoint(idx,_x_,_y_)
  return _y_

def returnsf_up(idx, graph):
  return returnsf(idx, graph) + graph.GetErrorYhigh(idx)
  return graph.GetErrorYhigh(idx)

def returnsf_down(idx, graph):
  print 'down', idx, graph.GetName(), graph.GetErrorYhigh(idx)
  return returnsf(idx, graph) - graph.GetErrorYlow(idx)

def ensuredir(directory):
  if not os.path.exists(directory):
    os.makedirs(directory)

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

def pullsVertical_noBonly(pulldirs,outdir="plots/pulls_pt"):
  print 'making pulls ...'
  for yearwp, val in pulldirs.iteritems():
  #print yearwp
  titles = val['titles']
  vals = val['vals']
  errs = val['errs']
  if len(titles) != len(vals):
    print 'ERROR !!!', len(titles), len(vals)
  nbins, off = len(titles), 0.10
  
  # Graphs
  h_pulls = TH2F("pulls_" + yearwp, "", 6, -3., 3., nbins, 0, nbins)
  S_pulls = TGraphAsymmErrors(nbins)
  boxes = []
  canvas = TCanvas("pcanvas_" + yearwp, "Pulls", 720, 300+nbins*18)#nbins*20)
  canvas.cd()
  canvas.SetGrid(0, 1)
  canvas.SetTopMargin(0.01)
  canvas.SetRightMargin(0.01)
  canvas.SetBottomMargin(0.10)
  canvas.SetLeftMargin(0.40)
  canvas.SetTicks(1, 1)
  
  for idx, title in enumerate(titles):
    h_pulls.GetYaxis().SetBinLabel(idx+1, title.replace('CMS_',''))
    #print idx, vals[idx]
    S_pulls.SetPoint(idx, float(vals[idx]), float(idx+1)-0.5)
    S_pulls.SetPointError(idx, float(errs[idx]), float(errs[idx]),0.,0.)
  
  h_pulls.GetXaxis().SetTitle("(#hat{#theta} - #theta_{0}) / #Delta#theta")
  h_pulls.GetXaxis().SetLabelOffset(0.0)
  h_pulls.GetXaxis().SetTitleOffset(0.8)
  h_pulls.GetXaxis().SetLabelSize(0.045)
  h_pulls.GetXaxis().SetTitleSize(0.050)
  h_pulls.GetYaxis().SetLabelSize(0.046)
  h_pulls.GetYaxis().SetNdivisions(nbins, 0, 0)
  
  S_pulls.SetFillColor(kBlack)
  S_pulls.SetLineColor(kBlack)
  S_pulls.SetMarkerColor(kBlack)
  S_pulls.SetLineWidth(2)
  S_pulls.SetMarkerStyle(20)
  S_pulls.SetMarkerSize(1)
  
  box1 = TBox(-1., 0., 1., nbins)
  #box1.SetFillStyle(3001) # 3001 checkered
  #box1.SetFillStyle(0)
  box1.SetFillColor(kGreen+1) # 417
  box1.SetLineWidth(2)
  box1.SetLineStyle(2)
  box1.SetLineColor(kGreen+1) # 417
  
  box2 = TBox(-2., 0., 2., nbins)
  #box2.SetFillStyle(3001) # 3001 checkered
  #box2.SetFillStyle(0)
  box2.SetFillColor(kOrange) # 800
  box2.SetLineWidth(2)
  box2.SetLineStyle(2)
  box2.SetLineColor(kOrange) # 800
  
  leg = TLegend(0.01, 0.01, 0.3, 0.15)
  leg.SetTextSize(0.05)
  leg.SetBorderSize(0)
  leg.SetFillStyle(0)
  leg.SetFillColor(0)
  #leg.SetNColumns(2)
  leg.AddEntry(S_pulls, "S+B fit", "lp")
  leg.AddEntry(0, yearwp.replace('_', ', '), "")
  
  h_pulls.Draw("")
  box2.Draw()
  box1.Draw()
  S_pulls.Draw("P6SAME")
  leg.Draw()
  canvas.RedrawAxis()
  
  ensuredir(outdir)
  canvas.Print(os.path.join(outdir,yearwp+".gif"))
  canvas.Print(os.path.join(outdir,yearwp+".pdf"))
  
  #############################################################
  #corfile = TFile('root/fitresults_' + yearwp + '.root')
  #corr = corfile.Get('correlation_matrix_channelmu')
  #corrcanvas = TCanvas("corrcanvas_" + yearwp, "corr. coeff")
  ##corrcanvas.cd(0).SetPadRightMargin(0.1)
  #
  #for ix in range(1, corr.GetXaxis().GetNbins()+1):
  #    corr.GetXaxis().SetBinLabel(ix, corr.GetXaxis().GetBinLabel(ix).replace('CMS_', ''))
  #
  #for iy in range(1, corr.GetYaxis().GetNbins()+1):
  #    corr.GetYaxis().SetBinLabel(iy, corr.GetXaxis().GetBinLabel(iy).replace('CMS_', ''))
  #
  #corrcanvas.SetRightMargin(0.13)
  #corrcanvas.SetLeftMargin(0.14)
  #gStyle.SetOptTitle(1)
  #corr.SetTitle(yearwp.replace('_',', '))
  #corr.Draw('colz')
  #corrcanvas.Print('plots/cor_' + yearwp + ".gif")
  #corrcanvas.Print('plots/cor_' + yearwp + ".pdf")   
  

def main(args):
  file_new = open('log_pt_20210618')
  file_prev = open('log_pt_20191114')
  #file = open('log_xs')
  graphs = {}
  graphs_prev = {}
  cols = [1,2,4]
  wpdict = { # average pt per pt bins
      '1':22.553480,
      '2':27.489354,
      '3':32.422438,
      '4':37.331050,
      '5':43.617665, 
      '6':56.683825,
      '7':99.550902,
      '8':140.393,
      '9':261.177,
      #'8':124,
      #'9':171,
      #'10':258,
      }
  ###wpdict = {
  ###    '1':22.390464,
  ###    '2':27.391137,
  ###    '3':32.363064,
  ###    '4':37.325283,
  ###    '5':43.855854,
  ###    '6':57.209096,
  ###    '7':93.227984,
  ###    '8':140.393,
  ###    '9':261.177,
  ####    '8':124,
  ####    '9':171,
  ####    '10':258,
  ###    }
  wprange = collections.OrderedDict()
  wprange['1'] = {'low':20, 'up':25}
  wprange['2'] = {'low':25, 'up':30}
  wprange['3'] = {'low':30, 'up':35}
  wprange['4'] = {'low':35, 'up':40}
  wprange['5'] = {'low':40, 'up':50}
  wprange['6'] = {'low':50, 'up':70}
  wprange['7'] = {'low':70, 'up':200}
  wprange['8'] = {'low':100, 'up':200}
  wprange['9'] = {'low':200, 'up':500}
  #wprange['8'] = {'low':100, 'up':150}
  #wprange['9'] = {'low':150, 'up':200}
  #wprange['10'] = {'low':200, 'up':500}
  
  year2draw = []
  pulldirs = {}
  #for line in file:
  #    line = lines.rstrip().split()
  jobdir = 'job/job_2021-08-02-143547/'
  for year in ['2016_preVFP', '2016_postVFP', '2017', '2018']:
    #for year in ['2016_preVFP']:
    for pt in ['1', '2', '3', '4', '5', '6', '7']:
      for wp in ['VVVLoose', 'VVLoose', 'VLoose', 'Loose', 'Medium', 'Tight', 'VTight', 'VVTight']:
        wplabel = year+'_'+wp
        binlabel = year+'_'+wp+'_pt'+pt
        file = open(jobdir + '/out.'+binlabel)
        for line in file:
          line = line.rstrip()
          words = line.split()
          if line.find('setting')!=-1:
            #print 'wp', words
            #year = words[1]
            #wp = words[2]
            #pt = words[3].replace('pt','')
            pulldirs[binlabel] = {'titles':[],
                                  'vals':[],
                                  'errs':[]}
            if year not in year2draw:
              year2draw.append(year)
            if not graphs.has_key(year + '_' + wp):
              graph = TGraphAsymmErrors()
              graphs[year + '_' + wp] = {'count':0, 'graph':graph}
          if line.find('ZTT_mu')!=-1:
            val = Double(words[2])
            errval_up = Double(words[4])
            errval_down = Double(words[4])
            if len(words)==6:
              errval_up = Double(words[4])
              errval_down = Double(words[5])
            print year, wp, '(pT = ', wprange[pt]['low'], '-', wprange[pt]['up'], ')', '{0:.3f}'.format(val), '+{0:.3f}'.format(errval_up), ' / -{0:.3f}'.format(errval_down)
            print 'SetPoint', graphs[year + '_' + wp]['count'], Double(wpdict[pt]), val
            graphs[year + '_' + wp]['graph'].SetPoint(graphs[year + '_' + wp]['count'], Double(wpdict[pt]), val)
            graphs[year + '_' + wp]['graph'].SetPointError(graphs[year + '_' + wp]['count'], Double(wpdict[pt]-wprange[pt]['low']), Double(wprange[pt]['up'] - wpdict[pt]), abs(errval_up), abs(errval_down))
            graphs[year + '_' + wp]['count'] += 1
          elif line.find('CMS_')!=-1 or line.find('shape_')!=-1:
             pulldirs[binlabel]['titles'].append(words[0])
             pulldirs[binlabel]['vals'].append(words[2])
             pulldirs[binlabel]['errs'].append(words[4])
  
  ##for line in file_new:
  ##    line = line.rstrip()
  ##    words = line.split()
  ##    if line.find('setting')!=-1:
  ##        year = words[1].replace('2016_preVFP','2016')
  ##        wp = words[2]
  ##        pt = words[3]
  ##        if not graphs.has_key(year + '_' + wp):
  ##            graph = TGraphAsymmErrors()
  ##            graphs[year + '_' + wp] = {'count':0, 'graph':graph}
  ##        if year not in year2draw:
  ##            year2draw.append(year)
  ##    if line.find('ZTT_mu')!=-1:
  ##        val = Double(words[2])
  ##        errval_up = Double(words[4])
  ##        errval_down = Double(words[4])
  ##        if len(words)==6:
  ##            errval_up = Double(words[4])
  ##            errval_down = Double(words[5])
  ##        #print year, wp, '(pT = ', wprange[pt]['low'], '-', wprange[pt]['up'], ')', '{0:.3f}'.format(val), '+{0:.3f}'.format(errval_up), ' / -{0:.3f}'.format(errval_down)
  ##        #print 'count = ', graphs[year + '_' + wp]['count'], '(x,y) = ', Double(wpdict[wp]), val, '-', val_down, '+', val_up
  ##        print 'old ... SetPoint', graphs[year + '_' + wp]['count'], Double(wpdict[pt]), val
  ##        graphs[year + '_' + wp]['graph'].SetPoint(graphs[year + '_' + wp]['count'], Double(wpdict[pt]), val)
  ##        graphs[year + '_' + wp]['graph'].SetPointError(graphs[year + '_' + wp]['count'], Double(wpdict[pt]-wprange[pt]['low']), Double(wprange[pt]['up'] - wpdict[pt]), abs(errval_up), abs(errval_down))
  ##        graphs[year + '_' + wp]['count'] += 1
  
  for line in file_prev:
    line = line.rstrip()
    words = line.split()
    if line.find('setting')!=-1:
      year = words[1]
      wp = words[2]
      pt = words[3]
      wplabel = year+'_'+wp
      binlabel = year+'_'+wp+'_pt'+pt
      if not graphs_prev.has_key(year + '_' + wp):
        graph_prev = TGraphAsymmErrors()
        graphs_prev[year + '_' + wp] = {'count':0, 'graph':graph_prev}
    if line.find('ZTT_mu')!=-1:
      val = Double(words[2])
      errval_up = Double(words[4])
      errval_down = Double(words[4])
      if len(words)==6:
        errval_up = Double(words[4])
        errval_down = Double(words[5])
      #print year, wp, '(pT = ', wprange[pt]['low'], '-', wprange[pt]['up'], ')', '{0:.3f}'.format(val), '+{0:.3f}'.format(errval_up), ' / -{0:.3f}'.format(errval_down)
      #print 'count = ', graphs[year + '_' + wp]['count'], '(x,y) = ', Double(wpdict[wp]), val, '-', val_down, '+', val_up
      print 'old ... SetPoint', graphs_prev[wplabel]['count'], Double(wpdict[pt]), val
      graphs_prev[wplabel]['graph'].SetPoint(graphs_prev[wplabel]['count'], Double(wpdict[pt]), val)
      graphs_prev[wplabel]['graph'].SetPointError(graphs_prev[wplabel]['count'], Double(wpdict[pt]-wprange[pt]['low']), Double(wprange[pt]['up'] - wpdict[pt]), abs(errval_up), abs(errval_down))
      graphs_prev[wplabel]['count'] += 1
  
  #idx = 0
  start=20
  #start=50
  start_flat = 40
  end=1000
  for idx, year in enumerate(year2draw):
    ensuredir('plots/sf_' + year)
    sfile = TFile('TauID_SF_pt_DeepTau2017v2p1VSjet_' + year + 'UL.root', 'recreate')
    for wp in ['VVVLoose', 'VVLoose', 'VLoose', 'Loose', 'Medium', 'Tight', 'VTight', 'VVTight']:
      if not graphs.has_key(year + '_' + wp): continue
      wplabel = year+'_'+wp
      binlabel = year+'_'+wp+'_dm'+dm
      canvas = TCanvas('canvas_' + year + '_' + wp)
      canvas.SetLogx()
      frame =  TH2F('frame_' + year + '_' + wp, year + '_' + wp, len(wpdict),start,end,100,0.,1.5)
      frame.SetMinimum(0.5)
      frame.SetMaximum(1.)
      frame.GetYaxis().SetTitle('Scale Factor')
      frame.GetXaxis().SetTitle('Tau pT (GeV)')
      frame.GetYaxis().SetNdivisions(505)
      #gStyle.SetOptTitle(0)
      #graphs[year + '_' + wp]['graph'].SetLineColor(cols[idx])
      #graphs[year + '_' + wp]['graph'].SetMarkerColor(cols[idx])
      #print ii, graphs[year + '_' + wp].GetName()
      #if idx==0: graphs[year + '_' + wp]['graph'].Draw('apl')
      #else: graphs[year + '_' + wp]['graph'].Draw('plsame')
      #  graphs[year + '_' + wp]['graph'].Draw('psame')
      fg = copy.deepcopy(graphs[year + '_' + wp]['graph'])
      fg.Fit('pol0', '', '', start_flat, 1000)
      flat = fg.GetFunction('pol0')
      flat.SetLineColor(2)
      flat.SetLineWidth(2)
      print 'flat:', '{0:.2f}'.format(flat.GetChisquare()), '{0:.2f}'.format(flat.GetNDF()), '{0:.2f}'.format(flat.GetProb())
      red_flat = 1.
      if flat.GetNDF()!=0:
        red_flat = flat.GetChisquare()/flat.GetNDF()
      band_up = abs(flat.GetParError(0))
      band_down = abs(flat.GetParError(0))
      cent = flat.GetParameter(0)
      _x_ = Double(0.)
      _y_ = Double(0.)
      graphs[year + '_' + wp]['graph'].GetPoint(3,_x_,_y_)
      print 'retrieve last bin SF = ', _y_, 'flat = ', cent
      if _y_ < cent:
        diff_down = (cent-_y_)/2.
        band_down = math.sqrt(band_down*band_down + diff_down*diff_down)
        print 'add in quadrature to the down side !!!', diff_down*2, band_down
      else:
        diff_up = (_y_ - cent)/2.
        band_up = math.sqrt(band_up*band_up + diff_up*diff_up)
        print 'add in quadrature to the up side !!!', diff_up*2, band_up
      flat_up = TF1('flat_up', str(cent+band_up), start_flat, 500)
      flat_down = TF1('flat_down', str(cent-band_down), start_flat, 500)
      flat_up.SetLineColor(2)
      flat_down.SetLineColor(2)  
      flat_up.SetLineStyle(3)
      flat_down.SetLineStyle(3)
      slope_up = band_up/(end-500.)
      slope_down = -band_down/(end-500.)
      ext_up = str(slope_up) + '*(x-500) + ' + str(cent+band_up)
      ext_down = str(slope_down) + '*(x-500) + ' + str(cent-band_down)
      flat_up2 = TF1('flat_up2', ext_up, 500., 1000)
      flat_down2 = TF1('flat_down2', ext_down, 500., 1000)
      flat_up2.SetLineColor(2)
      flat_down2.SetLineColor(2)
      flat_up2.SetLineStyle(3)
      flat_down2.SetLineStyle(3)
      frame.Draw()
      if args.overlay:
        yearnew = year.replace('_preVFP', '').replace('_postVFP','')
        graphs_prev[yearnew + '_' + wp]['graph'].SetLineColor(tt)
        graphs_prev[yearnew + '_' + wp]['graph'].SetMarkerColor(tt)
        graphs_prev[yearnew + '_' + wp]['graph'].Draw('pzsame')
        legend_comp = TLegend(0.18, 0.2, 0.8, 0.3)
        LegendSettings(legend_comp)
        legend_comp.AddEntry(graphs[year + '_' + wp]['graph'], 'UL' , 'l')
        legend_comp.AddEntry(graphs_prev[yearnew + '_' + wp]['graph'], 'previous' , 'l')
        legend_comp.Draw()
      graphs[year + '_' + wp]['graph'].SetLineColor(1)
      graphs[year + '_' + wp]['graph'].SetMarkerColor(1)
      graphs[year + '_' + wp]['graph'].Draw('pzsame')
      flat.Draw('lsame')
      flat_up.Draw('lsame')
      flat_down.Draw('lsame')
      flat_up2.Draw('lsame')
      flat_down2.Draw('lsame')
      legend = TLegend(0.18, 0.2, 0.8, 0.3)
      LegendSettings(legend)
      leg_flat = 'UL: y = {0:.3f}'.format(flat.GetParameter(0)) + '^{+' + '{0:.3f}'.format(band_up) + '}_{-' + '{0:.3f}'.format(band_down) + '} (red. #chi^{2} = ' + '{0:.1f}'.format(red_flat) + ', prob. = ' + '{0:.2f}'.format(flat.GetProb()) + ')'
      legend.AddEntry(flat, leg_flat , 'l')
      legend.Draw()
      
      canvas.Modified()
      canvas.Print('plots/sf_' + year + '/' + wp + '.gif')
      canvas.Print('plots/sf_' + year + '/' + wp + '.pdf')
      
      ############ create output root files ... 
      funcstr = '(x<=20)*0'
      funcstr_up = '(x<=20)*0'
      funcstr_down = '(x<=20)*0'
      for ip, wpdir in wprange.iteritems():
        if int(ip) >= 5: continue
        funcstr += '+ ( x > ' + str(wpdir['low']) + ' && x <=' + str(wpdir['up']) + ')*' + str(returnsf(int(ip)-1, graphs[year + '_' + wp]['graph']))
        funcstr_up += '+ ( x > ' + str(wpdir['low']) + ' && x <=' + str(wpdir['up']) + ')*' + str(returnsf_up(int(ip)-1, graphs[year + '_' + wp]['graph']))
        funcstr_down += '+ ( x > ' + str(wpdir['low']) + ' && x <=' + str(wpdir['up']) + ')*' + str(returnsf_down(int(ip)-1, graphs[year + '_' + wp]['graph']))
      funcstr += '+ (x > 40)*' + str(cent)
      funcstr_up += '+ (x > 40 && x <= 500)*' + str(cent+band_up)
      funcstr_up += '+ (x > 500 && x <= 1000)*(' + str(cent) + ' + ' + str(band_up) + '*(x/500.))'
      funcstr_up += '+ (x > 1000)*(' + str(cent) + ' + ' + str(2*band_up) + ')'
      #funcstr_up += '+ (x > 40)*' + str(cent)
      funcstr_down += '+ (x > 40 && x <= 500)*' + str(cent-band_down)
      funcstr_down += '+ (x > 500 && x <= 1000)*(' + str(cent) + ' - ' + str(band_down) + '*(x/500.))'
      #funcstr_down += '+ (x > 1000)*2*' + str(cent - 2*band_down)
      funcstr_down += '+ (x > 1000)*(' + str(cent) + ' - ' + str(2*band_down) + ')'
      #funcstr_down += '+ (x > 40)*' + str(cent)
      print funcstr
      print funcstr_up
      print funcstr_down
      func_SF      = TF1(wp + '_cent', funcstr,     0,1000)
      func_SF_up   = TF1(wp + '_up',   funcstr_up,  0,1000)
      func_SF_down = TF1(wp + '_down', funcstr_down,0,1000)
      func_SF.Write()
      func_SF_up.Write()
      func_SF_down.Write()
      frame.Delete()
    sfile.Write()
    sfile.Close()
  pullsVertical_noBonly(pulldirs)
  
  
if __name__ == '__main__':
  description = '''This script creates plots and ROOT files of the fit results.'''
  parser = ArgumentParser(prog="plotfit_dm",description=description,epilog="Good luck!")
  parser = ArgumentParser(prog="harvesterDatacards",description=description,epilog="Succes!")
  #parser.add_option("-o", "--outName",  action="store", type="string", dest="outName",  default="pulls"    )
  #parser.add_option("-t", "--text",     action="store", type="string", dest="text",     default=""         )
  #parser.add_option('-f', '--fit', action="store_true", default=False, dest='fit')
  parser.add_argument('-o', '--overlay',  dest='overlay', action="store_true")
  parser.add_argument('-v', '--verbose',  dest='verbosity', type=int, nargs='?', const=1, default=0,
                                          help="set verbosity level" )
  args = parser.parse_args()
  main(args)
  
