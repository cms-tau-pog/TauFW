# 7. Energy scale of &tau;<sub>h</sub> candidates

As an example of systematic effects, which can also change the shape of an event distribution of a process, we will consider the energy scale
correction for genuine &tau;<sub>h</sub> candidates.

Usually there are two effects on energy, for which corrections are considered in analyses:

* A change in energy scale, best visible on the example of a resonance mass peak shifted to lower or higher values of energy.
* A change in energy resolution, best visibly on the example of a resonance mass peak, which is made broader or narrower.

We will consider the first effect in the context of the exercise.

However, both of these effects can in principle be applied as event-by-event scale factors of the 4-momentum of the &tau;<sub>h</sub> candidate in question:

p<sub>&mu;</sub><sup>corrected</sup>(&tau;<sub>h</sub>) = SF &middot; p<sub>&mu;</sub>(&tau;<sub>h</sub>)

## Quantities affected by energy scale corrections

Let us first look, which quantities apart from the 4-momentum p<sub>&mu;</sub>(&tau;<sub>h</sub>) are affected by an energy scale correction.

Obviously, each quantity, which is using the 4-momentum of the &tau;<sub>h</sub> candidate, p<sub>&mu;</sub>(&tau;<sub>h</sub>), as input, should be recomputed. The simplest
technical way to update these quantities is to overwrite the 4-momentum of the existing &tau;<sub>h</sub> candidate, such that the corrected values go into the computation of
related quantities. Otherwise, you would need to do the correction for each quantity by hand.

In case you will go for the latter way, we should consider which quantities are affected by an energy shift.

* Are the angular quantities like &phi; and &eta; of p<sub>&mu;</sub>(&tau;<sub>h</sub>) changed?
* What about the angular distance &Delta;R between the muon and the &tau;<sub>h</sub> candidate of the &mu;&tau;<sub>h</sub> pair?
* What is the effect on the transverse momentum p<sub>T</sub>(&tau;<sub>h</sub>), the energy E(&tau;<sub>h</sub>) and the mass m(&tau;<sub>h</sub>)?
* How are the transverse momentum and the invariant mass of the &mu;&tau;<sub>h</sub> pair, p<sub>T</sub><sup>vis</sup> and m<sub>vis</sub>, affected?

Feel free to think about these questions, and also other quantities, with help of pen and paper, if needed. You will hopefully see,
that a change of p<sub>&mu;</sub>(&tau;<sub>h</sub>) itself before any computation would be the most elegant solution.

Another point, that should be taken into account are selection steps, which might be affected by a change of the 4-momentum of the &tau;<sub>h</sub> candidate. For example,
if it is shifted, then also p<sub>T</sub>(&tau;<sub>h</sub>) will change, such that a requirement on that quantity would have a different effect. Therefore, it is important
to apply energy corrections before any selection requirement on related quantities.

The last point to be taken into account is the consistency of the global event description. To ensure this,
you would need to propagate the change in the p<sub>T</sub>(&tau;<sub>h</sub>) vector also to the MET vector. Consequently, all quantities related to the MET vector should
also be recomputed with the changes. Please think in particular about the following quantities explicitly:

* How should the MET vector be recomputed?
* What is the impact on the transverse mass of the system of muon and MET vector?
* Is the best estimate for the transverse momentum of the &tau;&tau; pair (so including neutrinos), p<sub>T</sub>(&tau;&tau;), affected?

Also in this case, a change of the MET vector itself before any computation of related quantities would be the most elegant solution.

## Which &tau;<sub>h</sub> candidates should be corrected?

