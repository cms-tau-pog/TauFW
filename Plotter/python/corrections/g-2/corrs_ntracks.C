/*
 * @short: Provide PU and HS corrections
 * @author: Izaak Neutelings (July 2023)
 * @description: https://ineuteli.web.cern.ch/ineuteli/g-2/plots/ntracks_pu/
 *
 */
//#define corrs_ntracks_C
#include <iostream>
#include <algorithm>
#include <map>
#include "TROOT.h"
#include "TFile.h"
#include "TSystem.h" // for gSystem
//#include "TH1D.h"
#include "TH2D.h"
using namespace std;

// corrections_map
TString _corrdir_gmin2 = gSystem->ExpandPathName("$CMSSW_BASE/src/TauFW/Plotter/plots/g-2");
Int_t _iera = -1;
std::map<Int_t,TH2D*> corrs_hstracks;
std::map<Int_t,TH2D*> corrs_putracks;

Int_t getEraIndex(TString era){
  Int_t iera = _iera; // era index
  if(era=="UL2016_preVFP")       iera = 0;
  else if(era=="UL2016_postVFP") iera = 1;
  else if(era=="UL2017")         iera = 2;
  else if(era=="UL2018")         iera = 3;
  return iera;
}

void loadPUTrackWeights(const TString era, int verb=0){ //TString fname, 
  // https://github.com/cecilecaillol/MyNanoAnalyzer/blob/59f08466bedce37c2b77d6d950924e3ab9e7bcb8/NtupleAnalyzerCecile/FinalSelection_etau.cc#L1246-L1257
  ///TString fname = indir + "correction_acoplanarity_fine_"+year+".root"
  if(era=="Run2"){
    loadPUTrackWeights("UL2016_preVFP");
    loadPUTrackWeights("UL2016_postVFP");
    loadPUTrackWeights("UL2017");
    loadPUTrackWeights("UL2018");
  }else{
    Int_t iera = getEraIndex(era);
    TString fname = TString::Format(_corrdir_gmin2+"/ntracks_pu/corrs_ntracks_pu_%s.root",era.Data());
    if(verb>=1)
      std::cout << ">>> loadPUTrackWeights: Loading " << fname << "..." << std::endl;
    TFile* file = new TFile(fname,"READ");
    corrs_putracks[iera] = (TH2D*) file->Get("corr");
    corrs_putracks[iera]->SetDirectory(0);
    file->Close();
    _iera = iera; // set global default
  }
}

void loadHSTrackWeights(const TString era, int verb=0){ //TString fname, 
  // https://github.com/cecilecaillol/MyNanoAnalyzer/blob/59f08466bedce37c2b77d6d950924e3ab9e7bcb8/NtupleAnalyzerCecile/FinalSelection_etau.cc#L1246-L1257
  ///TString indir = "$CMSSW_DIR/src/TauFW/Plotter/python/corrections/";
  ///TString fname = indir + "correction_acoplanarity_fine_"+year+".root"
  //std::cout << ">>> loadPUTrackWeights: Loading" << fname << std::endl;
  if(era=="Run2"){
    loadHSTrackWeights("UL2016_preVFP");
    loadHSTrackWeights("UL2016_postVFP");
    loadHSTrackWeights("UL2017");
    loadHSTrackWeights("UL2018");
  }else{
    Int_t iera = getEraIndex(era);
    TString fname = TString::Format(_corrdir_gmin2+"/ntracks_hs/corrs_ntracks_hs_%s.root",era.Data());
    if(verb>=1)
      std::cout << ">>> loadHSTrackWeights: Loading " << fname << "..." << std::endl;
    TFile* file = new TFile(fname,"READ");
    corrs_hstracks[iera] = (TH2D*) file->Get("correction_map");
    corrs_hstracks[iera]->SetDirectory(0);
    file->Close();
    _iera = iera; // set global default
  }
}

Float_t getPUTrackWeight(const Int_t ntracks_pu, const Float_t z, const Int_t iera=_iera){
  return corrs_putracks[iera]->GetBinContent(corrs_putracks[iera]->GetXaxis()->FindBin(ntracks_pu),corrs_putracks[iera]->GetYaxis()->FindBin(z));
}

Float_t getHSTrackWeight(const Int_t ntracks_hs, const Float_t aco, const Int_t iera=_iera){
  return corrs_hstracks[iera]->GetBinContent(corrs_hstracks[iera]->GetXaxis()->FindBin(ntracks_hs),corrs_hstracks[iera]->GetYaxis()->FindBin(aco));
}

void pileup_tracks(){
  std::cout << ">>> Initializing ntracks_pileup.C ... " << std::endl;
}
