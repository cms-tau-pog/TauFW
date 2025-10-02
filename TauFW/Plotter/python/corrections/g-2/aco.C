/*
 * @short: Provide acoplanarity corrections
 * @author: Izaak Neutelings (July 2023)
 *
 */
#include <iostream>
#include <algorithm>
#include "TROOT.h"
#include "TFile.h"
#include "TF1.h"
#include "TSystem.h" // for gSystem
//#ifndef corrs_ntracks_C
//  #include "corrs_ntracks.C" // for getEraIndex
//#endif
//#include "python/corrections/g-2/corrs_ntracks.C" // for getEraIndex
//#include "$CMSSW_BASE/src/TauFW/Plotter/python/corrections/g-2/corrs_ntracks.C" // for getEraIndex
using namespace std;

// corrections_map
TString _corrdir_aco = gSystem->ExpandPathName("$CMSSW_BASE/src/TauFW/Plotter/python/corrections/g-2");
Int_t _iera2 = -1;
std::map<Int_t,TF1*> fit_aco_2030_2030;
std::map<Int_t,TF1*> fit_aco_3040_2030;
std::map<Int_t,TF1*> fit_aco_4050_2030;
std::map<Int_t,TF1*> fit_aco_gt50_2030;
std::map<Int_t,TF1*> fit_aco_3040_3040;
std::map<Int_t,TF1*> fit_aco_4050_3040;
std::map<Int_t,TF1*> fit_aco_gt50_3040;
std::map<Int_t,TF1*> fit_aco_4050_4050;
std::map<Int_t,TF1*> fit_aco_gt50_4050;
std::map<Int_t,TF1*> fit_aco_gt50_gt50;

Int_t getEraIndex2(const TString era){
  Int_t iera = _iera2; // era index
  if(era=="UL2016_preVFP")       iera = 0;
  else if(era=="UL2016_postVFP") iera = 1;
  else if(era=="UL2017")         iera = 2;
  else if(era=="UL2018")         iera = 3;
  return iera;
}

void loadAcoWeights(TString era, const int verb=0){
  // https://github.com/cecilecaillol/MyNanoAnalyzer/blob/59f08466bedce37c2b77d6d950924e3ab9e7bcb8/NtupleAnalyzerCecile/FinalSelection_etau.cc#L1246-L1257
  ///TString indir = "$CMSSW_DIR/src/TauFW/Plotter/python/corrections/";
  ///TString fname = indir + "correction_acoplanarity_fine_"+year+".root"
  if(era=="Run2"){
    loadAcoWeights("UL2016_preVFP");
    loadAcoWeights("UL2016_postVFP");
    loadAcoWeights("UL2017");
    loadAcoWeights("UL2018");
  }else{
    Int_t iera = getEraIndex2(era);
    if(era=="UL2016_preVFP")       era = "2016pre";
    else if(era=="UL2016_postVFP") era = "2016post";
    else if(era=="UL2017")         era = "2017";
    else if(era=="UL2018")         era = "2018";
    TString fname = TString::Format(_corrdir_aco+"/new_correction_acoplanarity_fine_%s.root",era.Data());
    if(verb>=1)
      std::cout << ">>> loadAcoWeights: Loading " << fname << "..." << std::endl;
    TFile* file = new TFile(fname,"READ");
    fit_aco_2030_2030[iera] = (TF1*) file->Get("fit_acoplanarity_2030_2030");
    fit_aco_3040_2030[iera] = (TF1*) file->Get("fit_acoplanarity_3040_2030");
    fit_aco_4050_2030[iera] = (TF1*) file->Get("fit_acoplanarity_4050_2030");
    fit_aco_gt50_2030[iera] = (TF1*) file->Get("fit_acoplanarity_gt50_2030");
    fit_aco_3040_3040[iera] = (TF1*) file->Get("fit_acoplanarity_3040_3040");
    fit_aco_4050_3040[iera] = (TF1*) file->Get("fit_acoplanarity_4050_3040");
    fit_aco_gt50_3040[iera] = (TF1*) file->Get("fit_acoplanarity_gt50_3040");
    fit_aco_4050_4050[iera] = (TF1*) file->Get("fit_acoplanarity_4050_4050");
    fit_aco_gt50_4050[iera] = (TF1*) file->Get("fit_acoplanarity_gt50_4050");
    fit_aco_gt50_gt50[iera] = (TF1*) file->Get("fit_acoplanarity_gt50_gt50");
    file->Close();
  }
}

void closeAcoWeights(){
  std::cout << ">>> Destructing aco.C ... " << std::endl;
  fit_aco_2030_2030.clear();
  fit_aco_3040_2030.clear();
  fit_aco_4050_2030.clear();
  fit_aco_gt50_2030.clear();
  fit_aco_3040_3040.clear();
  fit_aco_4050_3040.clear();
  fit_aco_gt50_3040.clear();
  fit_aco_4050_4050.clear();
  fit_aco_gt50_4050.clear();
  fit_aco_gt50_gt50.clear();
  //for (auto const& x: fit_aco_2030_2030) {
  //  delete fit_aco_2030_2030[x.first];
  //  delete fit_aco_3040_2030[x.first];
  //  delete fit_aco_4050_2030[x.first];
  //  delete fit_aco_gt50_2030[x.first];
  //  delete fit_aco_3040_3040[x.first];
  //  delete fit_aco_4050_3040[x.first];
  //  delete fit_aco_gt50_3040[x.first];
  //  delete fit_aco_4050_4050[x.first];
  //  delete fit_aco_gt50_4050[x.first];
  //  delete fit_aco_gt50_gt50[x.first];
  //}
}

Float_t getAcoWeight(Float_t aco, const Float_t pt1, const Float_t pt2, const Int_t iera){ //=_iera2
  if (aco>0.35)
    aco = 0.35;
  if (pt1<30 and pt2<30)
    return fit_aco_2030_2030[iera]->Eval(aco);
  else if (pt1>=30 and pt1<40 and pt2<30)
    return fit_aco_3040_2030[iera]->Eval(aco);
  else if (pt1>=40 and pt1<50 and pt2<30)
    return fit_aco_4050_2030[iera]->Eval(aco);
  else if (pt1>=50 and pt2<30)
    return fit_aco_gt50_2030[iera]->Eval(aco);
  else if (pt1>=30 and pt1<40 and pt2>=30 and pt2<40)
    return fit_aco_3040_3040[iera]->Eval(aco);
  else if (pt1>=40 and pt1<50 and pt2>=30 and pt2<40)
    return fit_aco_4050_3040[iera]->Eval(aco);
  else if (pt1>=50 and pt2>=30 and pt2<40)
    return fit_aco_gt50_3040[iera]->Eval(aco);
  else if (pt1>=40 and pt1<50 and pt2>=40 and pt2<50)
    return fit_aco_4050_4050[iera]->Eval(aco);
  else if (pt1>=50 and pt2>=40 and pt2<50)
    return fit_aco_gt50_4050[iera]->Eval(aco);
  else if (pt1>=50 and pt2>=50)
    return fit_aco_gt50_gt50[iera]->Eval(aco);
  return 1.0;
}

void aco(){
  std::cout << ">>> Initializing aco.C ... " << std::endl;
}
