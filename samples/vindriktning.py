# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

# Test stuff ------------------------------------------------------------------
from this import d
from networkx.algorithms import components

def make_t1_netlist_from_graph(comps):
    t1_netlist = [comp.get_comp() for comp in comps]

    return t1_netlist

def make_graph_from_components(components):
    import faebryk as fy
    import faebryk.library.library as lib
    import faebryk.library.traits as traits
    from faebryk.libs.exceptions import FaebrykException

    class wrapper():
        def __init__(self, component: lib.Component) -> None:
            self.component = component
            self._setup_non_rec()

        def _setup_non_rec(self):
            import random
            c = self.component
            self.real = c.has_trait(traits.has_footprint) and c.has_trait(traits.has_footprint_pinmap)
            self.properties = {}
            self.neighbors = {}
            if self.real:
                self.value = c.get_trait(traits.has_type_description).get_type_description()
                self.properties["footprint"] = \
                    c.get_trait(traits.has_footprint).get_footprint().get_trait(
                        traits.has_kicad_footprint).get_kicad_footprint()
            self.name = "COMP[{}:{}]@{:08X}".format(type(self.component).__name__, self.value if self.real else "virt", int(random.random()*2**32))
            self._comp = {}
            self._update_comp()

        def _update_comp(self):
            self._comp.update({
                "name": self.name,
                "real": self.real,
                "properties": self.properties,
                "neighbors": self.neighbors
            })
            if self.real:
                self._comp["value"] = self.value

        def _get_comp(self):
            return self._comp

        def get_comp(self):
            # only executed once
            neighbors = {}
            for pin, interface in self.component.get_trait(traits.has_footprint_pinmap).get_pin_map().items():
                neighbors[pin] = []
                for target_interface in interface.connections:
                    if target_interface.has_trait(traits.is_part_of_component):
                        target_component = target_interface.get_trait(traits.is_part_of_component).get_component()
                        target_pinmap = target_component.get_trait(traits.has_footprint_pinmap).get_pin_map()
                        target_pin = list(target_pinmap.items())[list(target_pinmap.values()).index(target_interface)][0]
                        try:
                            target_wrapped = [i for i in wrapped_list if i.component == target_component][0]
                        except IndexError:
                            raise FaebrykException("Discovered associated component not in component list:", target_component)

                        neighbors[pin].append({
                          "vertex": target_wrapped._get_comp(),
                          "pin": target_pin
                        })
                    else:
                        print("Warning: {comp} pin {pin} is connected to interface without component".format(
                            comp=self.name,
                            #intf=target_interface,
                            pin=pin,
                        ))

            self.neighbors = neighbors
            self._update_comp()

            return self._get_comp()

    wrapped_list = list(map(wrapper, components))
    for i in wrapped_list:
        i.wrapped_list = wrapped_list

    print("Making graph from components:\n\t{}".format("\n\t".join(map(str, components))))

    return wrapped_list


def run_experiment():
    import faebryk as fy
    import faebryk.library.library as lib
    import faebryk.library.traits as traits
    from faebryk.exporters.netlist.kicad.netlist_kicad import from_faebryk_t2_netlist
    from faebryk.exporters.netlist import make_t2_netlist_from_t1

    class _has_interfaces(traits.has_interfaces):
        def __init__(self, interfaces) -> None:
            super().__init__()
            self.interfaces = interfaces

        def get_interfaces(self):
            return lib.get_all_interfaces(self.interfaces)

    class _has_footprint_pinmap(traits.has_footprint_pinmap):
        def __init__(self, comp) -> None:
            super().__init__()
            self.comp = comp

        def get_pin_map(self):
            ifs = self.comp.get_trait(traits.has_interfaces).get_interfaces()
            return {k+1:v for k,v in enumerate(ifs)}

    # levels
    #high = lib.Electrical()
    #low = lib.Electrical()

    # power
    pwr_vbus = lib.Component()
    pwr_vbus.power = lib.Power()
    gnd = pwr_vbus.power.lv
    vbus = pwr_vbus.power.hv

    pwr_3v3 = lib.Component()
    pwr_3v3.power = lib.Power()
    v3v3 = pwr_3v3.power.hv
    pwr_3v3.power.lv.connect(gnd)

    # usb
    usb = lib.USBC()
    usb.VBUS.connect(vbus)
    usb.GND.connect(gnd)

    # usb pd
    cc1_resistor = lib.Resistor(resistance=lib.Constant(5100))
    cc2_resistor = lib.Resistor(resistance=lib.Constant(5100))
    usb.CC1.connect(cc1_resistor.interfaces[0])
    usb.CC2.connect(cc2_resistor.interfaces[0])
    cc1_resistor.interfaces[1].connect(gnd)
    cc2_resistor.interfaces[1].connect(gnd)
    
    # PM1006 sensor + UART 5v + fan
    fan = lib.PMFanConnector()
    fan.VCC_FAN.connect(vbus)
    sensor = lib.PM1006Connector()
    sensor.VCC_5v.connect(vbus)
    sensor.SGND.connect(gnd)

    uart_hv = lib.UART()
    uart_hv.rx.connect(sensor.PM_RX)
    uart_hv.tx.connect(sensor.PM_TX)

    # fan control
    fanfet = lib.MOSFET()
    fanfet.drain.connect(gnd)
    fanfet.source.connect(fan.GND)

    fanfet_puldown_resistor = lib.Resistor(resistance=lib.Constant(10000))
    fanfet_puldown_resistor.interfaces[1].connect(gnd)
    fanfet.gate.connect(fanfet_puldown_resistor.interfaces[0])

    # power indicator
    pwrled = lib.LED()
    pwrled.anode.connect(vbus)
    current_limiting_resistor = lib.Resistor(resistance=lib.TBD())

    # led current limit
    pwrled.cathode.connect(current_limiting_resistor.interfaces[0])
    current_limiting_resistor.interfaces[1].connect(gnd)

    decouplingcap = lib.Capacitor(capacitance=lib.Constant(1))
    decouplingcap.interfaces[0].connect(vbus)
    decouplingcap.interfaces[1].connect(gnd)

    # ESP32
    esp32 = lib.ESP32()
    esp32.power_rtc.connect(pwr_3v3.power)
    esp32.power_cpu.connect(pwr_3v3.power)
    esp32.power_analog.connect(pwr_3v3.power)
    esp32.GPIO0.connect(gnd)
    
    uart_lv = lib.UART()
    uart_lv.rx.connect(esp32.interface_UART0.rx)
    uart_lv.tx.connect(esp32.interface_UART0.tx)

    # UART level shifter
    tx_level_shift_fet = lib.MOSFET()
    rx_level_shift_fet = lib.MOSFET()

    class Pull(lib.Resistor):
        def __init__(self, line, target, resistance):
            super().__init__(resistance)
            self.interfaces[0].connect(line)
            self.interfaces[1].connect(target)

    pulls = [
        Pull(tx_level_shift_fet.drain,  vbus, resistance=lib.Constant(10000)),
        Pull(rx_level_shift_fet.drain,  vbus, resistance=lib.Constant(10000)),
        Pull(tx_level_shift_fet.source, v3v3, resistance=lib.Constant(10000)),
        Pull(rx_level_shift_fet.source, v3v3, resistance=lib.Constant(10000)),
    ]

    #tx_hv_pullup_resistor = Pull(vbus, tx_level_shift_fet.drain, resistance=lib.Constant(10000))
    #tx_hv_pullup_resistor = lib.Resistor(resistance=lib.Constant(10000))
    #tx_hv_pullup_resistor.interfaces[0].connect(vbus)
    #tx_hv_pullup_resistor.interfaces[1].connect(tx_level_shift_fet.drain)
    uart_hv.tx.connect(tx_level_shift_fet.drain)

    #rx_hv_pullup_resistor = lib.Resistor(resistance=lib.Constant(10000))
    #rx_hv_pullup_resistor.interfaces[0].connect(vbus)
    #rx_hv_pullup_resistor.interfaces[1].connect(rx_level_shift_fet.drain)
    uart_hv.rx.connect(rx_level_shift_fet.drain)

    #tx_lv_pullup_resistor = lib.Resistor(resistance=lib.Constant(10000))
    #tx_lv_pullup_resistor.interfaces[0].connect(v3v3)
    #tx_lv_pullup_resistor.interfaces[1].connect(tx_level_shift_fet.source)
    tx_level_shift_fet.gate.connect(v3v3)
    uart_lv.tx.connect(tx_level_shift_fet.source)
    #tx_level_shift_fet.source.connect(uart_lv.tx)

    #rx_lv_pullup_resistor = lib.Resistor(resistance=lib.Constant(10000))
    #rx_lv_pullup_resistor.interfaces[0].connect(v3v3)
    #rx_lv_pullup_resistor.interfaces[1].connect(rx_level_shift_fet.source)
    rx_level_shift_fet.gate.connect(v3v3)
    uart_lv.rx.connect(rx_level_shift_fet.source)

    # parametrizing
    pwr_vbus.voltage = 5
    pwrled.set_forward_parameters(
        voltage_V=lib.Constant(2.4),
        current_A=lib.Constant(0.020)
    )
    current_limiting_resistor.set_resistance(pwrled.get_trait(lib.LED.has_calculatable_needed_series_resistance).get_needed_series_resistance_ohm(pwr_vbus.voltage))

    # packaging
    for smd_comp in [pwrled, current_limiting_resistor, cc1_resistor, cc2_resistor, *pulls]:
        smd_comp.add_trait(traits.has_defined_footprint(lib.SMDTwoPin(
            lib.SMDTwoPin.Type._0805
        )))
    
    for resistor in [current_limiting_resistor, cc1_resistor, cc2_resistor, *pulls]:
        resistor.add_trait(traits.has_defined_footprint_pinmap(
            {
                1: resistor.interfaces[0],
                2: resistor.interfaces[1],
            }
        ))
    pwrled.add_trait(traits.has_defined_footprint_pinmap(
        {
            1: pwrled.anode,
            2: pwrled.cathode,
        }
    )) 

    tx_level_shift_fet_fp = lib.Footprint()
    tx_level_shift_fet_fp.add_trait(lib.has_kicad_manual_footprint("Package_TO_SOT_SMD:PQFN_8x8"))
    tx_level_shift_fet.add_trait(traits.has_defined_footprint(tx_level_shift_fet_fp))
    tx_level_shift_fet.add_trait(traits.has_defined_footprint_pinmap(
        {
            1: tx_level_shift_fet.source,
            2: tx_level_shift_fet.gate,
            3: tx_level_shift_fet.drain,
        }
    ))
    
    rx_level_shift_fet_fp = lib.Footprint()
    rx_level_shift_fet_fp.add_trait(lib.has_kicad_manual_footprint("Package_TO_SOT_SMD:PQFN_8x8"))
    rx_level_shift_fet.add_trait(traits.has_defined_footprint(tx_level_shift_fet_fp))
    rx_level_shift_fet.add_trait(traits.has_defined_footprint_pinmap(
        {
            1: rx_level_shift_fet.source,
            2: rx_level_shift_fet.gate,
            3: rx_level_shift_fet.drain,
        }
    ))

    usb_fp = lib.Footprint()
    usb_fp.add_trait(lib.has_kicad_manual_footprint("Mooie_USB_Connector_6p_vertical"))
    usb.add_trait(traits.has_defined_footprint(usb_fp))
    usb.add_trait(traits.has_defined_footprint_pinmap(
        {
            1: usb.GND,
            2: usb.VBUS,
            3: usb.CC2,
            4: usb.CC1,
            5: usb.VBUS,
            6: usb.GND,
        }
    ))
    
    fan_fp = lib.Footprint()
    fan_fp.add_trait(lib.has_kicad_manual_footprint("Mooie_FAN_Connector_2p_vertical"))
    fan.add_trait(traits.has_defined_footprint(fan_fp))
    fan.add_trait(traits.has_defined_footprint_pinmap(
        {
            1: fan.GND,
            2: fan.VCC_FAN,
        }
    ))

    sensor_fp = lib.Footprint()
    sensor_fp.add_trait(lib.has_kicad_manual_footprint("Mooie_Sensor_Connector_4p_vertical"))
    sensor.add_trait(traits.has_defined_footprint(sensor_fp))
    sensor.add_trait(traits.has_defined_footprint_pinmap(
        {
            1: sensor.SGND,
            2: sensor.VCC_5v,
            3: sensor.PM_RX,
            4: sensor.PM_TX,
        }
    ))

    esp32_fp = lib.Footprint()
    esp32_fp.add_trait(lib.has_kicad_manual_footprint("Mooie_ESP32"))
    esp32.add_trait(traits.has_defined_footprint(esp32_fp))
    esp32.add_trait(traits.has_defined_footprint_pinmap(
        {
            # Analog
            1: esp32.VDDA0,
            2: esp32.LNA_IN,
            3: esp32.VDD3P3,
            4: esp32.SENSOR_VP,
            # VDD3P3_RTC
            5: esp32.SENSOR_CAPP,
            6: esp32.SENSOR_CAPN,
            7: esp32.SENSOR_VN,
            8: esp32.CHIP_PU,
            9: esp32.VDET_1,
            10: esp32.VDET_2,
            11: esp32._32K_XP,
            12: esp32._32K_XN,
            13: esp32.GPIO25,
            14: esp32.GPIO26,
            15: esp32.GPIO27,
            16: esp32.MTMS,
            17: esp32.MTDI,
            18: esp32.VDD3P3_RTC,
            19: esp32.MTCK,
            10: esp32.MTDO,
            21: esp32.GPIO2,
            22: esp32.GPIO0,
            23: esp32.GPIO4,
            # VDD_SDIO
            24: esp32.GPIO16,
            25: esp32.VDD_SDIO,
            26: esp32.GPIO17,
            27: esp32.SD_DATA_2,
            28: esp32.SD_DATA_3,
            29: esp32.SD_CMD,
            30: esp32.SD_CLK,
            31: esp32.SD_DATA_0,
            32: esp32.SD_DATA_1,
            # VDD3P3_CPU
            33: esp32.GPIO5,
            34: esp32.GPIO18,
            35: esp32.GPIO23,
            36: esp32.VDD3P3_CPU,
            37: esp32.GPIO19,
            38: esp32.GPIO22,
            39: esp32.U0RXD,
            40: esp32.U0TXD,
            41: esp32.GPIO21,
            # Analog
            42: esp32.VDDA1,
            43: esp32.XTAL_N,
            44: esp32.XTAL_P,
            45: esp32.VDDA2,
            46: esp32.CAP2,
            47: esp32.CAP1,
            48: esp32.GND,
        }
    ))

    #TODO: remove, just compensation for old graph
    _extra_comps = []
    for c in [pwr_vbus, pwr_3v3]:
        c.add_trait(_has_interfaces([c.power]))
        c.get_trait(traits.has_interfaces).set_interface_comp(c)
        c.add_trait(_has_footprint_pinmap(c))
        _extra_comps.append(c)
    
    for i in [uart_lv, uart_hv]:
        c = lib.Component()
        c.intf = i
        c.add_trait(_has_interfaces([i]))
        c.get_trait(traits.has_interfaces).set_interface_comp(c)
        c.add_trait(_has_footprint_pinmap(c))
        _extra_comps.append(c)

    # make graph
    components = [
        pwrled, 
        usb,
        sensor,
        fan,
        cc1_resistor,
        cc2_resistor,
        current_limiting_resistor,
        tx_level_shift_fet,
        rx_level_shift_fet,
        esp32,
        *pulls,
        *_extra_comps,
    ]

    t1_ = make_t1_netlist_from_graph(
            make_graph_from_components(components)
        )

    netlist = from_faebryk_t2_netlist(
        make_t2_netlist_from_t1(
            t1_
        )
    )

    print("Experiment netlist:")
    print(netlist)

    from faebryk.exporters.netlist import render_graph
    render_graph(t1_, write_to_file=True)

import sys
import logging

def main(argc, argv, argi):
    logging.basicConfig(level=logging.INFO)

    print("Running experiment")
    run_experiment()

if __name__ == "__main__":
    import os
    import sys
    root = os.path.join(os.path.dirname(__file__), '..')
    sys.path.append(root)
    main(len(sys.argv), sys.argv, iter(sys.argv))
