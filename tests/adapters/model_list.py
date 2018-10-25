# Copyright 2015 Internap.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from fake_switches.arista.arista_core import AristaSwitchCore
from fake_switches.brocade.brocade_core import BrocadeSwitchCore
from fake_switches.cisco.cisco_core import CiscoSwitchCore
from fake_switches.cisco6500.cisco_core import Cisco6500SwitchCore
from fake_switches.dell.dell_core import DellSwitchCore
from fake_switches.dell10g.dell_core import Dell10GSwitchCore
from fake_switches.juniper.juniper_core import JuniperSwitchCore
from fake_switches.juniper_mx.juniper_mx_core import JuniperMXSwitchCore
from fake_switches.juniper_qfx_copper.juniper_qfx_copper_core import JuniperQfxCopperSwitchCore
from fake_switches.transports.ssh_service import SwitchSshService
from fake_switches.switch_configuration import Port, AggregatedPort
from fake_switches.transports.telnet_service import SwitchTelnetService
from fake_switches.transports.http_service import SwitchHttpService

from netman.core.objects.switch_descriptor import SwitchDescriptor

available_models = [
    {
        "switch_descriptor": SwitchDescriptor(
            model="cisco",
            hostname="127.0.0.1",
            port=11002,
            username="root",
            password="root",
        ),
        "test_port_name": "FastEthernet0/3",
        "test_vrrp_track_id": "101",
        "core_class": CiscoSwitchCore,
        "service_class": SwitchSshService,
        "ports": [
            Port("FastEthernet0/1"),
            Port("FastEthernet0/2"),
            Port("FastEthernet0/3"),
            Port("FastEthernet0/4"),
        ]
    }
]
