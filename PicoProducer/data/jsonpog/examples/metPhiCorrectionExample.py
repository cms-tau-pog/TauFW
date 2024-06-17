"""
In this test script, the different MET Phi Corrections are applied to uniform MET pt,phi distributions to check whether the corrections have an effect.
The number of primary vertices are also drawn from a uniform distribution. The run numbers come from a uniform distribution as well but the run ranges (for data)
are fitting the different eras to not cause crashes.
In the end two plots are created. The first one shows the effect of the corrections on the uniform MET phi distribution and the second one shows the same effect
but as a function of the primary vertices.
This is only a technical test, the resulting plots should not be taken too seriously.
"""

import sys
import correctionlib
import numpy as np
import matplotlib.pyplot as plt

# get random generator
rng = np.random.default_rng()

# existing corrections
correction_labels = ["metphicorr_pfmet_mc", "metphicorr_puppimet_mc", "metphicorr_pfmet_data", "metphicorr_puppimet_data"]
# existing eras
eras = ["2018_UL", "2017_UL", "2016postVFP_UL", "2016preVFP_UL"]
# run ranges corresponding to the eras
run_ranges = [[315252, 325274], [297020, 306463], [278769, 284045], [272007, 278771]]
# name of the correction json
infile = "met.json.gz"

# loop over available eras and run ranges
for era,run_range in zip(eras,run_ranges):
    print("\n####################### Era: {} #######################\n".format(era))
    # loop over corrections
    for correction_label in correction_labels:
        print("\n############ Correction: {} ############\n".format(correction_label))

        # basic sanity check to find out whether the correction is for data or mc
        is_data = None
        if ("mc" in correction_label) and (not ("data" in correction_label)):
            is_data = False
        elif ("data" in correction_label) and (not ("mc" in correction_label)):
            is_data = True
        else:
            print("data and mc are mixed in the correction labels")
            exit()

        # load correction set from file
        ceval = correctionlib.CorrectionSet.from_file("../POG/JME/{}/{}".format(era,infile))

        # print keys and values of the correction set
        # print(list(ceval.keys()))
        # print(list(ceval.values()))

        # print correction name and version
        for corr in ceval.values():
            print(f"Correction {corr.name}")
            print(f"Version {corr.version}")

        #pts = rng.uniform(low=0.,high=1000.,size=1000000)
        # draw the uncorrected met pts from a decaying power law (this is just to get a distribution which crudely resembles the met pt distribution)
        pts = (rng.pareto(1.5,size=1000000))*100
        # make sure to not cross the maximum allowed value for uncorrected met pt
        pts = np.minimum(pts, np.full_like(pts, 6499, dtype=float))
        # draw uncorrected met phis from a uniform distribution between -pi and pi
        phis = rng.uniform(low=-3.14,high=3.14,size=1000000)
        # draw number of vertices from a uniform distribution
        npvs = rng.integers(low=0,high=200,size=1000000)
        # use correct run ranges when working with data, otherwise use uniform run numbers in an arbitrary large window
        runs = None
        if is_data:
            runs = rng.integers(low=run_range[0],high=run_range[1],size=1000000)
        else:
            runs = rng.integers(low=0,high=100000,size=1000000)

        # print some values of the starting situation
        print("uncorrected pts:",pts[1:11])
        print("uncorrected phis:",phis[1:11])
        print("number of vertices:",npvs[1:11])
        print("run numbers:",runs[1:11])

        # retrieve the corrected pts and phis by using the evaluate method of the corrections
        corrected_pts = ceval["pt_{}".format(correction_label)].evaluate(pts,phis,npvs,runs)
        corrected_phis = ceval["phi_{}".format(correction_label)].evaluate(pts,phis,npvs,runs)

        # print the corresponding corrected values
        print("corrected pts:",corrected_pts[1:11])
        print("corrected phis:",corrected_phis[1:11])

        # draw the uncorrected and corrected phis in one plot
        fig, axs = plt.subplots(1, 2, sharey=True, tight_layout=True)
        axs[0].set(xlabel="uncorrected phi")
        axs[0].hist(phis, bins=32)
        axs[1].set(xlabel="corrected phi")
        axs[1].hist(corrected_phis, bins=32)

        #plt.show()
        plt.savefig("{}_{}_phi.pdf".format(correction_label,era))
        print("{}_{}_phi.pdf saved".format(correction_label,era))

        # draw the uncorrected and corrected pts in one plot
        fig, axs = plt.subplots(1, 2, sharey=True, tight_layout=True)
        axs[0].set(xlabel="uncorrected pt")
        axs[0].hist(pts, bins=20, range=[0.,1000.])
        axs[1].set(xlabel="corrected pt")
        axs[1].hist(corrected_pts, bins=20, range=[0.,1000.])

        #plt.show()
        plt.savefig("{}_{}_pt.pdf".format(correction_label,era))
        print("{}_{}_pt.pdf saved".format(correction_label,era))

        # draw the uncorrected and corrected phis as a function of the number of primary vertices in one plot
        fig, axs = plt.subplots(1, 2, tight_layout=True, sharey=True)
        axs[0].hist2d(npvs, phis, bins=(20,16))
        axs[0].set(xlabel="number of primary vertices", ylabel="uncorrected phi")
        axs[1].hist2d(npvs, corrected_phis, bins=(20,16))
        axs[1].set(xlabel="number of primary vertices", ylabel="corrected phi")

        #plt.show()
        plt.savefig("{}_{}_phi_vs_npvs.pdf".format(correction_label,era))
        print("{}_{}_phi_vs_npvs.pdf saved".format(correction_label,era))
