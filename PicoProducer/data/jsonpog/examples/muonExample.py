## example how to read the muon format v2
## (Adapted from JMAR and EGM examples)
from correctionlib import _core

############################
## Example A: 2016postVFP ##
############################

# Load CorrectionSet
fname = "../POG/MUO/2016postVFP_UL/muon_Z.json.gz"
if fname.endswith(".json.gz"):
    import gzip
    with gzip.open(fname,'rt') as file:
        data = file.read().strip()
        evaluator = _core.CorrectionSet.from_string(data)
else:
    evaluator = _core.CorrectionSet.from_file(fname)

# TrackerMuon Reconstruction UL scale factor ==> NOTE the year key has been removed, for consistency with Run 3
valsf = evaluator["NUM_TrackerMuons_DEN_genTracks"].evaluate(1.1, 50.0, "nominal")
print("sf is: " + str(valsf))

# Medium ID UL scale factor, down variation ==> NOTE the year key has been removed, for consistency with Run 3
valsf = evaluator["NUM_MediumID_DEN_TrackerMuons"].evaluate(0.8, 35.0, "systdown")
print("systdown is: " + str(valsf))

# Medium ID UL scale factor, up variation ==> NOTE the year key has been removed, for consistency with Run 3
valsf = evaluator["NUM_MediumID_DEN_TrackerMuons"].evaluate(0.8, 35.0, "systup")
print("systup is: " + str(valsf))

# Trigger UL systematic uncertainty only ==> NOTE the year key has been removed, for consistency with Run 3
valsyst = evaluator["NUM_IsoMu24_or_IsoTkMu24_DEN_CutBasedIdTight_and_PFIsoTight"].evaluate(1.8, 54.0, "syst")
print("syst is: " + str(valsyst))

##########################
## Example B: 2022preEE ##
##########################

fname = "../POG/MUO/2022_Summer22/muon_Z.json.gz"
if fname.endswith(".json.gz"):
    import gzip
    with gzip.open(fname,'rt') as file:
        data = file.read().strip()
        evaluator = _core.CorrectionSet.from_string(data)
else:
    evaluator = _core.CorrectionSet.from_file(fname)

# Medium ID 2022 scale factor using eta as input
valsf_eta = evaluator["NUM_MediumID_DEN_TrackerMuons"].evaluate(-1.1, 45.0, "nominal")
print("sf for eta = -1.1: " + str(valsf_eta))

# Medium ID 2022 scale factor using eta as input ==> Note that this value should be the same
# as the previous one, since even though the input can be signed eta, the SFs for 2022 were
# computed for |eta|. This is valid for ALL the years and jsons
valsf_eta = evaluator["NUM_MediumID_DEN_TrackerMuons"].evaluate(1.1, 45.0, "nominal")
print("sf for eta = 1.1 " + str(valsf_eta))

# Trigger 2022 systematic uncertainty only 
valsyst = evaluator["NUM_IsoMu24_DEN_CutBasedIdMedium_and_PFIsoMedium"].evaluate(-1.8, 54.0, "syst")
print("syst is: " + str(valsyst))
