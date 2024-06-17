## example how to read the electronHlt format v2
from correctionlib import _core

evaluator = _core.CorrectionSet.from_file('./../POG/EGM/2022_Summer22/electronHlt.json.gz')

valsf= evaluator["Electron-HLT-SF"].evaluate("2022Re-recoBCD","sf","HLT_SF_Ele30_TightID",1.1, 45.0)
print("sf is:"+str(valsf))

valsystup= evaluator["Electron-HLT-SF"].evaluate("2022Re-recoBCD","sfup","HLT_SF_Ele30_TightID",1.1, 45.0)
print("systup is:"+str(valsystup))

valsystdown= evaluator["Electron-HLT-SF"].evaluate("2022Re-recoBCD","sfdown","HLT_SF_Ele30_TightID",1.1, 45.0)
print("systdown is:"+str(valsystdown))

valeffdata= evaluator["Electron-HLT-DataEff"].evaluate("2022Re-recoBCD","nom","HLT_SF_Ele30_MVAiso90ID",1.1, 45.0)
print("sf is:"+str(valeffdata))

valeffMCup= evaluator["Electron-HLT-McEff"].evaluate("2022Re-recoE+PromptFG","up","HLT_SF_Ele30_MVAiso90ID",1.1, 45.0)
print("sf is:"+str(valeffMCup))