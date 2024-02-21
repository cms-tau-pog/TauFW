from argparse import ArgumentParser
import sys, os
import ROOT 
import numpy as np

def get_eta_regs_from_str(eta_arr):
  eta_reg_num = []
  if len(eta_arr)>=2:
    for eta_reg in eta_arr:
      if len(eta_reg_num)==0:
        eta_reg_num.append(float(eta_reg[3:6].replace('p','.')))
        continue
      eta_reg_num.append(float(eta_reg[3:6].replace('p','.')))
  eta_reg_num.append(2.5)
  print("eta regions: ", eta_reg_num)
  return eta_reg_num


def init_histos(args):
  h_dict = {}
  #bins = get_eta_regs_from_str(list(args.etareg))
  bins = [0.0,1.46,1.56,2.5]
  for wp in args.wps:
     for idm in args.dms:
       h_dict[wp+'_'+idm] = ROOT.TH1F(wp+'_'+idm, wp+'_'+idm, len(bins)-1, np.array(bins))
       h_dict[wp+'_'+idm].SetTitle(wp+'_'+idm)
       h_dict[wp+'_'+idm].GetXaxis().SetTitle("#tau_{h}|#eta|")
       h_dict[wp+'_'+idm].GetYaxis().SetTitle("SF")
  return h_dict

def init_graphs(args):
  g_dict = {}
  #bins = get_eta_regs_from_str(list(args.etareg))
  bins = [0.0,1.46,1.56,2.5]
  for wp in args.wps:
     for idm in args.dms:
       g_dict[wp+'_'+idm] = ROOT.TGraphAsymmErrors(len(bins)-2)
       g_dict[wp+'_'+idm].SetTitle(wp+"_"+idm+";#tau_{h}|#eta|;SF")
  return g_dict


def fill_graphs(g_dict, args):
  etareg = ['eta0to1p46','eta1p56to2p5']
  etareg_name =['barrel','endcap']
  era = args.era 
  for wp in args.wps:
     print("============")
     print("WP:",wp)
     for idm in args.dms:
        print("-----------")
        print("DM:",idm)
        wp_totake = wp
        unc_increase_factor = 1.0
        if wp == "Tight" and int(idm) > 1:
           unc_increase_factor = 2.0
           wp_totake = "VVLoose"
           print("Taking VVLoose results with inflated unc") 
        for i, eta_reg in enumerate(etareg):
           print("::::::::::::")
           print("Eta Region:",eta_reg)
           full_filename = f"./output/{era}/ETauFR/multidimfit_initialFit_{wp_totake}_{eta_reg}_dm{idm}.root"
           the_file = ROOT.TFile(full_filename,"R")
           print(full_filename)
           fit = the_file.Get('fit_mdf')
           fes_fit_res  = fit.floatParsFinal().find('fes')
           print("fes: ",fes_fit_res)
           print(fes_fit_res.getErrorHi())
           print(fes_fit_res.getErrorLo()) 
           #print(i)
           g_dict[wp+'_'+idm].SetPoint(i, i+1/2, fes_fit_res.getValV())
           g_dict[wp+'_'+idm].SetPointEYhigh(i, fes_fit_res.getErrorHi() * unc_increase_factor)
           g_dict[wp+'_'+idm].SetPointEYlow(i, abs(fes_fit_res.getErrorLo()) * unc_increase_factor)
           #g_dict[wp+'_'+idm].GetXaxis().SetBinLabel(g_dict[wp+'_'+idm].GetXaxis().FindBin(i+1/2), etareg_name[i])
           g_dict[wp+'_'+idm].GetXaxis().SetBinLabel(10, etareg_name[0])
           g_dict[wp+'_'+idm].GetXaxis().SetBinLabel(92, etareg_name[1]) 
           #g_dict[wp+'_'+idm].GetXaxis().SetNdivisions(2)

  return g_dict
 

def fill_hists(h_dict, args):
  etareg = ['eta0to1p46','eta1p56to2p5']
  era = args.era 
  for wp in args.wps:
     print("============")
     print("WP:",wp)
     for idm in args.dms:
        print("-----------")
        print("DM:",idm)
        wp_totake = wp
        unc_increase_factor = 1.0
        if wp == "Tight" and int(idm) > 1:
           unc_increase_factor = 2.0
           wp_totake = "VVLoose"
           print("Taking VVLoose results with inflated unc") 
        for i, eta_reg in enumerate(etareg):
           print("::::::::::::")
           print("Eta Region:",eta_reg)
           full_filename = f"./output/{era}/ETauFR/multidimfit_initialFit_{wp_totake}_{eta_reg}_dm{idm}.root"
           the_file = ROOT.TFile(full_filename,"R")
           print(full_filename)
           fit = the_file.Get('fit_mdf')
           norm_fit_res = fit.floatParsFinal().find('normalizationZEE')
           sf_fit_res   = fit.floatParsFinal().find('r')
           #fes_fit_res  = fit.floatParsFinal().find('fes')
           norm = norm_fit_res.getVal()
           etau_FR = ROOT.RooFormulaVar('etau_FR', 'x[0]*x[1]', ROOT.RooArgList(norm_fit_res, sf_fit_res))
           etau_FRerr = etau_FR.getPropagatedError(fit)
           print("r: ",sf_fit_res)
           print("norm: ",norm_fit_res)
           print("sf(r x norm): ", etau_FR.evaluate())
           print("sf err: ", etau_FRerr)
           #print("fes: ",fes_fit_res)
           print("error increased:", etau_FRerr * unc_increase_factor)
           h_dict[wp+'_'+idm].SetBinContent(2*i+1, etau_FR.evaluate())
           h_dict[wp+'_'+idm].SetBinError(2*i+1, etau_FRerr * unc_increase_factor)

        h_dict[wp+'_'+idm].SetBinContent(2,1.0)
        h_dict[wp+'_'+idm].SetBinError(2,1.0)  
  return h_dict
  
    
def main(args):
  etareg = ['eta0to1p46','eta1p56to2p5']
  era = args.era
  measure = args.measure
  outfile = ROOT.TFile.Open(f"./output/{era}/ETauFR/etau_{measure}_out.root", "RECREATE")

  if measure == 'FR':
    h_dict = init_histos(args)
    print("Init histos done")
    h_dict = fill_hists(h_dict, args)
    print("Fill histos done")
    for (h_name, hist) in h_dict.items():
       print(hist)
       outfile.WriteObject(hist, h_name)
  elif args.measure == 'FES':
    g_dict = init_graphs(args)
    print("Init graphs done")
    g_dict = fill_graphs(g_dict, args)
    print("Fill graphs done")
    for (g_name, graph) in g_dict.items():
       print(graph)
       outfile.WriteObject(graph, g_name)   

  outfile.Close()
                  
    
    
if __name__ == '__main__':
  argv = sys.argv
  description = '''This script Saves'''
  parser = ArgumentParser(prog="",description=description,epilog="Success!")
  parser.add_argument('--era',  dest='era', type=str, default='UL2018',help="era")
  #parser.add_argument('--out_root',  dest='out_root_file', type=str, nargs='*',default=['etau_SF.root'],
  #                                        help="path to store resutls in a form of root histograms")
  #parser.add_argument('--etareg',  dest='etareg', type=str, nargs='+', default=['eta0.0to0.0'],
  #                                        help="eta region of the workspace")
  parser.add_argument('--dms',      dest='dms', type=str, nargs='+', default=['0'],
                                          help="dm of the workspace")
  parser.add_argument('--WP',  dest='wps', type=str, nargs='+', default=['NotAWP'],
                                          help="working point")
  parser.add_argument('--measure',  dest='measure', type=str, default='FR', choices = ['FR','FES'],
                                          help="FR or FES") 
  args = parser.parse_args()
  main(args)

  #Example of usage: python3 dump_sf2root.py --era 2022_postEE --dms '0' '1' '10' '11' --WP VVLoose --measure FES
