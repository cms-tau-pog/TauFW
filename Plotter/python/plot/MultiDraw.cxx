// Author: Peter Waller (2011)
// Description: Draws many histograms in one loop over a tree. 
//              A little bit like a TTree::Draw which can make many histograms
// Source: https://github.com/pwaller/minty/blob/master/minty/junk/MultiDraw.cxx
// Edited: Izaak Neutelings (2017)

#include <TTree.h>
#include <TH1.h>
#include <TH2.h>
#include <TTreeFormula.h>
#include <TStopwatch.h>
#include <iostream>
using std::cout;
using std::endl;

void MultiDraw( TTree* tree, TTreeFormula* commonFormula, TObjArray* formulae, TObjArray* weights, TObjArray* hists, UInt_t listLen ){
    
    // Get an Element from an array
    #define EL(type, array, index) dynamic_cast<type*>(array->At(index))
    
    Long64_t i = 0, NumEvents = tree->GetEntries();
    Double_t commonWeight = 0, treeWeight = tree->GetWeight();
    Int_t treeNumber = -1;
    
    //TStopwatch watch;
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
            if(EL(TTreeFormula, formulae, j))
              value = EL(TTreeFormula, formulae, j)->EvalInstance();
            
            if(EL(TTreeFormula, weights,  j))
              weight = EL(TTreeFormula, weights, j)->EvalInstance() * commonWeight;
            
            if(weight)
              EL(TH1, hists, j)->Fill(value, weight);
        }
    }
}



void MultiDraw2D( TTree* tree, TTreeFormula* commonFormula, TObjArray* xformulae, TObjArray* yformulae, TObjArray* weights, TObjArray* hists, UInt_t listLen ){
    
    // Get an Element from an array
    #define EL(type, array, index) dynamic_cast<type*>(array->At(index))
    
    Long64_t i = 0, NumEvents = tree->GetEntries();
    Double_t commonWeight = 0, treeWeight = tree->GetWeight();
    Int_t treeNumber = -1;
    
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
            if(EL(TTreeFormula, xformulae, j))
                xvalue = EL(TTreeFormula, xformulae, j)->EvalInstance();
            
            if(EL(TTreeFormula, yformulae, j))
                yvalue = EL(TTreeFormula, yformulae, j)->EvalInstance();
            
            if(EL(TTreeFormula, weights,  j))
                weight = EL(TTreeFormula, weights, j)->EvalInstance() * commonWeight;
            
            if(weight)
                EL(TH2, hists, j)->Fill(xvalue, yvalue, weight);
        }
    }
}


