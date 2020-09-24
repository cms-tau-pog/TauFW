# 2. Initial analysis configuration

After having performed the setup explained in section [1](sw_setup.md), you have now to configure your environment.

A part of the configuration needs to be done in each fresh login terminal on the `lxplus` machines, the other part is required only to be done once, if you need to introduce changes to the configuration.

## Configuration after new login or in a new terminal

To be able to perform the analysis with [TauFW](https://github.com/ArturAkh/TauFW.git) framework covered by sections [3](preselection.md),
[4](flat_n-tuples.md), [5](norm_and_corr_exp.md), [6](refine_ztautau.md), [7](es_tau.md),
and [8](prep_stat_inference.md), you need to do the following each time you perform a new login on the CERN `lxplus` or open a new terminal window there.

```sh
# Moving into TauFW working directory
cd ~/TauLongCMSDAS2020/CMSSW_10_6_17_patch1/src

# Setting the CMSSW environment
cmsenv

# Fix the VOMS proxy path explicitly to avoid /tmp directories.
export X509_USER_PROXY=/afs/cern.ch/user/<first-letter-of-cern-username>/<cern-username>/public/x509_voms

# Check your VOMS proxy
voms-proxy-info

# In case the proxy is expired, refresh it via
voms-proxy-init --valid 192:00:00 --voms cms --rfc
```

The last three commands setup a proxy for your grid certificate and are needed to be able to access remotely stored datasets in the CERN grid,
and to write to CERN grid dCache storage servers with corresponding tools. A fixed `X509_USER_PROXY` environment variable is required to be avoid
`/tmp` directories used by default, which may be not accessible at batch system nodes.

You can add the `export` of the `X509_USER_PROXY` environment variable as an `alias` to you `~/.bashrc` by adding the following lines to it:

```sh
alias set-voms='export X509_USER_PROXY=/afs/cern.ch/user/<first-letter-of-cern-username>/<cern-username>/public/x509_voms'
```
In that way, you do not need to keep always the full path in mind, each time you would like to fix the variable, but just do this to check the proxy:

```sh
set-voms; voms-proxy-info
```

Side remark: you need to replace `<first-letter-of-cern-username>/<cern-username>/` where it apprears appropriately, of course :).

You can check the settings for your grid certificate, provided that it is imported into your browser, for example at [voms2.cern.ch](https://voms2.cern.ch:8443/voms/cms/user/home.action).

In case of the statistical inference covered in sections [8](prep_stat_inference.md) and [9](measurement.md) the setup of the environment for a new login or a new terminal is as follows:

```sh
# Moving into Combine & CombineHarvester working directory
cd ~/TauLongCMSDAS2020/CMSSW_10_2_23/src

# Setting the CMSSW environment
cmsenv

# Increase stack size to avoid crashes for too big workspaces in ROOT
ulimit -s unlimited
```

## Configuration done once per desired change

By default the [TauFW](https://github.com/ArturAkh/TauFW.git) framework is configured for analyses of the Tau POG, such that you have to change it a bit for the exercise.
At the same time, you get familiar with the configuration of the framework, such that you can introduce configuration changes, if these are required for your purpose.

To list the current configuration, execute the following command in the TauFW working directory:

```sh
pico.py list
```

At first, the list of input NanoAOD samples needs to be changed from default to [samples_mutau_2018.py](../../PicoProducer/samples/CMSDAS2020/samples_mutau_2018.py):

```sh
pico.py era 2018 CMSDAS2020/samples_mutau_2018.py
```

If this sample list is chosen, original NanoAOD samples will be processed for preselection explained in section [3](preselection.md) and further analysis starting from
section [4](flat_n-tuples.md). In case of an analysis in the &mu;&tau;<sub>h</sub> final state, preselected NanoAOD samples were already produced for you, such that you could run your analysis
on these samples. To do this, please change the sample list to [samples_mutau_2018_preselected.py](../../PicoProducer/samples/CMSDAS2020/samples_mutau_2018_preselected.py) as follows:

```sh
pico.py era 2018 CMSDAS2020/samples_mutau_2018_preselected.py
```

Please note, that the two lists `samples_mutau_2018.py` and `samples_mutau_2018_preselected.py` only differ by their `storage` setting. Check that in the TauFW working directory via:

```sh
vimdiff ${CMSSW_BASE}/src/TauFW/PicoProducer/samples/CMSDAS2020/samples_mutau_2018*.py
```

You could also use just `diff`, but `vimdiff` is so much cooler. For more details, please refer to [vim cheat sheet](https://vim.rtorr.com/)
and to [vimdiff cheat sheet](https://gist.github.com/brbsix/0d64ff0e798535a73778).

The preselected NanoAOD files contain a much smaller amount of events than the corresponding originals, and they have less quantities stored for each event. If running on these files,
it is best to try out to process several files at once per run. To configure this for all samples, perform the following command:

```sh
pico.py set nfilesperjob 10
```

Alternatively, you can configure this per sample in [samples_mutau_2018_preselected.py](../../PicoProducer/samples/CMSDAS2020/samples_mutau_2018_preselected.py) with the corresponding keyword argument.

Next step is to setup the proper analysis channel, that allows to create flat n-tuples.
Following the configuration of samples above, you should configure the analysis to the &mu;&tau;<sub>h</sub> final state of the Z&rarr;&tau;&tau; decay.
This analysis is constructed in [ModuleMuTau](../../PicoProducer/python/analysis/CMSDAS2020/ModuleMuTau.py) and is included into the configuartion as follows:

```sh
pico.py channel mutau CMSDAS2020.ModuleMuTau
```

For a different Z&rarr;&tau;&tau; final state, for example e&mu;, you will need to produce your own preselected NanoAOD, which will be stored in the directory configured as `nanodir`.

Finally, please check whether all directories configured (execute `pico.py list` to see them) are accessible, are properly written and you have the right permissions to read the files.
More details on which directories are used for which step, will be given in the corresponding analysis sections.
