# 2. Initial analysis configuration

After having performed the setup explained in section [1](sw_setup.md), you have now to configure your environment.

A part of the configuration needs to be done in each fresh login terminal on the `lxplus` machines, the other part is required only to be done once, if you need to introduce changes to the configuration.

## Configuration after new login or in a new terminal

To be able to perform the analysis with [TauFW](https://github.com/ArturAkh/TauFW.git) framework] covered by sections [3](preselection.md),
[4](flat_n-tuples.md), [5](norm_and_corr_exp.md), [6](refine_ztautau.md), [7](es_tau.md),
and [8](prep_stat_inference.md), you need to do the following each time you perform a new login on the CERN `lxplus` or open a new terminal window there.

```sh
# Moving into TauFW working directory
cd ~/TauLongCMSDAS2020/CMSSW_10_6_17_patch1/src

# Setting the CMSSW environment
cmsenv

# Check your VOMS proxy
voms-proxy-info

# In case the proxy is expired, refresh it via
voms-proxy-init --valid 192:00:00 --voms cms --rfc
```

The last two commands setup a proxy for your grid certificate and are needed to be able to access remotely stored datasets in the CERN grid,
and to write to CERN grid dCache storage servers with corresponding tools.

You can check the settings for your grid certificate, provided that it is imported into your browser, for example at [voms2.cern.ch](https://voms2.cern.ch:8443/voms/cms/user/home.action).
