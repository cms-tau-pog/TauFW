#! /usr/bin/env python
# Example of how to read the JME-JERC JSON files
# For more information, see the README in
# https://gitlab.cern.ch/cms-nanoAOD/jsonpog-integration/-/tree/master/POG/JME
# For a comparison to the CMSSW-syntax refer to
# https://github.com/cms-jet/JECDatabase/blob/master/scripts/JERC2JSON/minimalDemo.py

import os
import correctionlib._core as core

# path to directory of this script
__this_dir__ = os.path.dirname(__file__)

#
# helper functions
#

def get_corr_inputs(input_dict, corr_obj):
    """
    Helper function for getting values of input variables
    given a dictionary and a correction object.
    """
    input_values = [input_dict[inp.name] for inp in corr_obj.inputs]
    return input_values


#
# values of input variables
#

example_value_dict = {
    # jet transverse momentum
    "JetPt": 100.0,
    # jet pseudorapidity
    "JetEta": 0.0,
    # jet azimuthal angle
    "JetPhi": 0.2,
    # jet area
    "JetA": 0.5,
    # median energy density (pileup)
    "Rho": 15.0,
    # systematic variation (only for JER SF)
    "systematic": "nom",
    # pT of matched gen-level jet (only for JER smearing)
    "GenPt": 80.0,  # or -1 if no match
    # unique event ID used for deterministic
    # pseudorandom number generation (only for JER smearing)
    "EventID": 12345,
}


#
# JEC-related examples
#

# JEC base tag
jec = "Summer19UL16_V7_MC"

# jet algorithms
algo = "AK4PFchs"
algo_ak8 = "AK8PFPuppi"

# jet energy correction level
lvl = "L2Relative"

# jet energy correction level
lvl_compound = "L1L2L3Res"

# jet energy uncertainty
unc = "Total"

# print input information
print("\n\nJEC parameters")
print("##############\n")

print("jec = {}".format(jec))
print("algo = {}".format(algo))
print("algo_ak8 = {}".format(algo_ak8))
for v in ("JetPt", "JetEta", "JetA", "JetPhi", "JetA", "Rho"):
    print("{} = {}".format(v, example_value_dict[v]))


#
# load JSON files using correctionlib
#

# AK4
fname = os.path.join(__this_dir__, "../POG/JME/2016postVFP_UL/jet_jerc.json.gz")
print("\nLoading JSON file: {}".format(fname))
cset = core.CorrectionSet.from_file(os.path.join(fname))

# AK8
fname_ak8 = os.path.join(__this_dir__, "../POG/JME/2016postVFP_UL/fatJet_jerc.json.gz")
print("\nLoading JSON file: {}".format(fname_ak8))
cset_ak8 = core.CorrectionSet.from_file(os.path.join(fname_ak8))

# tool for JER smearing
fname_jersmear = os.path.join(__this_dir__, "../POG/JME/jer_smear.json.gz")
print("\nLoading JSON file: {}".format(fname_jersmear))
cset_jersmear = core.CorrectionSet.from_file(os.path.join(fname_jersmear))


#
# example 1: getting a single JEC level
#

print("\n\nExample 1: single JEC level\n===================")

key = "{}_{}_{}".format(jec, lvl, algo)
key_ak8 = "{}_{}_{}".format(jec, lvl, algo_ak8)
print("JSON access to keys: '{}' and '{}'".format(key, key_ak8))
sf = cset[key]
sf_ak8 = cset_ak8[key_ak8]

sf_input_names = [inp.name for inp in sf.inputs]
print("Inputs: " + ", ".join(sf_input_names))

inputs = get_corr_inputs(example_value_dict, sf)
print("JSON result AK4: {}".format(sf.evaluate(*inputs)))

inputs = get_corr_inputs(example_value_dict, sf_ak8)
print("JSON result AK8: {}".format(sf_ak8.evaluate(*inputs)))


#
# example 2: accessing the JEC as a CompoundCorrection
#

print("\n\nExample 2: compound JEC level\n===================")

key = "{}_{}_{}".format(jec, lvl_compound, algo)
key_ak8 = "{}_{}_{}".format(jec, lvl_compound, algo_ak8)
print("JSON access to keys: '{}' and '{}'".format(key, key_ak8))
sf = cset.compound[key]
sf_ak8 = cset_ak8.compound[key_ak8]

sf_input_names = [inp.name for inp in sf.inputs]
print("Inputs: " + ", ".join(sf_input_names))

inputs = get_corr_inputs(example_value_dict, sf)
print("JSON result AK4: {}".format(sf.evaluate(*inputs)))

inputs = get_corr_inputs(example_value_dict, sf_ak8)
print("JSON result AK8: {}".format(sf_ak8.evaluate(*inputs)))


#
# example 3: accessing the JEC uncertainty sources
#

print("\n\nExample 3: JEC uncertainty source\n===================")

# additional note: Regrouped/reduced set of uncertainty sorces as detailed in
# https://twiki.cern.ch/twiki/bin/viewauth/CMS/JECUncertaintySources#Run_2_reduced_set_of_uncertainty  # noqa
# are included in relevant JSON files (currently UL) with a "Regrouped_"-prefix,
# e.g. for 2016 one could access "Absolute_2016" via:
# sf = cset["Summer19UL16_V7_MC_Regrouped_Absolute_2016_AK4PFchs"]

key = "{}_{}_{}".format(jec, unc, algo)
print("JSON access to key: '{}'".format(key))
sf = cset[key]

sf_input_names = [inp.name for inp in sf.inputs]
print("Inputs: " + ", ".join(sf_input_names))

inputs = get_corr_inputs(example_value_dict, sf)
print("JSON result: {}".format(sf.evaluate(*inputs)))



########################
# JER-related examples #
########################

# JER base tag
jer = "Summer20UL16_JRV3_MC"

# algorithms
algo = "AK4PFchs"
algo_ak8 = "AK8PFchs"

# systematic variation (only for JER SF)
syst = "nom"

# print input information
print("\n\nJER parameters")
print("##############\n")

print("jer = {}".format(jer))
print("algo = {}".format(algo))
print("algo_ak8 = {}".format(algo_ak8))
for v in ("JetPt", "JetEta", "Rho"):
    print("{} = {}".format(v, example_value_dict[v]))


#
# example 4: accessing the JER scale factor
#

print("\n\nExample 4: JER scale factor\n===================")

key = "{}_{}_{}".format(jer, "ScaleFactor", algo)
print("JSON access to key: '{}'".format(key))
sf = cset[key]

sf_input_names = [inp.name for inp in sf.inputs]
print("Inputs: " + ", ".join(sf_input_names))

inputs = get_corr_inputs(example_value_dict, sf)
jersf_value = sf.evaluate(*inputs)
print("JSON result: {}".format(jersf_value))


#
# example 5: accessing the JER
#

print("\n\nExample 5: JER (pT resolution)\n===================")

key = "{}_{}_{}".format(jer, "PtResolution", algo)
print("JSON access to key: '{}'".format(key))
sf = cset[key]

sf_input_names = [inp.name for inp in sf.inputs]
print("Inputs: " + ", ".join(sf_input_names))

inputs = get_corr_inputs(example_value_dict, sf)
jer_value = sf.evaluate(*inputs)
print("JSON result: {}".format(jer_value))


#
# example 6: performing JER smearing
# (needs JER/JERSF from previous step)
#


print("\n\nExample 6: JER smearing\n===================")

key_jersmear = "JERSmear"
print("JSON access to key: '{}'".format(key_jersmear))
sf_jersmear = cset_jersmear[key_jersmear]

# add previously obtained JER/JERSF values to inputs
example_value_dict["JER"] = jer_value
example_value_dict["JERSF"] = jersf_value

sf_input_names = [inp.name for inp in sf_jersmear.inputs]
print("Inputs: " + ", ".join(sf_input_names))

inputs = get_corr_inputs(example_value_dict, sf_jersmear)
jersmear_factor = sf_jersmear.evaluate(*inputs)
print("JSON result: {}".format(jersmear_factor))

# to implement smearing in the analysis code, multiply
# the `jersmear_factor` obtained above to the `Jet_pt`
# and `Jet_mass` variables
