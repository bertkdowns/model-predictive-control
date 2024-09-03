from pyomo.environ import ConcreteModel, SolverFactory, value
from idaes.core import FlowsheetBlock
from idaes.models.properties.modular_properties.base.generic_property import GenericParameterBlock
from idaes.core.util.model_statistics import degrees_of_freedom
from idaes.models.unit_models import Heater
from configuration import configuration
 
 
m = ConcreteModel()
m.fs = FlowsheetBlock(dynamic=False)
m.fs.props = GenericParameterBlock(**configuration)
 
# Add a Heater unit to the flowsheet
m.fs.state = m.fs.props.build_state_block([0],defined_state=True)
 
# Set inlet conditions for the stream
m.fs.state[0].flow_mol.fix(10)  # mol/s
m.fs.state[0].enth_mol.fix(-241800)  # J/mol
#m.fs.state[0].enth_mol.unfix()
#m.fs.state[0].temperature.fix(300)
m.fs.state[0].pressure.fix(100000)  # Pa
m.fs.state[0].mole_frac_comp["water"].fix(1)
 
 
# Create a solver
solver = SolverFactory('ipopt')
 
# Solve the model
results = solver.solve(m, tee=True)
 
# Display results
print("\n*** Results ***")
print("Inlet enth_mol (J/mol):", value(m.fs.state[0].enth_mol))
print("Inlet Temperature (K):", value(m.fs.state[0].temperature))

dof = degrees_of_freedom(m)
print("degrees of freedom: ",dof)