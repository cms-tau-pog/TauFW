import os
import sys
import datetime
import time
import argparse
from concurrent.futures import ProcessPoolExecutor

parser = argparse.ArgumentParser()
parser.add_argument("--e ", type=str, dest="era", help="which era")
parser.add_argument("--c ", type=str, dest="channel", help="which channel", default='mutau')
parser.add_argument("--s ", nargs='+', dest="systematics", help="which systematics", default = ['central'])
parser.add_argument("--sa ", nargs='+', dest="samples", help="which samples", default = [])
parser.add_argument("--C ", action='store_true', dest="clean", help="want to clean root files", default=False)
parser.add_argument("--f ", action='store_true', dest="force", help="want to hadd forcefully", default=False)
options = parser.parse_args()
era = options.era
channel = options.channel
systematics = options.systematics
samples = options.samples
clean = options.clean
force = options.force

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
               taues_vars = [0.880, 0.882, 0.884, 0.886, 0.888, 0.890, 0.892, 0.894, 0.896, 0.898,0.900, 0.902, 0.904, 0.906, 0.908, 0.910, 0.912, 0.914, 0.916, 0.918, 0.920, 0.922, 0.924, 0.926, 0.928, 0.930, 0.932, 0.934, 0.936, 0.938, 0.940, 0.942, 0.944, 0.946, 0.948, 0.950, 0.952, 0.954, 0.956, 0.958, 0.960, 0.962, 0.964, 0.966, 0.968, 0.970, 0.972, 0.974, 0.976, 0.978, 0.980, 0.982, 0.986, 0.988, 0.990, 0.992, 0.994, 0.996, 0.998, 1.000, 1.002, 1.004, 1.006, 1.008, 1.010, 1.012, 1.014, 1.016, 1.018, 1.020, 1.022,1.024, 1.026, 1.028, 1.030] #1.024 0.9840.950, 0.951, 0.952, 0.953, 0.954, 0.955, 0.956, 0.957, 0.958, 0.959, 0.960, 0.961, 0.962, 0.963, 0.964, 0.965, 0.966, 0.967, 0.968, 0.969, 1.031, 1.032, 1.033, 1.034, 1.035, 1.036, 1.037, 1.038, 1.039, 1.040, 1.041, 1.042, 1.043, 1.044, 1.045, 1.046, 1.047, 1.048, 1.049, 1.050]#0.970, 0.971, 0.972, 0.973, 0.974, 0.975, 0.976, 0.977, 0.978, 0.979, 0.980, 0.981, 0.982, 0.983, 0.984, 0.985, 0.986, 0.987, 0.988, 0.989, 0.990, 0.991, 0.992, 0.993, 0.994, 0.995, 0.996, 0.997, 0.998, 0.999, 1.000, 1.001, 1.002, 1.003, 1.004, 1.005, 1.006, 1.007, 1.008, 1.009, 1.010, 1.011, 1.012, 1.013, 1.014, 1.015, 1.016, 1.017, 1.018, 1.019, 1.020, 1.021, 1.022, 1.023, 1.024, 1.025, 1.026, 1.027, 1.028, 1.029, 1.030]
               for taues_var in taues_vars:
                   taues_var_with_p = str(taues_var).replace('.', 'p')
                   if len(taues_var_with_p) != 5:
                       taues_var_with_p += '0'
                   cmd = common_cmd + f' tes={taues_var} -s DY -t _TES{taues_var_with_p}'
                   cmds.append(cmd)
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
