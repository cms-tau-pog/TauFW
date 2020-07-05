/*
 * @short: Compress gen matching.
 * @author: Izaak Neutelings (May 2019)
 *
 */

using namespace std;

Int_t compressGenMatching(Int_t genmatch){
  // compress gen matching
  if(genmatch==0)                     return 0; // jet      -> tau fake
  else if(genmatch==1 or genmatch==3) return 1; // electron -> tau fake
  else if(genmatch==2 or genmatch==4) return 2; // muon     -> tau fake
  else if(genmatch==5)                return 3; // real tau
  std::cout << ">>> compressGenMatching: Warning, found genmatch " << genmatch << " which is not in 0-5! Returning -1..." << std::endl;
  return -1;
}

void compressGenMatching(){
  std::cout << ">>> opening compressGenMatching.C ... " << std::endl;
}
