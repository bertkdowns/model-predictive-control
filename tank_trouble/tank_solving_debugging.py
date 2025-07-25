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
from idaes.core.util import DiagnosticsToolbox

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
from property_packages.build_package import build_package
from custom_tank import DynamicTank

m = pyo.ConcreteModel(name="Testing Tank model")
m.fs = FlowsheetBlock(
            dynamic=True, time_set=[0,1,2], time_units=pyo.units.s
        )
m.fs.prop_water = build_package("helmholtz",["water"],["Liq","Vap"])

m.fs.tank = DynamicTank(
    tank_type="rectangular_tank", has_holdup=True, property_package=m.fs.prop_water,
    has_heat_transfer=True, dynamic=True
)

m.discretizer = pyo.TransformationFactory("dae.finite_difference")
m.discretizer.apply_to(m, nfe=2, wrt=m.fs.time, scheme="BACKWARD")



m.fs.tank.inlet.flow_mol.fix(200)
m.fs.tank.inlet.pressure.fix(100000)
#m.fs.tank.inlet.enth_mol.fix(3700.36)
m.fs.tank.control_volume.properties_in[0].constrain("temperature",350)
m.fs.tank.control_volume.properties_in[1].constrain("temperature",350)
m.fs.tank.control_volume.properties_in[2].constrain("temperature",350)




m.fs.tank.tank_width.fix(0.4) #m
m.fs.tank.tank_length.fix(0.4)
m.fs.tank.heat_duty.fix(0)  # W

m.fs.tank.tank_level.fix(0.5)

#m.fs.tank.control_volume.material_accumulation[0,:,:].fix(0)
#m.fs.tank.control_volume.energy_accumulation[0,:].fix(0)

@m.fs.tank.Constraint()
def initial_material_accumulation_liq(b):
    return b.control_volume.material_accumulation[0, "Liq", "water"] == 0

@m.fs.tank.Constraint()
def initial_material_accumulation_vap(b):
    return b.control_volume.material_accumulation[0, "Vap", "water"] == 0

@m.fs.tank.Constraint()
def initial_energy_accumulation_liq(b):
    return b.control_volume.energy_accumulation[0, "Liq"] == 0

@m.fs.tank.Constraint()
def initial_energy_accumulation_vap(b):
    return b.control_volume.energy_accumulation[0, "Vap"] == 0

iscale.calculate_scaling_factors(m)

print('DoF:', degrees_of_freedom(m.fs))  
#assert degrees_of_freedom(m.fs) == 0, "Degrees of freedom is not zero, check model setup."

m.fs.tank.initialize()



assert degrees_of_freedom(m.fs) == 0, "Degrees of freedom is not zero, check model setup."

#m.fs.visualize("My Flowsheet", loop_forever = True)


dt = DiagnosticsToolbox(m)
dt.report_structural_issues()



dt.display_overconstrained_set()
dt.display_underconstrained_set()
dt.display_potential_evaluation_errors()


# solver = get_solver()

solver.solve(m, tee=True)

for t in m.fs.time:
    print (m.fs.tank.report(t))
    print(value(m.fs.tank.tank_level[t]))

# #m.fs.visualize("My Flowsheet", loop_forever = True)