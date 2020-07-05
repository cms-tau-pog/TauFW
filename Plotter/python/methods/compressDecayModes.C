/*
 * @short: compress decay modes
 * @author: Izaak Neutelings (August 2018)
 *
 */

#include "TROOT.h"
#include <iostream>
#include <algorithm>
using namespace std;



Int_t compressRecoDM(Int_t DM){
  // compress reco decay mode
  if     (DM== 0) return 0;
  else if(DM== 1) return 1;
  else if(DM==10) return 2;
  else if(DM==11) return 3;
  return 4;
}



Int_t compressGenDM(Int_t DM){
  // compress gen decay mode
  if     (DM== 0)          return 0;
  else if(DM== 1)          return 1;
  else if(DM==10)          return 3;
  else if(DM==11)          return 4;
  else if(DM>= 2 && DM<10) return 2;
  else if(DM>=12 && DM<20) return 5;
  return 6;
}



Int_t compressGenDM(Int_t DM, Int_t GM){
  // compress gen decay mode, and include genmatch
  if(GM==5){
    if     (DM== 0)           return 0;
    else if(DM== 1)           return 1;
    else if(DM==10)           return 3;
    else if(DM==11)           return 4;
    else if( 2<=DM and DM<10) return 2;
    else if(12<=DM and DM<20) return 5;
  }
  else if(1<=GM and GM<=4)    return 6; // LTF
  else if(GM==6)              return 7; // JTF
  return 8;
}



void compressDecayModes(){
  std::cout << ">>> opening decayMode.C ... " << std::endl;
}


