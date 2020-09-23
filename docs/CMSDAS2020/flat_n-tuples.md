# 4. Creating flat n-tuples

After the NanoAOD samples are preselected as described in the [previous section](preselection.md), you can create flat n-tuples based on these samples
with faster turn-around cycles, than using original NanoAOD as input.

This section is meant as an introduction to the way analysis modules in TauFW can be setup to create flat n-tuples, based on the example for &mu;&tau;<sub>h</sub>,
[ModuleMuTau](../../PicoProducer/python/analysis/CMSDAS2020/ModuleMuTau.py). You can use this example as a starting point for the further analysis in &mu;&tau;<sub>h</sub>, but also
for other final states with corresponding adaptions.

If your TauFW configuration still corresponds to the preselection setup (check with `pico.py list`), then please change it to be able to run on top of preselected NanoAOD samples.
For &mu;&tau;<sub>h</sub>, you can follow the instructions from section [2](configuration.md#configuration-done-once-per-desired-change) to change the settings,
including an increase of the number of processed files by default.

## Purpose of flat n-tuples

In contrast to NanoAOD samples, flat n-tuples are not meant to be of general purpose, and should not contain vectors of quantities.
This means, the only quantities stored in the TTree of a flat n-tuple are usually
floats, integers, booleans, and characters, and they should comprise only those being of particular need for the analysis, for example to:

+ check and improve agreement between data and expectation,
+ refine signal selection to enrich the signal,
+ define sideband regions for data-driven background estimation,
+ define analysis categories,
+ and compute high-level quantities with high discriminating power.

Among these highly discriminating quantities, you could find for example mass related variables of the &tau;&tau; system,
or MVA based discriminators for (multi-)classification of signals and backgrounds.

After having clarified the purpose of flat n-tuples in the context of this exercise, let us have a closer look at the corresponding TauFW module.

## Structure of an analysis module

The analysis module [ModuleMuTau](../../PicoProducer/python/analysis/CMSDAS2020/ModuleMuTau.py) is based on the [nanoAOD-tools](https://github.com/cms-nanoAOD/nanoAOD-tools) software.
The module is required to have the following methods:

+ `__init__(self,fname,**kwargs)`: Basic initialization of the module before starting the event loop. Here, the output file can be defined for example.
+ `beginJob(self)`: Instructions to be done at the beginning of the event loop, like the setup of a cutflow histogram and an output tree.
+ `endJob(self)`: Instructions after the configured event loop is finished, like storing everything in the output file and closing it.
+ `analyze(self, event)`: This is the main function of the analysis module, where the selection of physics objects and events is performed.

After this small overview over analysis module, let us now try to better understand the current selection implemented in the module, and what is
required from you to extend this selection in the context of the exercise.

## Initial analysis selection

The first step of the selection is to apply global event filters, like the requirement of a fired trigger.

After that, collections of different physics objects are created. In case of the &mu;&tau;<sub>h</sub> final state, the main collections are created for muons and &tau;<sub>h</sub> candidates.
These two collections are used to create a &tau;&tau; pair candidate.

However, additional physics objects could and should be considered to refine the selection of the analysis.

The collection of electrons can used together with the collection of muons to ensure, that the &mu;&tau;<sub>h</sub> final state does not overlap with other final states of the analysis, and to suppress
contributions from Z&rarr;&mu;&mu; or Z&rarr;ee events.

It is also good to have a look at jets and b-tagged jets to figure out, whether they can be used to enrich Z&rarr;&tau;&tau;, while suppressing backgrounds at the same time.

Finally, another important physics object is the missing transverse energy, called also missing E<sub>T</sub>, or simply MET. This physics object can be used to construct several
high-level quantities to distinguish Z&rarr;&tau;&tau; from W + jets and from tt&#773;.

The selection given in the [ModuleMuTau](../../PicoProducer/python/analysis/CMSDAS2020/ModuleMuTau.py) repository is essentially the one you have seen for [preselection](preselection.md)
of the &mu;&tau;<sub>h</sub> final state. The only more restrictive requirement is the separation
in &Delta;R = (&Delta;&phi;<sup>2</sup> + &Delta;&eta;<sup>2</sup>)<sup>0.5</sup> between the muon and the &tau;<sub>h</sub> candidate.

Therefore, several TODO&apos;s are defined for you to extend the inital selection to create flat n-tuples, partly also to be covered in section [6](refine_ztautau.md).

In the course of the exercise, you will come back often to this module to refine the selection further and further. That is also the reason, why it is good to have fast turn-arounds with this step.

But let us first define the tasks to be done for this section, which have the aim to make you familiar with NanoAOD content and to allow you to extend the content of the flat n-tuple outputs :).

## Tasks of this section

To avoid ambiguities, the tasks for this section are marked with `TODO section 3` in [ModuleMuTau](../../PicoProducer/python/analysis/CMSDAS2020/ModuleMuTau.py).

To make these tasks easier for yourself, you should get familiar with quantities stored in the NanoAOD files, by looking at preselected or original samples on one hand:

```sh
# Hopefully already known commands for you from previous section ;)
root -l <original>.root -e "Events->GetListOfLeaves()->Print(); exit(0)" | sort -V > original_content.txt
root -l <preselected>.root -e "Events->GetListOfLeaves()->Print(); exit(0)" | sort -V > preselected_content.txt
```

and having a look at the [NanoAOD documentation](https://cms-nanoaod-integration.web.cern.ch/integration/master-106X/mc102X_doc.html) of these samples on the other hand to understand how
to interpret the quantities.

To define new variables, let you inspire by already existing output variables, such as `m_vis`, `decayMode_2` or `id_2`.

### Task 1: electrons and muons for event veto

Define collections of muons and electrons used to veto events with additional muons and electrons. The selection for the leptons should be equal or looser than the
the signal selection. Therefore, if other final states than &mu;&tau;<sub>h</sub> are anticipated to be done by some of you, discuss and agree on similar signal and veto selections across
all considered final states.

An example for possible veto selections:

+ muons: the same as signal muons, but with a looser p<sub>T</sub> threshold, p<sub>T</sub> > 15.0 GeV.
  + Align this selection with signal and veto selections for muons in other final states appropriately, if necessary.
  + Define the requirement to reject events with additional muons. How would it look like in the code explicitly?
+ electrons: p<sub>T</sub> > 15.0 GeV, loose WP of MVA-based ID (Fall17 training without using isolation), custom isolation cut on PF based isolation using all PF candidates.
  + Align also this selection with signal and veto selections for electrons in other final states appropriately, if necessary.
  + How is the requirement to reject events with additional electrons defined in the code?

### Task 2 (optional): improve the selection of the &mu;&tau;<sub>h</sub> pair

This is an optional task, not necessarily needed to achieve proper results. However, those of you interested in the details of the more sophisticated
[&tau;&tau; pair selection algorithm](https://twiki.cern.ch/twiki/bin/view/CMS/HiggsToTauTauWorking2017#Pair_Selection_Algorithm) may tackle this task and share
the result with others, once concluded.

The main idea of this &tau;&tau; pair selection algorithm is to select the most *isolated* pair, not the one composed from physics objects with highest p<sub>T</sub>.

Some tips to understand the algorithm better:

+ The isolation values are considered to be the same, if they match up to a certain digit after comma, therefore you would need round the numbers appropriately before comparing them.
+ Isolation of muons and electrons is given relative to p<sub>T</sub> as energy sums. Therefore, the *smaller* the value, the more isolated is the physics object.
+ In contrast to that, the measure for isolation of a &tau;<sub>h</sub> candidate is its DNN based discriminator against jets. Here, the *higher* the value, the more isolated is the
&tau;<sub>h</sub> candidate.
+ In [ModuleMuTau](../../PicoProducer/python/analysis/CMSDAS2020/ModuleMuTau.py), the isolation measures for the muon and the &tau;<sub>h</sub> candidate are already chosen in the right
way and written out as `iso_1` and `iso_2`, respectively.

### Task 3: jet selection and variables

Jets are not directly used as signal objects, however, they can be quite useful to enrich Z&rarr;&tau;&tau; or to define signal categories and control regions regions for backgrounds.

For this reason, you are asked to selected good jets and store quantities related to them. The selection can be performed in three main steps:

+ Basic selection of jets with:
  + p<sub>T</sub> > 20.0 GeV, |&eta;| < 4.7,
  + passing loose WP of the pileup jet ID, tight WP of standard jet ID,
  + not overlapping with the muon or &tau;<sub>h</sub> candidate of the signal pair, having &Delta;R(&mu; or &tau;<sub>h</sub>, jet) &ge; 0.5 
+ p<sub>T</sub> > 30.0 GeV jets:
  + Starting from basic jets, keep only those with p<sub>T</sub> > 30.0 GeV to suppress pileup jets further.
  + Store as output quantities the number of the resulting jets, as well as p<sub>T</sub> and &eta; of the jets leading and subleading in p<sub>T</sub>
+ b-tagged jets:
  + Starting from basic jets, keep only those with |&eta;| < 2.5 and require [medium WP](https://twiki.cern.ch/twiki/bin/viewauth/CMS/BtagRecommendation102X#Supported_Algorithms_and_Operati)
of the DeepFlavour b+bb+lepb discriminator. Since the b-tagged jets are within the tracker acceptance, they may have lower p<sub>T</sub> because the existence of charged tracks allows for
a better discrimination of jets from pileup.
  + Store as output quantities the number of b-tagged jets, as well as p<sub>T</sub> and &eta; of the b-tagged jets leading and subleading in p<sub>T</sub>

### Task 4: MET choice and variables

Also the MET is a useful variable to construct high-level variables to enrich Z&rarr;&tau;&tau; or to define signal categories and control regions.

In the current NanoAOD format, there are various definitions of MET available. The most used ones - as you can see discussed in the corresponding
[MET paper](https://doi.org/10.1088/1748-0221/14/07/P07004) - are the PF-based MET (stored simply as `MET` in NanoAOD) and the PUPPI MET (stored as `PuppiMET` in NanoAOD). Both
are corrected for pileup contributions, the latter with the [**P**ile**u**p **p**er **P**article **I**dentification](https://doi.org/10.1007/JHEP10(2014)059) method.

To be able to compare these two definitions in terms of mean, resolution and data/expectation agreement, please store p<sub>T</sub>, &phi;, and &Sigma;E<sub>T</sub> for both
versions of the MET in different variables. As soon as you start to implement variables using MET in their computation, please also keep in mind to create two versions of the
computed variable.

### Task 5: Additional (high-level) variables

After all physics objects of interest are selected, variables can be computed and stored, which are computed from multiple input quantities, or are global properties of an event.
Please implement at least the following list of variables:

+ visible p<sub>T</sub> of the Z boson candidate. Tip: have a look at the `m_vis` computation.
+ best-estimate for the full p<sub>T</sub> of the Z boson candidate, including neutrinos. What should added to the p<sub>T</sub> vector of the &mu;&tau;<sub>h</sub> pair?
+ transverse mass for the system of the muon and MET, m<T>(&mu; MET). A definition is given for example in [doi:10.1140/epjc/s10052-018-6146-9](https://doi.org/10.1140/epjc/s10052-018-6146-9),
equation (3). Please check, whether the value for &Delta;&phi; is in the [-&pi;,+&pi;] interval. If not, does this have an influence on the result from applying Sine or Cosine functions on it?
+ D<sub>&zeta;</sub> variable, also defined in [doi:10.1140/epjc/s10052-018-6146-9](https://doi.org/10.1140/epjc/s10052-018-6146-9), formula (4) and Figure 1. The difference is that it
is considered for the e&mu; final state there, but could be used also for other &tau;&tau; final states.
+ Separation in &Delta;R between the muon and the &tau;<sub>h</sub> candidate. Here you can use the functions defined for the
[`Object`](https://github.com/cms-nanoAOD/nanoAOD-tools/blob/master/python/postprocessing/framework/datamodel.py#L49-L89) class defined in NanoAOD,
as already used in [ModuleMuTau](../../PicoProducer/python/analysis/CMSDAS2020/ModuleMuTau.py). Please note, that in this case, the interval of &Delta;&phi; is required to be [-&pi;,+&pi;].
+ Pileup density &rho;, computed from all PF Candidates.
+ Number of reconstructed primary vertices.
+ for MC only: number of **true** pileup interactions. Please use the `if self.ismc:` case to fill this variable to distinguish from data, where this quantity is not available in NanoAOD.

## Producing local n-tuple output and testing the code

In the process of your adaptions to the analysis module [ModuleMuTau](../../PicoProducer/python/analysis/CMSDAS2020/ModuleMuTau.py), you are advised to test your implementation frequently
after each small step you have done. This, you do best locally, using a limited number of events. Furthermore, it is always a good idea to do it for one simulated sample and one data sample separately,
in case you are working on simulation-specific implementations, for example.

A possible local test command using preselected NanoAOD samples could look like:

```sh
pico.py run -c mutau -y 2018 -s DY
```

Since the already preselected samples for &mu;&tau;<sub>h</sub> are quite small, you do not need to specify the number of events to be processed with `-m`. Furthermore,
for local tests with `pico.py run`, only one input file is user per default. The input file is chosen from the list of files for the Drell-Yan sample, which is chosen via `-s DY`.

A test for a data sample would then look similar:

```sh
pico.py run -c mutau -y 2018 -s SingleMuon
```

Having these commands at hand, test always extensions of the module, and have a look at the local outputs produced as `${CMSSW_BASE}/src/TauFW/PicoProducer/output/pico_*.root` by checking
the quantities stored in these files, and their values. Are these as you have expected?

There are several possibilities to check your local outputs, discussed in the following.

First step could be to check, whether the desired quantity is booked at all as a TLeaf in the TTree `tree`. By now, you should know the appropriate command, since it appeared already twice
in the course of this exercise :) Just scroll up a bit ;).

Next you can check in a very convenient way the values for some of the processed events in the ROOT shell:

```sh
root -l <path-to-pico-output>.root
# in the ROOT shell
root [0]
...
root [1] tree->Scan("m_vis:pt_1:decayMode_2")

```

Furthermore, you can test different cuts:

```sh
root -l <path-to-pico-output>.root
# in the ROOT shell
root [0]
...
root [1] tree->GetEntries("m_vis > 90.0")
...
root [2] tree->GetEntries("pt_1 < 20.0")
```

The best way to check your outputs is of course having a look at the various distributions of the stored quantities. Provided, that you have ROOT installed on the work system at your home institution,
you can copy the output file(s) there and have a look at the file using a graphical interface of ROOT.

First, get the absolute path of the output:

```sh
readlink -f <path-to-pico-output>.root
```

On the work system at your home institution, copy the file from CERN `lxplus` to yourself. The following command should work on unix-based operating systems:

```sh
scp <cern-username>@lxplus.cern.ch:<absolute-path-to-pico-output>.root .
```

Then you can open the file at your home institution and start the TBrowser with a graphical interface:

```sh
root -l  <path-to-pico-output>.root
# in the ROOT shell
root [0]
...
root [1] TBrowser b
```

In the TBrowser, you can relatively fast click through the structure of the opened file to get familiar with it.

You can for example plot the `cutflow` histogram to check, whether the tracked cuts are affecting the event selection. Besides that, you can get the distributions of the quantities stored in `tree`
by (double-)clicking on the corresponding leaves.

Furthermore, if you like to see the values of a quantity in a specified range, then, with the TBrowser still open, use the ROOT shell:

```sh
# in the ROOT shell, with TBrowser open
root [2] tree->Draw("m_vis","m_vis >=70 && m_vis < 110")
```

The plot in the TPad of TBrowser will be updated accordingly.

## Producing flat n-tuples using `lxplus` HTCondor batch system

Sidenote: please also have a look at details on [job submission at `lxplus`](https://batchdocs.web.cern.ch/local/submit.html)

As soon as you are happy with your developments and sure, that there are any bugs after checking your outputs, you are ready to start a large-scale production.

Before doing this, please check, whether the TauFW configuration is fine, using `pico.py list`, in particular the setting for `nfilesperjob`, which will be used during submission to
the batch system, and the samples list to be used. Choosing `nfilesperjob` to be 15 should be fine to stay within 5 minutes, when using the samples already preselected for &mu;&tau;.

Additionally check, whether your VOMS proxy is valid and renew it, if necessary (see section [2](configuration.md) for that).

Now you can use the submit commands familiar from section [3](preselection.md), adapted for the creation of flat n-tuples:

```sh
# Initial submission
pico.py submit -c mutau -y 2018 --queue "espresso" --time 300

# Status check, use repeatedly
pico.py status -c mutau -y 2018

# Resubmission with longer requested processing time
pico.py resubmit -c mutau -y 2018 --queue "espresso" --time 600

# After the jobs are all successfully finished, the job outputs can be put together to one file per sample
pico.py hadd -c mutau -y 2018
```

Since the input NanoAOD samples are already preselected, the `espresso` JobFlavour should be fine for the production of flat n-tuples.

Provided, that you get enough slots, production of n-tuples can be ready within 5 minutes. But submitting to a batch system is
also a bit of gambling, in particular for batch systems with a lot of users, like the one for `lxplus`.

If you have not submitted anything in the last days, you should have a low user priority value (the *lower*, the better). You can check it via:

```sh
condor_userprio | less

# within less tool (replace <cern-username> appropriately with yours)
/<cern-username>
```

In the output of this command, you will be able, how you are ranked, and who exactly is taking away all the slots :).

Small sidenote: to exit `less`, just press `q`.

Because of that, it is good to have a small number of jobs in total, which however stay within the runtime slot you request. Since the `pico.py` commands related to
batch system are wrapper around HTCondor commands, it is also good to know a bit, what is running under the hood. In the following, a few advices to optimize your batch system tasks.

The core shell script passed to HTCondor for execution is [submit_HTCondor.sh](../../PicoProducer/python/batch/submit_HTCondor.sh). You can see it also in the condor configuration file,
which is in case of CERN `lxplus` [submit_HTCondor.sub](../../PicoProducer/python/batch/submit_HTCondor.sub).

Try to get more familiar with that configuration by having a closer look at it. Please also
pay attention, what exactly is done when performing the initial submission. It is not more than passing [submit_HTCondor.sub](../../PicoProducer/python/batch/submit_HTCondor.sub) to the `condor_submit`
command with a bunch of specified options :).

If you would like to see, what is exactly running, you can also check the status without the `pico.py status` wrapper:

```sh
condor_q <cern-username>
```

To have a closer look at one particular job - `<jobid>` format is `$(ClusterId).$(ProcId)` - you can use:

```sh
condor_q <jobid> -l | less
```

A useful trick is also to `grep` through the `*.log` files of finished jobs:

```sh
grep "picojob.py done after" ${CMSSW_BASE}/src/TauFW/PicoProducer/output/2018/mutau/*/*/*.log
```

In that way, you can find out the runtime of the jobs, which produced the flat ntuples for the &mu;&tau;<sub>h</sub> final state. Feel free to adapt the trick to your needs ;).

If you would like to remove a specific job, you can perform:

```sh
condor_q <jobid>
```

You can even remove **all** your submitted job:

```sh
condor_rm <cern-username>
```

Finally, to have a look, why jobs are put on `hold` by the batch system, perform:

`condor_hold <cern-username>`

Usually a more or less understandable reason is given.

## Alternative: parallel processing with a script

After all the tips and tricks mentioned above you should be well prepared for an efficient submission to an HTCondor batch system.

But well, a batch system can have a bad day - or you can have bad luck, depends on the way you view at it :) - such that it is useful to know a few alternatives, which can be
accomplished with minimal effort.

One main requirement for the instructions in the following: you should know an appropriate machine - in other words, similar to `lxplus` - at your home institution with a bunch of CPU cores.
And you should be able to login there and perform calculations.

Trust me, you do **not** want to send 16 or more jobs to a machine with only 5 CPUs. The system administrators will be very angry about it...

At first, copy the already preselected files from CERN Tau POG EOS to your local storage.

The following two commands require a Grid environment and a valid VOMS proxy on the machine at your home institution. To setup a CentOS7 Grid environment, if unavailable, perform:

```sh
source /cvmfs/grid.cern.ch/umd-c7ui-latest/etc/profile.d/setup-c7-ui-example.sh
```
Then, a `gfal-copy` command:

```sh
mkdir -p <local/storage/path/for/the/ntuples>
gfal-copy -r gsiftp://eoscmsftp.cern.ch//eos/cms/store/group/phys_tau/CMSDAS2020/nano <local/storage/path/for/the/ntuples>/nano
```

Alternatively, you can use `xrdcopy`, which may be a bit faster:

```sh
mkdir -p <local/storage/path/for/the/ntuples>
xrdcopy -p -r root://eoscms.cern.ch//store/group/phys_tau/CMSDAS2020/nano <local/storage/path/for/the/ntuples>/
```

If you have your own preselected NanoAOD samples at your EOS user space, the only solution to copy these files from outside CERN is to use an `ssh` connection.
This is the slowest possibility, but does not require a Grid environment, if the source and target locations are accessible at the corresponding machines.

If installed, `rsync` is very useful to copy files, since it checks with appropriate options, whether a file is already copied over successfully, or not:

```sh
mkdir -p <local/storage/path/for/the/ntuples>
rsync -av --progress <cern-username>@lxplus.cern.ch:/eos/user/<first-letter-of-cern-username>/<cern-username>/nano <local/storage/path/for/the/ntuples>/
```

If `rsync` is not installed, you can always fallback to `scp`, although it does not have the same nice features:

```sh
mkdir -p <local/storage/path/for/the/ntuples>
scp -r <cern-username>@lxplus.cern.ch:/eos/user/<first-letter-of-cern-username>/<cern-username>/nano <local/storage/path/for/the/ntuples>/
```

After having copied the files over, you can start with parallel processing on one machine.

Provided that your machine has over 20 CPUs, it is fine to run all 16 samples in parallel. You can check the number of CPUs on the machine via:

```sh
nproc --all
```

In case of more than 20 CPUs, you can simply use a parallelization with a shell command. Before doing that, check **first** the load of the machine, for example via `htop` (if installed), or `top`:

```sh
# if the tool is available:
htop -u <username>

# if not, use
top -u <username>
```

The rule of thumb is, that the load average, devided by the number of CPUs should be significantly smaller than 1. In that case, the machine is free for the use of multiple CPUs :).

After setting up and configuring the TauFW software at your home machine, use the following command for parallel processing, based on a list of name patterns unambigious between each sample:

```
for sample in DY TTTo2L2Nu TTToSemi TTToHad ST_tW_antitop ST_tW_top ST_t-channel_antitop ST_t-channel_top WW WZ ZZ SingleMuon_Run2018A SingleMuon_Run2018B SingleMuon_Run2018C SingleMuon_Run2018D;
do
pico.py run -c mutau -y 2018 -s ${sample} -n 1 &
done; wait
```

Depending on whether the allowed load per user is limited or not, the ntuple production can be ready within 5 to 12 minutes.

Please use the above command with care! It does not have a limitation on spawned processes by itself, such that you could create 100 processes, if you have 100 samples in the list. And that is definetily
not good for a machine with only 20 CPUs...

If you need more control on the number of used CPUs in your parallel processing, a good way is to use the `multiprocessing` library in `python`:

```python
from multiprocessing import Pool
import os

ncpus = 5 # modify as you need it

def execute_cmd(cmd):
    return os.system(cmd)

samplenames = [
    'DY',
    'TTTo2L2Nu','TTToSemi','TTToHad',
    'ST_tW_antitop','ST_tW_top','ST_t-channel_antitop','ST_t-channel_top',
    'WW','WZ','ZZ',
    'SingleMuon_Run2018A','SingleMuon_Run2018B','SingleMuon_Run2018C','SingleMuon_Run2018D'
]

commands = ['pico.py run -c mutau -y 2018 -s {SAMPLE} -n -1'.format(SAMPLE=s) for s in samplenames]

for c in commands:
    print c

p = Pool(ncpus)
p.map(execute_cmd,commands)
```

Write the code snippet to a python script and execute it with `python <script>.py`. This result in the same procedure as the shell command above, but now resticted to 5 jobs running in parallel.

In this form, the python script can be used also on `lxplus` login nodes with 10 CPUs with an expected runtime of about 15 minutes.

In general, the better the connection to storage (e.g. SSDs) and the more CPUs you have, the faster the processing with such scripts.

Now you should have all tools you need to find your own way to have fast turn-around for the production of flat n-tuples. Enjoy, and play around with all the possibilities!
