# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

# Test stuff ------------------------------------------------------------------
from networkx.algorithms import components

def make_t1_netlist_from_graph(comps):
    t1_netlist = [comp.get_comp() for comp in comps]

    return t1_netlist

def make_graph_from_components(components):
    import faebryk as fy
    import faebryk.library.library as lib
    import faebryk.library.traits as traits

    class wrapper():
        def __init__(self, component: lib.Component) -> None:
            self.component = component
            self._setup_non_rec()

        def _setup_non_rec(self):
            import random
            c = self.component
            self.real = c.has_trait(traits.has_footprint) and c.has_trait(traits.has_footprint_pinmap)
            self.name = "COMP{}".format(random.random())
            self.value = c.get_trait(traits.has_type_description).get_type_description()
            self.properties = {}
            if self.real:
                self.properties["footprint"] = \
                    c.get_trait(traits.has_footprint).get_footprint().get_trait(
                        traits.has_kicad_footprint).get_kicad_footprint()

        def _get_comp(self):
            return {
                "name": self.name,
                "value": self.value,
                "real": self.real,
                "properties": self.properties,
                "neighbors": []
            }
        
        def get_comp(self):
            neighbors = {}
            #TODO
            #pseudo
            # for pin, interface in self.get_trait(has_footprint_pinmap).get_pin_map()
            #   for target_interface in interface.connections:
            #       if target_interface has trait[has_component]
            #           target_component = target_interface.get_trait(...).get_component()
            #           target_pinmap = target_component.get_trait(...).get_pin_map()
            #           target_pin = target_pinmap.items()[target_pinmap.values().index(target_interface)]       
            #           target_wrapped = find(i.component == target_component for i in wrapped_list) 
            #           self.neighbors[pin].append({
            #               "vertex": target_wrapped._get_comp(),
            #               "pin": target_pin
            #           })
            comp = self._get_comp()
            comp["neighbors"] = neighbors

            return comp

    wrapped_list = list(map(wrapper, components))
    for i in wrapped_list:
        i.wrapped_list = wrapped_list

    return wrapped_list


def run_experiment():
    import faebryk as fy
    import faebryk.library.library as lib
    import faebryk.library.traits as traits
    from faebryk.exporters.netlist.kicad.netlist_kicad import from_faebryk_t2_netlist
    from faebryk.exporters.netlist import make_t2_netlist_from_t1

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

    rx_hv_pullup_resistor = lib.Resistor(resistance=lib.Constant(10000))
    rx_hv_pullup_resistor.interfaces[0].connect(vbus)
    rx_hv_pullup_resistor.interfaces[1].connect(rx_level_shift_fet.drain)
    uart_hv.rx.connect(rx_level_shift_fet.drain)

    tx_lv_pullup_resistor = lib.Resistor(resistance=lib.Constant(10000))
    tx_lv_pullup_resistor.interfaces[0].connect(v3v3)
    tx_lv_pullup_resistor.interfaces[1].connect(tx_level_shift_fet.source)
    tx_level_shift_fet.gate.connect(v3v3)
    uart_lv.tx.connect(tx_level_shift_fet.source)
    #tx_level_shift_fet.source.connect(uart_lv.tx)

    rx_lv_pullup_resistor = lib.Resistor(resistance=lib.Constant(10000))
    rx_lv_pullup_resistor.interfaces[0].connect(v3v3)
    rx_lv_pullup_resistor.interfaces[1].connect(rx_level_shift_fet.source)
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
    for smd_comp in [pwrled, current_limiting_resistor, cc1_resistor, cc2_resistor]:
        smd_comp.add_trait(traits.has_defined_footprint(lib.SMDTwoPin(
            lib.SMDTwoPin.Type._0805
        )))
    
    for resistor in [current_limiting_resistor, cc1_resistor, cc2_resistor]:
        smd_comp.add_trait(traits.has_defined_footprint_pinmap(
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
            2: sensor.PM_RX,
            2: sensor.PM_TX,
        }
    ))

    # make graph
    #TODO
    components = [
        pwrled, 
        usb,
        sensor,
        fan,
        current_limiting_resistor,
        esp32,
        *pulls,
    ]

    netlist = from_faebryk_t2_netlist(
        make_t2_netlist_from_t1(
            make_t1_netlist_from_graph(
                make_graph_from_components(components)
            )
        )
    )

    print("Experiment netlist:")
    print(netlist)

    #from faebryk.exporters.netlist import render_graph
    #render_graph(make_t1_netlist_from_graph(comps))

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
