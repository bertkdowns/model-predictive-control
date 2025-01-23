# Import Pyomo tools
from pyomo.environ import (
    Constraint,
    Var,
    Param,
    Expression,
    Reals,
    NonNegativeReals,
    Suffix,
)
from pyomo.environ import units as pyunits

# Import IDAES cores
from idaes.core import (
    declare_process_block_class,
    MaterialFlowBasis,
    PhysicalParameterBlock,
    StateBlockData,
    StateBlock,
    MaterialBalanceType,
    EnergyBalanceType,
)
from idaes.core.base.components import Component
from idaes.core.base.phases import LiquidPhase
from idaes.core.util.initialization import (
    fix_state_vars,
    revert_state_vars,
    solve_indexed_blocks,
)
from idaes.core.base.process_base import ProcessBlockData, property_meta
from idaes.core.util.model_statistics import (
    degrees_of_freedom,
    number_unfixed_variables,
)
from idaes.core.util.exceptions import PropertyPackageError
import idaes.core.util.scaling as iscale
import idaes.logger as idaeslog
from idaes.core.solvers import get_solver

# Set up logger
_log = idaeslog.getLogger(__name__)


# STEP 2

# When using this file the name "PowerParameterBlock" is what is imported
@declare_process_block_class("PowerParameterBlock")
class PropParameterData(ProcessBlockData, property_meta.HasPropertyClassMetadata):
    CONFIG = ProcessBlockData.CONFIG()

    def build(self):
        """
        Callable method for Block construction.
        """
        super(PropParameterData, self).build()

        self._state_block_class = PowerStateBlock

        # Variables
        self.power = Var(initialize=0, domain=Reals, units=pyunits.W)

        # Default scaling values should be provided so that our tools can ensure the model is well-scaled
        # Generally scaling factors should be such that if it is multiplied by the variable it will range between 0.01 and 100
        self.set_default_scaling("power", 1e-3)

    @classmethod
    def define_metadata(cls, obj):
        # see https://github.com/watertap-org/watertap/blob/main/tutorials/creating_a_simple_property_model.ipynb
        obj.add_default_units(
            {
                "power": pyunits.W,
            }
        )

# STEP 3: State Block
class _PowerStateBlock(StateBlock):
    def initialize(
        self,
        state_args=None,
        state_vars_fixed=False,
        hold_state=False,
        outlvl=idaeslog.NOTSET,
        solver=None,
        optarg=None,
    ):
        """
        Initialization routine for property package.
        Keyword Arguments:
            state_args : Dictionary with initial guesses for the state vars
                         chosen. Note that if this method is triggered
                         through the control volume, and if initial guesses
                         were not provided at the unit model level, the
                         control volume passes the inlet values as initial
                         guess.The keys for the state_args dictionary are:

                         flow_mass_phase_comp : value at which to initialize
                                               phase component flows
                         pressure : value at which to initialize pressure
                         temperature : value at which to initialize temperature

            state_vars_fixed: Flag to denote if state vars have already been
                              fixed.
                              - True - states have already been fixed by the
                                       control volume 1D. Control volume 0D
                                       does not fix the state vars, so will
                                       be False if this state block is used
                                       with 0D blocks.
                             - False - states have not been fixed. The state
                                       block will deal with fixing/unfixing.
            hold_state : flag indicating whether the initialization routine
                         should unfix any state variables fixed during
                         initialization (default=False).
                         - True - states variables are not unfixed, and
                                 a dict of returned containing flags for
                                 which states were fixed during
                                 initialization.
                        - False - state variables are unfixed after
                                 initialization by calling the
                                 release_state method
            outlvl : sets output level of initialization routine (default=idaeslog.NOTSET)
            solver : Solver object to use during initialization if None is provided
                     it will use the default solver for IDAES (default = None)
            optarg : solver options dictionary object (default=None)
        Returns:
            If hold_states is True, returns a dict containing flags for
            which states were fixed during initialization.
        """
        # Get loggers
        init_log = idaeslog.getInitLogger(self.name, outlvl, tag="properties")
        solve_log = idaeslog.getSolveLogger(self.name, outlvl, tag="properties")

        # Set solver and options
        opt = get_solver(solver, optarg)

        # Fix state variables
        flags = fix_state_vars(self, state_args)
        # Check that dof = 0 when state variables are fixed
        for k in self.keys():
            dof = degrees_of_freedom(self[k])
            if dof != 0:
                raise PropertyPackageError(
                    "\nWhile initializing {sb_name}, the degrees of freedom "
                    "are {dof}, when zero is required. \nInitialization assumes "
                    "that the state variables should be fixed and that no other "
                    "variables are fixed. \nIf other properties have a "
                    "predetermined value, use the calculate_state method "
                    "before using initialize to determine the values for "
                    "the state variables and avoid fixing the property variables."
                    "".format(sb_name=self.name, dof=dof)
                )

        # If input block, return flags, else release state
        if state_vars_fixed is False:
            if hold_state is True:
                return flags
            else:
                self.release_state(flags)

    def release_state(self, flags, outlvl=idaeslog.NOTSET):
        """
        Method to release state variables fixed during initialisation.

        Keyword Arguments:
            flags : dict containing information of which state variables
                    were fixed during initialization, and should now be
                    unfixed. This dict is returned by initialize if
                    hold_state=True.
            outlvl : sets output level of of logging
        """
        if flags is None:
            return
        # Unfix state variables
        for attr in flags:
            if flags[attr] is True:
                getattr(self, attr).unfix()
        return
        
# STEP 4: 
@declare_process_block_class("PowerStateBlock", block_class=_PowerStateBlock)
class PowerStateBlockData(StateBlockData):
    def build(self):
        """Callable method for Block construction."""
        super(PowerStateBlockData, self).build()

        self.scaling_factor = Suffix(direction=Suffix.EXPORT)

        self.flow_mass_phase_comp = Var(
            initialize=0,
            domain=Reals,
            units=pyunits.W,
            doc="Power flow",
        )

    # -----------------------------------------------------------------------------

    def define_state_vars(self):
        """Define state vars."""
        return {
            "power": self.power,
        }

    # -----------------------------------------------------------------------------
    # Scaling methods
    def calculate_scaling_factors(self):
        super().calculate_scaling_factors()
        # This doesn't do anything, but it's a good example of how to get and set scaling factors in relation to each other.
        sf = iscale.get_scaling_factor(self.power)
        iscale.set_scaling_factor(self.power, sf)


