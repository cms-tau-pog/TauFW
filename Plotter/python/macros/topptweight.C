/*
 * @short: Macro to compute top pT reweighting
 * @author: Izaak Neutelings (July 2021)
 *
 */

#include <iostream>
#include "TMath.h"
//using namespace std;

// https://twiki.cern.ch/twiki/bin/viewauth/CMS/TopPtReweighting#TOP_PAG_corrections_based_on_the
Float_t _toppt_a =  0.0615; // Data / POWHEG+Pythia8
Float_t _toppt_b = -0.0005; // Data / POWHEG+Pythia8

Bool_t setTopPt(Float_t a, Float_t b){
  // Change parameters
  Bool_t changed = a!=_toppt_a or b!=_toppt_b;
  _toppt_a = a;
  _toppt_b = b;
  return changed;
}

Float_t getTopPtSF(Float_t toppt, Float_t a=_toppt_a, Float_t b=_toppt_b){
  // f = TF1("f","TMath::Exp(0.0615-0.0005*x)",0,1000); f.Draw()
  return TMath::Exp(a+b*toppt);
}

Float_t getTopPtWeight(Float_t toppt1, Float_t toppt2){
  return getTopPtSF(toppt1)*getTopPtSF(toppt2);
}

Float_t getTopPtSF_NNLO(Float_t toppt){
  // NNLO/NLO top pT reweighting function for a single top
  // f = TF1("f","0.103*TMath::Exp(-0.0118*x)-0.000134*x+0.973",0,1000); f.Draw()
  return 0.103*TMath::Exp(-0.0118*toppt)-0.000134*toppt+0.973;
}

Float_t getTopPtWeight_NNLO(Float_t toppt1, Float_t toppt2){
  // NNLO/NLO top pT reweighting function for two tops
  return getTopPtSF_NNLO(toppt1)*getTopPtSF_NNLO(toppt2);
}

void topptweight(){
  std::cout << ">>> Opening topptweight.C ... " << std::endl;
}

