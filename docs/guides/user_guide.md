# User Guide
To use our existing service, the steps are very simple:

* Signup at [qlued.alqor.io](https://qlued.alqor.io) for an account. At the moment the signup experience is not yet great. We are continously upgrading things and it will become more professional. But the username and token you obtain during signup will work.
* Try out one of [the tutorials](../../notebooks/rydberg_api_showcase_v2) we have provided.

## The quantum frameworks

We have integrated `qlued` with some quantum frameworks. To try it out, just do the following:

* Install  [Qiskit][Qiskit_github] or [Pennylane][Pennylane_github] (depreceated).
* Make yourself familiar with how to write quantum circuits in these frameworks.
* Look at our examples in which we explain circuit implementation of some previous experimental results achieved with cold atoms at Uni-Heidelberg.
    * QisKit examples : [``qiskit-cold-atom``](https://github.com/Qiskit-Extensions/qiskit-cold-atom)
    * Pennylane examples : [``pennylane-ls``](https://github.com/synqs/pennylane-ls)
* Start submitting your jobs. For the moment we only provide simulator backends.

[Qiskit_github]: https://github.com/Qiskit "Qiskit"
[Pennylane_github]: https://github.com/PennyLaneAI "Pennylane"