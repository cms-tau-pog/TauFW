/*
 * @short: provide lepton faking tau scale factors
 * @author: Izaak Neutelings (May 2018)
 *
 */

#include "TROOT.h"
#include "TMath.h"
#include <iostream>
//using namespace std;



Float_t getLeptonTauFake(const Int_t channel, const Int_t genmatch_2, const Float_t eta_2){
  //std::cout << "genMatchSF" << std::endl;
  // matching ID code:      https://twiki.cern.ch/twiki/bin/viewauth/CMS/HiggsToTauTauWorking2016#MC_Matching
  //                        https://twiki.cern.ch/twiki/bin/view/CMS/TauIDRecommendation13TeVMoriond17#Muon_to_tau_fake_rate (Moriond)
  //                        https://twiki.cern.ch/twiki/bin/view/CMS/TauIDRecommendation13TeV#Muon_to_tau_fake_rate (Moriond - better?)
  // tau reweighting:       https://indico.cern.ch/event/715039/timetable/#2-lepton-tau-fake-rates-update
  //                        https://indico.cern.ch/event/719250/contributions/2971854/attachments/1635435/2609013/tauid_recommendations2017.pdf
  //                        https://twiki.cern.ch/twiki/bin/viewauth/CMS/TauIDRecommendation13TeVMoriond17#Muon_to_tau_fake_rate
  //
  // mutau  (1): againstElectronVLooseMVA6 (idAntiELe>=1), againstMuonTight3 (idAntiMu>=2)
  // etau   (2): againstElectronTightMVA6  (idAntiEle>=8), againstMuonLoose3 (idAntiMu>=1)
  // tautau (4), both taus: idAntiMu>=1 (Loose), idAntiEle>=1 (VLoose)

  
  Float_t eta = fabs(eta_2);
  
  // electron -> tau
  if(genmatch_2==1){
    if(channel==1 or channel==4){     // VLoose for mutau and tautau
      if     ( eta < 1.460 ) return 1.09;
      else if( eta > 1.558 ) return 1.19;
    }
    else if(channel==2){ // Tight for etau
      if     ( eta < 1.460 ) return 1.80;
      else if( eta > 1.558 ) return 1.53;
    }
  }
  // muon -> tau
  else if(genmatch_2==2){
    if(channel==2 or channel==4){      // Loose for etau and tautau
        if     ( eta < 0.4 ) return 1.061;
        else if( eta < 0.8 ) return 1.022;
        else if( eta < 1.2 ) return 1.097;
        else if( eta < 1.7 ) return 1.030;
        else                 return 1.941;
    }
    else if(channel==1){  // Tight for mutau
        if     ( eta < 0.4 ) return 1.165;
        else if( eta < 0.8 ) return 1.290;
        else if( eta < 1.2 ) return 1.137;
        else if( eta < 1.7 ) return 0.927;
        else                 return 1.607;
    }
  }
  // real tau
  //else if(genmatch_2==5){
  //  return 0.88; // Tight
  //}
  
  return 1.0;
}



Float_t getLeptonTauFake2016(const Int_t channel, const Int_t genmatch_2, const Float_t eta_2){
  //std::cout << "genMatchSF" << std::endl;
  // mutau (1): againstElectronVLooseMVA6 againstMuonTight3
  // etau  (2): againstElectronTightMVA6  againstMuonLoose3
    
  Float_t eta = fabs(eta_2);
  
  // electron -> tau
  if(genmatch_2==1){
    if(channel==1){     // VLoose for mutau
      if     ( eta < 1.460 ) return 1.213;
      else if( eta > 1.558 ) return 1.375;
    }
    else if(channel==2){ // Tight for etau
      if     ( eta < 1.460 ) return 1.40;
      else if( eta > 1.558 ) return 1.90;
    }
  }
  // muon -> tau
  else if(genmatch_2==2){
    if (channel==2){      // Loose for etau
        if     ( eta < 0.4 ) return 1.012;
        else if( eta < 0.8 ) return 1.007;
        else if( eta < 1.2 ) return 0.870;
        else if( eta < 1.7 ) return 1.154;
        else                 return 2.281;
    }
    else if (channel==1){  // Tight for mutau
        if     ( eta < 0.4 ) return 1.012;
        else if( eta < 0.8 ) return 1.007;
        else if( eta < 1.2 ) return 0.870;
        else if( eta < 1.7 ) return 1.154;
        else                 return 2.281;
    }
  }
  // real tau
  else if(genmatch_2==5){
    return 0.95;
  }
  
  return 1.0;
}



void leptonTauFake(){
  //std::cout << std::endl;
  std::cout << ">>> initializing leptonTauFake.C ... " << std::endl;
  //std::cout << std::endl;
}


