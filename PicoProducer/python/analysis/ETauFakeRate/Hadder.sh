ERA=$1
#ERA=UL2017
#ERA=UL2018
#UL2016_postVFP
#UL2016_preVFP


pico.py hadd -y $ERA -c etau -E 'ees=0.95' -t _EES0p95
pico.py hadd -y $ERA -c etau -E 'ees=1.05' -t _EES1p05

pico.py hadd -y $ERA -c etau -E 'fes=0.60' -t _FES0p60
pico.py hadd -y $ERA -c etau -E 'fes=1.40' -t _FES1p40

pico.py hadd -y $ERA -c etau 

#pico.py hadd -y $ERA -c etau -E 'ees=0.99' -t _EES0p99 
#pico.py hadd -y $ERA -c etau -E 'ees=1.01' -t _EES1p01

#pico.py hadd -y $ERA -c etau  -E 'fes=0.75' -t _FES0p75
#pico.py hadd -y $ERA -c etau  -E 'fes=1.25' -t _FES1p25

pico.py hadd -y $ERA -c etau -E 'tes=0.95' -t _TES0p95
pico.py hadd -y $ERA -c etau -E 'tes=1.05' -t _TES1p05
