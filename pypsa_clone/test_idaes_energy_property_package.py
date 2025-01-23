from pyomo.environ import *
from pyomo.network import *
from pyomo.core.base.var import IndexedVar
from pyomo.network.port import IndexedPort
from idaes.core import FlowsheetBlock
from idaes.core.util.model_statistics import degrees_of_freedom
from idaes_energy_property_package import PowerParameterBlock

m = ConcreteModel()
m.fs = FlowsheetBlock(dynamic= False)

m.fs.power_props = PowerParameterBlock()
m.fs.ps = m.fs.power_props.build_state_block([0])

m.fs.ps[0].power.fix(100)

m.fs.pprint()