job=$1 # can be: run, submit, resubmit, hadd, ...

#pico.py $job -y 2022_postEE -c etau -t _TES0p95 -s DY -E tes=0.95 
#pico.py $job -y 2022_postEE -c etau -t _TES1p05 -s DY -E tes=1.05
#
#pico.py $job -y 2022_postEE -c etau -t _EES0p99 -s DY Tb TB TW TT WW WZ ZZ W*J -E ees=0.99
#pico.py $job -y 2022_postEE -c etau -t _EES1p01 -s DY Tb TB TW TT WW WZ ZZ W*J -E ees=1.01
#
#pico.py $job -y 2022_postEE -c etau -t _FES0p90 -s DY -E fes=0.90
#pico.py $job -y 2022_postEE -c etau -t _FES1p10 -s DY -E fes=1.10
#pico.py $job -y 2022_postEE -c etau -t _FES0p75 -s DY -E fes=0.75
#pico.py $job -y 2022_postEE -c etau -t _FES1p25 -s DY -E fes=1.25

pico.py $job -y 2022_postEE -c etau -t _FES1p05 -s DY -E fes=1.05
pico.py $job -y 2022_postEE -c etau -t _FES1p15 -s DY -E fes=1.15
pico.py $job -y 2022_postEE -c etau -t _FES1p20 -s DY -E fes=1.20
pico.py $job -y 2022_postEE -c etau -t _FES0p95 -s DY -E fes=0.95
pico.py $job -y 2022_postEE -c etau -t _FES0p85 -s DY -E fes=0.85
pico.py $job -y 2022_postEE -c etau -t _FES0p80 -s DY -E fes=0.80

#pico.py $job -y 2022_postEE -c etau -t _JTF0p95 -s DY T W -E jtf=0.95
#pico.py $job -y 2022_postEE -c etau -t _JTF1p05 -s DY T W -E jtf=1.05
