/*
 * @short: provide lepton efficiencies
 * @author: Izaak Neutelings (November 2018)
 *
 */

#include "TROOT.h"
#include "TMath.h"
#include "TFile.h"
#include "TGraphAsymmErrors.h"
#include <iostream>
//
#include <algorithm>
#include <map>
//using namespace std;
//std::map<TString,TH2F*> lepEffs;
//TH2F* lepEff;
//std::map<TString,TGraphAsymmErrors*> lepEffs;
std::map<TString,TGraphAsymmErrors*> effsData;
std::map<TString,TGraphAsymmErrors*> effsMC;
TString path = "/shome/ineuteli/analysis/SFrameAnalysis_ltau2017/plots/PlotTools/lepEff/";

void loadLepEff(TString channel="et"){
  
  TString filename = path+"Electron_Ele35.root";
  std::cout << ">>> opening "<<filename<<std::endl;
  TFile* file = new TFile(filename);
  effsData["EtaLt1p48"] = (TGraphAsymmErrors*) file->Get("ZMassEtaLt1p48_Data");
  effsData["EtaGt1p48"] = (TGraphAsymmErrors*) file->Get("ZMassEta1p48to2p1_Data");
  effsMC["EtaLt1p48"]   = (TGraphAsymmErrors*) file->Get("ZMassEtaLt1p48_MC");
  effsMC["EtaGt1p48"]   = (TGraphAsymmErrors*) file->Get("ZMassEta1p48to2p1_MC");
  
  //for (auto const& x: effsData)
  //  x.second->SetDirectory(0);
  //for (auto const& x: effsMC)
  //  x.second->SetDirectory(0);
  
  //effsData["EtaLt1p48"]->SetDirectory(0);
  file->Close();
  
}


Float_t getTrigEff(const Float_t pt, const Float_t eta){
  Float_t SF   = 0.0;
  Float_t data = 0.0;
  Float_t MC   = 0.0;
  if( fabs(eta)<1.48 ){
    data = effsData["EtaLt1p48"]->Eval(pt);
    MC   = effsMC["EtaLt1p48"]->Eval(pt);
    //std::cout << "data=" << data << ", MC=" << MC << std::endl;
    if(MC>0) SF = data/MC;
  }else{
    data = effsData["EtaGt1p48"]->Eval(pt);
    MC   = effsMC["EtaGt1p48"]->Eval(pt);
    if(MC>0) SF = data/MC;
  }
  return SF;
}



void lepEff(){
  //std::cout << std::endl;
  std::cout << ">>> initializing lepEff.C ... " << std::endl;
  loadLepEff();
  //std::cout << std::endl;
}


