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
m.fs.sb = m.fs.props.build_state_block([0], defined_state=True)
 
sb = m.fs.sb[0]
# Set inlet conditions for the stream
sb.flow_mol.fix(10)  # mol/s
sb.pressure.fix(100000)  # Pa
sb.enth_mol.fix(747.4)  # J/mol
# sb.mole_frac_comp["water"].fix(1)
# sb.flow_mol_phase["Liq"].fix(1)
 

solver = SolverFactory('ipopt')
 

dof = degrees_of_freedom(m)
print("degrees of freedom: ",dof)
# Solve the model
results = solver.solve(m, tee=True)


dof = degrees_of_freedom(m)
print("degrees of freedom: ",dof)
print("flow_mol:", value(sb.flow_mol))
print("pressure:", value(sb.pressure))
print("enth_mol:", value(sb.enth_mol))