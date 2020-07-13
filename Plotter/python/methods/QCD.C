/*
  functionmacro.C : provide QCD weights at drawing level
  modified from : https://github.com/CMS-HTT/QCDModelingEMu

  4 April 2017 Y.T
 */


#include "TMath.h"
#include "TFile.h"
#include "TH1.h"
#include "TH2.h"
#include <iostream>
#include "TROOT.h"

TH2F* h_weight[3];
Int_t nBinsQCD;
Float_t qcdMin;
Float_t qcdMax;



void readQCDFile_emu(){
  
  TFile *file = new TFile("/shome/ineuteli/analysis/SFrameAnalysis_Moriond/plots/PlotTools/QCDModelingEMu/data/QCD_weight_emu_2016BtoH.root");
  
  for(int dr=0; dr < 3; dr++){
    
    TString wname = "QCDratio_CR1_dR";
    if(dr==0) wname += "Lt2";
    else if(dr==1) wname += "2to4";
    else if(dr==2) wname += "Gt4";
    
    //std::cout << wname << " is read" << std::endl;

    h_weight[dr] = (TH2F*) gROOT->FindObject(wname);

    if(dr==0){
      nBinsQCD = h_weight[dr]->GetNbinsX();
      qcdMin = h_weight[dr]->GetXaxis()->GetBinLowEdge(1);
      qcdMax = h_weight[dr]->GetXaxis()->GetBinLowEdge(1+nBinsQCD);
    }
  }    
  
  //std::cout << "nBinsQCD, pt_min, pt_max = " << nBinsQCD << " " << qcdMin << " " << qcdMax << std::endl;
  //delete file;
}



float getQCDWeight(Double_t pt_1, Double_t pt_2, Double_t dr_tt){
  float ptlead  = pt_1;
  float pttrail = pt_2;
  
  if (ptlead<pttrail){
    ptlead  = pt_2;
    pttrail = pt_1;
  }
  
  if (ptlead>qcdMax)  ptlead = qcdMax-0.1;  
  if (ptlead<qcdMin)  ptlead = qcdMin+0.1; 
  if (pttrail>qcdMax) pttrail = qcdMax-0.1;  
  if (pttrail<qcdMin) pttrail = qcdMin+0.1; 
  
  float qcdweight = 1;
  
  int bin = -1;
  if(dr_tt < 2) bin = 0;
  else if(dr_tt >= 2 && dr_tt < 4) bin = 1;
  else if(dr_tt >= 4) bin = 2;
  else{
    std::cout << "Invalid dR ... !   ... return 1" << std::endl;
    return 1;
  }
  
  qcdweight = h_weight[bin]->GetBinContent(h_weight[bin]->FindBin(pttrail,ptlead));  
  //std::cout << "(pt_1, pt_2, dr, weight) = " << pt_1 << " " << pt_2 << " " << dr_tt << " " << qcdweight << std::endl;
  return qcdweight;
}



// Int_t isoRegion(Float_t lep_iso_1, Int_t tau_idMVA_2){
//   // Compress isolation region for ltau channel:
//   //  0: lepton and tau fail isolation
//   //  1: 0.15 < lep iso < 0.30, tau passes Tight (16)
//   //  2:        lep iso < 0.15, tau passes Tight (16)
//   if(tau_idMVA_2<16) return 0;
//   if(lep_iso_1<0.15) return 1;
//   if(lep_iso_1<0.30) return 2;
//   return 0;
// }


Int_t isoRegion(Int_t tau_idMVA_1, Int_t tau_idMVA_2, int wp_tight=16){
  // Compress isolation region for ditau channel:
  //  0: both taus fail Loose (4) WP
  //  1: one tau passes Medium (8), one tau passes Loose (4) but fails Tight (16)
  //     (tau_idMVA_1>=8 && tau_idMVA_2<16 && tau_idMVA_2>=4) || (tau_idMVA_2>=8 && tau_idMVA_1<16 && tau_idMVA_1>=4)
  //  2: both taus pass Tight (16)
  //
  //      T |  1  1  2
  //      M |  1  1  1
  //     _L_|__0__1__1__
  //        |  L  M  T
  //
  //std::cout << "isoRegion: " << tau_idMVA_1 << ", " << tau_idMVA_2 << std::endl;
  int wp_medium = wp_tight/2;
  int wp_loose  = wp_tight/4;
  if(tau_idMVA_1>=wp_tight){ // tau 1 passes Tight
    if(     tau_idMVA_2>=wp_tight) return 2;
    else if(tau_idMVA_2>=wp_loose) return 1;
  }
  else if(tau_idMVA_1>=wp_medium and tau_idMVA_2>=wp_loose){ // tau 1 fails Tight, but passes Medium
    return 1;
  }
  else if(tau_idMVA_1>=wp_loose and tau_idMVA_2>=wp_medium){  // tau 1 fails Medium, but passes Loose
    return 1;
  }
  return 0;
}

Int_t signRegion(Int_t q_1,Int_t q_2){
  //std::cout << "isoRegion: " << q_1 << ", " << q_2 << " => " << q_1*q_2 << std::endl;
  return q_1*q_2;
}


void QCD(){
  //std::cout << std::endl;
  std::cout << ">>> initializing QCD.C ... " << std::endl;
  //std::cout << std::endl;
  //readQCDFile_emu();
}


