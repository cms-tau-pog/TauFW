import os, numpy, math, copy, math
from ROOT import gStyle, TCanvas, TLegend, gROOT, TGraphAsymmErrors, Double, TH2F, kBlack, TBox, kGreen, kOrange, TFile, TH1F, TColor
from common.officialStyle import officialStyle

gROOT.SetBatch(True)
#gROOT.SetBatch(False)
officialStyle(gStyle)
gStyle.SetTitleX(0.5)

import optparse
usage = "usage: %prog [options]"
parser = optparse.OptionParser(usage)
#parser.add_option("-o", "--outName",  action="store", type="string", dest="outName",  default="pulls"    )
#parser.add_option("-t", "--text",     action="store", type="string", dest="text",     default=""         )
parser.add_option('-o', '--overlay', action="store_true", default=True, dest='overlay')
(options, args) = parser.parse_args()

tt = TColor.GetColor(135,206,250)

#outName  = options.outName
#text     = options.text


def ensureDir(directory):
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


def returnsf(idx, graph):
    
#    print graph, idx
    _x_ = Double(0.)
    _y_ = Double(0.)
    
    graph.GetPoint(idx,_x_,_y_)
    return _y_

def returnsf_up(idx, graph):
    
#    print 'up', idx, graph.GetName(), graph.GetErrorYhigh(idx)
    return returnsf(idx, graph) + graph.GetErrorYhigh(idx)
    return graph.GetErrorYhigh(idx)


def returnsf_down(idx, graph):
    
    print 'down', idx, graph.GetName(), graph.GetErrorYhigh(idx)
    return returnsf(idx, graph) - graph.GetErrorYlow(idx)
#    return graph.GetErrorYlow(idx)



def returnsf_unc(idx, graph):
    
#    print 'up', idx, graph.GetName(), graph.GetErrorYhigh(idx)
    return graph.GetErrorYhigh(idx)
#    return graph.GetErrorYhigh(idx)




def pullsVertical_noBonly(pulldirs):
    
    print 'making pulls ...'
    for yearwp, val in pulldirs.iteritems():

#        print yearwp

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
#            print idx, vals[idx]
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
 
        ensureDir('plots/pull_dm')   
        canvas.Print('plots/pull_dm/' + yearwp + ".gif")
        canvas.Print('plots/pull_dm/' + yearwp + ".pdf")

        #############################################################
    
#        corfile = TFile('root/fitresults_' + yearwp + '.root')
#        corr = corfile.Get('correlation_matrix_channelmu')
#        corrcanvas = TCanvas("corrcanvas_" + yearwp, "corr. coeff")
##        corrcanvas.cd(0).SetPadRightMargin(0.1)
#
#        for ix in range(1, corr.GetXaxis().GetNbins()+1):
#            corr.GetXaxis().SetBinLabel(ix, corr.GetXaxis().GetBinLabel(ix).replace('CMS_', ''))
#
#        for iy in range(1, corr.GetYaxis().GetNbins()+1):
#            corr.GetYaxis().SetBinLabel(iy, corr.GetXaxis().GetBinLabel(iy).replace('CMS_', ''))
#
#        corrcanvas.SetRightMargin(0.13)
#        corrcanvas.SetLeftMargin(0.14)
#        gStyle.SetOptTitle(1)
#        corr.SetTitle(yearwp.replace('_',', '))
#        corr.Draw('colz')
#        corrcanvas.Print('plots/cor_' + yearwp + ".gif")
#        corrcanvas.Print('plots/cor_' + yearwp + ".pdf")
        
        

#file = open('log_rateParam')
#file = open('log_dm_izaak')
file_new = open('log_dm_20210618')
file_prev = open('log_dm_20191114')

graphs = {}
graphs_prev = {}

cols = [1,2,4,6]

wpdict = {
    '0':0,
    '1':1,
    '10':2,
    '11':3
    }



yearshift={
    '2016':-0.1,
    '2016_preVFP':-0.12,
    '2016_postVFP':-0.08,
    '2017':0.,
    '2018':0.1,
    }


year2draw = []


pulldirs = {}



#jobdir='job/job_2020-09-09-141259/'
jobdir='job/job_2021-08-02-143547/'

for year in ['2016_preVFP', '2016_postVFP', '2017', '2018']:
#for year in ['2016_preVFP']:
    
    for dm in ['0', '1', '10', '11']:

	for iso in ['VVVLoose', 'VVLoose', 'VLoose', 'Loose', 'Medium', 'Tight', 'VTight', 'VVTight']:


            file = open(jobdir + '/out.' + year + '_' + iso + '_dm' + dm)
    
            
            for line in file:

                line = line.rstrip()

                words = line.split()


                if line.find('setting')!=-1:
#        print 'wp', words

#                    year = words[1]
#                    wp = words[2]
#                    dm = words[3].replace('dm','')

                    pulldirs[year + '_' + iso + '_' + dm] = {'titles':[],
                                                             'vals':[],
                                                             'errs':[]}


                    if year not in year2draw:
                        year2draw.append(year)



                    if not graphs.has_key(year + '_' + iso):
                        graph = TGraphAsymmErrors()
                        graphs[year + '_' + iso] = {'count':0, 'graph':graph}


                if line.find('ZTT_mu')!=-1:
                    val = Double(words[2])
                    errval_up = Double(words[4])
                    errval_down = Double(words[4])
        
                    if len(words)==6:
                        errval_up = Double(words[4])
                        errval_down = Double(words[5])
            

                    
#                    print year, wp, '(pT = ', wprange[pt]['low'], '-', wprange[pt]['up'], ')', '{0:.3f}'.format(val), '+{0:.3f}'.format(errval_up), ' / -{0:.3f}'.format(errval_down)
 

#                    print 'SetPoint', graphs[year + '_' + wp]['count'], Double(wpdict[pt]), val
                    graphs[year + '_' + iso]['graph'].SetPoint(graphs[year + '_' + iso]['count'], Double(wpdict[dm]) + Double(yearshift[year]), val)

            
                    graphs[year + '_' + iso]['graph'].SetPointError(graphs[year + '_' + iso]['count'], 0, 0, abs(errval_up), abs(errval_down))

                    graphs[year + '_' + iso]['count'] += 1


                elif line.find('CMS_')!=-1 or line.find('shape_')!=-1:
                
                    pulldirs[year + '_' + iso + '_' + dm]['titles'].append(words[0])
                    pulldirs[year + '_' + iso + '_' + dm]['vals'].append(words[2])
                    pulldirs[year + '_' + iso + '_' + dm]['errs'].append(words[4])


###for line in file_new:
###    
###    line = line.rstrip()
###
###    words = line.split()
###
###    if line.find('setting')!=-1:
###
###        year = words[1].replace('2016_preVFP','2016')
###        wp = words[2]
###        dm = words[3]
###
###        if not graphs.has_key(year + '_' + wp):
###            graph = TGraphAsymmErrors()
###            graphs[year + '_' + wp] = {'count':0, 'graph':graph}
###
###
###        if year not in year2draw:
###            year2draw.append(year)
###
###
###    if line.find('ZTT_mu')!=-1:
###        val = Double(words[2])
###        errval_up = Double(words[4])
###        errval_down = Double(words[4])
###        
###        if len(words)==6:
###            errval_up = Double(words[4])
###            errval_down = Double(words[5])
###            
###
####        print year, wp, '(pT = ', wprange[pt]['low'], '-', wprange[pt]['up'], ')', '{0:.3f}'.format(val), '+{0:.3f}'.format(errval_up), ' / -{0:.3f}'.format(errval_down)
### #       print 'count = ', graphs[year + '_' + wp]['count'], '(x,y) = ', Double(wpdict[wp]), val, '-', val_down, '+', val_up
###
###        print 'old ... SetPoint', graphs[year + '_' + wp]['count'], Double(wpdict[dm]), val
###        graphs[year + '_' + wp]['graph'].SetPoint(graphs[year + '_' + wp]['count'], Double(wpdict[dm]) + Double(yearshift[year]), val)
###
###
###        graphs[year + '_' + wp]['graph'].SetPointError(graphs[year + '_' + wp]['count'], 0, 0, abs(errval_up), abs(errval_down))
###
###
###        graphs[year + '_' + wp]['count'] += 1





for line in file_prev:
    
    line = line.rstrip()

    words = line.split()

    if line.find('setting')!=-1:

        year = words[1]
        wp = words[2]
        dm = words[3]

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
            

#        print year, wp, '(pT = ', wprange[pt]['low'], '-', wprange[pt]['up'], ')', '{0:.3f}'.format(val), '+{0:.3f}'.format(errval_up), ' / -{0:.3f}'.format(errval_down)
 #       print 'count = ', graphs[year + '_' + wp]['count'], '(x,y) = ', Double(wpdict[wp]), val, '-', val_down, '+', val_up

        print 'old ... SetPoint', graphs_prev[year + '_' + wp]['count'], Double(wpdict[dm]), val
        graphs_prev[year + '_' + wp]['graph'].SetPoint(graphs_prev[year + '_' + wp]['count'], Double(wpdict[dm]) + Double(yearshift[year]), val)


        graphs_prev[year + '_' + wp]['graph'].SetPointError(graphs_prev[year + '_' + wp]['count'], 0, 0, abs(errval_up), abs(errval_down))


        graphs_prev[year + '_' + wp]['count'] += 1




wpdict_v2 = dict((v,k) for k,v in wpdict.iteritems())
ensureDir('plots/dm/')

for wp in ['VVVLoose', 'VVLoose', 'VLoose', 'Loose', 'Medium', 'Tight', 'VTight', 'VVTight']:
#for wp in ['Medium', 'Tight']:

    canvas = TCanvas('canvas_' + wp)
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
    frame.SetTitle(wp + ' (p_{T} #geq 40 GeV inclusive)')

    for idx, year in enumerate(year2draw):


        if not graphs.has_key(year + '_' + wp): continue


        graphs[year + '_' + wp]['graph'].SetLineColor(cols[idx])
        graphs[year + '_' + wp]['graph'].SetMarkerColor(cols[idx])    
        graphs[year + '_' + wp]['graph'].Draw('pzsame')

        if options.overlay and year.find('postVFP')==-1:

            yearnew = year.replace('_preVFP', '').replace('_postVFP','')
            
            graphs_prev[yearnew + '_' + wp]['graph'].SetLineColor(cols[idx])
            graphs_prev[yearnew + '_' + wp]['graph'].SetMarkerColor(cols[idx])
            graphs_prev[yearnew + '_' + wp]['graph'].SetMarkerStyle(24)
            graphs_prev[yearnew + '_' + wp]['graph'].Draw('pzsame')
            legend.AddEntry(graphs_prev[yearnew + '_' + wp]['graph'], yearnew + '(prev)', 'lep')
        
        legend.AddEntry(graphs[year + '_' + wp]['graph'], year, 'lep')
 
#    idx += 1

    legend.Draw()
    canvas.Print('plots/dm/sf_' + wp + '.gif')
    canvas.Print('plots/dm/sf_' + wp + '.pdf')

pullsVertical_noBonly(pulldirs)


#for ibin in range(1, frame.GetXaxis().GetNbins()+1):
#for year in ['2016', '2017', '2018']:
#for year in ['2016', '2018']:
for idx, year in enumerate(year2draw):
    
    sfile = TFile('TauID_SF_dm_DeepTau2017v2p1VSjet_' + year + 'UL.root', 'recreate')
    
    for wp in ['VVVLoose', 'VVLoose', 'VLoose', 'Loose', 'Medium', 'Tight', 'VTight', 'VVTight']:
#    for wp in ['Medium', 'Tight']:

#        funcstr = ''
#        funcstr_up = ''
#        funcstr_down = ''

        hist_cent = TH1F(wp, wp, 12,0,12)

#        hist_prev = None
#        if options.overlay:
#            hist_prev = TH1F(wp, wp, 12,0,12)
#        hist_up = TH1F(wp + '_up', wp + '_up', 11,0,11)
#        hist_down = TH1F(wp + '_down', wp + '_down', 11,0,11)
        
        hist_cent.GetXaxis().SetTitle('dm')
        hist_cent.GetYaxis().SetTitle('SF (cent)')
#        hist_up.GetXaxis().SetTitle('dm')
#        hist_up.GetYaxis().SetTitle('SF (up)')
#        hist_down.GetXaxis().SetTitle('dm')
#        hist_down.GetYaxis().SetTitle('SF (down)')

        for idx, dm in enumerate(['0', '1', '10', '11']):

#            if funcstr != '':
#                funcstr += '+'
#                funcstr_up += '+'
#                funcstr_down += '+'

            print idx


            hist_cent.SetBinContent(int(dm)+1, returnsf(idx, graphs[year + '_' + wp]['graph']))
            hist_cent.SetBinError(int(dm)+1, returnsf_unc(idx, graphs[year + '_' + wp]['graph']))

#            if options.overlay:
#                hist_prev.SetBinContent(int(dm)+1, returnsf(idx, graphs_prev[year + '_' + wp]['graph']))
#                hist_prev.SetBinError(int(dm)+1, returnsf_unc(idx, graphs_prev[year + '_' + wp]['graph']))



#            hist_up.SetBinContent(int(dm)+1, returnsf_up(idx, graphs[year + '_' + wp]['graph']))
#            hist_down.SetBinContent(int(dm)+1, returnsf_down(idx, graphs[year + '_' + wp]['graph']))

#            funcstr += '( x == ' + str(dm) + ')*'+ str(returnsf(idx, graphs[year + '_' + wp]['graph']))
#            funcstr_up += '( x == ' + str(dm) + ')*'+ str(returnsf_up(idx, graphs[year + '_' + wp]['graph']))
#            funcstr_down += '( x == ' + str(dm) + ')*'+ str(returnsf_down(idx, graphs[year + '_' + wp]['graph']))


#        func_SF      = TF1(wp + '_cent',     funcstr,     0,11)
#        func_SF_up      = TF1(wp + '_up',     funcstr_up,     0,11)
#        func_SF_down     = TF1(wp + '_down',     funcstr_down,     0,11)

        hist_cent.Write()
#        hist_up.Write()
#        hist_down.Write()
        
            
    sfile.Write()
    sfile.Close()

