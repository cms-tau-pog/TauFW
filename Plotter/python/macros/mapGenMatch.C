/*
 * @short: Map tau gen match code.
 * @author: Izaak Neutelings (May 2019)
 *
 */

#include <iostream>
//using namespace std;

Int_t mapGM(Int_t gm){
  // Map gen matching to integer
  if(gm==0 or gm==6)      return 0; // jet      -> tau fake
  else if(gm==1 or gm==3) return 1; // electron -> tau fake
  else if(gm==2 or gm==4) return 2; // muon     -> tau fake
  else if(gm==5)          return 3; // real tau
  std::cout << ">>> Warning! mapGM: found gm " << gm << ", which is not in 0-6! Returning -1..." << std::endl;
  return -1;
}

void mapGenMatch(){
  std::cout << ">>> Opening mapGenMatch.C ... " << std::endl;
}
