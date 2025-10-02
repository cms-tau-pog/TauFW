# Authors: Paola Mastrapasqua (Jan 2024)
# Description: run text2ws for all categories reading prefit FR values from a json (created running writedatacard.py)

import argparse
import os
import json

parser = argparse.ArgumentParser()
parser.add_argument('-y', '--era', dest='era', nargs='*', choices=['2016','2017','2018','UL2017', 'UL2018', '2022_postEE', '2022_preEE'], required=True, action='store', help="set era" )
args   = parser.parse_args()
era    = args.era[0]
 
# Opening JSON file
with open("input/%s/ETauFR/prefitFR.json"%(era)) as json_file:
    data = json.load(json_file)

print(data)
#print(data.keys())
for iwp in data.keys():
    for ieta in data[iwp].keys():
        for idm in data[iwp][ieta].keys():
            fr = data[iwp][ieta][idm]["prefitFR"]
            print("Running >>> ")
            print('text2workspace.py -P TauFW.Fitter.ETauFR.zttmodels:ztt_eff --PO "eff=%f" ./input/%s/ETauFR/%s_eta%s_dm%s.txt -o  ./input/%s/ETauFR/WorkSpace%s_eta%s_dm%s.root'%(fr,era,iwp,ieta,idm,era,iwp,ieta,idm))
            os.system('text2workspace.py -P TauFW.Fitter.ETauFR.zttmodels:ztt_eff --PO "eff=%f" ./input/%s/ETauFR/%s_eta%s_dm%s.txt -o  ./input/%s/ETauFR/WorkSpace%s_eta%s_dm%s.root'%(fr,era,iwp,ieta,idm,era,iwp,ieta,idm))
            

