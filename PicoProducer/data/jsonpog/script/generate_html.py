#!/usr/bin/env python

import os
import argparse
import pathlib as pl
import re
import pandas as pd
from rich.console import Console
import shutil

from correctionlib.highlevel import model_auto, open_auto


template = \
"""<!DOCTYPE html>
<html>
<head>
    <title>Summary of common POG JSONs</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/twitter-bootstrap/4.1.3/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.6.1/jquery.min.js"></script>
    <script src="fancyTable/fancyTable.min.js"></script>

    <h3>Summary of common POG JSONs</h3>
    
    #TABLE#

    <script type="text/javascript">
        $(function() {
            $("#jsonTable").fancyTable({
                sortColumn: 0,
                pagination: true,
                exactMatch: "auto",
                perPage: 20
            });
        });
    </script>
</body>
</html>
"""


def get_year_from_era(era):
    """ Go from '2017'/'2018UL'/'2016ULpreVFP' to '17'/'18'/'16' """
    return re.search(r"20([0-9]+).*", era).group(1)


def get_run_from_era(era):
    year, camp = era.split("_")
    if int(get_year_from_era(year)) <= 18:
        return year, camp, "Run2"
    else:
        return year, camp, "Run3"


def generate_json_summary(inPath, outPath):
    with open(os.devnull, "w") as devnull:
        console = Console(width=100, file=devnull, record=True)
        cset = model_auto(open_auto(str(inPath)))
        console.print(cset)
        console.save_html(str(outPath))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", required=True, help="input jsonpog-integration POG folder")
    parser.add_argument("-o", "--output", required=True, help="output folder for html pages")
    args = parser.parse_args()

    out_dir_p = pl.Path(args.output)
    summary_dir_p = out_dir_p / "summaries"
    summary_dir_p.mkdir(parents=True, exist_ok=True)

    root_dir_p = pl.Path(args.input)
    files = []
    
    for pog_dir_p in root_dir_p.iterdir():
        if not pog_dir_p.is_dir(): continue
        pog = pog_dir_p.name
        
        for era_dir_p in pog_dir_p.iterdir():
            if not era_dir_p.is_dir(): continue

            era = era_dir_p.name
            year, campaign, run = get_run_from_era(era)

            for json_file_p in era_dir_p.iterdir():
                if json_file_p.suffixes not in [[".json"], [".json", ".gz"]]: continue
                file_name = json_file_p.name.split(".")[0]

                summary_file_p = summary_dir_p / f"{pog}_{era}_{file_name}.html"
                print(f"Generating HTML summary for {json_file_p}")
                generate_json_summary(json_file_p, summary_file_p)

                files.append({
                    "POG": pog,
                    "Era": year,
                    "Campaign": campaign,
                    "LHC Run": run,
                    "File summary": f'<a href="summaries/{summary_file_p.name}" target="_blank">{file_name}</a>'
                })

    print("Generating index page")

    files = pd.DataFrame(files)

    index_p = out_dir_p / "index.html"
    index_p.write_text(
        template.replace("#TABLE#",
                         files.to_html(index=False, table_id="jsonTable", escape=False)
                        )
    )

    # also install javascript
    script_dir_p = pl.Path(__file__).parent / "fancyTable"
    shutil.copytree(script_dir_p, out_dir_p / "fancyTable", dirs_exist_ok=True)

