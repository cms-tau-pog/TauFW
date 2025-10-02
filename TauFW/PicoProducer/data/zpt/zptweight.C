/* @short: provide Z pt weights at drawing level for checks
 * @author: Izaak Neutelings (June 2018)
 * @comment: in python:
 *   gROOT.Macro('weights/zptweight.C+')
 *   from ROOT import loadZptWeights
 *   loadZptWeights("weights.root","zpt_weight")
 *   tree.Draw("pt_ll >> h","(pt_1>20 && pt_2>30)*getZptWeight(pt_moth)",'gOff')
 */
#include "TROOT.h"
#include "TFile.h"
#include "TH1.h"
//#include "TH2.h"
//#include "TH1F.h"
//#include "TH2F.h"
#include <iostream>
#include <algorithm>
using namespace std;

TString _fname = "weights/zpt_weights_$ERA$TAG.root";
//TString _fname = "$CMSSW_BASE/src/TauFWFitter/Zpt/weights/$ERA/zpt_weights_$ERA$TAG.root";
TString _hname = "zptweight";
TH1* histZpt;
//TH2F* histZpt;

TString setZptFile(TString fname){
  _fname = fname;
  return fname;
}

void loadZptWeights(TString fname="2017", TString hname=_hname, TString tag=""){
  if(!fname.EndsWith(".root")){ // replace $-keys in file pattern _fname
    fname = _fname.Copy().ReplaceAll("$ERA",fname).ReplaceAll("$TAG",tag);
    if(hname.Contains("zptmass")) // 2D weights
      fname = fname.Copy().ReplaceAll("zpt_weight","zptmass_weight");
  }
  std::cout << ">>> loadZptWeights(): opening " << fname << ":" << hname << std::endl;
  if(histZpt)
    histZpt->Delete();
  TFile *file = new TFile(fname);
  histZpt = (TH1*) file->Get(hname); // allows both TH1 and TH2
  if(!histZpt){
    std::cerr << ">>> loadZptWeights(): Did not find " << hname << " in " << fname << std::endl;
    file->ls();
  }
  histZpt->SetDirectory(0);
  file->Close();
}

Float_t getZptWeight(Float_t pt){
  Int_t xbin = histZpt->GetXaxis()->FindBin(pt);
  Float_t weight = 1.0;
  while(xbin<1) xbin++;
  while(xbin>histZpt->GetXaxis()->GetNbins()) xbin--;
  weight = histZpt->GetBinContent(xbin);
  if(weight<=0.0) return 1.;
  return histZpt->GetBinContent(xbin);
}

Float_t getZptWeight(Float_t pt, Float_t mass){
  Int_t xbin = histZpt->GetXaxis()->FindBin(pt);
  Int_t ybin = histZpt->GetYaxis()->FindBin(mass);
  Float_t weight = 1.0;
  while(xbin<1) xbin++; while(xbin>histZpt->GetXaxis()->GetNbins()) xbin--;
  while(ybin<1) ybin++; while(ybin>histZpt->GetYaxis()->GetNbins()) ybin--;
  weight = histZpt->GetBinContent(xbin,ybin);
  if(weight<=0.0) return 1.;
  return histZpt->GetBinContent(xbin,ybin);
}

void zptweight(){
  std::cout << ">>> initializing zptweight.C ... " << std::endl;
}

