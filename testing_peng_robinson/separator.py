from pyomo.environ import ConcreteModel, SolverFactory, value
from idaes.core import FlowsheetBlock
from idaes.models.properties.modular_properties.base.generic_property import GenericParameterBlock
from idaes.core.util.model_statistics import degrees_of_freedom
from idaes.models.unit_models import Heater, Separator
from configuration import configuration
from idaes.models.unit_models.separator import SplittingType
 
m = ConcreteModel()
m.fs = FlowsheetBlock(dynamic=False)
m.fs.props = GenericParameterBlock(**configuration)
 
m.fs.sep = Separator(
    property_package=m.fs.props,
    split_basis= SplittingType.phaseFlow,
    num_outlets=2,
)

# Set inlet conditions for the stream
m.fs.sep.inlet.flow_mol.fix(10)  # mol/s
#m.fs.heater.inlet.temperature.fix(283)  # K
m.fs.sep.inlet.enth_mol.fix(747.4)  # J/mol
m.fs.sep.inlet.pressure.fix(100000)  # Pa
m.fs.sep.inlet.mole_frac_comp[0, "water"].fix(1)



print(m.fs.sep.split_fraction.index_set())
print([k for k in m.fs.sep.split_fraction.index_set()])
# Set outlet split fractions
m.fs.sep.split_fraction[0,"outlet_1", "Liq"].fix(0.9)
m.fs.sep.split_fraction[0,"outlet_2", "Vap"].fix(0.1)

print(degrees_of_freedom(m))
 
# Create a solver
solver = SolverFactory('ipopt')
 
# Solve the model
results = solver.solve(m, tee=True)

# Display results
m.fs.sep.report()
 