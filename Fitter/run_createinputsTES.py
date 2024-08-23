import os

for ele in ['VVLoose']: #, 'Tight']:
  for jet in ['VTight', 'Loose', 'Tight']: #, 'Medium']:
     for dm in ['DM0', 'DM1', 'DM10', 'DM11']:
       cmd = f'python3 TauES/createinputsTES.py -y 2023D -c TauES_ID/config/Default_FitSetupTES_mutau_DM_mt65pt_lessptregion.yml -d {dm} -j {jet} -e {ele}'
       print(cmd)
       os.system(cmd)
