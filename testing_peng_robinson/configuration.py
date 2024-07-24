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
        "benzene": {
            "type": Component,
            "enth_mol_ig_comp": ChemSep,
            "entr_mol_ig_comp": ChemSep,
            "pressure_sat_comp": ChemSep,
            "dens_mol_liq_comp": Perrys,
            "phase_equilibrium_form": {},
            "parameter_data": {
                "mw": (78.11184, pyunits.kg / pyunits.kmol),
                "pressure_crit": (4895000, pyunits.Pa),
                "temperature_crit": (562.05, pyunits.K),
                "omega": 0.209,
                "cp_mol_ig_comp_coeff": {
                    "A": (29525, pyunits.J / pyunits.kmol / pyunits.K),
                    "B": (-51.417, pyunits.J / pyunits.kmol / pyunits.K**2),
                    "C": (1.1944, pyunits.J / pyunits.kmol / pyunits.K**3),
                    "D": (-0.0016468, pyunits.J / pyunits.kmol / pyunits.K**4),
                    "E": (6.8461E-07, pyunits.J / pyunits.kmol / pyunits.K**5),
                },
                "enth_mol_form_vap_comp_ref": (8.288E+07, pyunits.J / pyunits.kmol),
                "entr_mol_form_vap_comp_ref": (-269300, pyunits.J / pyunits.kmol / pyunits.K),
                "pressure_sat_comp_coeff": {
                    "A": (21.075, None),
                    "B": (2977.3, pyunits.K),
                    "C": (-41.505, pyunits.K)
                },
                "dens_mol_liq_comp_coeff": {
                    "eqn_type": 1,
                    "1": (0.99938, pyunits.kmol / pyunits.m**3),
                    "2": (0.26348, None),
                    "3": (562.05, pyunits.K),
                    "4": (0.27856, None),
                }
            },
        },
        "toluene": {
            "type": Component,
            "enth_mol_ig_comp": RPP4,
            "entr_mol_ig_comp": RPP4,
            "pressure_sat_comp": ChemSep,
            "dens_mol_liq_comp": Perrys,
            "phase_equilibrium_form": {},
            "parameter_data": {
                "mw": (92.13843, pyunits.kg / pyunits.kmol),
                "pressure_crit": (4108000, pyunits.Pa),
                "temperature_crit": (591.75, pyunits.K),
                "omega": 0.264,
                "cp_mol_ig_comp_coeff": {
                    "A": (-43647.49, pyunits.J / pyunits.kmol / pyunits.K),
                    "B": (603.542, pyunits.J / pyunits.kmol / pyunits.K**2),
                    "C": (-0.399451, pyunits.J / pyunits.kmol / pyunits.K**3),
                    "D": (0.000104382, pyunits.J / pyunits.kmol / pyunits.K**4),
                },
                "enth_mol_form_vap_comp_ref": (5.017E+07, pyunits.J / pyunits.kmol),
                "entr_mol_form_vap_comp_ref": (-320990, pyunits.J / pyunits.kmol / pyunits.K),
                "pressure_sat_comp_coeff": {
                    "A": (20.864, None),
                    "B": (3019.2, pyunits.K),
                    "C": (-60.13, pyunits.K)
                },
                "dens_mol_liq_comp_coeff": {
                    "eqn_type": 1,
                    "1": (0.89799, pyunits.kmol / pyunits.m**3),
                    "2": (0.27359, None),
                    "3": (591.75, pyunits.K),
                    "4": (0.30006, None)
                }
            },
        },
    },
    "phases": {
        "Liq": {
            "type": LiquidPhase,
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
            ("benzene", "benzene"): 0.000,
            ("benzene", "toluene"): 0.000,
            ("toluene", "benzene"): 0.000,
            ("toluene", "toluene"): 0.000,
        }
    },
}
