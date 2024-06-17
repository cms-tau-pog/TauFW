## example how to read the electron format v2
from correctionlib import _core

evaluator = _core.CorrectionSet.from_file('./../POG/EGM/2016postVFP_UL/electron.json.gz')

valsf= evaluator["UL-Electron-ID-SF"].evaluate("2016postVFP","sf","RecoBelow20",1.1, 15.0)
print("sf is:"+str(valsf))

valsf= evaluator["UL-Electron-ID-SF"].evaluate("2016postVFP","sf","RecoAbove20",1.1, 25.0)
print("sf is:"+str(valsf))

valsf= evaluator["UL-Electron-ID-SF"].evaluate("2016postVFP","sf","Medium",1.1, 34.0)
print("sf is:"+str(valsf))

valsystup= evaluator["UL-Electron-ID-SF"].evaluate("2016postVFP","sfup","Medium",1.1, 34.0)
print("systup is:"+str(valsystup))

valsystdown= evaluator["UL-Electron-ID-SF"].evaluate("2016postVFP","sfdown","Medium",1.1, 34.0)
print("systdown is:"+str(valsystdown))

## example how to read the electron format in 2023 Prompt (eta, pT, phi)

evaluator = _core.CorrectionSet.from_file('./../POG/EGM/2023_Summer23BPix/electron.json.gz')

valsf= evaluator["Electron-ID-SF"].evaluate("2023PromptD","sf","RecoBelow20",1.1, 15.0, 2.0)
print("sf is:"+str(valsf))

valsf= evaluator["Electron-ID-SF"].evaluate("2023PromptD","sf","Reco20to75",1.1, 25.0, 2.0)
print("sf is:"+str(valsf))

valsf= evaluator["Electron-ID-SF"].evaluate("2023PromptD","sf","Medium",1.1, 34.0, -1.0)
print("sf is:"+str(valsf))

valsystup= evaluator["Electron-ID-SF"].evaluate("2023PromptD","sfup","Medium",1.1, 34.0, -1.0)
print("systup is:"+str(valsystup))

valsystdown= evaluator["Electron-ID-SF"].evaluate("2023PromptD","sfdown","Medium",1.1, 34.0, -1.0)
print("systdown is:"+str(valsystdown))