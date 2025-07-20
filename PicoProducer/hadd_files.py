import os
import shutil
import subprocess
import argparse
import getpass

def main():
    parser = argparse.ArgumentParser(description='Process ROOT files by era and year.')
    parser.add_argument('-year', required=True, help='Year of the data, e.g., 2025')
    parser.add_argument('-era', required=True, help='Eras to process, e.g., BCDEFGHI')

    args = parser.parse_args()
    year = args.year
    eras = list(args.era)

    user = getpass.getuser()
    eos_input_dir = f'/eos/user/{user[0]}/{user}/analysis/{year}/Data'
    samples_dir = 'samples'
    era_wise_dir = 'era_wise'

    os.makedirs(samples_dir, exist_ok=True)
    os.makedirs(era_wise_dir, exist_ok=True)

    for file in os.listdir(eos_input_dir):
        if file.endswith('.root') and os.path.isfile(os.path.join(eos_input_dir, file)):
            shutil.copy(os.path.join(eos_input_dir, file), os.path.join(samples_dir, file))

    for era in eras:
        output_file = os.path.join(era_wise_dir, f'Muon_Run{year}{era}_mutau.root')
        input_files = [os.path.join(samples_dir, f)
                       for f in os.listdir(samples_dir) if f.endswith(f'Run{year}{era}_mutau.root')]
        if input_files:
            subprocess.run(['hadd', output_file] + input_files)

    final_output = f'Muon_Run{year}_mutau.root'
    all_era_files = [os.path.join(era_wise_dir, f)
                     for f in os.listdir(era_wise_dir) if f.endswith('.root')]
    if all_era_files:
        subprocess.run(['hadd', final_output] + all_era_files)

if __name__ == '__main__':
    main()
