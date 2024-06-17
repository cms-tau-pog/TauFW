#!/usr/bin/env python

import argparse
import os
import json

import correctionlib
import correctionlib.schemav2

from rich.console import Console
from rich.columns import Columns


class Report:
    def __init__(self):
        self.corr_added = list()  # added corrections
        self.corr_removed = set()  # (name, version) of removed corrections
        self.corr_updated = list()  # (old, new) for modified corrections
        self.corr_version_error = set()  # (name, version) of modified corrections but where the version number wasn't bumped

    def generate(self, files):
        # Some ugly mix of markdown for gitlab and rich console output...

        def _print_cv(lst, msg=""):
            for c,v in lst:
                console.print(f" * `{c}` -> version `{v}`{msg}")

        console = Console(width=100, color_system=None)

        console.print(f"\n### Comparison: file {files[1]}\n")
        console.print(f"Old file: `{files[0]}`\n")

        if len(self.corr_version_error):
            console.print("\n#### Version errors\n")
            console.print("These corrections should increase their version numbers:\n")
            _print_cv(self.corr_version_error, msg=" is already in use")

        if len(self.corr_removed):
            console.print("\n#### Removed corrections\n")
            _print_cv(self.corr_removed)

        if len(self.corr_added):
            console.print("\n#### Added corrections\n")
            for added in self.corr_added:
                console.print(added)

        if len(self.corr_updated):
            console.print("\n#### Updated corrections\n")
            for old, new in self.corr_updated:
                console.print(Columns([old, new], width=40, equal=True, expand=True))

        if len(self.corr_version_error) + \
            len(self.corr_removed) + \
            len(self.corr_added) + \
            len(self.corr_updated) == 0:
            console.print("No significant difference in the corrections")

    def status_code(self):
        if len(self.corr_version_error):
            return 1
        return 0


def compare_corrections(c1, c2):
    """Return False if the two corrections differ in their content
    Differences in name, version or description are not considered"""

    for key in ["inputs", "output", "data", "generic_formulas"]:
        if c1.get(key) != c2.get(key):
            return False
    return True


def compare_files(old, new):
    corrs_old = old["corrections"]
    names_vers_old = { (c["name"], c["version"]) for c in corrs_old }
    names_old = { nv[0] for nv in names_vers_old }
    corrs_new = new["corrections"]
    names_vers_new = { (c["name"], c["version"]) for c in corrs_new }

    report = Report()
    report.corrs_removed = names_vers_old - names_vers_new

    for corr in corrs_new:
        name = corr["name"]
        vers = corr["version"]

        # new correction name, not present in old file
        if name not in names_old:
            report.corr_added.append(correctionlib.schemav2.Correction.parse_obj(corr))
            continue

        # we know there is a correction with the same name in the old file
        corrs_old_same_name = [ c for c in corrs_old if c["name"] == name ]

        # -> check if there is one with the same version
        old_same_version = next((c for c in corrs_old_same_name if c["version"] == vers), None)

        if old_same_version:
            # same version but different content -> problem!
            if not compare_corrections(old_same_version, corr):
                report.corr_version_error.add((name, vers))
            continue

        # different version -> check the version increased
        old_max_version = max(corrs_old_same_name, key=lambda c: c["version"])
        if old_max_version["version"] > vers:
            report.corr_version_error.add((name, vers))
        else:
            report.corr_updated.append(
                (correctionlib.schemav2.Correction.parse_obj(old_max_version),
                correctionlib.schemav2.Correction.parse_obj(corr)))

    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compares the content of two correction JSON files. Assumes their content are valid schemav2.")
    parser.add_argument("files", nargs=2, help="Two json files to compare: old and new")
    args = parser.parse_args()

    def json_load(path):
        data = correctionlib.highlevel.open_auto(path)
        return json.loads(data)
    files = map(json_load, args.files)

    report = compare_files(*files)
    report.generate(args.files)

    exit(report.status_code())

