# Copyright 2016-2017 Open Source Robotics Foundation, Inc.
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

import os
import time
from collections import namedtuple
from enum import Enum

try:
    from argcomplete.completers import DirectoriesCompleter
except ImportError:
    def DirectoriesCompleter():
        return None
try:
    from argcomplete.completers import FilesCompleter
except ImportError:
    def FilesCompleter(*, allowednames, directories):
        return None

from lxml import etree

from rclpy.duration import Duration
from rclpy.time import Time
from ros2cli.node.direct import DirectNode
from ros2cli.node.strategy import NodeStrategy

from sros2.api import (
    get_node_names,
    get_publisher_info,
    get_service_info,
    get_subscriber_info
)

from sros2.policy import (
    dump_policy,
    load_policy,
    POLICY_VERSION,
)

from sros2.verb import VerbExtension

Event = namedtuple('Event', ('node_name', 'permission_type', 'rule_type', 'expression'))

"""
Returns an expression's fully qualified name
"""
def getFQN(node_name, expression):
    fqn = ''
    #Expression name is already fully qualified
    if expression.startswith('/') or expression.startswith('rostopic://'):
        fqn = expression;
    #Private name
    elif expression.startswith('~'):
        fqn = node_name.fqn + '/' + expression[len('~'):]
    #Relative or base name
    else:
        fqn = node_name.ns + '/' +  expression
    return fqn

class EventPermission(Enum):
    ALLOW = 'ALLOW'
    DENY = 'DENY'
    NOT_ALLOWED = 'NOT_ALLOWED'
"""
def eventPermissionForProfile(profile, event):
    path='{permission_type}s[@{rule_type}="{rule_qualifier}"]'.format(
                permission_type=event.permission_type,
                rule_type=event.rule_type)
"""


class AmendPolicyVerb(VerbExtension):
    """Interactively add missing permissions to a permission file."""

    def __init__(self):
        self.unregistered_event_cache = []

    def add_arguments(self, parser, cli_name):
        arg = parser.add_argument(
            'POLICY_FILE_PATH', help='path of the policy xml file')
        arg.completer = FilesCompleter(
            allowednames=('xml'), directories=False)
        parser.add_argument(
            '--time-out', '-t',
            default=int(9999), type=int,
            help='a duration for monitoring the events (seconds)')
        parser.add_argument(
            '--rate', '-r',
            default=float(0.25), type=float,
            help='the rate to re-run the monitor (seconds)')


    def getEvents(self):
        pass

    def getPolicyEventStatus(self, event):
        pass

    def addPermission(self, event):
        pass

    def keepCached(self, event):
        self.unregistered_event_cache.append(event)

    def promptUserAboutPermission(self, event):
        usr_input = None
        while usr_input not in ['Y', 'y', 'N', 'n', '']:
            print('Event: ', event)
            usr_input = input('Do you want to add this event '
                              'to the permission list? (Y/n) : ')

            if usr_input not in ['Y', 'y', 'N', 'n', '']:
                print("Unknown command '", usr_input, "'.")
                print('Please try again.\n')

        if usr_input in ['Y', 'y', '']:
            self.addPermission(event)
            print('Permission granted !')
        elif usr_input in ['N', 'n']:
            print('Permission denied !')

        self.keepCached(event)

        print('\n')

    def main(self, *, args):
        node = DirectNode(args)

        time_point_final = node.get_clock().now() + \
            Duration(seconds=args.time_out)

        try:
            while (node._clock.now() < time_point_final):
                print('Scanning for events...', end='\r')

                unregistered_events = ['Foo', 'Bar']  # get_unregistered_events

                filtered_unregistered_events = list(
                    set(unregistered_events).difference(
                        self.unregistered_event_cache))

                for unregistered_event in filtered_unregistered_events:
                    self.promptUserAboutPermission(unregistered_event)

                # print(node._clock.now(), ' < ', time_point_final)
                # TODO(artivis) use rate once available
                time.sleep(args.rate)
        except KeyboardInterrupt:
            print('done.')
