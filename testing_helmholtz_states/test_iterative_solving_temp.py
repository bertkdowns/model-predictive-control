### Imports
from pyomo.environ import ConcreteModel, SolverFactory, SolverStatus, TerminationCondition, Block, TransformationFactory
from pyomo.network import SequentialDecomposition, Port, Arc
from pyomo.core.base.units_container import _PyomoUnit, units as pyomo_units
from idaes.core import FlowsheetBlock
from idaes.core.util.model_statistics import report_statistics, degrees_of_freedom
import idaes.logger as idaeslog
from property_packages.build_package import build_package
from idaes.models.unit_models.pressure_changer import Compressor
from idaes.models.properties.general_helmholtz import HelmholtzParameterBlock, PhaseType, StateVars, AmountBasis
from pyomo.environ import Var, Objective, value, Constraint

# This works well, by skewing the pressure based on the enthalpy of the stream
# enabling the model to solve even across the phase boundary.
# By iteratively re-solving the model, the effects of skewing the pressure are reduced. 
# This works!

### Utility Methods
def units(item: str) -> _PyomoUnit:
    ureg = pyomo_units._pint_registry
    pint_unit = getattr(ureg, item)
    return _PyomoUnit(pint_unit, ureg)
 
 
### Build Model
m = ConcreteModel()
m.fs = FlowsheetBlock(dynamic=False)
 
# Set up property packages
m.fs.properties = HelmholtzParameterBlock(
    pure_component="h2o",
    phase_presentation=PhaseType.MIX,
    amount_basis=AmountBasis.MOLE,
    state_vars=StateVars.PH,
)
pressure = 1 * units("atm")
temperature = 283.15 * units("K")

bias = 0




m.fs.sb1 = m.fs.properties.build_state_block([0], defined_state=True)


m.fs.bias = Var(initialize=0)
m.fs.scale = Var(initialize=0.001)
m.fs.pressure_constraint = Constraint(expr=m.fs.sb1[0].pressure == 101325 + (m.fs.sb1[0].enth_mol-m.fs.bias) * -m.fs.scale)
m.fs.sb1[0].flow_mol.fix(1 * units("mol/s"))
m.fs.temperature = Constraint(expr=m.fs.sb1[0].temperature == temperature)

print("degrees of freedom should be 2:", degrees_of_freedom(m))
solver = SolverFactory("ipopt")

m.fs.sb1[0].enth_mol.fix(60000)
m.fs.sb1[0].enth_mol.unfix()
guess = 0
for i in range (1, 10):
    m.fs.bias.fix(guess)
    m.fs.scale.fix(-0.001* i *10)
    
    result = solver.solve(m)
    
    if result.solver.status != SolverStatus.ok or result.solver.termination_condition != TerminationCondition.optimal:
        raise Exception("Solver did not converge to an optimal solution")
    
    new_enth_mol = m.fs.sb1[0].enth_mol.value
    guess = new_enth_mol
    print("new_enth_mol:", new_enth_mol)
    
    

 
print("degrees of freedom", degrees_of_freedom(m))
 
### Solve


### Report
print("flow_mol:", value(m.fs.sb1[0].flow_mol))
print("pressure:", value(m.fs.sb1[0].pressure))
print("enth_mol:", value(m.fs.sb1[0].enth_mol))
print("temperature:", value(m.fs.sb1[0].temperature))
print("vapor_frac:", value(m.fs.sb1[0].vapor_frac))

# check for optimal solution

 
 
