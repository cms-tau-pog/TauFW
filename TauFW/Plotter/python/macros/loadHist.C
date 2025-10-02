/*
 * @short: General macro to load histogram from ROOT file
 * @author: Izaak Neutelings (July 2021)
 *   
 *   import ROOT
 *   ROOT.gROOT.ProcessLine(".L loadHist.C+O") # compile macro
 *   
 *   ROOT.loadHist("weight.root","weight") # load histogram from file
 *   tree.Draw("m_vis >> h","(pt_1>20 && pt_2>20)*getBin(pt_1)")
 *   
 *   tree.SetAlias("sf","getBin(dm_2,+0)")
 *   tree.Draw("m_vis >> h","(pt_1>20 && pt_2>20 && idDeepTau2017v2p1VSjet_2>=16)*sf")
 *
 */
#include <iostream>
#include <map>
#include "TFile.h"
#include "TH1.h"

TH1* _lh_hist;
std::map<TString,TH1*> _lh_hists;
//enum class HistSyst { Nom, Up, Down }; // does not work in pyROOT ?

void loadHist(){
  std::cout << ">>> Opening loadHist.C ... " << std::endl;
}

TH1* loadHist(TString fname, TString hname, TString key=""){
  // Load histogram from ROOT file
  if(key=="")
    key = hname;
  TFile* file = TFile::Open(fname);
  if(!file or file->IsZombie()){
    std::cerr << "loadHist.C::loadHist: Could not open file "<<fname<<"!";
  }
  TH1* hist = (TH1*) file->Get(hname); // assume either TH1 or TH2
  if(!hist){
    std::cerr << "loadHist.C::loadHist: Could not open histogram "<<hname<<"!";
  }
  hist->SetDirectory(0); // detach from file before closing
  _lh_hist = hist; // default histogram for getBin
  _lh_hists[hname] = hist; // store by key for parallel use of multiple histogram
  file->Close();
  return hist;
}

TH1* loadHist(TString hname){
  // Set default histogram to given key stored in map
  _lh_hist = _lh_hists[hname]; // default histogram for getBin
  return _lh_hist;
}

void closeHist(TH1* hist){
  if(hist->GetDirectory()) hist->GetDirectory()->Delete(hist->GetName());
  else hist->Delete();
}

void closeHist(TString hname=""){
  if(hname) closeHist(_lh_hists[hname]);
  else closeHist(_lh_hist);
}

Float_t getBin1D(TH1* hist, Float_t x, Int_t stddev=0){
  // Get bin content from given 1D histogram
  // @param stddev Standard deviation: -1 (down), 0 (nominal), +1 (up)
  Int_t xbin = hist->GetXaxis()->FindBin(x);
  Float_t binc = hist->GetBinContent(xbin);
  if(stddev!=0) binc += stddev*hist->GetBinError(xbin);
  return binc;
}

Float_t getBin2D(TH1* hist, Float_t x, Float_t y, Int_t stddev=0){
  // Get bin content from given 2D histogram
  Int_t xbin = hist->GetXaxis()->FindBin(x);
  Int_t ybin = hist->GetYaxis()->FindBin(y);
  Float_t binc = hist->GetBinContent(xbin,ybin);
  if(stddev!=0) binc += stddev*hist->GetBinError(xbin,ybin);
  return binc;
}

Float_t getBin(Float_t x, Int_t stddev=0){
  // Get bin content from default 1D histogram
  return getBin1D(_lh_hist,x,stddev);
}

Float_t getBin2D(Float_t x, Float_t y, Int_t stddev=0){
  // Get bin content from default 2D histogram
  return getBin2D(_lh_hist,x,y,stddev);
}

Float_t getBin(TString hname, Float_t x, Int_t stddev=0){
  // Get bin content from 1D histogram by key
  return getBin1D(_lh_hists[hname],x,stddev);
}

Float_t getBin2D(TString hname, Float_t x, Float_t y, Int_t stddev=0){
  // Get bin content from 2D histogram by key
  return getBin2D(_lh_hists[hname],x,y,stddev);
}
