## example how to read the photon format v2
from correctionlib import _core

evaluator = _core.CorrectionSet.from_file('./../POG/EGM/2016postVFP_UL/photon.json.gz')

valsyst= evaluator["UL-Photon-ID-SF"].evaluate("2016postVFP","sfup","Medium",1.1, 34.0)
print("sfup is:"+str(valsyst))

valsf= evaluator["UL-Photon-CSEV-SF"].evaluate("2016postVFP","sf","Loose","EBInc")
print("sf is:"+str(valsf))

valsf= evaluator["UL-Photon-PixVeto-SF"].evaluate("2016postVFP","sf","Loose","EBInc")
print("sf is:"+str(valsf))

valsf= evaluator["UL-Photon-PixVeto-SF"].evaluate("2016postVFP","sfup","Loose","EBInc")
print("sfup is:"+str(valsf))

valsf= evaluator["UL-Photon-PixVeto-SF"].evaluate("2016postVFP","sfdown","Loose","EBInc")
print("sfdown is:"+str(valsf))


## example how to read the photon format v3
from correctionlib import _core

evaluator = _core.CorrectionSet.from_file('./../POG/EGM/2023Summer23/photon.json.gz')

valsyst= evaluator["Photon-ID-SF"].evaluate("2023PromptC","sfup","Medium",1.1, 34.0, -1.8)
print("sfup is:"+str(valsyst))

valsf= evaluator["Photon-CSEV-SF"].evaluate("2023PromptC","sf","Loose",1.2, 0.85)
print("sf is:"+str(valsf))

valsf= evaluator["Photon-PixVeto-SF"].evaluate("2023PromptC","sf","Loose",1.2, 0.98)
print("sf is:"+str(valsf))

valsf= evaluator["Photon-PixVeto-SF"].evaluate("2023PromptC","sfup","Loose",1.2, 0.98)
print("sfup is:"+str(valsf))

valsf= evaluator["Photon-PixVeto-SF"].evaluate("2023PromptC","sfdown","Loose",1.2, 0.98)
print("sfdown is:"+str(valsf))
