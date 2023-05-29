# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging
from typing import Iterator

logger = logging.getLogger("library")

from faebryk.library.core import Interface
from faebryk.library.traits.interface import contructable_from_interface_list


class Electrical(Interface):
    def __init__(self) -> None:
        super().__init__()

        class _contructable_from_interface_list(
            contructable_from_interface_list.impl()
        ):
            @staticmethod
            def from_interfaces(interfaces: Iterator[Electrical]) -> Electrical:
                return next(interfaces)

        self.add_trait(_contructable_from_interface_list())


class Power(Interface):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        class _IFs(Interface.InterfacesCls()):
            hv = Electrical()
            lv = Electrical()

        self.IFs = _IFs(self)

        class _contructable_from_interface_list(
            contructable_from_interface_list.impl()
        ):
            @staticmethod
            def from_interfaces(interfaces: Iterator[Electrical]) -> Power:
                p = Power()
                p.IFs.hv = next(interfaces)
                p.IFs.lv = next(interfaces)

                return p

        self.add_trait(_contructable_from_interface_list())

    def connect(self, other: Interface) -> Interface:
        # TODO feels a bit weird
        # maybe we need to look at how aggregate interfaces connect
        assert type(other) is Power, "can't connect to non power"
        for s, d in zip(self.IFs.get_all(), other.IFs.get_all()):
            s.connect(d)

        return self


class DifferentialPair(Interface):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        class _IFs(Interface.InterfacesCls()):
            p = Electrical()
            n = Electrical()

        self.IFs = _IFs(self)

    def connect(self, other: Interface) -> Interface:
        assert type(other) is DifferentialPair, "can't connect to different type"
        for s, d in zip(self.IFs.get_all(), other.IFs.get_all()):
            s.connect(d)
        return self


class USB2_0(Interface):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        class _IFs(Interface.InterfacesCls()):
            usb = DifferentialPair()
            dp = usb.IFs.p
            dn = usb.IFs.n
            gnd = Electrical()

        self.IFs = _IFs(self)

    def connect(self, other: Interface) -> Interface:
        # TODO feels a bit weird
        # maybe we need to look at how aggregate interfaces connect
        assert type(other) is USB2_0, "can't connect to non USB2_0"
        for s, d in zip(self.IFs.get_all(), other.IFs.get_all()):
            s.connect(d)

        return self


class SWD(Interface):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        class _IFs(Interface.InterfacesCls()):
            clk = Electrical()
            dio = Electrical()
            gnd = Electrical()

        self.IFs = _IFs(self)

    def connect(self, other: Interface) -> Interface:
        # TODO feels a bit weird
        # maybe we need to look at how aggregate interfaces connect
        assert type(other) is SWD, "can't connect to non SWD"
        for s, d in zip(self.IFs.get_all(), other.IFs.get_all()):
            s.connect(d)

        return self


class SPI(Interface):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        class _IFs(Interface.InterfacesCls()):
            sclk = Electrical()
            miso = Electrical()
            mosi = Electrical()
            gnd = Electrical()

        self.IFs = _IFs(self)

    def connect(self, other: Interface) -> Interface:
        # TODO feels a bit weird
        # maybe we need to look at how aggregate interfaces connect
        assert type(other) is SPI, "can't connect to non SPI"
        for s, d in zip(self.IFs.get_all(), other.IFs.get_all()):
            s.connect(d)

        return self


class QUAD_SPI(Interface):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        class _IFs(Interface.InterfacesCls()):
            sd0 = Electrical()
            sd1 = Electrical()
            sd2 = Electrical()
            sd3 = Electrical()
            sclk = Electrical()
            ss_n = Electrical()
            gnd = Electrical()

        self.IFs = _IFs(self)

    def connect(self, other: Interface) -> Interface:
        # TODO feels a bit weird
        # maybe we need to look at how aggregate interfaces connect
        assert type(other) is QUAD_SPI, "can't connect to non QUAD_SPI"
        for s, d in zip(self.IFs.get_all(), other.IFs.get_all()):
            s.connect(d)

        return self


class I2C(Interface):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        class _IFs(Interface.InterfacesCls()):
            scl = Electrical()
            sda = Electrical()
            gnd = Electrical()

        self.IFs = _IFs(self)

    def connect(self, other: Interface) -> Interface:
        # TODO feels a bit weird
        # maybe we need to look at how aggregate interfaces connect
        assert type(other) is I2C, "can't connect to non I2C"
        for s, d in zip(self.IFs.get_all(), other.IFs.get_all()):
            s.connect(d)

        return self


class UART_SIMPLE(Interface):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        class _IFs(Interface.InterfacesCls()):
            rx = Electrical()
            tx = Electrical()
            gnd = Electrical()

        self.IFs = _IFs(self)

    def connect(self, other: Interface) -> Interface:
        # TODO feels a bit weird
        # maybe we need to look at how aggregate interfaces connect
        assert type(other) is UART_SIMPLE, "can't connect to non UART_SIMPLE"
        for s, d in zip(self.IFs.get_all(), other.IFs.get_all()):
            s.connect(d)

        return self
