job=$1 # can be: run, submit, resubmit, hadd, ...

pico.py $job -y 2022_preEE -c etau -t _TES0p95 -s DY -E tes=0.95 
pico.py $job -y 2022_preEE -c etau -t _TES1p05 -s DY -E tes=1.05

pico.py $job -y 2022_preEE -c etau -t _RES0p90 -s DY -E Zres=0.90
pico.py $job -y 2022_preEE -c etau -t _RES1p10 -s DY -E Zres=1.10


pico.py $job -y 2022_preEE -c etau -t _FES0p75 -s DY -E fes=0.75
pico.py $job -y 2022_preEE -c etau -t _FES0p80 -s DY -E fes=0.80
pico.py $job -y 2022_preEE -c etau -t _FES0p85 -s DY -E fes=0.85
pico.py $job -y 2022_preEE -c etau -t _FES0p90 -s DY -E fes=0.90
pico.py $job -y 2022_preEE -c etau -t _FES0p95 -s DY -E fes=0.95
pico.py $job -y 2022_preEE -c etau -t _FES1p00 -s DY -E fes=1.00
pico.py $job -y 2022_preEE -c etau -t _FES1p05 -s DY -E fes=1.05
pico.py $job -y 2022_preEE -c etau -t _FES1p10 -s DY -E fes=1.10
pico.py $job -y 2022_preEE -c etau -t _FES1p15 -s DY -E fes=1.15
pico.py $job -y 2022_preEE -c etau -t _FES1p20 -s DY -E fes=1.20
pico.py $job -y 2022_preEE -c etau -t _FES1p25 -s DY -E fes=1.25

pico.py $job -y 2022_preEE -c etau -t _FES0p90_RES0p90 -s DY -E fes=0.90 Zres=0.90
pico.py $job -y 2022_preEE -c etau -t _FES1p10_RES0p90 -s DY -E fes=1.10 Zres=0.90
pico.py $job -y 2022_preEE -c etau -t _FES0p75_RES0p90 -s DY -E fes=0.75 Zres=0.90
pico.py $job -y 2022_preEE -c etau -t _FES1p25_RES0p90 -s DY -E fes=1.25 Zres=0.90

pico.py $job -y 2022_preEE -c etau -t _FES0p90_RES1p10 -s DY -E fes=0.90 Zres=1.10
pico.py $job -y 2022_preEE -c etau -t _FES1p10_RES1p10 -s DY -E fes=1.10 Zres=1.10
pico.py $job -y 2022_preEE -c etau -t _FES0p75_RES1p10 -s DY -E fes=0.75 Zres=1.10
pico.py $job -y 2022_preEE -c etau -t _FES1p25_RES1p10 -s DY -E fes=1.25 Zres=1.10

pico.py $job -y 2022_preEE -c etau -t _FES1p05_RES0p90 -s DY -E fes=1.05 Zres=0.90
pico.py $job -y 2022_preEE -c etau -t _FES1p15_RES0p90 -s DY -E fes=1.15 Zres=0.90
pico.py $job -y 2022_preEE -c etau -t _FES1p20_RES0p90 -s DY -E fes=1.20 Zres=0.90
pico.py $job -y 2022_preEE -c etau -t _FES0p95_RES0p90 -s DY -E fes=0.95 Zres=0.90
pico.py $job -y 2022_preEE -c etau -t _FES0p85_RES0p90 -s DY -E fes=0.85 Zres=0.90
pico.py $job -y 2022_preEE -c etau -t _FES0p80_RES0p90 -s DY -E fes=0.80 Zres=0.90

pico.py $job -y 2022_preEE -c etau -t _FES1p05_RES1p10 -s DY -E fes=1.05 Zres=1.10
pico.py $job -y 2022_preEE -c etau -t _FES1p15_RES1p10 -s DY -E fes=1.15 Zres=1.10
pico.py $job -y 2022_preEE -c etau -t _FES1p20_RES1p10 -s DY -E fes=1.20 Zres=1.10
pico.py $job -y 2022_preEE -c etau -t _FES0p95_RES1p10 -s DY -E fes=0.95 Zres=1.10
pico.py $job -y 2022_preEE -c etau -t _FES0p85_RES1p10 -s DY -E fes=0.85 Zres=1.10
pico.py $job -y 2022_preEE -c etau -t _FES0p80_RES1p10 -s DY -E fes=0.80 Zres=1.10


#
pico.py $job -y 2022_preEE -c etau -t _EES0p96 -s DY Tb TB TW TT WW WZ ZZ W*J -E ees=0.96
pico.py $job -y 2022_preEE -c etau -t _EES1p04 -s DY Tb TB TW TT WW WZ ZZ W*J -E ees=1.04

pico.py $job -y 2022_preEE -c etau -t _FES0p90_EES0p96 -s DY -E fes=0.90 ees=0.96
pico.py $job -y 2022_preEE -c etau -t _FES1p10_EES0p96 -s DY -E fes=1.10 ees=0.96
pico.py $job -y 2022_preEE -c etau -t _FES0p75_EES0p96 -s DY -E fes=0.75 ees=0.96
pico.py $job -y 2022_preEE -c etau -t _FES1p25_EES0p96 -s DY -E fes=1.25 ees=0.96

pico.py $job -y 2022_preEE -c etau -t _FES0p90_EES1p04 -s DY -E fes=0.90 ees=1.04
pico.py $job -y 2022_preEE -c etau -t _FES1p10_EES1p04 -s DY -E fes=1.10 ees=1.04
pico.py $job -y 2022_preEE -c etau -t _FES0p75_EES1p04 -s DY -E fes=0.75 ees=1.04
pico.py $job -y 2022_preEE -c etau -t _FES1p25_EES1p04 -s DY -E fes=1.25 ees=1.04

pico.py $job -y 2022_preEE -c etau -t _FES1p05_EES0p96 -s DY -E fes=1.05 ees=0.96
pico.py $job -y 2022_preEE -c etau -t _FES1p15_EES0p96 -s DY -E fes=1.15 ees=0.96
pico.py $job -y 2022_preEE -c etau -t _FES1p20_EES0p96 -s DY -E fes=1.20 ees=0.96
pico.py $job -y 2022_preEE -c etau -t _FES0p95_EES0p96 -s DY -E fes=0.95 ees=0.96
pico.py $job -y 2022_preEE -c etau -t _FES0p85_EES0p96 -s DY -E fes=0.85 ees=0.96
pico.py $job -y 2022_preEE -c etau -t _FES0p80_EES0p96 -s DY -E fes=0.80 ees=0.96

pico.py $job -y 2022_preEE -c etau -t _FES1p05_EES1p04 -s DY -E fes=1.05 ees=1.04
pico.py $job -y 2022_preEE -c etau -t _FES1p15_EES1p04 -s DY -E fes=1.15 ees=1.04
pico.py $job -y 2022_preEE -c etau -t _FES1p20_EES1p04 -s DY -E fes=1.20 ees=1.04
pico.py $job -y 2022_preEE -c etau -t _FES0p95_EES1p04 -s DY -E fes=0.95 ees=1.04
pico.py $job -y 2022_preEE -c etau -t _FES0p85_EES1p04 -s DY -E fes=0.85 ees=1.04
pico.py $job -y 2022_preEE -c etau -t _FES0p80_EES1p04 -s DY -E fes=0.80 ees=1.04




