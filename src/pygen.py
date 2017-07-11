import os

import jinja2

from actions import RestartAction, SignalAction
from api import *
from errors import *
from timer import NotificationTimer
from utils import get_logger

logger = get_logger('pygen')


class PyGen(object):
    EMPTY_DICT = dict()

    def __init__(self, **kwargs):
        self.target_path = kwargs.get('target')
        self.template_source = kwargs.get('template')
        self.restart_targets = kwargs.get('restart', list())
        self.signal_targets = kwargs.get('signal', list())

        if not self.template_source:
            raise PyGenException('No template is defined')

        intervals = kwargs.get('interval', [0.5, 2])
        if len(intervals) > 2:
            raise PyGenException('Invalid intervals, see help for usage')

        if len(intervals) == 1:
            min_interval = max_interval = intervals[0]

        else:
            min_interval, max_interval = intervals

        self.template = self._init_template(self.template_source)
        self.timer = NotificationTimer(self._signal_targets, min_interval, max_interval)

        self.api = DockerApi()

    @staticmethod
    def _init_template(source):
        jinja_env_options = {
            'trim_blocks': True,
            'lstrip_blocks': True,
            'extensions': ['jinja2.ext.loopcontrols']
        }

        if source.startswith('#'):
            template_filename = 'inline'

            jinja_environment = jinja2.Environment(loader=jinja2.DictLoader({template_filename: source[1:].strip()}),
                                                   **jinja_env_options)

        else:
            template_directory, template_filename = os.path.split(os.path.abspath(source))

            jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(template_directory),
                                                   **jinja_env_options)

        jinja_environment.filters.update({
            'any': any,
            'all': all
        })

        return jinja_environment.get_template(template_filename)

    def generate(self):
        containers = self.api.containers()
        return self.template.render(containers=containers)

    def update_target(self):
        if not self.target_path:
            logger.info('Printing generated content to stdout')

            print(self.generate())
            self.timer.schedule()

            return

        logger.info('Updating target file at %s', self.target_path)

        existing_content = ''

        if os.path.exists(self.target_path):
            with open(self.target_path, 'r') as target:
                existing_content = target.read()

        content = self.generate()

        if content == existing_content:
            logger.info('Skip updating target file, contents have not changed')
            return

        with open(self.target_path, 'w') as target:
            target.write(content)

        logger.info('Target file updated at %s', self.target_path)

        self.timer.schedule()

    def signal(self):
        self._restart_targets()
        self._signal_targets()

    def _restart_targets(self):
        for target in self.restart_targets:
            self.api.run_action(RestartAction, target)

    def _signal_targets(self):
        for target, signal in self.signal_targets:
            self.api.run_action(SignalAction, target, signal)

    def watch(self, **kwargs):
        kwargs['decode'] = True

        for event in self.api.events(**kwargs):
            if event.get('status') in ('start', 'stop', 'die'):
                logger.info('Received %s event from %s',
                            event.get('status'),
                            event.get('Actor', self.EMPTY_DICT).get('Attributes', self.EMPTY_DICT).get('name', '<?>'))

                self.update_target()
