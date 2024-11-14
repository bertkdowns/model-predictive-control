from idaes.models.properties.modular_properties.phase_equil.bubble_dew import LogBubbleDew
from idaes.models.properties.modular_properties.phase_equil.forms import log_fugacity
from idaes.models.properties.modular_properties.eos.ceos import Cubic, CubicType
from idaes.models.properties.modular_properties.state_definitions import FTPx, FPhx
from idaes.models.properties.modular_properties.phase_equil import SmoothVLE
from idaes.models.properties.modular_properties.pure import RPP4, Perrys
from idaes.core import LiquidPhase, VaporPhase, Component
from chem_sep import ChemSep
from pyomo.environ import units as pyunits


# Property Parameter Block Configuration, used in solve.py
# Raw Data Sourced from:
# https://raw.githubusercontent.com/DanWBR/dwsim/windows/DWSIM.Thermodynamics/Assets/Databases/chemsep1.xml

configuration = {
    "components": {
        "water": {
            "type": Component,
            "enth_mol_ig_comp": ChemSep,
            "entr_mol_ig_comp": ChemSep,
            "pressure_sat_comp": RPP4,
            "parameter_data": {
                "mw": (18.01528, pyunits.kg / pyunits.kmol),
                "pressure_crit": (22064000, pyunits.Pa),
                "temperature_crit": (647.14, pyunits.K),
                "omega": 0.344,
                "cp_mol_ig_comp_coeff": {
                    "A": (33444.62, pyunits.J / pyunits.kmol / pyunits.K),
                    "B": (-5.799206, pyunits.J / pyunits.kmol / pyunits.K**2),
                    "C": (0.0251681, pyunits.J / pyunits.kmol / pyunits.K**3),
                    "D": (-0.0000143103, pyunits.J / pyunits.kmol / pyunits.K**4),
                    "E": (2.76249E-09, pyunits.J / pyunits.kmol / pyunits.K**5),
                },
                "enth_mol_form_vap_comp_ref": (-241814000, pyunits.J / pyunits.kmol),
                "entr_mol_form_vap_comp_ref": (-188724, pyunits.J / pyunits.kmol / pyunits.K),
                "pressure_sat_comp_coeff": {
                    "A": (23.401, None),
                    "B": (3987.3, None),
                    "C": (-37.161, None),
                    "D": (-37.161, None)
                },
            },
        },
    },
    "phases": {
        "Liq": {
            "type": VaporPhase,
            "equation_of_state": Cubic,
            "equation_of_state_options": {"type": CubicType.PR},
        },
    },
    "base_units": {
        "time": pyunits.s,
        "length": pyunits.m,
        "mass": pyunits.kg,
        "amount": pyunits.mol,
        "temperature": pyunits.K,
    },
    "state_definition": FPhx,
    "state_bounds": {
        "flow_mol": (0, 100, 1000, pyunits.mol / pyunits.s),
        "temperature": (273.15, 300, 500, pyunits.K),
        "pressure": (5e4, 1e5, 1e6, pyunits.Pa),
    },
    "pressure_ref": (101325, pyunits.Pa),
    "temperature_ref": (298.15, pyunits.K),
    "phases_in_equilibrium": [],
    "phase_equilibrium_state": {},
    "bubble_dew_method": LogBubbleDew,
    "parameter_data": {
        "PR_kappa": {
            ("water", "water"): 0.000,
        }
    },
}
