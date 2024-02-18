import os
import sys


job = sys.argv[1] #submit-resubmit-hadd-clean 
year = sys.argv[2] # year
tes_start = 0.800
# tes_stop = 0.972
# tes_step = 0.002
tes_stop = 0.848
tes_step = 0.002
#year = "2022_postEE"

for tes_val in [tes_start + i * tes_step for i in range(int((tes_stop - tes_start) / tes_step) + 1)]:
    tes = "TES" + "{:.3f}".format(tes_val).replace(".", "p")
    #command = "pico.py %s -y UL2018_v10 -c mutau_%s -s DY - " %(job,tes)
    command = "pico.py %s -c mutau_%s -y %s -E jec=False --dtype mc -s DY" %(job,tes, year)
    print(command)
    os.system(command)

