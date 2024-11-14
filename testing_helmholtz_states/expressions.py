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
 
m.fs.state_block = m.fs.properties.build_state_block([0], defined_state=True)
m.fs.state_block[0].flow_mol.fix(1 * units("mol/s"))
m.fs.state_block[0].pressure.fix(101325.0 * units("Pa"))

m.fs.state_block[0].enth_mol.fix(m.fs.properties.htpx(p=m.fs.state_block[0].pressure, T = 373.15 * units("K")))
# add vapor fraction constraint
#m.fs.constraint1 = Constraint(expr=m.fs.state_block[0].vapor_frac == 0.5)
# add temperature constraint
# m.fs.constraint2 = Constraint(expr=m.fs.state_block[0].temperature == 373.15)  # K
 
# flow_mol, pressure, enth_mol: working
# flow_mol, pressure, vapor_frac: appears to be working, is enthalpy valid?
# flow_mol, temperature, vapor_frac: not working
 
 
 
### Initialize Model
m.fs.state_block.initialize(outlvl=idaeslog.INFO)
 
# add a dummy objective (for some reason, doesn't run a solve when you use the exact state variables molar_flow, pressure, enthalpy - thinks there are no variables to solve for)
m._dummy_var = Var(bounds=(0, 1))
m._dummy_obj = Objective(expr=m._dummy_var)
 
### Solve
solver = SolverFactory("ipopt")
result = solver.solve(m, tee=True)
# check for optimal solution
if result.solver.status != SolverStatus.ok or result.solver.termination_condition != TerminationCondition.optimal:
    raise Exception("Solver did not converge to an optimal solution")
 
 
### Report
print("flow_mol:", value(m.fs.state_block[0].flow_mol))
print("pressure:", value(m.fs.state_block[0].pressure))
print("enth_mol:", value(m.fs.state_block[0].enth_mol))
print("temperature:", value(m.fs.state_block[0].temperature))
print("vapor_frac:", value(m.fs.state_block[0].vapor_frac))