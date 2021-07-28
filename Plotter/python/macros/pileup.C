/*
 * @short: Provide pileup weights at drawing level
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

TString _fname_data = "../PicoProducer/data/pileup/Data_PileUp_UL2017_69p2.root";
TString _fname_MC = "../PicoProducer/data/pileup/MC_PileUp_UL2017_Summer19.root";
TH1F* hist_PU_data;
TH1F* hist_PU_MC;
//TH1F* hist_PU_weights;


TH1F* getPUHist(TString fname, TString hname="pileup"){
  std::cout << ">>> Loading histogram " << hname << " from " << fname << std::endl;
  TFile *file = new TFile(fname);
  TH1F* hist = (TH1F*) file->Get(hname);
  hist->SetDirectory(0);
  hist->Scale(1./hist->Integral());
  file->Close();
  return hist;
}


void loadPU(TString fname_data=_fname_data,TString fname_MC=_fname_MC){
  hist_PU_data = getPUHist(fname_data);
  hist_PU_MC = getPUHist(fname_MC);
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


void pileup(){
  std::cout << ">>> Initializing pileup.C ... " << std::endl;
}

