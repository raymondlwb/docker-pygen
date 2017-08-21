import six

from utils import EnhancedList


class ResourceList(EnhancedList):
    def matching(self, target):
        return EnhancedList(self._unique_matching(target))

    def _unique_matching(self, target):
        yielded = set()

        for match in self._matching(target):
            if match.raw not in yielded:
                yielded.add(match.raw)
                yield match

    def _matching(self, target):
        if isinstance(target, six.string_types):
            for resource in self:
                if resource.id == target or resource.name == target:
                    yield resource

            # try short IDs
            for resource in self:
                if resource.id.startswith(target):
                    yield resource


class ContainerList(ResourceList):
    def _matching(self, target):
        for matching_resource in super(ContainerList, self)._matching(target):
            yield matching_resource

        # check compose services
        for container in self:
            if target == container.labels.get('com.docker.compose.service', ''):
                yield container


class NetworkList(ResourceList):
    def _matching(self, target):
        for matching_resource in super(NetworkList, self)._matching(target):
            yield matching_resource

        if hasattr(target, 'raw'):
            target = target.raw
            target_network_ids = set(net['NetworkID']
                                     for net in target.attrs['NetworkSettings']['Networks'].values())

        elif hasattr(target, 'id'):
            target_network_ids = {target.id}

        else:
            return

        for net in self:
            if net.id in target_network_ids:
                yield net