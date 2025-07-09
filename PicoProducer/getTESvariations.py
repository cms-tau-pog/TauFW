import os
import subprocess
import yaml
import numpy as np
from termcolor import colored
import sys
import glob  # For finding log files

# Define the configuration file path
config_file = "tes_config.yml"

# Initialize the TES values if the config file doesn't exist
def initialize_config(file, start, end, step):
    if not os.path.exists(file):
        # Convert TES values into a Python list
        tes_values = [float(tes) for tes in np.arange(start, end + step, step)]
        with open(file, "w") as f:
            yaml.dump({"tes_values": tes_values}, f)

# Load TES values from the config file
def load_config(file):
    with open(file, "r") as f:
        data = yaml.safe_load(f)
        # Ensure TES values are loaded as Python floats
        data["tes_values"] = [float(tes) for tes in data["tes_values"]]
        return data

# Save updated TES values to the config file
def save_config(file, data):
    # Convert TES values into plain Python floats
    data["tes_values"] = [float(tes) for tes in data["tes_values"]]
    with open(file, "w") as f:
        yaml.dump(data, f)

# Function to delete log files for a specific TES, year, channel, and samples
def delete_log_files(tes_formatted, year, channel, samples):
    """
    Deletes log files matching the TES value, year, channel, and sample list.
    """
    base_log_dir = "/afs/cern.ch/user/h/haawedik/CMSSW_14_1_0_pre4/src/TauFW/PicoProducer/output/2024/mutau"  # Base log file directory

    # Iterate over each sample to delete its corresponding log files
    for sample in samples:
        log_dir = os.path.join(base_log_dir, sample, "log")  # Construct the full log directory
        pattern = f"{log_dir}/{sample}_{channel}_TES{tes_formatted.replace('.', 'p')}_{year}*.log"
        print(pattern)
        # Find all log files matching the pattern
        log_files = glob.glob(pattern)
        print(log_files)
        if not log_files:
            print(colored(f"No log files found for {sample}, TES={tes_formatted}.", "yellow"))
        else:
            for log_file in log_files:
                try:
                    os.remove(log_file)  # Delete the log file
                    print(colored(f"Deleted log file: {log_file}", "green"))
                except Exception as e:
                    print(colored(f"Error deleting log file {log_file}: {e}", "red"))

# Initialize the configuration file with TES values
#initialize_config(config_file, start=0.902, end=0.930, step=0.004) #TEST AND SEE IF IT WILL DO SOMETHING WEIRD 
#initialize_config(config_file, start=1.064, end=1.096, step=0.004)
# Load the TES values
config = load_config(config_file)
tes_values = config["tes_values"]

# Get user input for the action
action = input("'submit', check 'status', or 'hadd'? \n").strip().lower()
if action not in ["submit", "status", "hadd"]:
    print("Invalid choice. Please type 'submit', 'status', or 'hadd'. Exiting.")
    exit(1)

year = "2022_postEE"
channel = "mutau"
samples = [
           "DYto2L-4Jets_MLL-50",
           "DYto2L-4Jets_MLL-50_1J",
           "DYto2L-4Jets_MLL-50_2J",
           "DYto2L-4Jets_MLL-50_3J",
           "DYto2L-4Jets_MLL-50_4J",
           "DYto2TautoMuTauh_M-50",
           "TTTo2L2Nu",
           "TTto4Q",
           "TTtoLNu2Q"
           ]
verbose_mode = "-v" in sys.argv

summary = []

# Process each TES value
for tes in tes_values[:]:
    tes_formatted = f"{tes:.3f}"  # Format TES value
    tag = f"_TES{tes_formatted.replace('.', 'p')}"  # Format tag

    if action == "submit":
        command = f"pico.py submit -y {year} -c {channel} -t {tag} -s {' '.join(samples)} -E tes={tes_formatted}"
        print(f"Submitting: {command}")
        os.system(command)

    elif action == "status":
        command = f"pico.py status -y {year} -c {channel} -t {tag} -s {' '.join(samples)} -E tes={tes_formatted}"
        print(colored(f"Checking status for: {command}", "yellow"))
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        output = result.stdout

        if verbose_mode:
            print(f"\nFull Output for tag {tag} (tes={tes_formatted}):")
            print(output)
        else:
            success_count = 0
            failed_count = 0
            pending_count = 0

            for line in output.split("\n"):
                if "SUCCESS" in line:
                    success_count += 1
                elif "MISS" in line:
                    failed_count += 1
                elif "PEND" in line:
                    pending_count += 1

            print(f"\nResults for tag {tag} (tes={tes_formatted}):")
            if success_count > 0:
                print(colored(f"  SUCCESS: {success_count}", "green"))
            if failed_count > 0:
                print(colored(f"  FAILED: {failed_count}", "red"))
            if pending_count > 0:
                print(colored(f"  PENDING: {pending_count}", "grey"))

            # Automatically handle finished samples
            if pending_count == 0 and failed_count == 0:
                print(colored(f"HADD-ing FINISHED SAMPLE: ", "green"))
                hadd_command = f"pico.py hadd -y {year} -c {channel} -t {tag} -s {' '.join(samples)} -E tes={tes_formatted}"
                os.system(hadd_command)
                tes_values.remove(tes)  # Remove TES value from the list
                save_config(config_file, {"tes_values": tes_values})

                # Delete corresponding log files
                delete_log_files(tes_formatted, year, channel, samples)

    elif action == "hadd":
        hadd_command = f"pico.py hadd -y {year} -c {channel} -t {tag} -s {' '.join(samples)} -E tes={tes_formatted}"
        print(f"Merging files for tag {tag} (tes={tes_formatted})...")
        print(f"Running: {hadd_command}")
        hadd_result = os.system(hadd_command)

        # If hadd is successful, remove the TES value from the list and delete logs
        if hadd_result == 0:
            tes_values.remove(tes)
            save_config(config_file, {"tes_values": tes_values})
            delete_log_files(tes_formatted, year, channel, samples)

# Final summary for the "status" action
if action == "status" and not verbose_mode:
    print("\n###############################################")
    print("                Final Summary                  ")
    print("###############################################")
    for entry in summary:
        print(f"Tag: {entry['tag']} (TES={entry['tes']})")
        print(colored(f"  SUCCESS: {entry['success']}", "green"))
        print(colored(f"  FAILED: {entry['failed']}", "red"))
        print(colored(f"  PENDING: {entry['pending']}", "grey"))
        print("-----------------------------------------------")

