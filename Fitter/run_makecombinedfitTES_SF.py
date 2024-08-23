import os

for ele in ['VVLoose']: #, 'Tight']:
  for jet in ['Tight']: #, 'Medium']:
       input = os.path.join('input_pt_less_region', f'againstjet_{jet}', f'againstelectron_{ele}')
       cmd = f'python3 TauES_ID/makecombinedfitTES_SF.py -y 2023C -o 1 -c TauES_ID/config/Default_FitSetupTES_mutau_DM_mt65pt.yml -cmm TauES/config/FitSetup_mumu.yml -i {input}'
       print(cmd)
       os.system(cmd)
