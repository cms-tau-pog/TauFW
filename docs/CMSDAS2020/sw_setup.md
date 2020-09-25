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

## EOS user space

If not already done, you can activate your EOS space following the corresponding [instructions](https://resources.web.cern.ch/resources/Manage/EOS/Default.aspx).

This will give you access to 1 TB personal storage space, accessible from CERN `lxplus` machines e.g. via the path `/eos/user/<first-letter-of-cern-username>/<cern-username>`.
There, you can store for example large files needed for the analysis.

## Checking out the analysis software

At first, please create a separate working directory in your home folder at lxplus and move into it:

```sh
cd ~
mkdir -p TauLongCMSDAS2020
cd TauLongCMSDAS2020
```

In this folder, you a fast access connection, but only 10 GB local space. If you think, that you need more space for the software
and the outputs produced by it (could actually be the case in case of [preselection](preselection.md)), you can move to a `work` folder on `lxplus` and setup the software there:

```sh
cd /afs/cern.ch/work/<first-letter-of-cern-username>/<cern-username>/

# and then, the folder creation, etc.
...
```

Before doing this, make sure, that you have such a folder. You can check it at [CERN Resources Portal](https://resources.web.cern.ch/resources/Manage/AFS/Settings.aspx). You can increase
your `work` folder quota up to 100 TB. The connection to that folder from the `lxplus` folder might be slower, but you have a bunch of space there on the other hand :).

To install the analysis framework adapted for the exercise in this directory, please execute the following commands:

```sh
# Moving into your exercise working directory
cd ~/TauLongCMSDAS2020

# Checking out CMSSW
cmsrel CMSSW_10_6_17_patch1
cd CMSSW_10_6_17_patch1/src
cmsenv

# Analysis SW
git clone https://github.com/ArturAkh/TauFW.git

# Tools to process NanoAOD
git clone https://github.com/cms-nanoAOD/nanoAOD-tools.git PhysicsTools/NanoAODTools

# Compiling everything
scram b -j 4
```

Additionally, you will need to install the software for statistical inference in a different CMSSW environment.
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

## Introducing your own changes

After this initial setup of the software, you are advised to *fork* the repositories [TauFW](https://github.com/ArturAkh/TauFW) and
[CombineHarvester/CMSDAS2020TauLong](https://github.com/ArturAkh/CMSDAS2020TauLong.git) to be able to introduce your own changes to the software and to save your progress
on github.

For forking, just open the two github links above, create a github account in case you do not have one yet, and click on the **Fork** button on the top right of the webpage of each repository.

After the forking process is finished, you can add the forked repositories as additional remotes to the checked out software in your home directory:

```sh
# your fork for TauFW
cd ~/TauLongCMSDAS2020/CMSSW_10_6_17_patch1/src/TauFW/
git remote add myfork https://github.com/<github-username>/TauFW

# print out all remotes of TauFW
git remote -v

# your fork for CombineHarvester/CMSDAS2020TauLong
cd ~/TauLongCMSDAS2020/CMSSW_10_2_23/src/CombineHarvester/CMSDAS2020TauLong
git remote add myfork https://github.com/<github-username>/CMSDAS2020TauLong.git

# print out all remotes of CombineHarvester/CMSDAS2020TauLong
git remote -v
```

In that way, you can safely do your own developments on the local master branch, and if you would like to push your changes to your fork,
you will need to specify the appropriate remote different from `origin`:

```sh
git push myfork master
```

Another advantage of having your personal fork of the repository is the possibility to discuss changes introduced by everyone of you, just by comparing across forks on github.

After some of you have completed a subtask for the analysis and the corresponding changes to the software have been discussed, others can profit from these developments by merging them
from the corresponding fork after adding it as an additional remote to their own fork.

Long story short: Make use of strengths of github to improve the collaborative work among you during this exercise! Do not forget, that you all should consider yourselves as an entire analysis group
working hand in hand to achieve a nice measurement :)
