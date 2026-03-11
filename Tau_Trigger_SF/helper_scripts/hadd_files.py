#!/usr/bin/env python3
import os
import shutil
import subprocess
import argparse
import getpass

def is_valid_root_file(path):
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return False
    try:
        result = subprocess.run(
            ["rootls", "-t", path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10
        )
        return result.returncode == 0 and b"tree" in result.stdout
    except Exception:
        return False

def hadd_files(target, inputs, force=False):
    if not inputs:
        print(f"[WARN] No inputs for {target}")
        return

    print(f"\nHADD → {target}")
    for f in inputs:
        print("  input:", f)

    if os.path.exists(target):
        if not force:
            if is_valid_root_file(target):
                print(f"[INFO] Skipping valid file {target}")
                return
            else:
                print(f"[WARN] Removing invalid {target}")
        os.remove(target)

    cmd = ["hadd", "-f", target] + inputs
    print("Executing:", " ".join(cmd))
    subprocess.run(cmd, check=True)
    print("[OK] Created:", target)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-year", required=True)
    parser.add_argument("-era",  required=True)
    parser.add_argument("-f", "--force", action="store_true")
    args = parser.parse_args()

    year  = args.year
    eras  = list(args.era.upper())
    force = args.force
    user  = getpass.getuser()

    base      = f"/eos/user/{user[0]}/{user}/analysis/{year}/Data"
    samples   = os.path.join(base, "samples")
    era_wise  = os.path.join(base, "era_wise")

    os.makedirs(samples, exist_ok=True)
    os.makedirs(era_wise, exist_ok=True)

    print("\nStep 1: Hadding per-era files from base/ → era_wise/")

    for era in eras:
        out_file = os.path.join(era_wise, f"Muon_Run{year}{era}_mutau.root")

        input_files = [
            os.path.join(base, f)
            for f in os.listdir(base)
            if f.endswith(f"Run{year}{era}_mutau.root")
            and "Muon" in f
            and ".sys." not in f
        ]

        if input_files:
            hadd_files(out_file, input_files, force)
        else:
            print(f"[WARN] No input files for era {era}")

    print("\nStep 2: Hadding all era_wise files → final total file")

    final_file = os.path.join(base, f"Muon_Run{year}_mutau.root")

    era_inputs = [
        os.path.join(era_wise, f)
        for f in os.listdir(era_wise)
        if f.endswith("_mutau.root")
    ]

    if era_inputs:
        hadd_files(final_file, era_inputs, force)
    else:
        print("[ERROR] No era-wise files found")

    print("\nStep 3: Moving raw Muon*_Run files from base/ → samples/")

    for f in os.listdir(base):
        if (
            f.startswith("Muon") and
            f.endswith("_mutau.root") and
            f != os.path.basename(final_file) and
            "era_wise" not in f
        ):
            src = os.path.join(base, f)
            dst = os.path.join(samples, f)
            print("  moving:", f)
            shutil.move(src, dst)

    print("\nDone.")
    print("Final total file:", final_file)

if __name__ == "__main__":
    main()