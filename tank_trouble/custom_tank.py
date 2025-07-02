from idaes.core import declare_process_block_class
from idaes.models_extra.power_generation.unit_models.watertank import WaterTankData
from add_initial_dynamics import add_initial_dynamics
from pyomo.environ import Reference, Var, units

@declare_process_block_class("DynamicTank")
class DynamicTankData(WaterTankData):
    """
    Dynamic Heater unit model class.
    This extends the Heater class to include reference variables for initial holdup and initial accumulation. 
    Which makes it easier for us to set initial conditions in the frontend.
    """

    def build(self,*args, **kwargs):
        """
        Build method for the DynamicHeaterData class.
        This method initializes the control volume and sets up the model.
        """
        super().build(*args, **kwargs)

        add_initial_dynamics(self)

        self.initial_tank_level = Var(initialize=0.5, doc="Initial tank level")
        self.tank_level[:].fix(0.5)
        self.tank_level.unfix()
        @self.Constraint(
            doc="Initial level constraint"
        )
        def initial_level_constraint(b):
            return b.initial_tank_level == b.tank_level[0]