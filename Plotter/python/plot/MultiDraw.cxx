// Author: Peter Waller (2011)
// Description: Draws many histograms in one loop over a tree. 
//              A little bit like a TTree::Draw which can make many histograms
// Source: https://github.com/pwaller/minty/blob/master/minty/junk/MultiDraw.cxx
// Edited: Izaak Neutelings (2017)
#include <TTree.h>
#include <TH1.h>
#include <TH2.h>
#include <TTreeFormula.h>
#include <TTreeFormulaManager.h>
#include <TStopwatch.h>
#include <iostream>
#include <iomanip> // for std::setprecision()
using std::cout;
using std::endl;


bool hasVarLenBranch(TObjArray* formulae,int verb=0){
  for(Int_t iobj=0; iobj<formulae->GetEntries(); iobj++){
    if(!formulae->At(iobj)->InheritsFrom("TTreeFormula")) continue;
    TTreeFormula* formula = (TTreeFormula*) formulae->At(iobj);
    for(Int_t i=0; i<formula->GetNcodes(); i++){
      if(formula->GetLeaf(i)->GetLeafCount()){
        if(verb>=2)
          cout << ">>> MultiDraw::hasVarLenBranch: TTreeFormula '" << formula->GetTitle()
               << "' has a branch of variable length!" << endl;
        return true; // at least one branch is an array of variable length
      }
    }
  }
  return false;
}


void MultiDraw( TTree* tree, TTreeFormula* commonFormula, TObjArray* formulae, TObjArray* weights,
                TObjArray* hists, UInt_t listLen, int verb=0 ){
    
    // Get an Element from an array
    #define EL(type, array, index) dynamic_cast<type*>(array->At(index))
    
    Long64_t i = 0, NumEvents = tree->GetEntries();
    Double_t commonWeight = 0, treeWeight = tree->GetWeight();
    Int_t treeNumber = -1;
    bool xvarlen = hasVarLenBranch(formulae,verb); // for performance
    bool wvarlen = hasVarLenBranch(weights,verb);
    
    TStopwatch watch;
    for(i=0; i<NumEvents; i++){
        
        // Display progress every 20000 events
        //if (i%20000==0){
        //    cout.precision(2);
        //    double nTodo  = NumEvents - i, perSecond = 20000 / watch.RealTime();
        //    Int_t seconds = (Int_t)(nTodo / perSecond), minutes = (Int_t)(seconds / 60.);
        //    seconds -= (Int_t)(minutes*60.);
        //    cout << "Done " << (double(i) / ( double(NumEvents)) * 100.0f) << "% ";
        //    if ( minutes ) cout << minutes << " minutes ";
        //    cout << seconds << " seconds remain.                            \r";
        //    cout.flush();
        //    watch.Start();
        //}
        
        if(treeNumber!=tree->GetTreeNumber()){
            treeWeight = tree->GetWeight();
            treeNumber = tree->GetTreeNumber();
        }
        
        tree->LoadTree(tree->GetEntryNumber(i));
        commonWeight = commonFormula->EvalInstance();
        if(!commonWeight) continue;        
        commonWeight *= treeWeight;
        
        Double_t value = 0, weight = 0;
        for(UInt_t j=0; j<listLen; j++){
            // If the value or the weight formula is the same as the previous, then it can be re-used.
            // In which case, this element fails to dynamic_cast to a formula, and evaluates to NULL
            if(EL(TTreeFormula, formulae, j)){
              if(xvarlen) EL(TTreeFormula, formulae, j)->GetNdata(); // load data of array branch with variable size
              value = EL(TTreeFormula, formulae, j)->EvalInstance();
            }
            
            if(EL(TTreeFormula, weights,  j)){
              if(wvarlen) EL(TTreeFormula, weights, j)->GetNdata(); // load data of array branch with variable size
              weight = EL(TTreeFormula, weights, j)->EvalInstance() * commonWeight;
            }
            
            if(weight) // only fill if weight!=0
              EL(TH1, hists, j)->Fill(value, weight);
        }
    }
    if(verb>=1)
      cout << std::fixed << std::setprecision(3) << ">>> MultiDraw::MultiDraw: Done! Took "
           << watch.RealTime() << "s in real time, " << watch.CpuTime() << "s in CPU time" << endl;
}


void MultiDraw2D( TTree* tree, TTreeFormula* commonFormula, TObjArray* xformulae, TObjArray* yformulae, TObjArray* weights,
                  TObjArray* hists, UInt_t listLen, int verb=0){
    
    // Get an Element from an array
    #define EL(type, array, index) dynamic_cast<type*>(array->At(index))
    
    Long64_t i = 0, NumEvents = tree->GetEntries();
    Double_t commonWeight = 0, treeWeight = tree->GetWeight();
    Int_t treeNumber = -1;
    bool xvarlen = hasVarLenBranch(xformulae,verb); // for performance
    bool yvarlen = hasVarLenBranch(yformulae,verb);
    bool wvarlen = hasVarLenBranch(weights,verb);
    
    TStopwatch watch;
    for(i=0; i<NumEvents; i++){
        
        if(treeNumber!=tree->GetTreeNumber()){
            treeWeight = tree->GetWeight();
            treeNumber = tree->GetTreeNumber();
        }
        
        tree->LoadTree(tree->GetEntryNumber(i));
        commonWeight = commonFormula->EvalInstance();
        if(!commonWeight) continue;        
        commonWeight *= treeWeight;
        
        Double_t xvalue = 0, yvalue = 0, weight = 0;
        for(UInt_t j=0; j<listLen; j++){
            // If the value or the weight formula is the same as the previous, then it can be re-used.
            // In which case, this element fails to dynamic_cast to a formula, and evaluates to NULL
            if(EL(TTreeFormula, xformulae, j)){
                if(xvarlen) EL(TTreeFormula, xformulae, j)->GetNdata(); // load data of array branch with variable size
                xvalue = EL(TTreeFormula, xformulae, j)->EvalInstance();
            }
            
            if(EL(TTreeFormula, yformulae, j)){
                if(yvarlen) EL(TTreeFormula, yformulae, j)->GetNdata(); // load data of array branch with variable size
                yvalue = EL(TTreeFormula, yformulae, j)->EvalInstance();
            }
            
            if(EL(TTreeFormula, weights,  j)){
                if(wvarlen) EL(TTreeFormula, weights, j)->GetNdata(); // load data of array branch with variable size
                weight = EL(TTreeFormula, weights, j)->EvalInstance() * commonWeight;
            }
            
            if(weight)
                EL(TH2, hists, j)->Fill(xvalue, yvalue, weight);
        }
    }
    if(verb>=1)
      cout << std::fixed << std::setprecision(3) << ">>> MultiDraw::MultiDraw2D: Done! Took "
           << watch.RealTime() << "s in real time, " << watch.CpuTime() << "s in CPU time" << endl;
}


