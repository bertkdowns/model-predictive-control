import pyomo.environ as pyo
from idaes.core import FlowsheetBlock
from idaes.models.unit_models import Heater
from idaes.models.properties.general_helmholtz import (
    HelmholtzParameterBlock,
    PhaseType,
    StateVars,
)
from idaes.core.util.model_statistics import degrees_of_freedom
from data import temperature, pressure, power, indexes

m = pyo.ConcreteModel()
m.fs = FlowsheetBlock(dynamic=False,time_set=indexes)
m.fs.properties = HelmholtzParameterBlock(
    pure_component="h2o",
    phase_presentation=PhaseType.MIX,
    state_vars=StateVars.TPX,
)
m.fs.heater = Heater(property_package=m.fs.properties)


for i in indexes:
    m.fs.heater.inlet.flow_mol[i].fix(100)
    m.fs.heater.inlet.temperature[i].fix(temperature[i])
    m.fs.heater.inlet.vapor_frac[i].fix(1)
    m.fs.heater.inlet.pressure[i].fix(pressure[i])
    m.fs.heater.heat_duty[i].fix(power[i])

solver = pyo.SolverFactory("ipopt")
solver.solve(m)


outlet_temperatures = [m.fs.heater.outlet.temperature[i].value for i in indexes]


