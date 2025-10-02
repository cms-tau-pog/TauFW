/*
 * @short: Map decay modes
 * @author: Izaak Neutelings (August 2018)
 *
 */

#include <iostream>
//using namespace std;

Int_t mapRecoDM(Int_t dm){
  // Map reco decay mode to integer
  if     (dm== 0) return 0;
  else if(dm== 1) return 1;
  else if(dm==10) return 2;
  else if(dm==11) return 3;
  return 4;
}

Int_t mapGenDM(Int_t dm){
  // Map gen decay mode to integer
  if     (dm== 0)          return 0;
  else if(dm== 1)          return 1;
  else if(dm==10)          return 3;
  else if(dm==11)          return 4;
  else if(dm>= 2 && dm<10) return 2;
  else if(dm>=12 && dm<20) return 5;
  return 6;
}

Int_t mapGenDM(Int_t dm, Int_t gm){
  // Map gen decay mode to integer, and include genmatch
  if(gm==5){
    if     (dm== 0)           return 0;
    else if(dm== 1)           return 1;
    else if(dm==10)           return 3;
    else if(dm==11)           return 4;
    else if( 2<=dm and dm<10) return 2;
    else if(12<=dm and dm<20) return 5;
  }
  else if(1<=gm and gm<=4)    return 6; // LTF
  else if(gm==6)              return 7; // JTF
  return 8;
}

void mapDecayModes(){
  std::cout << ">>> Opening mapDecayModes.C ... " << std::endl;
}
