### Saswati Nandan, India###
import numpy as np
import os
import sys
import datetime
import time
import argparse
from concurrent.futures import ProcessPoolExecutor

parser = argparse.ArgumentParser()
parser.add_argument("--e ", type=str, dest="era", help="which era")
parser.add_argument("--c ", type=str, dest="channel", help="which channel", default='mutau')
parser.add_argument("--s ", nargs='+', dest="systematics", help="which systematics", choices=['central', 'LTFUp', 'LTFDown', 'JTFUp', 'JTFDown', 'tauES'], default = ['central'])
parser.add_argument("--S ", nargs='+', dest="samples", help="which samples", default = [])
parser.add_argument("--C ", action='store_true', dest="clean", help="want to clean root files", default=False)
parser.add_argument("--f ", action='store_true', dest="force", help="want to hadd forcefully", default=False)
parser.add_argument("--st ", dest="start", help="lower variation of tau energy scale", default=0.750)
parser.add_argument("--en ", dest="end", help="upper variation of tau energy scale", default=1.03)
options = parser.parse_args()
era = options.era
channel = options.channel
systematics = options.systematics
samples = options.samples
clean = options.clean
force = options.force
start = options.start
end = options.end

def run_pico(cmd):
        ret = 0
        if 'hadd' in cmd:
            print('running hadd')
            print(cmd)
            os.system(cmd)
        elif 'status' in cmd:
            if not os.system(f'{cmd} | grep MISS'):
                cmd = cmd.replace('status', 'resubmit')
                print('jobs are missing, resubmitting')
                print(cmd)
                os.system(cmd)
                ret = 1
            elif not os.system(f'{cmd} | grep PEND'):
                print(cmd)
                print('jobs are on pending state')
                ret = 1
            else:
                print('jobs are done')
        else:
            if not os.system(f'{cmd} | grep exist'):
                print('jobs were already submitted, check the status')
                cmd = cmd.replace('submit', 'status')
                ret = run_pico(cmd)
            else:
                print(cmd)
                os.system(cmd)
                ret = 1
        print(f'returning {ret}')
        return ret

def run_cmd(which_cmd):
    print(f'calling run_cmd with {which_cmd}')
    common_cmd = f'pico.py {which_cmd}  -c {channel} -y {era}  -E jec=False useT1=False'
    if samples:
      sample = ' ' .join(s for s in samples)
      common_cmd += f' -s {sample}'
    cmds = []
    for sys in systematics:
        if 'central' in sys:
            cmds.append(common_cmd)
        elif 'LTF' in sys:
            cmd = common_cmd + f' -s DY TT -t {sys}'
            if 'Up' in sys:
                cmd += ' -E ltf=1.03'
            else:
                assert('Down' in sys)
                cmd += ' -E ltf=0.97'
            cmds.append(cmd)
        elif 'JTF' in sys:
            cmd = common_cmd + f' -s DY TT W*J -t {sys}'
            if 'Up' in sys:
                cmd += ' -E jtf=1.10'
            else:
                assert('Down' in sys)
                cmd += ' -E jtf=0.90'
            cmds.append(cmd)
        elif 'tauES' in sys:
               taues_vars = np.arange(start, end, 0.002)
               if end not in taues_vars:
                   taues_vars = np.append(taues_vars, end)
               for taues_var in taues_vars:
                   taues_var_with_p = str(taues_var).replace('.', 'p')
                   if len(taues_var_with_p) != 5:
                       taues_var_with_p += '0'
                   cmd = common_cmd + f' tes={taues_var} -s DY -t _TES{taues_var_with_p}'
                   cmds.append(cmd)
    #https://stackoverflow.com/questions/7207309/how-to-run-functions-in-parallel
    with ProcessPoolExecutor() as executor:
       ret = list(executor.map(run_pico, cmds))
       return any([ i !=0 for i in ret])

first_submit = False
while True and not force:
    if not first_submit:
        ret = run_cmd('submit')
        print('return value: ', ret)
        if ret == 0:
            break
        first_submit = True
    print('sleeping')
    time.sleep(600)
    ret = run_cmd('status')
    print('return: ', ret)
    print(datetime.datetime.now())
    if ret == 0:
        break
hadd = 'hadd'
if clean:
   hadd+= ' clean'
if force:
   hadd+= ' --force'
run_cmd(hadd)
