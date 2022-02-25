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
//   Load in python:
//     gROOT.ProcessLine(".L Unroll.cxx+O")
//     from ROOT import Unroll
//   Create unrolled histogram in Tree::Draw:
//     hist2d = TH2D('hist2d',"y vs. x",nxbins,0,100,nybins,0,100) # original 2D for defining bins
//     hist1d = TH2D('hist1d',"Unrolled",nxbins*nybins,1,21) # unrolled with bin numbers 1 to nxbins*nybins
//     Unroll.SetBins(hist2d) # set bin axis globally for unrolling in Unroll::GetBin
//     tree.Draw("Unroll::GetBin(x,y) >> hist1d") # create unrolled 1D histogram (with under/overflow)
//   Unroll existing 2D histogram:
//     gROOT.ProcessLine(".L Unroll.cxx+O")
//     from ROOT import Unroll
//     hist2d = TH2D('hist2d',"y vs. x",nxbins,0,100,nybins,0,100) # original 2D
//     tree.Draw("y:x >> hist2d") # create 2D histogram
//     hist1d = Unroll.Unroll(hist2d,"Unrolled") # unroll 2D to 1D (without under/overflow)
//   Roll back up 1D to 2D histogram:
//     hist2d_rollup = Unroll.RollUp(hist1d,"Rolled up",hist2d) # roll 1D back up to 2D
//   4D migration / response matrix unrolled to 2D:
//     hist4d = TH2D('h_response',"Response",20,1,21,20,1,21) # original 2D
//     tree.Draw("Unroll::GetBin(xgen,ygen):Unroll::GetBin(xreco,yreco) >> h_response")
//   
#include <iostream>
#include <iomanip> // for setw, setprecision
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
  
  Double_t GetBin(Double_t x, Double_t y, const TH2* hist2d, bool transpose=false, bool addoverflow=false) {
    // Get bin number from given 2D histogram for "unrolled" 1D histogram
    assert(hist2d && "Unroll::GetBin: No 2D histogram set for axes!");
    //bin = _hist2d->GetBin(x,y) // includes under/overflow...
    Int_t xbin = hist2d->GetXaxis()->FindBin(x);
    Int_t ybin = hist2d->GetYaxis()->FindBin(y);
    if(addoverflow){ // add overflow to the last bin
      if(xbin>hist2d->GetXaxis()->GetNbins()) xbin -= 1;
      if(ybin>hist2d->GetYaxis()->GetNbins()) ybin -= 1;
    }
    Double_t bin = 0; // unrolled bin
    if(xbin==0 or ybin==0){
      bin = -0.5; // underflow 0
    }else if(xbin>hist2d->GetXaxis()->GetNbins() or ybin>hist2d->GetYaxis()->GetNbins()){
      bin = hist2d->GetXaxis()->GetNbins()*hist2d->GetYaxis()->GetNbins()+1.5; // overflow: nbinsx*nbinsx+1
    }else if(transpose){ // switch x and y axes
      bin = 0.5+hist2d->GetYaxis()->GetNbins()*(xbin-1)+ybin; // range: [1,nbinsx*nbinsx]
    }else{
      bin = 0.5+hist2d->GetXaxis()->GetNbins()*(ybin-1)+xbin; // range: [1,nbinsx*nbinsx]
    }
    return bin;
  }
  
  Double_t GetBin(Double_t x, Double_t y, bool transpose=false, bool addoverflow=false) {
    // Get bin number from global 2D histogram for "unrolled" 1D histogram
    // Useful for TTree::Draw: e.g. tree.Draw("Unroll::GetBin(x,y) >> hist1d")
    return GetBin(x,y,_hist2d,transpose,addoverflow);
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
      for(Int_t xbin=0; xbin<=hist2d->GetXaxis()->GetNbins()+1; xbin++){
        for(Int_t ybin=0; ybin<=hist2d->GetYaxis()->GetNbins()+1; ybin++){
          Int_t bin = GetBin(hist2d->GetXaxis()->GetBinCenter(xbin),hist2d->GetYaxis()->GetBinCenter(ybin),hist2d);
          Double_t zval = hist2d->GetBinContent(xbin,ybin);
          Double_t zerr = hist2d->GetBinError(xbin,ybin);
          if(hist1d->GetBinError(bin)>0.)
            zerr = TMath::Sqrt(zerr*zerr+TMath::Power(hist1d->GetBinError(bin),2));
          if(verb>=2)
            std::cout << ">>> Unroll::Unroll: xbin=" << xbin << ", ybin=" << ybin << ", bin=" << std::setw(2) << bin
                      << ": " << std::fixed << std::setprecision(2) << std::setw(7) << zval << " +- " << std::setw(7) << zerr << std::endl;
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
    assert(hist2d_axes && "Unroll::RollUp: No 2D histogram set for axes!");
    Int_t nxbins = hist2d_axes->GetXaxis()->GetNbins();
    Int_t nybins = hist2d_axes->GetYaxis()->GetNbins();
    Int_t nbins  = nxbins*nybins;
    if(hist1d->GetXaxis()->GetNbins()!=nbins)
      std::cerr << ">>> Unroll::RollUp: Bins between 1D '" << hist1d->GetName() << "' and 2D '" << hist2d_axes->GetName()
                << "' do not match: " << hist1d->GetXaxis()->GetNbins() << " != " << nxbins << " x " << nybins << std::endl;
    if(hname=="")
      hname = TString(hist2d_axes->GetName())+TString("_rolledup");
    TH2D* hist2d = (TH2D*) hist2d_axes->Clone(hname); // reuse axes and any other settings
    for(Int_t xbin=0; xbin<=nxbins+1; xbin++){
      for(Int_t ybin=0; ybin<=nybins+1; ybin++){
        if((xbin==0 or ybin==0) and xbin!=ybin)
          continue; // fill underflow only once in (0,0)
        if((xbin>nxbins and ybin<=nybins) or (xbin<=nxbins and ybin>nybins))
          continue; // fill overflow only once in (nxbins+1,nybins+1)
        Int_t bin = GetBin(hist2d->GetXaxis()->GetBinCenter(xbin),hist2d->GetYaxis()->GetBinCenter(ybin),hist2d);
        Double_t zval = hist1d->GetBinContent(bin);
        Double_t zerr = hist1d->GetBinError(bin);
        if(verb>=2)
          std::cout << ">>> Unroll::RollUp: xbin=" << xbin << ", ybin=" << ybin << ", bin=" << std::setw(2) << bin
                    << ": " << std::fixed << std::setprecision(2) << std::setw(7) << zval << " +- " << std::setw(7) << zerr << std::endl;
        hist2d->SetBinContent(xbin,ybin,zval);
        hist2d->SetBinError(xbin,ybin,zerr);
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
  
  TH1D* Transpose(const TH1* hist1d, TString hname, const Int_t nxbins, const Int_t nybins, int verb=0) {
    // Transpose given unrolled 1D histogram, i.e. switch x and y of 2D and update bin numbering
    // Reconstruct original x and y bin numbers using the original nxbins and nybins.
    if(verb>=1)
      std::cout << ">>> Unroll::Transpose: Transposing '" << hist1d->GetName() << "'... " << std::endl;
    Int_t nbins = nxbins*nybins;
    if(hist1d->GetXaxis()->GetNbins()!=nbins)
      std::cerr << ">>> Unroll::Transpose: Bins of 1D '" << hist1d->GetName() << " do not match: "
                << hist1d->GetXaxis()->GetNbins() << " != " << nxbins << " x " << nybins << std::endl;
    if(hname=="")
      hname = TString(hist1d->GetName())+TString("_transposed");
    TH1D* hist1d_T = (TH1D*) hist1d->Clone(hname); // reuse axes and any other settings
    //if(hist1d->GetBinErrorOption()==TH1::kPoisson){
    //  hist1d_T->SetBinErrorOption(TH1::kPoisson);
    //}
    for(Int_t bin=0; bin<=nbins+1; bin++){
      Int_t xbin = 1+(bin-1)%nxbins; // reconstruct original xbin
      Int_t ybin = 1+(bin-1)/nxbins; // reconstruct original ybin
      assert(bin==nxbins*(ybin-1)+xbin && "Sanity check failed!?!");
      Int_t bin_T = bin; // under-/overflow
      if(0<bin and bin<=nbins){ // not under-/overflow
        bin_T = nybins*(xbin-1)+ybin; // transpose
      }
      Double_t zval = hist1d->GetBinContent(bin);
      Double_t zerr = hist1d->GetBinError(bin);
      if(verb>=2)
        std::cout << ">>> Unroll::Transpose: xbin=" << xbin << ", ybin=" << ybin << ", bin="
                  << std::setw(2) << bin << ", bin_T=" << std::setw(2) << bin_T << ": " << std::fixed << std::setprecision(2)
                  << std::setw(7) << zval << " +- " << std::setw(7) << zerr << std::endl;
      hist1d_T->SetBinContent(bin_T,zval);
      hist1d_T->SetBinError(bin_T,zerr);
    }
    return hist1d_T;
  }
  
  TH1D* Transpose(const TH1* hist1d, const Int_t nxbins, const Int_t nybins, int verb=0) {
    // Transpose given unrolled 1D histogram, i.e. switch x and y of 2D and update bin numbering
    return Transpose(hist1d,"",nxbins,nybins,verb);
  }
  
  TH1D* Transpose(const TH1* hist1d, TString hname, const TH2* hist2d_axes, int verb=0) {
    // Transpose given unrolled 1D histogram, i.e. switch x and y of 2D and update bin numbering
    // Get the original nxbins and nybins from a given 2D histogram
    assert(hist2d_axes && "Unroll::Transpose: No 2D histogram set for axes!");
    Int_t nxbins = hist2d_axes->GetXaxis()->GetNbins();
    Int_t nybins = hist2d_axes->GetYaxis()->GetNbins();
    return Transpose(hist1d,hname,nxbins,nybins,verb);
  }
  
  TH1D* Transpose(const TH1* hist1d, const TH2* hist2d_axes, int verb=0) {
    // Transpose given unrolled 1D histogram, i.e. switch x and y of 2D and update bin numbering
    // Get the original nxbins and nybins from a given 2D histogram
    return Transpose(hist1d,"",hist2d_axes,verb);
  }
  
  TH1D* Transpose(const TH1* hist1d, TString hname="", int verb=0) {
    // Transpose given unrolled 1D histogram, i.e. switch x and y of 2D and update bin numbering
    // Get the original nxbins and nybins from the global 2D histogram
    return Transpose(hist1d,hname,_hist2d,verb);
  }
  
  void DivideByBinSize(TH1* hist1d, const TH2* hist2d_axes=_hist2d, bool transpose=false, int verb=0) {
    // Divide unrolled 1D histogram by bin width in x-axis
    if(verb>=1)
      std::cout << ">>> Unroll::DivideByBinSize: '" << hist1d->GetName() << "'... " << std::endl;
    assert(hist2d_axes && "Unroll::DivideByBinSize: No 2D histogram set for axes!");
    Int_t nxbins = hist2d_axes->GetXaxis()->GetNbins();
    Int_t nybins = hist2d_axes->GetYaxis()->GetNbins();
    Int_t nbins  = nxbins*nybins;
    if(hist1d->GetXaxis()->GetNbins()!=nbins)
      std::cerr << ">>> Unroll::DivideByBinSize: Bins between 1D '" << hist1d->GetName() << "' and 2D '" << hist2d_axes->GetName()
                << "' do not match: " << hist1d->GetXaxis()->GetNbins() << " != " << nxbins << " x " << nybins << std::endl;
    for(Int_t xbin=1; xbin<=nxbins; xbin++){
      for(Int_t ybin=1; ybin<=nybins; ybin++){
        Double_t width = (transpose ? hist2d_axes->GetYaxis()->GetBinWidth(ybin) : hist2d_axes->GetXaxis()->GetBinWidth(xbin));
        if(width<=0) continue;
        Int_t bin = GetBin(hist2d_axes->GetXaxis()->GetBinCenter(xbin),hist2d_axes->GetYaxis()->GetBinCenter(ybin),hist2d_axes,transpose);
        Double_t zval = hist1d->GetBinContent(bin);
        Double_t zerr = hist1d->GetBinError(bin);
        if(verb>=2)
          std::cout << ">>> Unroll::DivideByBinSize: xbin=" << xbin << ", ybin=" << ybin << ", bin=" << std::setw(2) << bin << ", width=" << width
                    << ": " << std::fixed << std::setprecision(2) << std::setw(7) << zval << " +- " << std::setw(7) << zerr
                    << " -> " << std::setw(7) << zval/width << " +- " << std::setw(7) << zerr/width << std::endl;
        hist1d->SetBinContent(bin,zval/width);
        hist1d->SetBinError(bin,zerr/width);
      }
    }
  }
  
}

//void Unroll() {
//  std::cout << ">>> Initialize Unroll.cxx ... " << std::endl;
//}
