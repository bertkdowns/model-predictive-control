from pyomo.environ import *
from pyomo.network import *
from pyomo.core.base.var import IndexedVar
from pyomo.network.port import IndexedPort
from idaes.core import FlowsheetBlock
from idaes.core.util.model_statistics import degrees_of_freedom



def Bus(num_connections,parent,name):
    self = Block()
    parent.add_component(name, self)
    # get kwarg for num_connections

    # create a list of ports
    self.port_set = RangeSet(1, num_connections)
    self.power = Var(self.port_set)

    for i in self.port_set:
        port = Port()
        port.add(self.power[i],"power")
        port_name = "port_"+str(i)
        self.add_component(port_name, port)

    # assert that the power at each port is equal

    self.kirchoff = Constraint(expr = sum(getattr(self,"port_" + str(i)).power for i in self.port_set) == 0)
    return self


def Generator(parent,name):
    self = Block()
    parent.add_component(name, self)

    self.port = Port()
    self.power = Var()
    self.port.add(self.power)
    return self



def Load(parent, name):
    self = Block()
    parent.add_component(name, self)
    self.port = Port()
    self.power = Var()
    self.port.add(self.power)
    return self



m = ConcreteModel()
Bus(num_connections=2, parent=m,name="bus")
Generator(m, "generator")
Load(m, "demand")

m.pprint()

m.generator.port.power.fix(100)

m.arc_1 = Arc(source=m.bus.port_1, destination=m.generator.port)
m.arc_2 = Arc(source=m.bus.port_2, destination=m.demand.port)

TransformationFactory("network.expand_arcs").apply_to(m)
# solve the model
solver = SolverFactory('ipopt')
solver.solve(m)

print(degrees_of_freedom(m))
print("power at load:", value(m.demand.port.power))
