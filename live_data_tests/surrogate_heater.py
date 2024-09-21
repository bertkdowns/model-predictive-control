# Methods and helper functions to train and use a surrogate heater.
import pyomo.environ as pyo
from idaes.core import FlowsheetBlock, MaterialBalanceType, ControlVolume0DBlock, declare_process_block_class, EnergyBalanceType, MomentumBalanceType, MaterialBalanceType, useDefault, UnitModelBlockData
from idaes.models.unit_models import Heater
from pyomo.common.config import ConfigBlock, ConfigValue, In
from idaes.core.surrogate.surrogate_block import SurrogateBlock
from idaes.core.util.config import is_physical_parameter_block
from idaes.models.properties.general_helmholtz import (
    HelmholtzParameterBlock,
    PhaseType,
    StateVars,
)
from idaes.core.util.model_statistics import degrees_of_freedom
from idaes.core.surrogate.pysmo.sampling import HammersleySampling
import pandas as pd
from idaes.core.surrogate.pysmo_surrogate import PysmoRBFTrainer, PysmoSurrogate
from idaes.core.surrogate.plotting.sm_plotter import surrogate_scatter2D, surrogate_parity, surrogate_residual
import contextlib

# To see the properties of a heater, including the degrees of freedom and
# why the following function is required, see
# https://idaes-pse.readthedocs.io/en/stable/reference_guides/model_libraries/generic/unit_models/heater.html



def train_heater_model():
    """
    Creates a surrogate heater model using IDAES's internal pySMO surrogate modelling library.
    First, an idaes model for a heater is created and a bunch of data is generated using the model.
    Then, a surrogate model is trained using the data.
    """
    m = pyo.ConcreteModel()
    m.fs = FlowsheetBlock(dynamic=False)
    m.fs.properties = HelmholtzParameterBlock(
    pure_component="h2o",
    phase_presentation=PhaseType.MIX,
    state_vars=StateVars.TPX,
)
    m.fs.unit = Heater(property_package=m.fs.properties)
    
    #print("Degrees of freedom: ", degrees_of_freedom(m.fs))
    solver = pyo.SolverFactory("ipopt")
    # solver.solve(m.fs)
    # Now we need to generate data to train the surrogate model.

    # min and max bounds for [inlet_pressure, inlet_temperature, heat_duty, inlet_flow]
    sample_range = [
        [10132,500,0,50],
        [201325,800,250_000,500]
    ]
    # we need to be careful with the sampling, because e.g high heat duty is fine with high flow rate
    # but not with low flow rate
    sample_points = HammersleySampling(data_input=sample_range, 
                                        number_of_samples=300,
                                        sampling_type='creation').sample_points()

    # All should be gas phase
    m.fs.unit.inlet.vapor_frac.fix(1)
    # Calculate the outlet pressure for each sample point
    # we can assume the outlet flow rate is the same as the inlet flow rate
    # and the outlet temperature is the same as the inlet temperature
    outlet_pressure = []
    outlet_temperature = []
    outlet_vapor_frac = []
    for point in sample_points:
        m.fs.unit.inlet.pressure.fix(point[0])
        m.fs.unit.inlet.temperature.fix(point[1])
        m.fs.unit.heat_duty.fix(point[2])
        m.fs.unit.inlet.flow_mol.fix(point[3])
        # display the values of the variables
        print("Inlet pressure: ", pyo.value(m.fs.unit.inlet.pressure[0]))
        print("Inlet temperature: ", pyo.value(m.fs.unit.inlet.temperature[0]))
        print("Heat duty: ", pyo.value(m.fs.unit.heat_duty[0]))
        print("Inlet flow: ", pyo.value(m.fs.unit.inlet.flow_mol[0]))
        
        solver.solve(m.fs)
        outlet_pressure.append(pyo.value(m.fs.unit.outlet.pressure[0]))
        outlet_temperature.append(pyo.value(m.fs.unit.outlet.temperature[0]))
        outlet_vapor_frac.append(pyo.value(m.fs.unit.outlet.vapor_frac[0]))
    
    # Now we have the data, we can train the surrogate model
    df = pd.DataFrame(sample_points, columns=["inlet_pressure", "inlet_temperature", "heat_duty", "inlet_flow"])
    df["outlet_pressure"] = outlet_pressure
    df["outlet_temperature"] = outlet_temperature
    df["outlet_vapor_frac"] = outlet_vapor_frac
    
    input_labels = ["inlet_pressure", "inlet_temperature", "heat_duty", "inlet_flow"]
    output_labels = ["outlet_pressure","outlet_temperature","outlet_vapor_frac"]
    
    trainer = PysmoRBFTrainer(input_labels=input_labels, 
                              output_labels=output_labels,
                              training_dataframe=df)
    trainer.config.basis_function = 'gaussian'
    
    with contextlib.redirect_stdout(None):
        rbf_train = trainer.train_surrogate()
    
    #rbf_train.display_pysmo_results()
    
    # set model bounds
    bounds = {
        'inlet_pressure': [10132, 201325],
        'inlet_temperature': [500, 800],
        'heat_duty': [-3000, 300_000],
        'inlet_flow': [50, 500]
    }
    rbf_surr = PysmoSurrogate(rbf_train, input_labels, output_labels, bounds)
    
    surrogate_scatter2D(rbf_surr, df, filename='pysmo_poly_train_scatter2D.pdf')
    
    model = rbf_surr.save_to_file('pysmo_heater_surrogate.json', overwrite=True)

# TODO: Make a function that returns a SurrogateheaterBlock
# either using an idaes custom unitBlock api: https://idaes-pse.readthedocs.io/en/stable/how_to_guides/custom_models/unit_model_development.html
# or just by creating a custom block manually
# see: surrogate_modelling.ipynb for an example of how to use the surrogate model

# I am going to use an idaes custom unitBlock api, following the example in 
# https://idaes.github.io/examples-pse/latest/Examples/Advanced/CustomUnitModels/custom_compressor_doc.html



# Utility function to make a control volume block for the heater for material and energy balances
# (remember the heater is isenthalpic and doesn't have a holdup)



def make_control_volume(unit, name, config):
    # TODO: the control volume doesnt' support dynamics, not sure how to check for that (errors raised incorrectly)
    # view the properties of the object
    # [print( o) for o in config.dynamic.__attrs__]
    # if config.dynamic is not False and config.dynamic is not None:
    #     raise ValueError('SurrogateHeater does not support dynamics', config.dynamic)
    # if config.has_holdup is not False and config.has_holdup is not None:
    #     raise ValueError('Surrogateheater does not support holdup')

    control_volume = ControlVolume0DBlock(
                                          dynamic=config.dynamic,
                                          has_holdup=config.has_holdup,
                                          property_package=config.property_package,
                                          property_package_args=config.property_package_args)

    # Add the control volume block to the unit
    setattr(unit, name, control_volume)

    control_volume.add_state_blocks(has_phase_equilibrium=config.has_phase_equilibrium)
    control_volume.add_material_balances(balance_type=config.material_balance_type,
                                         has_phase_equilibrium=config.has_phase_equilibrium)
    # control_volume.add_total_enthalpy_balances(has_heat_of_reaction=False, 
    #                                            has_heat_transfer=False, 
    #                                            has_work_transfer=True)
    # enthalpy doens't balance because it's a heater
    



@declare_process_block_class("SurrogateHeater")
class SurrogateHeaterData(UnitModelBlockData):
    CONFIG = UnitModelBlockData.CONFIG()
    # Declare all the standard config arguments for the control_volume
    CONFIG.declare("material_balance_type", ConfigValue(default=MaterialBalanceType.componentPhase, domain=In(MaterialBalanceType)))
    CONFIG.declare("energy_balance_type", ConfigValue(default=EnergyBalanceType.enthalpyTotal, domain=In([EnergyBalanceType.enthalpyTotal])))
    CONFIG.declare("momentum_balance_type", ConfigValue(default=MomentumBalanceType.none, domain=In([MomentumBalanceType.none])))
    CONFIG.declare("has_phase_equilibrium", ConfigValue(default=False, domain=In([False])))
    CONFIG.declare("has_pressure_change", ConfigValue(default=False, domain=In([False])))
    CONFIG.declare("property_package", ConfigValue(default=useDefault, domain=is_physical_parameter_block))
    CONFIG.declare("property_package_args", ConfigBlock(implicit=True))
    # no other args need to be declared, we are just hardcoding the heater model.

    def build(self):
        super(SurrogateHeaterData, self).build()
        
        # This function handles adding the control volume block to the unit,
        # and addiing the necessary material and energy balances.
        make_control_volume(self, "control_volume", self.CONFIG)

        self.add_inlet_port()
        self.add_outlet_port()
        self.heat_duty = pyo.Var(initialize=1.0, bounds=(-3000, 300_000))
        self.outlet_vapor = pyo.Var(initialize=0.0, bounds=(0, 1))

        # Load Surrogate model to predict pressure
        model = PysmoSurrogate.load_from_file('pysmo_heater_surrogate.json')
        inputs = [self.inlet.pressure, self.inlet.temperature, self.heat_duty, self.inlet.flow_mol ]
        outputs = [self.outlet.pressure,self.outlet.temperature,self.outlet_vapor]
        self.surrogate = SurrogateBlock(concrete=True)
        self.surrogate.build_model(model,input_vars=inputs, output_vars=outputs)
        

    

if __name__ == "__main__":
    train_heater_model()
    print("Training complete.")