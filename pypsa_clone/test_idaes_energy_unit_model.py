from pyomo.environ import *
from pyomo.network import *
from pyomo.core.base.var import IndexedVar
from pyomo.network.port import IndexedPort
from idaes.core import FlowsheetBlock
from idaes.core.util.model_statistics import degrees_of_freedom
from idaes_energy_property_package import PowerParameterBlock
from idaes_energy_unit_model import Bus

m = ConcreteModel()
m.fs = FlowsheetBlock(dynamic= False)

m.fs.power_props = PowerParameterBlock()
m.fs.bus = Bus(property_package = m.fs.power_props)

m.fs.bus.inlet.power.fix(100)

m.fs.bus.pprint()