### Imports
from pyomo.environ import ConcreteModel, SolverFactory, SolverStatus, TerminationCondition, Block, TransformationFactory, value, Constraint
from pyomo.network import SequentialDecomposition, Port, Arc
from pyomo.core.base.units_container import _PyomoUnit, units as pyomo_units
from idaes.core import FlowsheetBlock
from idaes.core.util.model_statistics import report_statistics, degrees_of_freedom
import idaes.logger as idaeslog
from property_packages.build_package import build_package
from idaes.models.unit_models.heater import Heater


### Utility Methods
def units(item: str) -> _PyomoUnit:
    ureg = pyomo_units._pint_registry
    pint_unit = getattr(ureg, item)
    return _PyomoUnit(pint_unit, ureg)

def init_unit(unit: Block) -> None:
    unit.initialize(outlvl=idaeslog.INFO)


### Build Model
m = ConcreteModel()
m.fs = FlowsheetBlock(dynamic=False)

# Set up property packages
m.fs.PP_0 = build_package(
    "helmholtz",
    ["water"],
)

# Create unit models
T = 400 * units("K")
T2 = 450 * units("K")
# Heater2
m.fs.Heater2 = Heater(
    property_package=m.fs.PP_0,
    has_pressure_change=False
)
#m.fs.Heater2.deltaP.fix(-1e-06 * units("kPa"))
m.fs.Heater2.inlet.flow_mol.fix(1.0 * units("mol/s"))
m.fs.Heater2.inlet.pressure.fix(10000.0 * units("Pa"))
m.fs.Heater2.inlet.enth_mol.fix(2500)
#m.fs.Heater2.outlet.enth_mol.fix(3100)
#m.fs.Heater2.outlet.enth_mol.fix(m.fs.PP_0.htpx(p=m.fs.Heater2.outlet.pressure[0], T=T))
m.fs.enth = Constraint(expr=m.fs.Heater2.outlet.enth_mol[0] == m.fs.PP_0.htpx(p=m.fs.Heater2.inlet.pressure[0], T=T))
print(value(m.fs.Heater2.outlet.pressure[0]))
print(m.fs.PP_0.htpx(p=m.fs.Heater2.outlet.pressure[0], T=T))

# Heater32
m.fs.Heater32 = Heater(
    property_package=m.fs.PP_0,
    has_pressure_change= False
)
#m.fs.Heater32.deltaP.fix(-1e-06 * units("kPa"))
#m.fs.Heater32.inlet.enth_mol.fix(3500)
#m.fs.Heater32.outlet.enth_mol.fix(3200)
m.fs.Heater32.outlet.enth_mol.fix(m.fs.PP_0.htpx(p=m.fs.Heater32.inlet.pressure[0], T=T2))


## Connect Unit Models
m.fs.arc_1 = Arc(source=m.fs.Heater2.outlet, destination=m.fs.Heater32.inlet)


### Check Model Status
report_statistics(m)



### Initialize Model
TransformationFactory("network.expand_arcs").apply_to(m)
print("Degrees of freedom:", degrees_of_freedom(m))
seq = SequentialDecomposition()
seq.set_tear_set([])
seq.run(m, init_unit)


### Solve
solver = SolverFactory("ipopt")
result = solver.solve(m, tee=True)
# check for optimal solution
if result.solver.status != SolverStatus.ok or result.solver.termination_condition != TerminationCondition.optimal:
    raise Exception("Solver did not converge to an optimal solution")

#result = solver.solve(m, tee=True)
### Report
m.fs.Heater2.report()
m.fs.Heater32.report()
result = solver.solve(m, tee=True)
m.fs.Heater2.report()
m.fs.Heater32.report()