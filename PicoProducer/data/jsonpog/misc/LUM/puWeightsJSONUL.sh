scriptName="makePUReWeightJSON.py"

python "${scriptName}" --nominal=/afs/cern.ch/cms/CAF/CMSCOMM/COMM_DQM/certification/Collisions16/13TeV/PileUp/UltraLegacy/PileupHistogram-goldenJSON-13tev-2016-preVFP-69200ub-99bins.root --up=/afs/cern.ch/cms/CAF/CMSCOMM/COMM_DQM/certification/Collisions16/13TeV/PileUp/UltraLegacy/PileupHistogram-goldenJSON-13tev-2016-preVFP-72400ub-99bins.root --down=/afs/cern.ch/cms/CAF/CMSCOMM/COMM_DQM/certification/Collisions16/13TeV/PileUp/UltraLegacy/PileupHistogram-goldenJSON-13tev-2016-preVFP-66000ub-99bins.root --makePlot -o 2016preVFP_UL/puWeights.json --gzip --mcprofile=2016UL_25ns --format=correctionlib --name=Collisions16_UltraLegacy_goldenJSON

python "${scriptName}" --nominal=/afs/cern.ch/cms/CAF/CMSCOMM/COMM_DQM/certification/Collisions16/13TeV/PileUp/UltraLegacy/PileupHistogram-goldenJSON-13tev-2016-postVFP-69200ub-99bins.root --up=/afs/cern.ch/cms/CAF/CMSCOMM/COMM_DQM/certification/Collisions16/13TeV/PileUp/UltraLegacy/PileupHistogram-goldenJSON-13tev-2016-postVFP-72400ub-99bins.root --down=/afs/cern.ch/cms/CAF/CMSCOMM/COMM_DQM/certification/Collisions16/13TeV/PileUp/UltraLegacy/PileupHistogram-goldenJSON-13tev-2016-postVFP-66000ub-99bins.root --makePlot -o 2016postVFP_UL/puWeights.json --gzip --mcprofile=2016UL_25ns --format=correctionlib --name=Collisions16_UltraLegacy_goldenJSON

python "${scriptName}" --nominal=/afs/cern.ch/cms/CAF/CMSCOMM/COMM_DQM/certification/Collisions17/13TeV/PileUp/UltraLegacy/PileupHistogram-goldenJSON-13tev-2017-69200ub-99bins.root --up=/afs/cern.ch/cms/CAF/CMSCOMM/COMM_DQM/certification/Collisions17/13TeV/PileUp/UltraLegacy/PileupHistogram-goldenJSON-13tev-2017-72400ub-99bins.root --down=/afs/cern.ch/cms/CAF/CMSCOMM/COMM_DQM/certification/Collisions17/13TeV/PileUp/UltraLegacy/PileupHistogram-goldenJSON-13tev-2017-66000ub-99bins.root --makePlot -o 2017_UL/puWeights.json --gzip --mcprofile=2017UL_25ns --format=correctionlib --name=Collisions17_UltraLegacy_goldenJSON

python "${scriptName}" --nominal=/afs/cern.ch/cms/CAF/CMSCOMM/COMM_DQM/certification/Collisions18/13TeV/PileUp/UltraLegacy/PileupHistogram-goldenJSON-13tev-2018-69200ub-99bins.root --up=/afs/cern.ch/cms/CAF/CMSCOMM/COMM_DQM/certification/Collisions18/13TeV/PileUp/UltraLegacy/PileupHistogram-goldenJSON-13tev-2018-72400ub-99bins.root --down=/afs/cern.ch/cms/CAF/CMSCOMM/COMM_DQM/certification/Collisions18/13TeV/PileUp/UltraLegacy/PileupHistogram-goldenJSON-13tev-2018-66000ub-99bins.root --makePlot -o 2018_UL/puWeights.json --gzip --mcprofile=2018UL_25ns --format=correctionlib --name=Collisions18_UltraLegacy_goldenJSON

for file in */puWeights.json.gz
do
    mv $file ../../POG/LUM/$file
done
