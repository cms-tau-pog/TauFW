import numpy as np
import os
import correctionlib

sfDir = os.path.join(".", "..", "POG", "BTV", "2018_UL")
btvjson = correctionlib.CorrectionSet.from_file(os.path.join(sfDir, "btagging.json.gz"))

# generate 20 dummy jet features
jet_pt    = np.random.exponential(50., 20)
jet_eta   = np.random.uniform(0.0, 2.4, 20)
jet_flav  = np.random.choice([0, 4, 5], 20)
jet_discr = np.random.uniform(0.0, 1.0, 20)

# separate light and b/c jets
light_jets = np.where(jet_flav == 0)
bc_jets    = np.where(jet_flav != 0)

# case 1: fixedWP correction with mujets (here medium WP)
# evaluate('systematic', 'working_point', 'flavor', 'abseta', 'pt')
bc_jet_sf = btvjson["deepJet_mujets"].evaluate("central", "M", 
            jet_flav[bc_jets], jet_eta[bc_jets], jet_pt[bc_jets])
light_jet_sf = btvjson["deepJet_incl"].evaluate("central", "M", 
            jet_flav[light_jets], jet_eta[light_jets], jet_pt[light_jets])
print("\njet SFs for mujets at medium WP:")
print(f"SF b/c: {bc_jet_sf}")
print(f"SF light: {light_jet_sf}")

# case 2: fixedWP correction uncertainty (here tight WP and comb SF)
# evaluate('systematic', 'working_point', 'flavor', 'abseta', 'pt')
bc_jet_sf = btvjson["deepJet_comb"].evaluate("up_correlated", "T", 
            jet_flav[bc_jets], jet_eta[bc_jets], jet_pt[bc_jets])
light_jet_sf = btvjson["deepJet_incl"].evaluate("up_correlated", "T", 
            jet_flav[light_jets], jet_eta[light_jets], jet_pt[light_jets])
print("\njet SF up_correlated for comb at tight WP:")
print(f"SF b/c: {bc_jet_sf}")
print(f"SF light: {light_jet_sf}")

# case 3: shape correction SF
# evaluate('systematic', 'flavor', 'eta', 'pt', 'discriminator')
jet_sf = btvjson["deepJet_shape"].evaluate("central", 
        jet_flav, jet_eta, jet_pt, jet_discr)
print("\njet SF for shape correction:")
print(f"SF: {jet_sf}")

# case 4: shape correction SF uncertainties
# evaluate('systematic', 'flavor', 'eta', 'pt', 'discriminator')
c_jets = np.where(jet_flav == 4)
blight_jets = np.where(jet_flav != 4)
b_jet_sf = btvjson["deepJet_shape"].evaluate("up_hfstats2", 
        jet_flav[blight_jets], jet_eta[blight_jets], jet_pt[blight_jets], jet_discr[blight_jets])
c_jet_sf = btvjson["deepJet_shape"].evaluate("up_cferr1", 
        jet_flav[c_jets], jet_eta[c_jets], jet_pt[c_jets], jet_discr[c_jets])
print("\njet SF up_hfstats2 for shape correction b/light jets:")
print(f"SF b/light: {b_jet_sf}")
print("jet SF up_cferr1 for shape correction c jets:")
print(f"SF c: {c_jet_sf}")
