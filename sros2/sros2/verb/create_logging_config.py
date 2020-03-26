# Copyright 2020 Canonical Ltd.
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

try:
    from argcomplete.completers import DirectoriesCompleter
except ImportError:
    def DirectoriesCompleter():
        return None

from sros2.api import create_logging_config
from sros2.verb import VerbExtension

from string import Template


CONFIG = """
<?xml version='1.0' encoding='UTF-8'?>
<security_log version='1'>
    <file>$absolute_path</file>
    <verbosity>$log_level</verbosity>
    <distribute>$distribute</distribute>
    <qos>
        <profile>SENSOR_DATA</profile>
        <reliability>RELIABLE</reliability>
        <history>KEEP_LAST</history>
        <durability>TRANSIENT_LOCAL</durability>
        <liveliness>AUTOMATIC</liveliness>
        <depth>1024</depth>
        <deadline>10.5</deadline>
        <lifespan>12.2</lifespan>
        <liveliness_lease_duration>30.4</liveliness_lease_duration>
    </qos>
</security_log>
"""


class CreateLoggingConfigVerb(VerbExtension):
    """Create logging config."""

    def add_arguments(self, parser, cli_name):
        arg = parser.add_argument('ROOT', help='root path of keystore')
        arg.completer = DirectoriesCompleter()
        parser.add_argument('NAME', help='key name, aka ROS node name')

    def main(self, *, args):
        success = create_logging_config(args.ROOT, args.NAME, CONFIG)
        return 0 if success else 1
