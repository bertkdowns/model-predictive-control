import pyomo.environ as pyo
from idaes.core import FlowsheetBlock
from idaes.models.unit_models import Heater
from idaes.models.properties.general_helmholtz import (
    HelmholtzParameterBlock,
    PhaseType,
    StateVars,
)
from idaes.core.util.model_statistics import degrees_of_freedom

m = pyo.ConcreteModel()
m.fs = FlowsheetBlock(dynamic=False)
m.fs.properties = HelmholtzParameterBlock(
    pure_component="h2o",
    phase_presentation=PhaseType.MIX,
    state_vars=StateVars.TPX,
)
m.fs.heater = Heater(property_package=m.fs.properties)

m.fs.heater.inlet.flow_mol[0].fix(100)
m.fs.heater.inlet.temperature[0].fix(380)
m.fs.heater.inlet.vapor_frac[0].fix(1)
m.fs.heater.inlet.pressure[0].fix(101325)
m.fs.heater.heat_duty[0].fix(100_000)

solver = pyo.SolverFactory("ipopt")
solver.solve(m)

print(degrees_of_freedom(m))

print(m.fs.heater.outlet.temperature[0].value)
print(m.fs.heater.outlet.pressure[0].value)
print(m.fs.heater.outlet.vapor_frac[0].value)
print(m.fs.heater.inlet.vapor_frac[0].value)