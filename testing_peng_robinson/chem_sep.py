"""
Methods for calculating pure component properties from:

http://www.chemsep.org/downloads/docs/book.htm

IDAES naming conventions followed for compatibility with modular property packages
"""

from pyomo.environ import log, exp, units as pyunits
from idaes.core.util.misc import set_param_from_config
from pyomo.environ import Var, value

class ChemSep(object):

    class cp_mol_ig_comp:
        @staticmethod
        def build_parameters(cobj):
            cobj.cp_mol_ig_comp_coeff_A = Var(
                doc="Parameter A for ideal gas molar heat capacity",
                units=pyunits.J / pyunits.kilomol / pyunits.K,
            )
            set_param_from_config(cobj, param="cp_mol_ig_comp_coeff", index="A")

            cobj.cp_mol_ig_comp_coeff_B = Var(
                doc="Parameter B for ideal gas molar heat capacity",
                units=pyunits.J / pyunits.kilomol / pyunits.K ** 2,
            )
            set_param_from_config(cobj, param="cp_mol_ig_comp_coeff", index="B")

            cobj.cp_mol_ig_comp_coeff_C = Var(
                doc="Parameter C for ideal gas molar heat capacity",
                units=pyunits.J / pyunits.kilomol / pyunits.K ** 3,
            )
            set_param_from_config(cobj, param="cp_mol_ig_comp_coeff", index="C")

            cobj.cp_mol_ig_comp_coeff_D = Var(
                doc="Parameter D for ideal gas molar heat capacity",
                units=pyunits.J / pyunits.kilomol / pyunits.K ** 4,
            )
            set_param_from_config(cobj, param="cp_mol_ig_comp_coeff", index="D")

            cobj.cp_mol_ig_comp_coeff_E = Var(
                doc="Parameter E for ideal gas molar heat capacity",
                units=pyunits.J / pyunits.kilomol / pyunits.K ** 5,
            )
            set_param_from_config(cobj, param="cp_mol_ig_comp_coeff", index="E")

        @staticmethod
        def return_expression(b, cobj, T):
            T = pyunits.convert(T, to_units=pyunits.K)
            cp = (
                cobj.cp_mol_ig_comp_coeff_A +
                cobj.cp_mol_ig_comp_coeff_B*T +
                cobj.cp_mol_ig_comp_coeff_C*T**2 +
                cobj.cp_mol_ig_comp_coeff_D*T**3 +
                cobj.cp_mol_ig_comp_coeff_E*T**4
            )

            units = b.params.get_metadata().derived_units
            return pyunits.convert(cp, units.HEAT_CAPACITY_MOLE)

    class enth_mol_ig_comp:
        @staticmethod
        def build_parameters(cobj):
            # Required for calculating entropy
            if not hasattr(cobj, "cp_mol_ig_comp_coeff_A"):
                ChemSep.cp_mol_ig_comp.build_parameters(cobj)

            if cobj.parent_block().config.include_enthalpy_of_formation:

                units = cobj.parent_block().get_metadata().derived_units

                cobj.enth_mol_form_vap_comp_ref = Var(
                    doc="Vapor phase molar heat of formation",
                    units=units.ENERGY_MOLE,
                )
                set_param_from_config(cobj, param="enth_mol_form_vap_comp_ref")

        @staticmethod
        def return_expression(b, cobj, T):
            # Specific enthalpy
            T = pyunits.convert(T, to_units=pyunits.K)
            Tr = pyunits.convert(b.params.temperature_ref, to_units=pyunits.K)

            units = b.params.get_metadata().derived_units

            h_form = (
                cobj.enth_mol_form_vap_comp_ref
                if b.params.config.include_enthalpy_of_formation
                else 0 * units.ENERGY_MOLE
            )

            h = (
                pyunits.convert(
                    (cobj.cp_mol_ig_comp_coeff_A * (T - Tr)
                     + (cobj.cp_mol_ig_comp_coeff_B / 2) * (T**2 - Tr**2)
                     + (cobj.cp_mol_ig_comp_coeff_C / 3) * (T**3 - Tr**3)
                     + (cobj.cp_mol_ig_comp_coeff_D / 4) * (T**4 - Tr**4)
                     + (cobj.cp_mol_ig_comp_coeff_E / 5) * (T**5 - Tr**5)),
                    units.ENERGY_MOLE,
                ) + h_form
            )

            return h

    class entr_mol_ig_comp:
        @staticmethod
        def build_parameters(cobj):
            # Required for calculating enthalpy
            if not hasattr(cobj, "cp_mol_ig_comp_coeff_A"):
                ChemSep.cp_mol_ig_comp.build_parameters(cobj)

            units = cobj.parent_block().get_metadata().derived_units

            cobj.entr_mol_form_vap_comp_ref = Var(
                doc="Vapor phase molar entropy of formation",
                units=units.ENTROPY_MOLE,
            )

            set_param_from_config(cobj, param="entr_mol_form_vap_comp_ref")

        @staticmethod
        def return_expression(b, cobj, T):
            # Specific entropy
            T = pyunits.convert(T, to_units=pyunits.K)
            Tr = pyunits.convert(b.params.temperature_ref, to_units=pyunits.K)

            units = b.params.get_metadata().derived_units

            s = (
                pyunits.convert(
                    (cobj.cp_mol_ig_comp_coeff_A * log(T / Tr)
                     + cobj.cp_mol_ig_comp_coeff_B * (T - Tr)
                     + (cobj.cp_mol_ig_comp_coeff_C / 2) * (T ** 2 - Tr ** 2)
                     + (cobj.cp_mol_ig_comp_coeff_D / 3) * (T ** 3 - Tr ** 3)
                     + (cobj.cp_mol_ig_comp_coeff_E / 4) * (T ** 4 - Tr ** 4)),
                    units.ENTROPY_MOLE,
                ) + cobj.entr_mol_form_vap_comp_ref
            )

            return s

    class pressure_sat_comp:
        @staticmethod
        def build_parameters(cobj):
            cobj.pressure_sat_comp_coeff_A = Var(
                doc="Antoine A coefficient for calculating P-sat",
                units=pyunits.dimensionless
            )
            set_param_from_config(cobj, param="pressure_sat_comp_coeff", index="A")

            cobj.pressure_sat_comp_coeff_B = Var(
                doc="Antoine B coefficient for calculating P-sat",
                units=pyunits.K
            )
            set_param_from_config(cobj, param="pressure_sat_comp_coeff", index="B")

            cobj.pressure_sat_comp_coeff_C = Var(
                doc="Antoine C coefficient for calculating P-sat",
                units=pyunits.K
            )
            set_param_from_config(cobj, param="pressure_sat_comp_coeff", index="C")

        @staticmethod
        def return_expression(b, cobj, T, dT=False):
            psat = (
                    exp(
                        cobj.pressure_sat_comp_coeff_A - cobj.pressure_sat_comp_coeff_B /
                        (pyunits.convert(T, to_units=pyunits.K) + cobj.pressure_sat_comp_coeff_C))
                    ) * pyunits.Pa

            units = b.params.get_metadata().derived_units
            return pyunits.convert(psat, to_units=units.PRESSURE)
