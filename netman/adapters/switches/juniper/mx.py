# Copyright 2018 Internap.
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
from ncclient.xml_ import to_ele, new_ele
from netaddr import IPNetwork
from netman.adapters.switches.juniper.base import first, Juniper, Update, one_interface, parse_range
from netman.adapters.switches.juniper.base import first_text
from netman.adapters.switches.juniper.qfx_copper import JuniperQfxCopperCustomStrategies
from netman.core.objects.exceptions import BadVlanName, BadVlanNumber, VlanAlreadyExist, \
    UnknownVlan, IPAlreadySet, \
    UnknownIP, AccessVlanNotSet, UnknownInterface, VrrpDoesNotExistForVlan

IRB = "irb"
PREEMPT_HOLD_TIME = 60


class MxJuniper(Juniper):
    def unset_interface_access_vlan(self, interface_id):
        config = self.query(one_interface(interface_id))
        if len(config.xpath("data/configuration/interfaces/interface")) < 1:
            raise UnknownInterface(interface_id)

        if len(config.xpath("data/configuration/interfaces/interface/unit/family/bridge/vlan-id")) < 1:
            raise AccessVlanNotSet(interface_id)

        update = Update()
        update.add_interface(self.custom_strategies.interface_update(interface_id, "0", [to_ele('<vlan-id operation="delete" />')]))
        self._push(update)

    def remove_trunk_vlan(self, interface_id, vlan):
        raise NotImplementedError()

    def set_interface_state(self, interface_id, state):
        raise NotImplementedError()

    def unset_interface_state(self, interface_id):
        raise NotImplementedError()

    def set_interface_auto_negotiation_state(self, interface_id, negotiation_state):
        raise NotImplementedError()

    def unset_interface_auto_negotiation_state(self, interface_id):
        raise NotImplementedError()

    def set_interface_native_vlan(self, interface_id, vlan):
        raise NotImplementedError()

    def unset_interface_native_vlan(self, interface_id):
        raise NotImplementedError()

    def reset_interface(self, interface_id):
        raise NotImplementedError()

    def get_vlan_interfaces(self, vlan_number):
        raise NotImplementedError()

    def add_ip_to_vlan(self, vlan_number, ip_network):
        config = self.query(self.custom_strategies.one_vlan_by_vlan_id(vlan_number), one_interface_vlan(vlan_number))
        self.custom_strategies.vlan_node(config, vlan_number)

        update = Update()
        self.custom_strategies.add_update_vlan_interface(update, vlan_number, name=None)

        for addr_node in config.xpath("data/configuration/interfaces/interface/unit/family/inet/address/name"):
            address = IPNetwork(addr_node.text)
            if ip_network in address:
                raise IPAlreadySet(ip_network)

        update.add_interface(irb_address_update(vlan_number, ip_network))

        self._push(update)

    def remove_ip_from_vlan(self, vlan_number, ip_network):
        config = self.query(one_interface_vlan(vlan_number))

        if len(config.xpath("data/configuration/interfaces/interface/unit")) < 1:
            raise UnknownVlan(vlan_number)

        for addr_node in config.xpath("data/configuration/interfaces/interface/unit/family/inet/address/name"):
            address = IPNetwork(addr_node.text)
            if ip_network in address:
                update = Update()
                update.add_interface(irb_address_update(vlan_number, ip_network, operation="delete"))

                self._push(update)
                return

        raise UnknownIP(ip_network)

    def set_vlan_access_group(self, vlan_number, direction, name):
        raise NotImplementedError()

    def unset_vlan_access_group(self, vlan_number, direction):
        raise NotImplementedError()

    def set_vlan_vrf(self, vlan_number, vrf_name):
        raise NotImplementedError()

    def unset_vlan_vrf(self, vlan_number):
        raise NotImplementedError()

    def set_interface_description(self, interface_id, description):
        raise NotImplementedError()

    def unset_interface_description(self, interface_id):
        raise NotImplementedError()

    def edit_interface_spanning_tree(self, interface_id, edge=None):
        raise NotImplementedError()

    def add_bond(self, number):
        raise NotImplementedError()

    def remove_bond(self, number):
        raise NotImplementedError()

    def get_bond(self, number):
        raise NotImplementedError()

    def get_bonds(self):
        raise NotImplementedError()

    def add_interface_to_bond(self, interface, bond_number):
        raise NotImplementedError()

    def remove_interface_from_bond(self, interface):
        raise NotImplementedError()

    def set_bond_link_speed(self, number, speed):
        raise NotImplementedError()

    def set_bond_description(self, number, description):
        raise NotImplementedError()

    def unset_bond_description(self, number):
        raise NotImplementedError()

    def set_bond_native_vlan(self, number, vlan):
        raise NotImplementedError()

    def unset_bond_native_vlan(self, number):
        raise NotImplementedError()

    def edit_bond_spanning_tree(self, number, edge=None):
        raise NotImplementedError()

    def add_vrrp_group(self, vlan_number, group_id, ips=None, priority=None, hello_interval=None, dead_interval=None,
                       track_id=None, track_decrement=None):
        config = self.query(one_interface_vlan(vlan_number))

        if len(config.xpath("data/configuration/interfaces/interface/unit")) < 1:
            raise UnknownVlan(vlan_number)

        adresses = [IPNetwork(addr_node.text) for addr_node in config.xpath(
            "data/configuration/interfaces/interface/unit/family/inet/address/name")]

        parent_address = self._get_address_that_contains_all_ips(adresses, ips)

        vrrp_node = to_ele("""
            <vrrp-group>
              <name>{group_id}</name>
              <priority>{priority}</priority>
              <preempt>
                <hold-time>{preempt_hold_time}</hold-time>
              </preempt>
              <accept-data/>
              <authentication-type>simple</authentication-type>
              <authentication-key>{auth}</authentication-key>
              <track>
                <route>
                  <route_address>{tracking}</route_address>
                  <routing-instance>default</routing-instance>
                  <priority-cost>{tracking_decrement}</priority-cost>
                </route>
              </track>
            </vrrp-group>""".format(vlan_number=vlan_number,
                                    parent_address=parent_address,
                                    group_id=group_id,
                                    vip=ips[0],
                                    preempt_hold_time=PREEMPT_HOLD_TIME,
                                    priority=priority,
                                    auth="VLAN{}".format(vlan_number),
                                    tracking=track_id,
                                    tracking_decrement=track_decrement))

        for ip in ips:
            vrrp_node.append(to_ele("<virtual-address>{}</virtual-address>".format(ip)))

        update = Update()
        update.add_interface(irb_address_update(vlan_number, parent_address, children=[vrrp_node]))

        self._push(update)

    def _get_address_that_contains_all_ips(self, subnets, ips):
        def subnet_contains_all_ips(ips, subnet):
            return all(ip in subnet for ip in ips)

        subnet_found = None
        for subnet in subnets:
            if subnet_contains_all_ips(ips, subnet):
                subnet_found = subnet

        if not subnet_found:
            raise UnknownIP(",".join(map(str, ips)))

        return subnet_found

    def remove_vrrp_group(self, vlan_id, group_id):
        config = self.query(one_interface_vlan(vlan_id))

        if len(config.xpath("data/configuration/interfaces/interface/unit")) < 1:
            raise UnknownVlan(vlan_id)

        address_node = first(config.xpath("data/configuration/interfaces/interface/unit/family"
                                          "/inet/address/vrrp-group/name[text()=\"{}\"]/../..".format(group_id)))

        if address_node is None:
            raise VrrpDoesNotExistForVlan(vlan=vlan_id, vrrp_group_id=group_id)

        vrrp_node = to_ele("""
            <vrrp-group operation="delete">
              <name>{group_id}</name>
            </vrrp-group>""".format(group_id=group_id))

        update = Update()
        update.add_interface(irb_address_update(vlan_id, first_text(address_node.xpath("name")), children=[vrrp_node]))

        self._push(update)

    def add_dhcp_relay_server(self, vlan_number, ip_address):
        raise NotImplementedError()

    def remove_dhcp_relay_server(self, vlan_number, ip_address):
        raise NotImplementedError()

    def set_interface_lldp_state(self, interface_id, enabled):
        raise NotImplementedError()

    def set_vlan_arp_routing_state(self, vlan_number, state):
        raise NotImplementedError()

    def set_vlan_icmp_redirects_state(self, vlan_number, state):
        raise NotImplementedError()

    def set_vlan_unicast_rpf_mode(self, vlan_number, mode):
        raise NotImplementedError()

    def unset_vlan_unicast_rpf_mode(self, vlan_number):
        raise NotImplementedError()

    def get_versions(self):
        raise NotImplementedError()

    def set_interface_mtu(self, interface_id, size):
        raise NotImplementedError()

    def unset_interface_mtu(self, interface_id):
        raise NotImplementedError()

    def set_bond_mtu(self, number, size):
        raise NotImplementedError()

    def unset_bond_mtu(self, number):
        raise NotImplementedError()


def netconf(switch_descriptor):
    return MxJuniper(switch_descriptor, custom_strategies=JuniperMXCustomStrategies())


class JuniperMXCustomStrategies(JuniperQfxCopperCustomStrategies):
    def get_port_mode_node_in_inteface_node(self, interface_node):
        return interface_node.xpath("unit/family/bridge/interface-mode")

    def get_vlan_member_update_element(self, vlan):
        return to_ele("<vlan-id-list>{}</vlan-id-list>".format(vlan))

    def add_update_vlans(self, update, number, name):
        update.add_vlan(self.vlan_update(number, name), "bridge-domains")

    def add_update_vlan_interface(self, update, number, name):
        update.add_vlan(self.vlan_interface_update(number, name), "bridge-domains")

    def remove_update_vlans(self, update, vlan_name):
        update.add_vlan(self.vlan_removal(vlan_name), "bridge-domains")

    def all_vlans(self):
        return new_ele("bridge-domains")

    def one_vlan_by_vlan_id(self, vlan_id):
        def m():
            return to_ele("""
                <bridge-domains>
                    <domain>
                        <vlan-id>{}</vlan-id>
                    </domain>
                </bridge-domains>
            """.format(vlan_id))

        return m

    def vlan_update(self, number, description):
        content = to_ele("""
            <domain>
                <name>VLAN{0}</name>
                <vlan-id>{0}</vlan-id>
            </domain>
        """.format(number))

        if description is not None:
            content.append(to_ele("<description>{}</description>".format(description)))
        return content

    def vlan_interface_update(self, vlan_id, description):
        vlan_node = self.vlan_update(vlan_id, description)
        vlan_node.append(to_ele("<routing-interface>irb.{}</routing-interface>".format(vlan_id)))
        return vlan_node

    def vlan_removal(self, name):
        return to_ele("""
        <domain operation="delete">
            <name>{}</name>
        </domain>""".format(name))

    def vlan_nodes(self, config):
        return config.xpath("data/configuration/bridge-domains/domain")

    def vlan_node(self, config, number):
        vlan_node = first(config.xpath("data/configuration/bridge-domains/domain/vlan-id[text()=\"{}\"]/.."
                                       .format(number)))

        if vlan_node is None:
            raise UnknownVlan(number)
        return vlan_node

    def manage_update_vlan_exception(self, message, number):
        if "being used by" in message:
            raise VlanAlreadyExist(number)
        elif "not within range" in message:
            if message.startswith("Value"):
                raise BadVlanNumber()
        elif "Must be a string" in message:
            raise BadVlanName()

    def interface_update(self, name, unit, attributes=None, vlan_members=None):
        content = to_ele("""
            <interface>
                <name>{interface}</name>
                <unit>
                    <name>{unit}</name>
                    <family>
                        <bridge>
                        </bridge>
                    </family>
                </unit>
            </interface>
            """.format(interface=name, unit=unit))
        bridge = first(content.xpath("//bridge"))

        for attribute in (attributes if attributes is not None else []):
            bridge.append(attribute)

        if vlan_members:
            for attribute in vlan_members:
                bridge.append(attribute)

        return content

    def get_l3_interface(self, vlan_node):
        if_name_node = first(vlan_node.xpath("routing-interface"))
        if if_name_node is not None:
            return if_name_node.text.split(".")
        else:
            return None, None

    def list_vlan_members(self, interface_node, config):
        vlans = set()

        vlan_id_list = interface_node.xpath("unit/family/bridge/vlan-id-list") + interface_node.xpath("unit/family/bridge/vlan-id")

        for members in vlan_id_list:
            vlans = vlans.union(parse_range(members.text))

        return sorted(vlans)

    def update_vlan_members(self, interface_node, vlan_members, vlan):
        if interface_node is not None:
            for members in interface_node.xpath("unit/family/bridge/vlan-id"):
                vlan_members.append(to_ele('<vlan-id operation="delete">{}</vlan-id>'.format(members.text)))
        vlan_members.append(to_ele("<vlan-id>{}</vlan-id>".format(vlan)))


def one_interface_vlan(vlan_number):
    def m():
        return to_ele("""
            <interfaces>
                <interface>
                    <name>{interface}</name>
                    <unit>
                        <name>{unit}</name>
                    </unit>
                </interface>
            </interfaces>
        """.format(interface=IRB, unit=vlan_number))

    return m


def irb_address_update(vlan_number, ip_network, operation=None, children=None):
    content = to_ele("""
        <interface>
            <name>irb</name>
            <unit>
              <name>{vlan_number}</name>
              <family>
                <inet>
                  <address{operation}>
                    <name>{ip_network}</name>
                  </address>
                </inet>
              </family>
            </unit>
        </interface>""".format(vlan_number=vlan_number,
                               ip_network=ip_network,
                               operation=' operation="{}"'.format(operation) if operation else ""))

    if children is not None:
        address = first(content.xpath("//address"))
        for child in children:
            address.append(child)

    return content
