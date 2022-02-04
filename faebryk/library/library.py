# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

from __future__ import annotations
from enum import Enum
from typing import Iterable

from faebryk.library.core import *
from faebryk.library.traits import *
from faebryk.libs.exceptions import FaebrykException

import logging
logger = logging.getLogger("library")

# Parameter -------------------------------------------------------------------
class Constant(Parameter):
    def __init__(self, value: typing.Any) -> None:
        super().__init__()
        self.value = value
        self.add_trait(is_representable_by_single_value(
            self.value
        ))

class Range(Parameter):
    def __init__(self, value_min: typing.Any, value_max: typing.Any) -> None:
        super().__init__()
        self.min = value_min
        self.max = value_max
    
    def pick(self, value_to_check: typing.Any):
        if not self.min <= value_to_check <= self.max:
            raise FaebrykException(f"Value not in range: {value_to_check} not in [{self.min},{self.max}]")

        self.add_trait(is_representable_by_single_value(
            value_to_check
        ))

class TBD(Parameter):
    def __init__(self) -> None:
        super().__init__()
# -----------------------------------------------------------------------------

# Footprints ------------------------------------------------------------------
class DIP(Footprint):
    def __init__(self, pin_cnt: int, spacing_mm: int, long_pads: bool) -> None:
        super().__init__()

        class _has_kicad_footprint(has_kicad_footprint):
            @staticmethod
            def get_kicad_footprint() -> str:
                return \
                    "Package_DIP:DIP-{leads}_W{spacing:.2f}mm{longpads}".format(
                        leads=pin_cnt,
                        spacing=spacing_mm,
                        longpads="_LongPads" if long_pads else ""
                    )

        self.add_trait(_has_kicad_footprint())

class SMDTwoPin(Footprint):
    class Type(Enum):
        _01005 = 0
        _0201  = 1
        _0402  = 2
        _0603  = 3
        _0805  = 4
        _1206  = 5
        _1210  = 6
        _1218  = 7
        _2010  = 8
        _2512  = 9

    def __init__(self, type: Type) -> None:
        super().__init__()

        class _has_kicad_footprint(has_kicad_footprint):
            @staticmethod
            def get_kicad_footprint() -> str:
                table = {
                    self.Type._01005: "0402",
                    self.Type._0201:  "0603",
                    self.Type._0402:  "1005",
                    self.Type._0603:  "1005",
                    self.Type._0805:  "2012",
                    self.Type._1206:  "3216",
                    self.Type._1210:  "3225",
                    self.Type._1218:  "3246",
                    self.Type._2010:  "5025",
                    self.Type._2512:  "6332",
                }

                return \
                    "Resistor_SMD:R_{imperial}_{metric}Metric".format(
                        imperial=type.name[1:],
                        metric=table[type]
                    )

        self.add_trait(_has_kicad_footprint())
# ------------------------------------------------------------------------

# Interfaces ------------------------------------------------------------------
class Electrical(Interface):
    def __init__(self) -> None:
        super().__init__()

        class _can_list_interfaces(can_list_interfaces):
            @staticmethod
            def get_interfaces() -> list(Electrical):
                return [self]

        class _contructable_from_interface_list(contructable_from_interface_list):
            @staticmethod
            def from_interfaces(interfaces: Iterable(Electrical)) -> Electrical:
                return next(interfaces)

        self.add_trait(_can_list_interfaces())
        self.add_trait(_contructable_from_interface_list())

class Power(Interface):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.hv = Electrical()
        self.lv = Electrical()

        self.set_component(kwargs.get("component"))

        class _can_list_interfaces(can_list_interfaces):
            @staticmethod
            def get_interfaces() -> list(Electrical):
                return [self.hv, self.lv]

        class _contructable_from_interface_list(contructable_from_interface_list):
            @staticmethod
            def from_interfaces(interfaces: Iterable(Electrical)) -> Power:
                p = Power()
                p.hv = next(interfaces)
                p.lv = next(interfaces)

                comps = get_components_of_interfaces(p.get_trait(can_list_interfaces).get_interfaces())
                assert (len(comps) < 2 or comps[0] == comps[1])
                if len(comps) > 0:
                    p.set_component(comps[0])

                return p

        self.add_trait(_can_list_interfaces())
        self.add_trait(_contructable_from_interface_list())

        #TODO finish the trait stuff
#        self.add_trait(is_composed([self.hv, self.lv]))

<<<<<<< HEAD
    def connect(self, other: Interface):
        #TODO feels a bit weird
        # maybe we need to look at how aggregate interfaces connect
        assert(type(other) is Power), "can't connect to non power"
        for s,d in zip(
                self.get_trait(can_list_interfaces).get_interfaces(),
                other.get_trait(can_list_interfaces).get_interfaces(),
            ):
            s.connect(d)




=======
class SDIO(Interface):
    def __init__(self) -> None:
        super().__init__()
        self.SD0 = Electrical()
        self.SD1 = Electrical()
        self.SD2 = Electrical()
        self.SD3 = Electrical()
        self.CLK = Electrical()
        self.CMD = Electrical()

        class _can_list_interfaces(can_list_interfaces):
            @staticmethod
            def get_interfaces() -> list(Electrical):
                return [self.SD0, self.SD1, self.SD2, self.SD3, self.CLK, self.CMD]

        class _contructable_from_interface_list(contructable_from_interface_list):
            @staticmethod
            def from_interfaces(interfaces: Iterable(Electrical)) -> Electrical():
                i = Electrical()
                i.SD0 = next(interfaces)
                i.SD1 = next(interfaces)
                i.SD2 = next(interfaces)
                i.SD3 = next(interfaces)
                i.CLK = next(interfaces)
                i.CMD = next(interfaces)
                return i

        self.add_trait(_can_list_interfaces())
        self.add_trait(_contructable_from_interface_list())
>>>>>>> 7dbe936 (Feature: Add: Components for vindriktning)

#class I2C(Interface):
#    def __init__(self) -> None:
#        super().__init__()
#        self.sda = Electrical()
#        self.sdc = Electrical()
#        self.gnd = Electrical()
#        self.add_trait(is_composed(
#            [self.sda, self.sdc, self.gnd]
#        ))
# -----------------------------------------------------------------------------


# Links -----------------------------------------------------------------------
# -----------------------------------------------------------------------------

#class Component:
#    def __init__(self, name, pins, real):
#        self.comp = {
#            "name": name,
#            "properties": {
#            },
#            "real": real,
#            "neighbors": {pin: [] for pin in pins}
#        }
#        self.pins = pins
#
#    def connect(self, spin, other, dpin=None):
#        self.comp["neighbors"][spin].append({
#            "vertex": other.get_comp(),
#            "pin": dpin,
#        })

# META SHIT -------------------------------------------------------------------
def default_with(given, default):
    if given is not None:
        return given
    return default

def times(cnt, lamb):
    return [lamb() for _ in range(cnt)]

def unit_map(value: int, units, start=None, base=1000):
    if start is None:
        start_idx = 0
    else:
        start_idx = units.index(start)

    cur = base**((-start_idx)+1)
    ptr = 0
    while value >= cur:
        cur *= base
        ptr += 1
    form_value = integer_base(value, base=base)
    return f"{form_value}{units[ptr]}"

def integer_base(value: int, base=1000):
    while value < 1:
        value *= base
    while value >= base:
        value /= base
    return value

def get_all_interfaces(interfaces : Iterable(Interface)) -> list(Interface):
    return [
        nested for i in interfaces
            for nested in i.get_trait(can_list_interfaces).get_interfaces()
    ]

def get_components_of_interfaces(interfaces: list(Interface)) -> list(Component):
    out = [
        i.get_trait(is_part_of_component).get_component() for i in interfaces
            if i.has_trait(is_part_of_component)
    ]
    return out

# -----------------------------------------------------------------------------

# Components ------------------------------------------------------------------
class Resistor(Component):
    def _setup_traits(self):
        class _contructable_from_component(contructable_from_component):
            @staticmethod
            def from_component(comp: Component, resistance: Parameter) -> Resistor:
                assert(comp.has_trait(has_interfaces))
                interfaces = comp.get_trait(has_interfaces).get_interfaces()
                assert(len(interfaces) == 2)
                assert(len([i for i in interfaces if type(i) is not Electrical]) == 0)

                r = Resistor.__new__(Resistor)
                r._setup_resistance(resistance)
                r.interfaces = interfaces
                r.get_trait(has_interfaces).set_interface_comp(r)

                return r

        self.add_trait(has_interfaces_list(self))
        self.add_trait(_contructable_from_component())

    def _setup_interfaces(self):
        self.interfaces = times(2, Electrical)
        self.get_trait(has_interfaces).set_interface_comp(self)

    def __new__(cls, *args, **kwargs):
        self = super().__new__(cls)
        self._setup_traits()
        return self

    def __init__(self, resistance : Parameter):
        super().__init__()

        self._setup_interfaces()
        self.set_resistance(resistance)

    def set_resistance(self, resistance: Parameter):
        self.resistance = resistance

        if type(resistance) is not Constant:
            #TODO this is a bit ugly
            # it might be that there was another more abstract valid trait
            # but this challenges the whole trait overriding mechanism
            # might have to make a trait stack thats popped or so
            self.del_trait(has_type_description)
            return

        class _has_type_description(has_type_description):
            @staticmethod
            def get_type_description():
                resistance = self.resistance
                return unit_map(resistance.value, ["µΩ", "mΩ", "Ω", "KΩ", "MΩ", "GΩ"], start="Ω")
        self.add_trait(_has_type_description())

class Capacitor(Component):
    def _setup_traits(self):
        class _has_interfaces(has_interfaces):
            @staticmethod
            def get_interfaces() -> list(Interface):
                return self.interfaces

        class _contructable_from_component(contructable_from_component):
            @staticmethod
            def from_component(comp: Component, capacitance: Parameter) -> Capacitor:
                assert(comp.has_trait(has_interfaces))
                interfaces = comp.get_trait(has_interfaces).get_interfaces()
                assert(len(interfaces) == 2)
                assert(len([i for i in interfaces if type(i) is not Electrical]) == 0)

                c = Capacitor.__new__(Capacitor)
                c._setup_capacitance(capacitance)
                c.interfaces = interfaces

                return c

        self.add_trait(_has_interfaces())
        self.add_trait(_contructable_from_component())

    def _setup_interfaces(self):
        self.interfaces = [Electrical(), Electrical()]

    def __new__(cls, *args, **kwargs):
        self = super().__new__(cls)
        self._setup_traits()
        return self

    def __init__(self, capacitance : Parameter):
        super().__init__()

        self._setup_interfaces()
        self.set_capacitance(capacitance)

    def set_capacitance(self, capacitance: Parameter):
        self.capacitance = capacitance

        if type(capacitance) is not Constant:
            return

        class _has_type_description(has_type_description):
            @staticmethod
            def get_type_description():
                capacitance = self.capacitance
                return unit_map(capacitance.value, ["µF", "mF", "F", "KF", "MF", "GF"], start="µF")
        self.add_trait(_has_type_description())

class PM1006Connector(Component):
    def _setup_traits(self):
        self.add_trait(has_defined_type_description("Connector"))
        
    def _setup_interfaces(self):
        self.PM_TX = Electrical()
        self.PM_RX = Electrical()
        self.VCC_5v = Electrical()
        self.SGND = Electrical()

    def __new__(cls):
        self = super().__new__(cls)
        self._setup_traits()
        return self

    def __init__(self) -> None:
        super().__init__()
        self._setup_interfaces()

class PMFanConnector(Component):
    def _setup_traits(self):
        self.add_trait(has_defined_type_description("Connector"))
        
    def _setup_interfaces(self):
        self.VCC_FAN = Electrical()
        self.GND = Electrical()

    def __new__(cls):
        self = super().__new__(cls)
        self._setup_traits()
        return self

    def __init__(self) -> None:
        super().__init__()
        self._setup_interfaces()

class MOSFET(Component):
    def _setup_traits(self):
        self.add_trait(has_defined_type_description("Transistor_FET"))
        
    def _setup_interfaces(self):
        self.source = Electrical()
        self.gate = Electrical()
        self.drain = Electrical()

    def __new__(cls):
        self = super().__new__(cls)
        self._setup_traits()
        return self

    def __init__(self) -> None:
        super().__init__()
        self._setup_interfaces()

class USBC(Component):
    def _setup_traits(self):
        self.add_trait(has_defined_type_description("Connector_USB"))
        
    def _setup_interfaces(self):
        self.GND = Electrical()
        self.VBUS = Electrical()
        self.CC1 = Electrical()
        self.CC2 = Electrical()
        self.VBUS = Electrical()
        self.GND = Electrical()

    def __new__(cls):
        self = super().__new__(cls)
        self._setup_traits()
        return self

    def __init__(self) -> None:
        super().__init__()
        self._setup_interfaces()

class LED(Component):
    class has_calculatable_needed_series_resistance(ComponentTrait):
        @staticmethod
        def get_needed_series_resistance_ohm(input_voltage_V) -> int:
            raise NotImplemented

    def _setup_traits(self):
        class _has_interfaces(has_interfaces):
            @staticmethod
            def get_interfaces() -> list[Interface]:
                return [self.anode, self.cathode]

        self.add_trait(has_defined_type_description("LED"))
        self.add_trait(_has_interfaces())

    def _setup_interfaces(self):
        self.anode = Electrical()
        self.cathode = Electrical()
        self.get_trait(has_interfaces).set_interface_comp(self)

    def __new__(cls):
        self = super().__new__(cls)
        self._setup_traits()
        return self

    def __init__(self) -> None:
        super().__init__()
        self._setup_interfaces()

    def set_forward_parameters(self, voltage_V: Parameter, current_A: Parameter):
        if type(voltage_V) is Constant and type(current_A) is Constant:
            class _(self.has_calculatable_needed_series_resistance):
                @staticmethod
                def get_needed_series_resistance_ohm(input_voltage_V) -> int:
                    return LED.needed_series_resistance_ohm(
                        input_voltage_V,
                        voltage_V.value,
                        current_A.value
                    )
            self.add_trait(_())


    @staticmethod
    def needed_series_resistance_ohm(input_voltage_V, forward_voltage_V, forward_current_A) -> Constant:
        return Constant((input_voltage_V-forward_voltage_V)/forward_current_A)

class Switch(Component):
    def _setup_traits(self):
        self.add_trait(has_defined_type_description("SW"))
        self.add_trait(has_interfaces_list(self))

    def _setup_interfaces(self):
        self.interfaces = times(2, Electrical)
        self.get_trait(has_interfaces).set_interface_comp(self)

    def __new__(cls):
        self = super().__new__(cls)
        self._setup_traits()
        return self

    def __init__(self) -> None:
        super().__init__()
        self._setup_interfaces()

class NAND(Component):
    def _setup_traits(self):
        class _has_interfaces(has_interfaces):
            @staticmethod
            def get_interfaces():
                return get_all_interfaces([self.power, self.output, *self.inputs])

        class _constructable_from_component(contructable_from_component):
            @staticmethod
            def from_comp(comp: Component) -> NAND:
                n = NAND.__new__(NAND)
                n.__init_from_comp(comp)
                return n

        self.add_trait(_has_interfaces())
        self.add_trait(_constructable_from_component())

    def _setup_power(self):
        self.power = Power()

    def _setup_inouts(self, input_cnt):
        self.output = Electrical()
        self.inputs = times(input_cnt, Electrical)
        self._set_interface_comp()

    def _set_interface_comp(self):
        self.get_trait(has_interfaces).set_interface_comp(self)

    def __new__(cls, *args, **kwargs):
        self = super().__new__(cls)

        self._setup_traits()

        return self

    def __init__(self, input_cnt: int):
        super().__init__()

        self._setup_power()
        self._setup_inouts(input_cnt)

        self.input_cnt = input_cnt

    def __init_from_comp(self, comp: Component):
        dummy = NAND(2)
        base_cnt = len(get_all_interfaces(dummy))

        assert(comp.has_trait(has_interfaces))
        interfaces = comp.get_trait(has_interfaces).get_interfaces()
        assert(len(interfaces) >= base_cnt)
        assert(len([i for i in interfaces if type(i) is not Electrical]) == 0)

        it = iter(interfaces)

        self.power = Power().get_trait(contructable_from_interface_list).from_interfaces(it)
        self.output = Electrical().get_trait(contructable_from_interface_list).from_interfaces(it)
        self.inputs = [Electrical().get_trait(contructable_from_interface_list).from_interfaces(it) for i in n.inputs]

        self.input_cnt = len(self.inputs)
        self._set_interface_comp()



class CD4011(Component):
    class constructable_from_nands(ComponentTrait):
        @staticmethod
        def from_comp(comp: Component):
            raise NotImplemented


    def _setup_traits(self):
        class _has_interfaces(has_interfaces):
            @staticmethod
            def get_interfaces():
                return get_all_interfaces([self.power, *self.in_outs])

        class _constructable_from_component(contructable_from_component):
            @staticmethod
            def from_comp(comp: Component) -> CD4011:
                c = CD4011.__new__(CD4011)
                c._init_from_comp(comp)
                return c

        class _constructable_from_nands(self.constructable_from_nands):
            @staticmethod
            def from_nands(nands : list(NAND)) -> CD4011:
                c = CD4011.__new__(CD4011)
                c._init_from_nands(nands)
                return c


        self.add_trait(_has_interfaces())
        self.add_trait(_constructable_from_component())
        self.add_trait(_constructable_from_nands())
        self.add_trait(has_defined_type_description("cd4011"))


    def _setup_power(self):
        self.power = Power()

    def _setup_nands(self):
        self.nands = times(4, lambda: NAND(input_cnt=2))

    def _setup_inouts(self):
        nand_inout_interfaces = [i for n in self.nands for i in get_all_interfaces([n.output, *n.inputs])]
        self.in_outs = times(len(nand_inout_interfaces), Electrical)

    def _setup_internal_connections(self):
        self.get_trait(has_interfaces).set_interface_comp(self)

        self.connection_map = {}

        it = iter(self.in_outs)
        for n in self.nands:
            n.power.connect(self.power)
            target = next(it)
            target.connect(n.output)
            self.connection_map[n.output] = target

            for i in n.inputs:
                target = next(it)
                target.connect(i)
                self.connection_map[i] = target

        #TODO
        #assert(len(self.interfaces) == 14)

    def __new__(cls):
        self = super().__new__(cls)

        self._setup_traits()
        return self

    def __init__(self):
        super().__init__()

        # setup
        self._setup_power()
        self._setup_nands()
        self._setup_inouts()
        self._setup_internal_connections()

    def _init_from_comp(self, comp: Component):
        # checks
        assert(comp.has_trait(has_interfaces))
        interfaces = comp.get_trait(has_interfaces).get_interfaces()
        assert(len(interfaces) == len(self.get_trait(has_interfaces).get_interfaces()))
        assert(len([i for i in interfaces if type(i) is not Electrical]) == 0)

        it = iter(interfaces)

        # setup
        self.power = Power().get_trait(contructable_from_interface_list).from_interfaces(it)
        self._setup_nands()
        self.in_outs = [Electrical().get_trait(contructable_from_interface_list).from_interfaces(i) for i in it]
        self._setup_internal_connections()

    def _init_from_nands(self, nands : list(NAND)):
        # checks
        assert(len(nands) <= 4)
        cd_nands = list(nands)
        cd_nands += times(4-len(cd_nands), lambda: NAND(input_cnt=2))


        for nand in cd_nands:
            assert(nand.input_cnt == 2)

        # setup
        self._setup_power()
        self.nands = cd_nands
        self._setup_inouts()
        self._setup_internal_connections()


<<<<<<< HEAD

=======
class ESP32(Component):
    def _setup_traits(self):
        self.add_trait(has_defined_type_description("ESP32"))
        
    def _setup_interfaces(self):
        # Analog
        self.VDDA0 = Electrical()
        self.LNA_IN = Electrical()
        self.VDD3P3 = Electrical()
        self.SENSOR_VP = Electrical()
        # VDD3P3_RTC
        self.SENSOR_CAPP = Electrical()
        self.SENSOR_CAPN = Electrical()
        self.SENSOR_VN = Electrical()
        self.CHIP_PU = Electrical()
        self.VDET_1 = Electrical()
        self.VDET_2 = Electrical()
        self._32K_XP = Electrical()
        self._32K_XN = Electrical()
        self.GPIO25 = Electrical()
        self.GPIO26 = Electrical()
        self.GPIO27 = Electrical()
        self.MTMS = Electrical()
        self.MTDI = Electrical()
        self.VDD3P3_RTC = Electrical()
        self.MTCK = Electrical()
        self.MTDO = Electrical()
        self.GPIO2 = Electrical()
        self.GPIO0 = Electrical()
        self.GPIO4 = Electrical()
        # VDD_SDIO
        self.GPIO16 = Electrical()
        self.VDD_SDIO = Electrical()
        self.GPIO17 = Electrical()
        self.SD_DATA_2 = Electrical()
        self.SD_DATA_3 = Electrical()
        self.SD_CMD = Electrical()
        self.SD_CLK = Electrical()
        self.SD_DATA_0 = Electrical()
        self.SD_DATA_1 = Electrical()
        # VDD3P3_CPU
        self.GPIO5 = Electrical()
        self.GPIO18 = Electrical()
        self.GPIO23 = Electrical()
        self.VDD3P3_CPU = Electrical()
        self.GPIO19 = Electrical()
        self.GPIO22 = Electrical()
        self.U0RXD = Electrical()
        self.U0TXD = Electrical()
        self.GPIO21 = Electrical()
        # Analog
        self.VDDA1 = Electrical()
        self.XTAL_N = Electrical()
        self.XTAL_P = Electrical()
        self.VDDA2 = Electrical()
        self.CAP2 = Electrical()
        self.CAP1 = Electrical()
        self.GND = Electrical()

        self.interface_sdio = SDIO()
        self.interface_sdio.SD0.connect(self.SD_DATA_0)
        self.interface_sdio.SD1.connect(self.SD_DATA_1)
        self.interface_sdio.SD2.connect(self.SD_DATA_2)
        self.interface_sdio.SD3.connect(self.SD_DATA_3)
        self.interface_sdio.CLK.connect(self.SD_CLK)
        self.interface_sdio.CMD.connect(self.SD_CMD)

    def _setup_power(self):
        self.power_rtc = Power()
        self.power_cpu = Power()
        self.power_sdio = Power()
        self.power_analog = Power()

        self.power_rtc.hv.connect(self.VDD3P3_RTC)
        self.power_rtc.lv.connect(self.GND)
        
        self.power_cpu.hv.connect(self.VDD3P3_CPU)
        self.power_cpu.lv.connect(self.GND)
        
        self.power_sdio.hv.connect(self.VDD_SDIO)
        self.power_sdio.lv.connect(self.GND)
        
        self.power_analog.hv.connect(self.VDDA0)
        self.power_analog.hv.connect(self.VDDA1)
        self.power_analog.hv.connect(self.VDDA2)
        self.power_analog.lv.connect(self.GND)

    def __new__(cls):
        self = super().__new__(cls)
        self._setup_traits()
        return self

    def __init__(self) -> None:
        super().__init__()
        self._setup_interfaces()
        self._setup_power()
        
>>>>>>> 7dbe936 (Feature: Add: Components for vindriktning)
# -----------------------------------------------------------------------------
