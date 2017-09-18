import docker

from models import ContainerInfo, ServiceInfo
from resources import ResourceList, ContainerList
from utils import EnhancedDict


class DockerApi(object):
    def __init__(self):
        self.client = docker.DockerClient()

    @property
    def is_swarm_mode(self):
        return len(self.client.swarm.attrs) > 0

    def containers(self, **kwargs):
        return ContainerList(ContainerInfo(c) for c in self.client.containers.list(**kwargs))

    def services(self, **kwargs):
        if self.is_swarm_mode:
            return ResourceList(ServiceInfo(s) for s in self.client.services.list(**kwargs))

        else:
            return ResourceList()

    @property
    def state(self):
        return EnhancedDict(containers=self.containers(), services=self.services())

    def events(self, **kwargs):
        for event in self.client.events(**kwargs):
            yield event

    def run_action(self, action_type, *args, **kwargs):
        action = action_type(self)
        action.execute(*args, **kwargs)

    def close(self):
        self.client.api.close()
