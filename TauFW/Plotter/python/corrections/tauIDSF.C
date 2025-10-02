/*
 * @short: Simple macro to load DM-dependent tau ID SF from ROOT file
 * @author: Izaak Neutelings (July 2021)
 *   
 *   import ROOT
 *   ROOT.gROOT.ProcessLine(".L python/macros/tauIDSF.C+O") # compile macro
 *   
 *   fname = "TauID_SF_dm_DeepTau2017v2p1VSjet_2016Legacy_ptgt20.root"
 *   ROOT.loadHist(fname,"Medium") # load histogram from file
 *   tree.Draw("m_vis >> h","(pt_1>20 && pt_2>20 && idDeepTau2017v2p1VSjet_2>=16)*getTauIDSF(dm_2,genmatch_2)")
 *   
 *   tree.SetAlias("sf","getTauIDSF(dm_2,genmatch_2,+0)")
 *   tree.SetAlias("sfDown","getTauIDSF(dm_2,genmatch_2,-1)")
 *   tree.SetAlias("sfUp","getTauIDSF(dm_2,genmatch_2,+1)")
 *   tree.Draw("m_vis >> h","(pt_1>20 && pt_2>20 && idDeepTau2017v2p1VSjet_2>=16)*sf")
 *   
 */
#include <iostream>
#include <map>
#include "TFile.h"
#include "TH1D.h"

TH1D* _tid_hist;
std::map<TString,TH1D*> _tid_hists;
//enum class TIDSyst { Nom, Up, Down }; // does not compile or work in pyROOT ?
//enum TIDSyst { TIDNom=0, TIDUp=1, TIDDown=-1 }; // does not compile or work in pyROOT ?

void tauIDSF(){
  std::cout << ">>> Opening tauIDSF.C ... " << std::endl;
}

TH1D* loadTauIDSF(TString fname, TString hname){
  TFile* file = TFile::Open(fname);
  if(!file or file->IsZombie()){
    std::cerr << "tauIDSF.C::tauIDSF: Could not open file "<<fname<<"!";
  }
  TH1D* hist = (TH1D*) file->Get(hname);
  if(!hist){
    std::cerr << "tauIDSF.C::tauIDSF: Could not open histogram "<<hname<<"!";
  }
  hist->SetDirectory(0); // detach from file before closing
  _tid_hist = hist; // default histogram for loading SFs
  _tid_hists[hname] = hist; // for parallel use of multiple histogram
  file->Close();
  return hist;
}

void closeTauIDSF(TH1D* hist){
  if(hist->GetDirectory()) hist->GetDirectory()->Delete(hist->GetName());
  else hist->Delete();
}

void closeTauIDSF(TString hname=""){
  if(hname) closeTauIDSF(_tid_hists[hname]);
  else closeTauIDSF(_tid_hist);
}

Float_t getTauIDSF(Int_t dm, Int_t gm=5, Int_t stddev=0){
  // Get SF from given histogram
  // @param stddev Standard deviation: -1 (down), 0 (nominal), +1 (up)
  if(gm!=5) return 1.0; // only apply to genmatch==5 (real tau)
  Int_t xbin = _tid_hist->GetXaxis()->FindBin(dm);
  Float_t sf = _tid_hist->GetBinContent(xbin);
  if(stddev!=0) sf += stddev*_tid_hist->GetBinError(xbin);
  return sf;
}
