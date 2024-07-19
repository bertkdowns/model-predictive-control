from pyomo.environ import ConcreteModel, SolverFactory, value
from idaes.core import FlowsheetBlock
from idaes.models.properties.modular_properties.base.generic_property import GenericParameterBlock
from idaes.models.unit_models import Heater
from configuration import configuration
 
 
m = ConcreteModel()
m.fs = FlowsheetBlock(dynamic=False)
m.fs.props = GenericParameterBlock(**configuration)
 
# Add a Heater unit to the flowsheet
m.fs.heater = Heater(property_package=m.fs.props)
 
# Set inlet conditions for the stream
m.fs.heater.inlet.flow_mol.fix(10)  # mol/s
m.fs.heater.inlet.temperature.fix(283)  # K
m.fs.heater.inlet.pressure.fix(100000)  # Pa
m.fs.heater.inlet.mole_frac_comp[0, "benzene"].fix(0.5)
m.fs.heater.inlet.mole_frac_comp[0, "toluene"].fix(0.5)
 
# Set the outlet temperature
m.fs.heater.outlet.temperature[0].fix(284)  # K
 
# Define the energy balance (heater duty)
# For some reason, even though this heat duty if calculated by the model,
# the model does not converge if the heat duty is fixed instead of outlet temperature.
#m.fs.heater.heat_duty.fix(1258.86)
 
# Create a solver
solver = SolverFactory('ipopt')
 
# Solve the model
results = solver.solve(m, tee=True)
 
# Display results
print("\n*** Results ***")
print("Inlet Temperature (K):", value(m.fs.heater.inlet.temperature[0]))
print("Outlet Temperature (K):", value(m.fs.heater.outlet.temperature[0]))
print("Heater Duty (J/s):", value(m.fs.heater.heat_duty[0]))
 