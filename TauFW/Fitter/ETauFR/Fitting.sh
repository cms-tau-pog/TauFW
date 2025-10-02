###WIP###
#### CHOOSE YOUR ERA HERE #####
#ERA=2016
#ERA=UL2016_preVFP
#ERA=UL2016_postVFP
ERA=UL2018
#ERA=UL2017
#########


OUTDIR=coutFR_$ERA
WORKSPDIR=WorkSpace
FITDIR=PostFitShape

mkdir $OUTDIR
mkdir $WORKSPDIR
mkdir $WORKSPDIR/$ERA
mkdir $FITDIR
mkdir $FITDIR/$ERA

apath=/afs/cern.ch/work/l/lvigilan/TauWork/CMSSW_8_1_0/src/

cd /afs/cern.ch/work/l/lvigilan/TauWork/CMSSW_8_1_0/src/
eval `scramv1 runtime -sh`
cd - 

#templateFittingETauFR zee_fr_m_vis_eta0to1.448_et-$ERA.inputs.root Loose | tee ./zee_fr_m_vis_eta0to1.448_et-$ERA.inputs.txt
#text2workspace.py -m 90 -P TauFW.Fitter.ETauFR.zttmodels:ztt_eff --PO "eff=0.0491043" ./input/$ERA/ETauFR/VVTight_eta1.56to2.3.txt -o  ./$WORKDIR/$ERA/WorkSpaceVTightLt1p460.root
#text2workspace.py -m 90 -P HiggsAnalysis.ETauFR.zttmodels:ztt_eff --PO "0.7012745376" ./input/$ERA/ETauFR/VLoose_eta0to1.46.txt -o  ./$WORKDIR/$ERA/WorkSpaceVLooseLt1p46.root
text2workspace.py -m 90 -P HiggsAnalysis.ETauFR.zttmodels:ztt_eff --PO "0.31356317424" ./input/$ERA/ETauFR/VLoose_eta1.56to2.3.txt -o  ./$WORKDIR/$ERA/WorkSpaceVLooseLt2p300.root
#combine -m 90  -M FitDiagnostics --robustFit=1 --expectSignal=1.0 --rMin=0.7 --rMax=1.5 --cminFallbackAlgo "Minuit2,0:1" -n "" ./$WORKDIR/$ERA/WorkSpaceVLooseLt1p46.root | tee ./$OUTDIR/ScaleVLooseLt1p46.txt
combine -m 90  -M FitDiagnostics --robustFit=1 --expectSignal=1.0 --rMin=0.7 --rMax=1.5 --cminFallbackAlgo "Minuit2,0:1" -n "" ./$WORKDIR/$ERA/WorkSpaceVLooseLt2p300.root | tee ./$OUTDIR/ScaleVLooseLt2p300.txt
#combine -m 90  -M FitDiagnostics --robustFit=1 --expectSignal=1.0 --rMin=0.0 --rMax=3.0 --cminFallbackAlgo "Minuit2,0:1" -n "" ./$WORKDIR/$ERA/WorkSpaceVLooseLt1p46.root | tee ./$OUTDIR/ScaleVLooseLt1p46.txt
#combine -m 90  -M FitDiagnostics --robustFit=1 --expectSignal=1.5 --rMin=1.0 --rMax=5.0 --cminFallbackAlgo "Minuit2,0:1" -n "" ./$WORKDIR/$ERA/WorkSpaceVLooseLt2p300.root | tee ./$OUTDIR/ScaleVLooseLt2p300.txt
#./compare.py -a fitDiagnostics.root | tee ./$OUTDIR/VLooseLt1p46Pull.txt
./compare.py -a fitDiagnostics.root | tee ./$OUTDIR/VLooseLt2p300Pull.txt
#PostFitShapesFromWorkspace -o ./$FITDIR/$ERA/ETauFRVLooseLt1p46_PostFitShape.root -m 90 -f fitDiagnostics.root:fit_s --postfit --sampling --print -d ./input/$ERA/ETauFR/VLoose_eta0to1.46.txt -w ./$WORKDIR/$ERA/WorkSpaceVLooseLt1p46.root
PostFitShapesFromWorkspace -o ./$FITDIR/$ERA/ETauFRVLooseLt2p300_PostFitShape.root -m 90 -f fitDiagnostics.root:fit_s --postfit --sampling --print -d ./input/$ERA/ETauFR/VLoose_eta1.56to2.3.txt -w ./$WORKDIR/$ERA/WorkSpaceVLooseLt2p300.root
