# 1. Setting up the analysis software

## Connecting to CERN

For the entire exercise it is assumed, that you have access to the `lxplus.cern.ch` login nodes at CERN.

To connect to one of these machines (which use CentOS7 as operating system) from a Linux based system at your home institution, please use the following command, which needs to be adapted to your CERN computing account:

```sh
ssh <cern-username>@lxplus.cern.ch
```

You can additionally add on your home machine the following configuration to `~/.ssh/config` to enable for example X11 forwarding and to have a shorter command for connection:

```sh
Host cern7
    Hostname = lxplus.cern.ch
    User = <cern-username>
    Compression = yes
    ForwardX11 = yes
    ForwardAgent = yes
```

After adding this, you can connect to the CERN login nodes simply via `ssh cern7`

## Checking out the analysis software

At first, please create a separate working directory in your home folder at lxplus and move into it:

```sh
cd ~
mkdir -p TauLongCMSDAS2020
cd TauLongCMSDAS2020
```

To install the analysis framework adapted for the exercise in this directory, please execute the following commands:

```sh
# Moving into your exercise working directory
cd ~/TauLongCMSDAS2020

# Checking out CMSSW
cmsrel CMSSW_10_6_17_patch1
cd CMSSW_10_6_17_patch1/src
cmsenv

# Analysis SW
git clone https://github.com/ArturAkh/TauFW

# Tools to process NanoAOD
git clone https://github.com/cms-nanoAOD/nanoAOD-tools.git PhysicsTools/NanoAODTools

# Compiling everything
scram b -j 4
```

Additionally, you will need to install the SW for statistical inference in a different CMSSW environment.
To do this, perform the following commands, safest in a separate, fresh terminal tab on lxplus:

```sh
# Moving into your exercise working directory
cd ~/TauLongCMSDAS2020

# Checking out CMSSW for statistical inference (different from TauFW)
cmsrel CMSSW_10_2_23
cd CMSSW_10_2_23/src
cmsenv

# Combine package
git clone https://github.com/cms-analysis/HiggsAnalysis-CombinedLimit.git HiggsAnalysis/CombinedLimit
cd HiggsAnalysis/CombinedLimit
git fetch origin
git checkout v8.1.0

# CombineHarvester
cd $CMSSW_BASE/src
git clone https://github.com/cms-analysis/CombineHarvester.git CombineHarvester

# Analysis-specific CombineHarvester package
git clone https://github.com/ArturAkh/CMSDAS2020TauLong.git CombineHarvester/CMSDAS2020TauLong

# Compiling everything
scram b -j 4
```
