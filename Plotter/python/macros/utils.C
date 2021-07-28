/*
 * @short: Some basic functions to use at drawing level
 * @author: Izaak Neutelings (July 2021)
 *   
 *   import ROOT
 *   ROOT.gROOT.ProcessLine(".L utils.C+O") # compile macro
 *   tree.Draw("DeltaPhi(phi1,phi2) >> h","pt_1>20 && pt_2>20")
 *   tree.SetAlias("dR","DeltaR(eta1,phi1,eta2,phi2)")
 *   tree.Draw("dR >> h","pt_1>20 && pt_2>20")
 *
 */

#include <iostream>
#include "TMath.h"
//#include "TLorentzVector.h"


Float_t DeltaPhi(Float_t phi1, Float_t phi2){
  // DeltaPhi between two angles in [-pi,pi]
  Float_t dphi = phi1-phi2;
  while(dphi>TMath::Pi())  dphi -= 2*TMath::Pi();
  while(dphi<-TMath::Pi()) dphi += 2*TMath::Pi();
  return dphi;
}


Float_t DeltaPhi2Pi(Float_t phi1, Float_t phi2){
  // DeltaPhi between two angles in [0,2pi]
  Float_t dphi = TMath::Abs(phi1-phi2);
  while(dphi>2*TMath::Pi()) dphi -= 2*TMath::Pi();
  return dphi;
}


Float_t DeltaR(Float_t eta1, Float_t phi1, Float_t eta2, Float_t phi2){
  // DeltaR between two lorentz vectors given by eta and phi
  Float_t deta = eta1-eta2;
  Float_t dphi = DeltaPhi(phi1,phi2);
  return TMath::Sqrt(deta*deta+dphi*dphi);
}


Float_t Mom(Float_t pt, Float_t eta){
  // Full 3-momentum
  return pt*TMath::CosH(eta);
}


Float_t InvMass(Float_t pt1, Float_t eta1, Float_t phi1,
                Float_t pt2, Float_t eta2, Float_t phi2){
  // Invariant mass without using TLorentzVector, assuming E >> m
  // https://en.wikipedia.org/wiki/Invariant_mass#Collider_experiments
  //std::cout << "InvMass: cosh(eta1-eta2)="<<TMath::CosH(eta1-eta2)<<", cos(phi1-phi2)="<<TMath::Cos(phi1-phi2)<<std::endl;
  return TMath::Sqrt( 2.*pt1*pt2*(TMath::CosH(eta1-eta2)-TMath::Cos(phi1-phi2)) );
}


Float_t InvMass(Float_t pt1, Float_t eta1, Float_t phi1, Float_t m1,
                Float_t pt2, Float_t eta2, Float_t phi2, Float_t m2){
  // Invariant mass without using TLorentzVector
  // https://en.wikipedia.org/wiki/Invariant_mass#Example:_two-particle_collision
  Float_t p1 = pt1*TMath::CosH(eta1); // full 3-momentum
  Float_t p2 = pt2*TMath::CosH(eta2); // full 3-momentum
  Float_t EE = TMath::Sqrt( (m1*m1+p1*p1)*(m2*m2+p2*p2) ); // E1*E2
  //std::cout << "InvMass: p1="<<p1<<", E1="<<TMath::Sqrt(m1*m1+p1*p1)
  //                  <<", p2="<<p2<<", E2="<<TMath::Sqrt(m2*m2+p2*p2)<<", EE="<<EE<<std::endl;
  Float_t mm = m1*m1 + m2*m2 + 2.*EE - 2.*pt1*pt2*(TMath::Cos(phi1-phi2)+TMath::SinH(eta1)*TMath::SinH(eta2));
  return mm<0.0 ? -TMath::Sqrt(-mm) : TMath::Sqrt(mm);
}


//Float_t InvMass(Float_t pt1, Float_t m1, Float_t e1, Float_t p1, Float_t pt2, Float_t m2, Float_t e2, Float_t p2){
//// Invariant mass using TLorentzVector
//  TLorentzVector v1, v2;
//  v1.SetPtEtaPhiM(pt1,e1,p1,m1);
//  v2.SetPtEtaPhiM(pt2,e2,p2,m2);
//  return (v1+v2).M();
//}


void utils(){
  std::cout << ">>> Opening utils.C ... " << std::endl;
}

