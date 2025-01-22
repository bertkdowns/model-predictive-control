from pyomo.environ import *
from pyomo.network import *
from pyomo.core.base.var import IndexedVar
from pyomo.network.port import IndexedPort
from idaes.core import FlowsheetBlock




def Bus(num_connections,parent):
    self = Block()
    parent.add_component('bus', self)
    # get kwarg for num_connections

    # create a list of ports
    self.port_set = RangeSet(0, num_connections)
    self.power = Var(self.port_set)
    self.port = Port(self.port_set,initialize=)

    # assert that the power at each port is equal

    self.kirchoff = Constraint(expr = sum(self.port[i].power for i in range(num_connections)) == 0)
    return self


def Generator():
    self = Block()
    self.port = Port()
    self.port.power = Var()
    return self



def Load():
    self = Block()
    self.port = Port()
    self.port.power = Var()
    return self



m = ConcreteModel()
Bus(num_connections=2, parent=m)
m.generator = Generator()
m.demand = Load()

m.arc_1 = Arc(source=m.bus.port[0], destination=m.generator.port)
m.arc_2 = Arc(source=m.bus.port[1], destination=m.demand.port)

TransformationFactory("network.expand_arcs").apply_to(m)
# solve the model
solver = SolverFactory('ipopt')
solver.solve(m)
