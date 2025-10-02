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
#include "TSystem.h" // for gSystem
using namespace std;
TString _datadir_pu = gSystem->ExpandPathName("$CMSSW_BASE/src/TauFW/PicoProducer/data/pileup");
TString _fname_pu_data = _datadir_pu+"/Data_PileUp_UL2018_69p2.root";
TString _fname_pu_mc = _datadir_pu+"/MC_PileUp_UL2018.root";
TH1F* _hist_pu_data;
TH1F* _hist_pu_mc;


TH1F* getPUHist(TString filename, TString histname="pileup"){
  std::cout << ">>> opening " << filename << std::endl;
  TFile *file = new TFile(filename);
  TH1F* hist = (TH1F*) file->Get(histname);
  hist->SetDirectory(0);
  hist->Scale(1./hist->Integral());
  file->Close();
  return hist;
}


void readPUFile(TString filename_data=_fname_pu_data,TString filename_mc=_fname_pu_mc){
  _hist_pu_data = getPUHist(filename_data);
  _hist_pu_mc = getPUHist(filename_mc);
}


Float_t getPUWeight(Int_t npu){
  float data = _hist_pu_data->GetBinContent(_hist_pu_data->FindBin(npu));
  float mc   = _hist_pu_mc->GetBinContent(_hist_pu_mc->FindBin(npu));
  //std::cout << data << " " << mc << " " << npu << " -> " << data/mc << std::endl;
  if(mc > 0.){
    return data/mc;
    //std::cout << "pu weight =" << data/mc << std::endl;
  }//else{
    //std::cout << "No predefined pileup weights" << std::endl;
  //  }
  return 1.0;
}


void pileup(){
  std::cout << ">>> initializing pileup.C ... " << std::endl;
}

