# Model Predictive Control, Idaes Dynamic Simulation, and Surrogate Modelling

This repository contains some scripts and test examples for creating a surrogate model, dynamic simulation,
or model predictive control simulation in IDAES.

So far, I have concluded:

- There are no issues with doing surrogate modelling, we can follow the IDAES docs. However, we will need to make a custom unit op to support it

Next Steps:

- We need to figure out how to use live data in a dynamic simulation. Idaes does seem to have some things for data reconcilliation that we can use.
- We need to figure out how to put this in the platform This involves storing a time series of values.
