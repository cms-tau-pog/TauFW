// Author: Izaak Neutelings (May 2021)
// Description:
//   Macro with help functions to unroll 2D histogram in TTree::Draw() to 1D histogram
//   with bin bin numbers, excluding under/overflow.
//   E.g. 2D histogram (4x5):
//     +----+----+----+----+----+
//   y | 16 | 17 | 18 | 19 | 20 |
//     +----+----+----+----+----+
//     | 11 | 12 | 13 | 14 | 15 |
//     +----+----+----+----+----+
//     |  6 |  7 |  8 |  9 | 10 |
//     +----+----+----+----+----+
//     |  1 |  2 |  3 |  4 |  5 |
//     +----+----+----+----+----+--> x axis
//
//   Unrolled 1D histogram:
//     +---+---+---+---+---+--     --+----+
//     | 1 | 2 | 3 | 4 | 5 |   ...   | 20 |
//     +---+---+---+---+---+--     --+----+--> x axis
//     1   2   3   4   5   6        20   21
//
//   In python:
//     gROOT.ProcessLine(".L Unroll.cxx+O")
//     from ROOT import Unroll
//     hist2d = TH2D('hist2d',"y vs. x",5,0,100,4,0,100) # original 2D
//     hist1d = TH2D('hist1d',"Unrolled",20,1,21) # unrolled with bin numbers 1 to nxbins*nybins
//     tree.Draw("y:x >> hist2d")
//     Unroll.SetBins(hist2d) # set axis globally for unrolling in Unroll::GetBin
//     tree.Draw("Unroll::GetBin(x,y) >> hist1d") # unrolled
//     hist1d_unroll = Unroll.Unroll(hist2d,"Unrolled") # unroll 2D to 1D
//     hist2d_rollup = Unroll.RollUp(hist1d,"Rolled up",hist2d) # roll 1D back up to 2D
//   
//   4D migration / response matrix unrolled to 2D:
//     hist4d = TH2D('h_response',"Response",20,1,21,20,1,21) # original 2D
//     tree.Draw("Unroll::GetBin(xgen,ygen):Unroll::GetBin(xreco,yreco) >> h_response")
//   
#include <iostream>
#include "TROOT.h"
#include "TMath.h"
#include "TH2.h"
#include "TH1D.h"
#include "TH2D.h"

namespace Unroll {

  TH2* _hist2d; // global histogram to define axes unrolling
  
  Int_t SetBins(TH2* hist2d, int verb=0) {
    // Set 2D histogram to use axes from during unrolling
    assert(hist2d && "Unroll::SetBins: No 2D histogram set for axes!");
    Int_t nxbins = hist2d->GetXaxis()->GetNbins();
    Int_t nybins = hist2d->GetYaxis()->GetNbins();
    if(verb>=1)
      std::cout << ">>> Unroll::SetBins: Setting unroll bins to '" << hist2d->GetName() << "' ("
                << nxbins << "x" << nybins << ")... " << std::endl;
    _hist2d = (TH2*) hist2d->Clone("axes");
    _hist2d->SetDirectory(0);
    return nxbins*nybins;
  }
  
  Double_t GetBin(Double_t x, Double_t y, const TH2* hist2d) {
    // Get bin number from given 2D histogram for "unrolled" 1D histogram
    assert(hist2d && "Unroll::GetBin: No 2D histogram set for axes!");
    //bin = _hist2d->GetBin(x,y) // includes under/overflow...
    Int_t xbin = hist2d->GetXaxis()->FindBin(x);
    Int_t ybin = hist2d->GetYaxis()->FindBin(y);
    Double_t bin = 0; // unrolled bin
    if(xbin==0 or ybin==0){
      bin = -0.5; // underflow 0
    }else if(xbin>hist2d->GetXaxis()->GetNbins() or ybin>hist2d->GetYaxis()->GetNbins()){
      bin = hist2d->GetXaxis()->GetNbins()*hist2d->GetYaxis()->GetNbins()+1.5; // overflow nbinsx*nbinsx+1
    }else{
      bin = 0.5+hist2d->GetXaxis()->GetNbins()*(ybin-1)+xbin; // range: [1,nbinsx*nbinsx]
    }
    return bin;
  }
  
  Double_t GetBin(Double_t x, Double_t y) {
    // Get bin number from global 2D histogram for "unrolled" 1D histogram
    // Useful for TTree::Draw: e.g. tree.Draw("Unroll::GetBin(x,y) >> hist1d")
    return GetBin(x,y,_hist2d);
  }
  
  TH1D* Unroll(const TH2* hist2d, TString hname="", bool empty=false, int verb=0) {
    // Unroll 2D histogram without under/overflow
    if(verb>=1)
      std::cout << ">>> Unroll::Unroll: Unrolling '" << hist2d->GetName() << "'... " << std::endl;
    Int_t nxbins = hist2d->GetXaxis()->GetNbins();
    Int_t nybins = hist2d->GetYaxis()->GetNbins();
    Int_t nbins = nxbins*nybins;
    if(hname=="")
      hname = TString(hist2d->GetName())+TString("_unrolled");
    TH1D* hist1d = new TH1D(hname,hname,nbins,1.,1.+nbins);
    if(!empty){
      for(Int_t ix=0; ix<=hist2d->GetXaxis()->GetNbins()+1; ix++){
        for(Int_t iy=0; iy<=hist2d->GetYaxis()->GetNbins()+1; iy++){
          Int_t bin = GetBin(hist2d->GetXaxis()->GetBinCenter(ix),hist2d->GetYaxis()->GetBinCenter(iy),hist2d);
          Double_t zval = hist2d->GetBinContent(ix,iy);
          Double_t zerr = hist2d->GetBinError(ix,iy);
          if(hist1d->GetBinError(bin)>0.)
            zerr = TMath::Sqrt(zerr*zerr+TMath::Power(hist1d->GetBinError(bin),2));
          if(verb>=2)
            std::cout << ">>> Unroll::Unroll: ix=" << ix << ", iy=" << iy << ", bin=" << bin
                      << ": " << zval << " +- " << zerr << std::endl;
          hist1d->SetBinContent(bin,hist1d->GetBinContent(bin)+zval);
          hist1d->SetBinError(bin,zerr);
        }
      }
    }
    return hist1d;
  }
  
  TH2D* RollUp(const TH1* hist1d, TString hname, const TH2* hist2d_axes, int verb=0) {
    // Roll back up 1D histogram to a 2D histogram using the axes of a given 2D histogram
    if(verb>=1)
      std::cout << ">>> Unroll::RollUp: Rolling up '" << hist1d->GetName() << "'... " << std::endl;
    assert(hist2d && "Unroll::GetBin: No 2D histogram set for axes!");
    Int_t nxbins = hist2d_axes->GetXaxis()->GetNbins();
    Int_t nybins = hist2d_axes->GetYaxis()->GetNbins();
    Int_t nbins = nxbins*nybins;
    if(hist1d->GetXaxis()->GetNbins()!=nbins)
      std::cerr << ">>> Unroll::RollUp: Bins between 1D '" << hist1d->GetName() << "' and 2D '" << hist2d_axes->GetName()
                << "' do not match: " << hist1d->GetXaxis()->GetNbins() << " != " << nxbins << " x " << nybins << std::endl;
    if(hname=="")
      hname = TString(hist2d_axes->GetName())+TString("_rolledup");
    TH2D* hist2d = (TH2D*) hist2d_axes->Clone(hname); // reuse axes and any other settings
    for(Int_t ix=0; ix<=nxbins+1; ix++){
      for(Int_t iy=0; iy<=nybins+1; iy++){
        if((ix==0 or iy==0) and ix!=iy)
          continue; // fill underflow only once in (0,0)
        if((ix>nxbins and iy<=nybins) or (ix<=nxbins and iy>nybins))
          continue; // fill overflow only once in (nxbins+1,nybins+1)
        Int_t bin = GetBin(hist2d->GetXaxis()->GetBinCenter(ix),hist2d->GetYaxis()->GetBinCenter(iy),hist2d);
        Double_t zval = hist1d->GetBinContent(bin);
        Double_t zerr = hist1d->GetBinError(bin);
        if(verb>=2)
          std::cout << ">>> Unroll::RollUp: ix=" << ix << ", iy=" << iy << ", bin=" << bin
                    << ": " << zval << " +- " << zerr << std::endl;
        hist2d->SetBinContent(ix,iy,zval);
        hist2d->SetBinError(ix,iy,zerr);
      }
    }
    return hist2d;
  }
  
  TH2D* RollUp(const TH1* hist1d, const TH2* hist2d_axes, int verb=0) {
    // Roll back up 1D histogram to a 2D histogram using the axes of a given 2D histogram
    return RollUp(hist1d,"",hist2d_axes,verb);
  }
  
  TH2D* RollUp(const TH1* hist1d, TString hname="", int verb=0) {
    // Roll back up 1D histogram to a 2D histogram using the axes of the global 2D histogram
    return RollUp(hist1d,hname,_hist2d,verb);
  }
  
}

//void Unroll() {
//  std::cout << ">>> Initialize Unroll.cxx ... " << std::endl;
//}
