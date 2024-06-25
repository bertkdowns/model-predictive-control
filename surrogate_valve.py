# Methods and helper functions to train and use a surrogate valve.
import pyomo.environ as pyo
from idaes.core import FlowsheetBlock, MaterialBalanceType, ControlVolume0DBlock, declare_process_block_class, EnergyBalanceType, MomentumBalanceType, MaterialBalanceType, useDefault, UnitModelBlockData
from idaes.models.unit_models import Valve
from pyomo.common.config import ConfigBlock, ConfigValue, In
from idaes.core.surrogate.surrogate_block import SurrogateBlock
from idaes.core.util.config import is_physical_parameter_block
from idaes.models.properties import iapws95
from idaes.core.util.model_statistics import degrees_of_freedom
from idaes.core.surrogate.pysmo.sampling import HammersleySampling
import pandas as pd
from idaes.core.surrogate.pysmo_surrogate import PysmoRBFTrainer, PysmoSurrogate
from idaes.core.surrogate.plotting.sm_plotter import surrogate_scatter2D, surrogate_parity, surrogate_residual
import contextlib

# To see the properties of a valve, including the degrees of freedom and
# why the following function is required, see
# https://idaes-pse.readthedocs.io/en/stable/reference_guides/model_libraries/generic/unit_models/valve.html
def _valve_pressure_flow_cb(b):
    """
    This function is a callback that will be used to define the pressure-flow of a valve.
    It isn't strictly necessary to use this function, e.g there are built in functions that could be used instead.
    see https://idaes-pse.readthedocs.io/en/stable/reference_guides/model_libraries/generic/unit_models/valve.html?highlight=valve#built-in-valve-functions
    """
    umeta = b.config.property_package.get_metadata().get_derived_units

    b.Cv = pyo.Var(
        initialize=0.1,
        doc="Valve flow coefficent",
        units=umeta("amount") / umeta("time") / umeta("pressure"),
    )
    b.Cv.fix()

    b.flow_var = pyo.Reference(b.control_volume.properties_in[:].flow_mol)
    b.pressure_flow_equation_scale = lambda x: x**2

    @b.Constraint(b.flowsheet().time)
    def pressure_flow_equation(b2, t):
        Po = b2.control_volume.properties_out[t].pressure
        Pi = b2.control_volume.properties_in[t].pressure
        F = b2.control_volume.properties_in[t].flow_mol
        Cv = b2.Cv
        fun = b2.valve_function[t]
        return F**2 == Cv**2 * (Pi**2 - Po**2) * fun**2


def train_valve_model():
    """
    Creates a surrogate valve model using IDAES's internal pySMO surrogate modelling library.
    First, an idaes model for a valve is created and a bunch of data is generated using the model.
    Then, a surrogate model is trained using the data.
    """
    m = pyo.ConcreteModel()
    m.fs = FlowsheetBlock(dynamic=False)
    m.fs.properties = iapws95.Iapws95ParameterBlock() # Water property package
    m.fs.unit = Valve(property_package=m.fs.properties,
                      pressure_flow_callback=_valve_pressure_flow_cb,
                      material_balance_type=MaterialBalanceType.componentTotal)
    
    #print("Degrees of freedom: ", degrees_of_freedom(m.fs))
    # Currently the model has 3 degrees of freedom. However, this is because
    # by default the valve_opening is fixed at 100%
    m.fs.unit.valve_opening.unfix()
    #print("Degrees of freedom after unfixing valve_opening: ", degrees_of_freedom(m.fs))
    # Now the model has 4 degrees of freedom.
    # The degrees of freedom are:
    # 1. Inlet pressure
    # 2. Inlet enthalpy. Valves are isenthalpic, meaning the outlet enthalpy is the same as the inlet enthalpy.
    # 3. Valve opening fraction. 0 is closed, 1 is open.
    # 4. Either the outlet pressure or the flow rate.
    #    The inlet flow rate == the outlet flow rate,
    #    but the flow rate is dependent on the pressure, and vice versa.
    #    (a high pressure drop means the flow is constricted a lot, or
    #     a high flow rate means the pressure drop is low)
    
    # m.fs.unit.inlet.flow_mol.fix(1000)
    # m.fs.unit.inlet.enth_mol.fix(40000)
    # m.fs.unit.inlet.pressure.fix(101325)
    # m.fs.unit.outlet.pressure.fix(100000)
    # print("Degrees of freedom: ", degrees_of_freedom(m.fs.unit))
    solver = pyo.SolverFactory("ipopt")
    # solver.solve(m.fs)
        
    # Now we need to generate data to train the surrogate model.
    
    # min and max bounds for [inlet_pressure, inlet_enthalpy, valve_opening, inlet_flow]
    sample_range = [
        [1e4,5e3,0.2,100],
        [1e6,7e4,1.0,500]
    ]
    sample_points = HammersleySampling(data_input=sample_range, 
                                        number_of_samples=500,
                                        sampling_type='creation').sample_points()
    

    # Calculate the outlet pressure for each sample point
    # we can assume the outlet flow rate is the same as the inlet flow rate
    # and the outlet enthalpy is the same as the inlet enthalpy
    outlet_pressure = []
    for point in sample_points:
        m.fs.unit.inlet.pressure.fix(point[0])
        m.fs.unit.inlet.enth_mol.fix(point[1])
        m.fs.unit.valve_opening.fix(point[2])
        m.fs.unit.inlet.flow_mol.fix(point[3])
        solver.solve(m.fs)
        outlet_pressure.append(pyo.value(m.fs.unit.outlet.pressure[0]))
    
    # Now we have the data, we can train the surrogate model
    df = pd.DataFrame(sample_points, columns=["inlet_pressure", "inlet_enthalpy", "valve_opening", "inlet_flow"])
    df["outlet_pressure"] = outlet_pressure
    
    input_labels = ["inlet_pressure", "inlet_enthalpy", "valve_opening", "inlet_flow"]
    output_labels = ["outlet_pressure"]
    
    trainer = PysmoRBFTrainer(input_labels=input_labels, 
                              output_labels=output_labels,
                              training_dataframe=df)
    trainer.config.basis_function = 'gaussian'
    
    with contextlib.redirect_stdout(None):
        rbf_train = trainer.train_surrogate()
    
    rbf_train.display_pysmo_results()
    
    # set model bounds
    bounds = {
        'inlet_pressure': [1e4, 1e6],
        'inlet_enthalpy': [5e3, 7e4],
        'valve_opening': [0.2, 1.0],
        'inlet_flow': [100, 500]
    }
    rbf_surr = PysmoSurrogate(rbf_train, input_labels, output_labels, bounds)
    
    surrogate_scatter2D(rbf_surr, df, filename='pysmo_poly_train_scatter2D.pdf')
    
    model = rbf_surr.save_to_file('pysmo_valve_surrogate.json', overwrite=True)

# TODO: Make a function that returns a SurrogateValveBlock
# either using an idaes custom unitBlock api: https://idaes-pse.readthedocs.io/en/stable/how_to_guides/custom_models/unit_model_development.html
# or just by creating a custom block manually
# see: surrogate_modelling.ipynb for an example of how to use the surrogate model

# I am going to use an idaes custom unitBlock api, following the example in 
# https://idaes.github.io/examples-pse/latest/Examples/Advanced/CustomUnitModels/custom_compressor_doc.html



# Utility function to make a control volume block for the valve for material and energy balances
# (remember the valve is isenthalpic and doesn't have a holdup)



def make_control_volume(unit, name, config):
    if config.dynamic is not False:
        raise ValueError('SurrogateValve does not support dynamics')
    if config.has_holdup is not False:
        raise ValueError('SurrogateValve does not support holdup')

    control_volume = ControlVolume0DBlock(property_package=config.property_package,
                                          property_package_args=config.property_package_args)

    # Add the control volume block to the unit
    setattr(unit, name, control_volume)

    control_volume.add_state_blocks(has_phase_equilibrium=config.has_phase_equilibrium)
    control_volume.add_material_balances(balance_type=config.material_balance_type,
                                         has_phase_equilibrium=config.has_phase_equilibrium)
    control_volume.add_total_enthalpy_balances(has_heat_of_reaction=False, 
                                               has_heat_transfer=False, 
                                               has_work_transfer=True)



@declare_process_block_class("SurrogateValve")
class SurrogateValveData(UnitModelBlockData):
    CONFIG = UnitModelBlockData.CONFIG()
    # Declare all the standard config arguments for the control_volume
    CONFIG.declare("material_balance_type", ConfigValue(default=MaterialBalanceType.componentPhase, domain=In(MaterialBalanceType)))
    CONFIG.declare("energy_balance_type", ConfigValue(default=EnergyBalanceType.enthalpyTotal, domain=In([EnergyBalanceType.enthalpyTotal])))
    CONFIG.declare("momentum_balance_type", ConfigValue(default=MomentumBalanceType.none, domain=In([MomentumBalanceType.none])))
    CONFIG.declare("has_phase_equilibrium", ConfigValue(default=False, domain=In([False])))
    CONFIG.declare("has_pressure_change", ConfigValue(default=False, domain=In([False])))
    CONFIG.declare("property_package", ConfigValue(default=useDefault, domain=is_physical_parameter_block))
    CONFIG.declare("property_package_args", ConfigBlock(implicit=True))
    # no other args need to be declared, we are just hardcoding the valve model.

    def build(self):
        super(SurrogateValveData, self).build()
        
        # This function handles adding the control volume block to the unit,
        # and addiing the necessary material and energy balances.
        make_control_volume(self, "control_volume", self.config)

        self.add_inlet_port()
        self.add_outlet_port()
        self.valve_opening = pyo.Var(initialize=1.0, bounds=(0.0, 1.0))

        # Load Surrogate model to predict pressure
        model = PysmoSurrogate.load_from_file('pysmo_valve_surrogate.json')
        inputs = [self.inlet.pressure, self.inlet.enthalpy, self.valve_opening, self.inlet.flow ]
        outputs = [self.outlet.pressure]
        self.surrogate = SurrogateBlock(concrete=True)
        self.surrogate.build_model(model,input_vars=inputs, output_vars=outputs)
        

    

if __name__ == "__main__":
    train_valve_model()
    print("Training complete.")