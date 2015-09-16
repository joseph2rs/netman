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

import threading

from fake_switches.ssh_service import SwitchSshService
from fake_switches.switch_configuration import SwitchConfiguration


class ThreadedReactor(threading.Thread):

    _threaded_reactor = None

    @classmethod
    def start_reactor(cls, models):
        cls._threaded_reactor = ThreadedReactor()

        for specs in models:

            switch_config = SwitchConfiguration(
                ip=specs["hostname"],
                name="my_switch",
                privileged_passwords=[specs["password"]],
                ports=specs["ports"])

            SwitchSshService(
                specs["hostname"],
                ssh_port=specs["port"],
                switch_core=specs["core_class"](switch_config),
                users={specs["username"]: specs["password"]}
            ).hook_to_reactor(cls._threaded_reactor.reactor)

        cls._threaded_reactor.start()

    @classmethod
    def stop_reactor(cls):
        cls._threaded_reactor.stop()

    def __init__(self, *args, **kwargs):
        threading.Thread.__init__(self, *args, **kwargs)
        from twisted.internet import reactor
        self.reactor = reactor

    def run(self):
        self.reactor.run(installSignalHandlers=False)

    def stop(self):
        self.reactor.callFromThread(self.reactor.stop)
