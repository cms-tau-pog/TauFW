import os 

for ele_wp in ['VVLoose', 'Tight']:
  for era in ['2023C', '2023D']:
      os.system(f'python3 createroot_TES.py -y {era} -e {ele_wp}')
  os.system('hadd tau_sf/TauID_SF_dm_DeepTau2018v2p5_{era}_VSjet{jet_wp}_VSele{ele_wp}_Run3_May24.root tau_sf/TauID*2023*root') 
