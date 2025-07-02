#Courtesy of Ben Lincoln

# Import Pyomo libraries
from pyomo.environ import (
    Constraint,
    Var,
    ConcreteModel,
    Expression,
    Objective,
    TransformationFactory,
    value,
    SolverFactory
)

import pyomo.environ as pyo
from pyomo.network import Arc

from idaes.core import FlowsheetBlock
from idaes.models_extra.power_generation.unit_models.watertank import WaterTank
from idaes.models.control.controller import PIDController, ControllerType
import idaes.core.util.scaling as iscale
from idaes.models.unit_models import Heater, Separator as Splitter,Mixer, HeatExchanger,Pump
from idaes.models.unit_models.separator import SplittingType
from idaes.models_extra.power_generation.unit_models.helm import (
    HelmValve as WaterValve,
    HelmIsentropicCompressor as WaterPump,
)
from idaes.core.util.model_statistics import degrees_of_freedom
from idaes.models.properties import iapws95
from idaes.core.util.dyn_utils import copy_values_at_time, copy_non_time_indexed_values
from idaes.core.solvers import get_solver
from idaes.models.properties.general_helmholtz import helmholtz_available
from matplotlib import pyplot as plt
import math
import CoolProp.CoolProp as CoolProp  


m = pyo.ConcreteModel(name="Testing Tank model")
m.fs = FlowsheetBlock(
            dynamic=True, time_set=[0], time_units=pyo.units.s
        )
m.fs.prop_water = iapws95.Iapws95ParameterBlock()


m.fs.tank = WaterTank(
    tank_type="rectangular_tank", has_holdup=True, property_package=m.fs.prop_water
)

m.discretizer = pyo.TransformationFactory("dae.finite_difference")
m.discretizer.apply_to(m, nfe=3, wrt=m.fs.time, scheme="BACKWARD")



m.fs.tank.inlet.flow_mol.fix(200)
m.fs.tank.inlet.pressure.fix(100000)
m.fs.tank.inlet.enth_mol.fix(3700.36)

m.fs.tank.tank_width.fix(0.4) #m
m.fs.tank.tank_length.fix(0.4)


m.fs.tank.set_initial_condition()

# set initial tank level
m.fs.tank.tank_level.unfix()
m.fs.tank.tank_level[0].fix(0.5)

# set tank outlet flow after that.
m.fs.tank.outlet.flow_mol[:].fix(1)
m.fs.tank.outlet.flow_mol[0].unfix()

iscale.calculate_scaling_factors(m)

print('DoF:', degrees_of_freedom(m.fs))  
assert degrees_of_freedom(m.fs) == 0, "Degrees of freedom is not zero, check model setup."

m.fs.tank.initialize()

assert degrees_of_freedom(m.fs) == 0, "Degrees of freedom is not zero, check model setup."

#m.fs.visualize("My Flowsheet", loop_forever = True)

solver = get_solver()

solver.solve(m, tee=True)

for t in m.fs.time:
    print (m.fs.tank.report(t))
    print(value(m.fs.tank.tank_level[t]))

#m.fs.visualize("My Flowsheet", loop_forever = True)