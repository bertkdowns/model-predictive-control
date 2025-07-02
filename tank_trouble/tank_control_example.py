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



def set_scaling_factors(m):
    """Set scaling factors for variables and expressions. These are used for
    variable scaling and used by the framework to scale constraints.

    Args:
        m: plant model to set scaling factors for.

    Returns:
        None
    """


m = pyo.ConcreteModel(name="Testing PID controller model")
m.fs = FlowsheetBlock(
            dynamic=True, time_set=[0], time_units=pyo.units.s
        )
m.fs.prop_water = iapws95.Iapws95ParameterBlock()


#heater

m.fs.tee = Splitter(
    property_package=m.fs.prop_water, outlet_list=["cooler", "bypass"],dynamic = False, split_basis = SplittingType.totalFlow)


m.fs.valve = WaterValve(
    dynamic=False, has_holdup=False, phase="Liq", property_package=m.fs.prop_water
)
m.fs.valvepipe = WaterValve(
    dynamic=False, has_holdup=False, phase="Liq", property_package=m.fs.prop_water
)
# m.fs.valvetank = WaterValve(
#     dynamic=False, has_holdup=False, phase="Liq", property_package=m.fs.prop_water
# )

m.fs.cooler = HeatExchanger(dynamic = False,
    hot_side_name="shell",
    cold_side_name="tube",
    shell={"property_package": m.fs.prop_water},
    tube={"property_package": m.fs.prop_water}
)
m.fs.mix = Mixer(property_package=m.fs.prop_water,inlet_list=["cooler_out","bypass_out"],dynamic = False)
m.fs.tank = WaterTank(
    tank_type="vertical_cylindrical_tank", has_holdup=True, property_package=m.fs.prop_water
)

# water pump
m.fs.pump = Pump(dynamic=False, property_package=m.fs.prop_water)

m.discretizer = pyo.TransformationFactory("dae.finite_difference")
m.discretizer.apply_to(m, nfe=3, wrt=m.fs.time, scheme="BACKWARD")
# m.fs.controller = PIDController(
#         process_var=m.fs.tank.tank_level,
#         manipulated_var=m.fs.valve.valve_opening,
#         controller_type=ControllerType.PI,)

m.fs.split_valve = Arc(source=m.fs.tee.cooler, destination=m.fs.valve.inlet)
m.fs.split_pipe = Arc(source=m.fs.tee.bypass, destination=m.fs.valvepipe.inlet)
m.fs.valve_hx = Arc(source=m.fs.valve.outlet, destination=m.fs.cooler.shell_inlet)
m.fs.pipe_mixer = Arc(source=m.fs.valvepipe.outlet, destination=m.fs.mix.bypass_out)
m.fs.HX_mix = Arc(source=m.fs.cooler.shell_outlet, destination=m.fs.mix.cooler_out)
m.fs.mix_tank = Arc(source=m.fs.mix.outlet, destination=m.fs.tank.inlet)
m.fs.tank_pump = Arc(source=m.fs.tank.outlet, destination=m.fs.pump.inlet)
# m.fs.pump_pipe = Arc(source=m.fs.pump.outlet, destination=m.fs.valvetank.inlet)

TransformationFactory("network.expand_arcs").apply_to(m)

#m.fs.visualize("My Flowsheet", loop_forever = True)
pin = 200000 # Pa
pout = 100000 # Pa


m.fs.valvepipe.Cv.fix(100/math.sqrt(pin - pout)/0.5)
m.fs.valvepipe.outlet.pressure[:].fix(pout)
m.fs.valvepipe.valve_opening[:].fix(0.5)

m.fs.valve.Cv.fix(100/math.sqrt(pin - pout)/0.5)
m.fs.valve.outlet.pressure[:].fix(pout)
m.fs.valve.valve_opening[:].fix(0.5)


m.fs.tee.inlet.flow_mol[:].fix(270)
m.fs.tee.inlet.flow_mol[:].unfix()
m.fs.tee.inlet.pressure[:].fix(2*100*1000)
m.fs.tee.inlet.enth_mol[:].fix(CoolProp.PropsSI('HMOLAR', 'T', 70+273.15, "P", 3*100*1000, "Water"))

m.fs.cooler.area.fix(1)
m.fs.cooler.overall_heat_transfer_coefficient[:].fix(14.6*1000)
m.fs.cooler.tube_inlet.pressure[:].fix(1*100*1000)
m.fs.cooler.tube_inlet.flow_mol[:].fix(1000)
m.fs.cooler.tube_inlet.enth_mol[:].fix(CoolProp.PropsSI('HMOLAR', 'T', 20+273.15, "P", 1*100*1000, "Water"))

m.fs.tank.tank_diameter.fix(0.4) #m
m.fs.tank.tank_level[:].fix(0.5)
m.fs.tank.outlet.flow_mol[:].fix(1)
m.fs.tank.set_initial_condition()
m.fs.tank.tank_level.unfix()
m.fs.tank.tank_level[0].fix()

#m.fs.tank.outlet.flow_mol[:].unfix()
m.fs.tank.outlet.flow_mol[0].unfix()

m.fs.pump.deltaP.fix(100000)
m.fs.pump.efficiency_pump.fix(0.8)



# m.fs.valvetank.Cv.fix(0.2)
# m.fs.valvetank.outlet.pressure[:].fix(pin)
# m.fs.valvetank.valve_opening[:].fix(1)
# m.fs.valvetank.valve_opening[0].unfix()



# m.fs.valve.Cv.fix(100/math.sqrt(1000001 - pout)/0.5)
# m.fs.valve.outlet.pressure[:].fix(pout)
# m.fs.valve.valve_opening[:].fix(0.5)


iscale.calculate_scaling_factors(m)
#m.fs.valve.valve_opening.unfix()

print('DoF:', degrees_of_freedom(m.fs))  

m.fs.tee.initialize()
m.fs.valve.initialize()
m.fs.valvepipe.initialize()
m.fs.cooler.initialize()
m.fs.tank.initialize()
m.fs.pump.initialize()
    
#m.fs.visualize("My Flowsheet", loop_forever = True)

solver = get_solver()

solver.solve(m, tee=True)

for t in m.fs.time:
    print (m.fs.tank.report(t))
    print(value(m.fs.tank.tank_level[t]))
    #m.fs.cooler.report(t)
    m.fs.pump.report(t)

#m.fs.visualize("My Flowsheet", loop_forever = True)