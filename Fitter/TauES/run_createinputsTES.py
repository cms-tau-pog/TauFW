import os
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--e ", nargs='+', dest="eras", default=['2023D'], help="which era")
parser.add_argument("--ew ", nargs='+', dest="ele_wps", default=['Tight'], choices=['Tight', 'VVLoose'], help="which against electron wp")
parser.add_argument("--d ", nargs='+', dest="dms", default=['DM1'], choices=['DM0', 'DM1', 'DM10', 'DM11'], help="which decay mode")
parser.add_argument("--jw ", nargs='+', dest="jet_wps", default=['Tight'], choices=['Loose', 'Medium', 'Tight', 'VTight'], help="which against jet wp")
options = parser.parse_args()

for ele in options.ele_wps:
  for jet in options.jet_wps:
     for dm in options.dms:
         for era in options.eras:
            cmd = f'python3 TauES/createinputsTES.py -y {era} -c TauES_ID/config/Default_FitSetupTES_mutau_DM_mt65pt_lessptregion.yml -d {dm} -j {jet} -e {ele}'
            print(cmd)
            os.system(cmd)
