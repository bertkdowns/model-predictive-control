# Import Pyomo libraries
from pyomo.environ import (
    Var,
    Suffix,
    units as pyunits,
)
from pyomo.common.config import ConfigBlock, ConfigValue, In
from idaes.core.util.tables import create_stream_table_dataframe
from idaes.core.util.exceptions import ConfigurationError
# Import IDAES cores
from idaes.core import (
    declare_process_block_class,
    UnitModelBlockData,
    useDefault,
)
from idaes.core.util.config import is_physical_parameter_block
import idaes.core.util.scaling as iscale
import idaes.logger as idaeslog

# Set up logger
_log = idaeslog.getLogger(__name__)


# When using this file the name "Load" is what is imported
@declare_process_block_class("Dsi")
class dsiData(UnitModelBlockData):
    """
    Direct Steam Injection Unit Model

    This unit model is used to represent a direct steam injection
    process. There are no degrees of freedom, but the steam is mixed with the inlet fluid to heat it up.
    It is assumed that the pressure of the fluid doesn't change, i.e the steam loses its pressure.
    However, the enthalpy of the steam remains the same. 
    This allows to use two different property packages for the steam and for the inlet fluid, however,
    it only works if the reference enthalpy of the steam and the inlet fluid are the same.

    It's basically a combination of a mixer and a translator.
    """
    # CONFIG are options for the unit model
    CONFIG = ConfigBlock()

    CONFIG.declare(
        "dynamic",
        ConfigValue(
            domain=In([False]),
            default=False,
            description="Dynamic model flag - must be False",
            doc="""Indicates whether this model will be dynamic or not,
    **default** = False. The Bus unit does not support dynamic
    behavior, thus this must be False.""",
        ),
    )
    CONFIG.declare(
        "has_holdup",
        ConfigValue(
            default=False,
            domain=In([False]),
            description="Holdup construction flag - must be False",
            doc="""Indicates whether holdup terms should be constructed or not.
    **default** - False. The Bus unit does not have defined volume, thus
    this must be False.""",
        ),
    )
    CONFIG.declare(
        "property_package",
        ConfigValue(
            default=useDefault,
            domain=is_physical_parameter_block,
            description="Property package to use for control volume",
            doc="""Property parameter object used to define property calculations,
    **default** - useDefault.
    **Valid values:** {
    **useDefault** - use default package from parent model or flowsheet,
    **PhysicalParameterObject** - a PhysicalParameterBlock object.}""",
        ),
    )
    CONFIG.declare(
        "property_package_args",
        ConfigBlock(
            implicit=True,
            description="Arguments to use for constructing property packages",
            doc="""A ConfigBlock with arguments to be passed to a property block(s)
    and used when constructing these,
    **default** - None.
    **Valid values:** {
    see property package for documentation.}""",
        ),
    )
    CONFIG.declare(
        "steam_property_package",
        ConfigValue(
            default=useDefault,
            domain=is_physical_parameter_block,
            description="Property package to use for control volume",
            doc="""Property parameter object used to define property calculations,
    **default** - useDefault.
    **Valid values:** {
   **useDefault** - use default package from parent model or flowsheet,
    **PhysicalParameterObject** - a PhysicalParameterBlock object.}""",
        ),
    )
    CONFIG.declare(
        "steam_property_package_args",
        ConfigBlock(
            implicit=True,
            description="Arguments to use for constructing property packages",
            doc="""A ConfigBlock with arguments to be passed to a property block(s)
    and used when constructing these,
    **default** - None.
    **Valid values:** {
    see property package for documentation.}""",
        ),
    )

    def build(self):
        # build always starts by calling super().build()
        # This triggers a lot of boilerplate in the background for you
        super().build()

        # This creates blank scaling factors, which are populated later
        self.scaling_factor = Suffix(direction=Suffix.EXPORT)


        # Add state blocks for inlet, outlet, and waste
        # These include the state variables and any other properties on demand
        # Add inlet block
        tmp_dict = dict(**self.config.property_package_args)
        tmp_dict["parameters"] = self.config.property_package
        tmp_dict["defined_state"] = True  # inlet block is an inlet
        self.properties_in = self.config.property_package.state_block_class(
            self.flowsheet().config.time, doc="Material properties of inlet", **tmp_dict
        )
        steam_dict = dict(**self.config.steam_property_package_args)
        steam_dict["parameters"] = self.config.steam_property_package
        steam_dict["defined_state"] = True  
        self.properties_steam_in = self.config.steam_property_package.state_block_class(
            self.flowsheet().config.time, doc="Material properties of steam inlet", **steam_dict
        )

        # Add outlet and waste block
        tmp_dict["defined_state"] = False  # In this case, defined state is still true because the mole_frac_phase_comp is defined 
        self.properties_out = self.config.property_package.state_block_class(
            self.flowsheet().config.time,
            doc="Material properties of outlet",
            **tmp_dict
        )
        

        # Add ports
        self.add_port(name="outlet", block=self.properties_out)
        self.add_port(name="inlet", block=self.properties_in, doc="Inlet port")
        self.add_port(name="steam_inlet", block=self.properties_steam_in, doc="Steam inlet port")

        # Add constraints
        @self.Constraint(
            self.flowsheet().time,
            doc="Energy balance",
        )
        def eq_energy_balance(b, t):
            return (
                b.properties_out[t].enth_mol
                == b.properties_in[t].enth_mol
                + b.properties_steam_in[t].enth_mol
            )
        
        @self.Constraint(
            self.flowsheet().time,
            doc="Pressure balance",
        )
        def eq_pressure_balance(b, t):
            return (
                b.properties_out[t].pressure
                == b.properties_in[t].pressure
            )
        
        # Mass balance is more complicated, because we need to merge each compound and phase.
        @self.Constraint(
            self.flowsheet().time,
            self.config.property_package.component_list,
            doc="Mass balance",
        )
        def eq_mass_balance(b, t, c): # this is too simple, we need to also had constraints for mole_frac_phase_comp
            return (
                sum(b.properties_out[t].get_material_flow_terms(p, c)
                    for p in b.properties_out[t].phase_list
                    if (p,c) in b.properties_out[t].phase_component_set) # handle the case where a component is not in that phase (e.g no milk vapor)
                == sum(b.properties_in[t].get_material_flow_terms(p, c)
                for p in b.properties_in[t].phase_list 
                if (p,c) in b.properties_out[t].phase_component_set
                )
            )
        
        # @self.Constraint(
        #     self.flowsheet().time,
        #     self.config.property_package.component_list,
        #     doc="Mass balance",
        # )
        # def eq_mass_balance(b, t, c):
        #     # block, time, phase, compound
        #     return (
        #         sum(b.properties_out[t].get_material_flow_terms(p, c)
        #             for p in b.properties_out[t].phase_list
        #             if (p,c) in b.properties_out[t].phase_component_set) # handle the case where a component is not in that phase (e.g no milk vapor)
        #         == sum(b.properties_in[t].get_material_flow_terms(p, c)
        #         # note that the steam inlet has less properties, e.g it doesn't have milk.
        #         + (b.properties_steam_in[t].get_material_flow_terms(p, c)
        #             if c in b.properties_steam_in[t].component_list  # handle the case where a component isn't in the steam inlet (e.g no milk in helmholtz)
        #             else 0)
        #         for p in b.properties_in[t].phase_list 
        #         if (p,c) in b.properties_out[t].phase_component_set
        #         )
        #     )

    def calculate_scaling_factors(self):
        super().calculate_scaling_factors()
    
    def initialize(blk, *args, **kwargs):
        pass

    def _get_stream_table_contents(self, time_point=0):
        """
        Assume unit has standard configuration of 1 inlet and 1 outlet.

        Developers should overload this as appropriate.
        """
        try:
            return create_stream_table_dataframe(
                {"outlet": self.outlet,
                "inlet": self.inlet,
                "steam_inlet": self.steam_inlet}, time_point=time_point

            )
        except AttributeError:
            raise ConfigurationError(
                f"Unit model {self.name} does not have the standard Port "
                f"names (inlet and outlet). Please contact the unit model "
                f"developer to develop a unit specific stream table."
            )            