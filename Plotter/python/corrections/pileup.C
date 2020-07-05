/*
 * @short: provide pileup weights at drawing level
 * @author: Izaak Neutelings (October 2018)
 *
 */

#include "TROOT.h"
#include "TFile.h"
#include "TH2.h"
#include "TH2F.h"
#include <iostream>
#include <algorithm>
using namespace std;

TString filename_data_2017 = "$SFRAME_DIR/../plots/PlotTools/pileup/Data_PileUp_2017_69p2.root";
TString filename_MC_2017 = "$SFRAME_DIR/../plots/PlotTools/pileup/MC_PileUp_2017_Winter17_V2.root";
TH1F* hist_PU_data;
TH1F* hist_PU_data_old;
TH1F* hist_PU_MC;
//TH1F* hist_PU_weights;


TH1F* getPUHist(TString filename, TString histname="pileup"){
  std::cout << ">>> opening " << filename << std::endl;
  TFile *file = new TFile(filename);
  TH1F* hist = (TH1F*) file->Get(histname);
  hist->SetDirectory(0);
  file->Close();
  return hist;
}


void readPUFile(TString filename_data=filename_data_2017,TString filename_MC=filename_MC_2017, TString filename_data_old=""){
  
  // DATA
  hist_PU_data = getPUHist(filename_data);
  hist_PU_data->Scale(1./hist_PU_data->Integral());
  
  // OLD DATA PROFILE
  if(filename_data_old!=""){
    hist_PU_data_old = getPUHist(filename_data_old);
    hist_PU_data_old->Scale(1./hist_PU_data_old->Integral());
  }
  
  // MC
  hist_PU_MC = getPUHist(filename_MC);
  hist_PU_MC->Scale(1./hist_PU_MC->Integral());
  
}



Float_t getPUWeight(Int_t npu){
  float data = hist_PU_data->GetBinContent(hist_PU_data->FindBin(npu));
  float mc   = hist_PU_MC->GetBinContent(hist_PU_MC->FindBin(npu));
  //std::cout << data << " " << mc << " " << npu << " -> " << data/mc << std::endl;
  if(mc > 0.){
    return data/mc;
    //std::cout << "pu weight =" << data/mc << std::endl;
  }//else{
    //std::cout << "No predefined pileup weights" << std::endl;
  //  }
  return 1;
}



Float_t reweightDataPU(Int_t npu){
  // Reweight PU weight, by dividing out old data PU
  float data_new = hist_PU_data->GetBinContent(hist_PU_data->FindBin(npu));
  float data_old = hist_PU_data_old->GetBinContent(hist_PU_data_old->FindBin(npu));
  if(data_old > 0.)
    return data_new/data_old;
  return 1;
}



void pileup(){
  std::cout << ">>> initializing pileup.C ... " << std::endl;
}


