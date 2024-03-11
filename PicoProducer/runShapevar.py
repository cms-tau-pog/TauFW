import os
import sys

# year = "2022_postEE"
# job = "clean"

job = sys.argv[1] #submit-resubmit-hadd-clean 
year = sys.argv[2] # year

os.system("pico.py %s -c mutau_LTFUp -y %s  -E jec=False --dtype mc" %(job,year)) 
os.system("pico.py %s -c mutau_LTFDown -y %s   -E jec=False --dtype mc" %(job,year))
os.system("pico.py %s -c mutau_JTFUp -y %s   -E jec=False --dtype mc" %(job,year))
os.system("pico.py %s -c mutau_JTFDown -y %s  -E jec=False --dtype mc"%(job,year))