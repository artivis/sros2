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
from ros2cli.node.direct import DirectNode

from sros2.verb import VerbExtension

POLICY_FILE_NOT_FOUND = 'Package policy file not found'

Event = namedtuple('Event',
                   ('node_name', 'permission_type', 'rule_type', 'expression'))


def getFQN(node_name, expression):
    """Return an expression's fully qualified name."""
    fqn = expression
    # Expression name is already fully qualified
    if expression.startswith('/'):
        fqn = expression
    # Fully qualified with uri
    elif expression.startswith('rostopic://'):
        fqn = '/' + expression[len('rostopic://'):]
    # Private name
    elif expression.startswith('~'):
        fqn = node_name.fqn + '/' + expression[len('~'):]
    # Relative or base name
    else:
        fqn = node_name.ns + '/' + expression
    return fqn


class EventPermission:
    ALLOW = 'ALLOW'
    DENY = 'DENY'
    NOT_SPECIFIED = 'NOT_SPECIFIED'

    @staticmethod
    def reduce(rule_qualifiers):
        if EventPermission.DENY in rule_qualifiers:
            return EventPermission.DENY
        if EventPermission.ALLOW in rule_qualifiers:
            return EventPermission.ALLOW
        else:
            return EventPermission.NOT_SPECIFIED


def getEventPermissionForProfile(profile, event):
    permission_groups = profile.findall(
            path='{permission_type}s[@{rule_type}]'.format(
                permission_type=event.permission_type,
                rule_type=event.rule_type))
    rule_qualifiers = set()
    for permission_group in permission_groups:
        expression_in_group = False
        for elem in permission_group:
            if getFQN(event.node_name, elem.text) == getFQN(event.node_name,
                                                            event.expression):
                expression_in_group = True
                break
        if expression_in_group:
            rule_qualifiers.add(permission_group.attrib[event.rule_type])
    return EventPermission.reduce(rule_qualifiers)


class AmendPolicyVerb(VerbExtension):
    """Interactively add missing permissions to a permission file."""

    def __init__(self):
        self.event_cache = []
        self.profile = None

    def add_arguments(self, parser, cli_name):
        arg = parser.add_argument(
            'policy_file_path', help='path of the policy xml file')
        arg.completer = FilesCompleter(
            allowednames=('xml'), directories=False)
        parser.add_argument(
            '--time-out', '-t',
            default=int(9999), type=int,
            help='a duration for monitoring the events (seconds)')

    def getEvents(self):
        return ['Foo', 'Bar', 'Baz']

    def getPolicyEventStatus(self, policy, event):
        # Find all profiles for the node in the event
        profiles = policy.findall(
            path='profiles/profile[@ns="{ns}"][@node="{node}"]'.format(
                ns=event.node_name.ns,
                node=event.node_name.node))

        event_permissions =
        [getEventPermissionForProfile(p, event) for p in profiles]

        return EventPermission.reduce(event_permissions)

    def filterEvents(self, events):

        not_cached_events = list(set(events).difference(
                                self.event_cache))

        filtered_events = []
        for not_cached_event in not_cached_events:
            if getEventPermissionForProfile(self.profile, not_cached_event) ==
            EventPermission.ALLOW:
                keepCached(not_cached_event)
            else:
                filtered_events.append(not_cached_event)

        return not_cached_event

    def addPermission(self, event):
        pass

    def keepCached(self, event):
        self.event_cache.append(event)

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

        time_point_final = node.get_clock().now() +
        Duration(seconds=args.time_out)

        if not os.path.isfile(policy_file_path):
            return POLICY_FILE_NOT_FOUND

        self.profile = etree.parse(policy_file_path)

        try:
            while (node._clock.now() < time_point_final):
                print('Scanning for events...', end='\r')

                unregistered_events = self.getEvents()

                filtered_unregistered_events =
                filterEvents(unregistered_events)

                for unregistered_event in filtered_unregistered_events:
                    self.promptUserAboutPermission(unregistered_event)

                # print(node._clock.now(), ' < ', time_point_final)
                # TODO(artivis) use rate once available
                time.sleep(0.25)
        except KeyboardInterrupt:
            print('done.')
