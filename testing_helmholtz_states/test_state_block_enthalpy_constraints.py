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
pressure = 1 * units("atm")
temperature = 383.15 * units("K")

m.fs.sb1 = m.fs.properties.build_state_block([0], defined_state=True)
m.fs.sb2 = m.fs.properties.build_state_block([0], defined_state=True)

m.fs.pressure_constraint = Constraint(expr=m.fs.sb1[0].pressure == m.fs.sb2[0].pressure + (m.fs.sb1[0].enth_mol-m.fs.sb2[0].enth_mol) * 0.00001)
m.fs.flow_constraint = Constraint(expr=m.fs.sb1[0].flow_mol == m.fs.sb2[0].flow_mol)
m.fs.error = Var()
#m.fs.temperature_constraint = Constraint(expr=m.fs.sb1[0].temperature == m.fs.sb2[0].temperature + m.fs.error)
m.fs.enthalpy_constraint = Constraint(expr=m.fs.sb1[0].enth_mol == m.fs.sb2[0].enth_mol + m.fs.error)


# Set flow, pressure, temperature
m.fs.sb1[0].flow_mol.fix(1 * units("mol/s"))
m.fs.sb2[0].pressure.fix(pressure)
m.fs.temperature = Constraint(expr=m.fs.sb1[0].temperature == temperature)

m.fs.objective = Objective(expr=m.fs.error**2)
# m.fs.sb1[0].enth_mol.fix(40000 * units("J/mol"))
# add vapor fraction constraint
# m.fs.constraint1 = Constraint(expr=m.fs.sb1[0].vapor_frac == 0.5)
# add temperature constraint
# m.fs.constraint2 = Constraint(expr=m.fs.sb1[0].temperature == 373.15)  # K
 
# flow_mol, pressure, enth_mol: working
# flow_mol, pressure, vapor_frac: appears to be working, is enthalpy valid?
# flow_mol, temperature, vapor_frac: not working
 
print("degrees of freedom", degrees_of_freedom(m))
 
### Solve
solver = SolverFactory("ipopt")
result = solver.solve(m, tee=True)

### Report
print("flow_mol:", value(m.fs.sb1[0].flow_mol))
print("pressure:", value(m.fs.sb1[0].pressure))
print("enth_mol:", value(m.fs.sb1[0].enth_mol))
print("temperature:", value(m.fs.sb1[0].temperature))
print("vapor_frac:", value(m.fs.sb1[0].vapor_frac))

# check for optimal solution
if result.solver.status != SolverStatus.ok or result.solver.termination_condition != TerminationCondition.optimal:
    raise Exception("Solver did not converge to an optimal solution")
 
 
