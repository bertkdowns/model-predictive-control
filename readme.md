# Model Predictive Control, Idaes Dynamic Simulation, and Surrogate Modelling

This repository contains some scripts and test examples for creating a surrogate model, dynamic simulation,
or model predictive control simulation in IDAES.

So far, I have concluded:

- There are no issues with doing surrogate modelling, we can follow the IDAES docs. However, we will need to make a custom unit op to support it
- Model predictive control is pretty simple, however that's the point where you need live data. Caprese only simulates it, we might need something else to work with live data (maybe pyomo MPC).


Next Steps:

- We need to figure out how to use live data in a dynamic simulation. Idaes does seem to have some things for data reconcilliation that we can use.
- We need to figure out how to put this in the platform This involves storing a time series of values for each property. We also have to be able to specify which timesteps are fixed and which are not (usually initial conditions are fixed and the others arent for example)
- Surrogate Modelling: This is a seperate project, but could involve: creating a data structure and apis for training models. The models will need to be stored somewhere, so they can be used by idaes. A UI and backend for specifying which model to use, which things are custom properties, which material balances or manual constraints are used, etc all would need to be specified. The methods to pass objects to IDAES would need to be updated to support all this configuration.


Architecture thoughts:

- I'm thinking it's gonna be easiest to keep ahuora stateless for as long as possible, and use integrations with databases (e.g influxdb) and dataprocessing platforms (e.g apache kafa/storm) to handle the "state" and "realtime" aspects. Ahuora can focus on what it does best, providing an easy interface to these tools, specifically modelling tools such as idaes. 

If possible, UIs for integrating with kafka/influx/storm etc can be made to show realtime data in a dashboard, which could lead to control stuff. Alternatively, this could be developed as a seperate product.

The basic update to the ahuora platforms required would then be:
- Dynamic simulation (for model predictive control, and predicting ahead)
- Some way of specifying that "this field will be filled with live data". 

- Additional API endpoints for solving, that a data processing platform can use to pass the required live data and get back a solved model. (or, a way of compiling an idaes script to do the same thing so it can be run and scaled by a data processing platform). Could also try using G-RPC or something for that.

The biggest obstacle to implementing dynamics in ahuora is that we have to store a bunch of values for a timestamp, rather than a single timestep. Fortunately, there is an array type in Django. However, we will also have to specify the indexes for the array type, because in IDAES the timestep units may not always be equal. We also might have to index by things other than time at some point, especially for DAE components

