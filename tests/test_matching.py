import unittest

from resources import ResourceList, ContainerList, ServiceList, TaskList, NetworkList
from utils import EnhancedDict as ED


class MatchingTest(unittest.TestCase):
    def test_match_by_id(self):
        source = ResourceList([
            ED(id='001'), ED(id='002'), ED(id='003')
        ])

        self.assertEqual(len(source.matching('002')), 1)
        self.assertEqual(len(source.not_matching('001')), 2)

    def test_match_by_name(self):
        source = ResourceList([
            ED(id='1', name='R01'), ED(id='2', name='R02'), ED(id='3', name='R03')
        ])

        self.assertEqual(len(source.matching('R02')), 1)
        self.assertEqual(len(source.not_matching('R01')), 2)

    def test_match_by_pygen_target_label(self):
        source = ResourceList([
            ED(id='1', labels={'pygen.target': 'pt01'}),
            ED(id='2', labels={'pygen.target': 'pt02'}),
            ED(id='3', labels={'pygen.target': 'pt03'})
        ])

        self.assertEqual(len(source.matching('pt02')), 1)
        self.assertEqual(len(source.not_matching('pt01')), 2)

    def test_match_by_pygen_target_env(self):
        source = ResourceList([
            ED(id='1', env={'PYGEN_TARGET': 'PT01'}),
            ED(id='2', env={'PYGEN_TARGET': 'PT02'}),
            ED(id='3', env={'PYGEN_TARGET': 'PT03'})
        ])

        self.assertEqual(len(source.matching('PT02')), 1)
        self.assertEqual(len(source.not_matching('PT01')), 2)

    def test_match_by_short_id(self):
        source = ResourceList([
            ED(id='11234'), ED(id='11345'), ED(id='11456')
        ])

        self.assertEqual(len(source.matching('112')), 1)
        self.assertEqual(len(source.not_matching('114')), 2)

    def test_match_by_compose_service(self):
        source = ContainerList([
            ED(id='1', labels={'com.docker.compose.service': 'cs01'}),
            ED(id='2', labels={'com.docker.compose.service': 'cs01'}),
            ED(id='3', labels={})
        ])

        self.assertEqual(len(source.matching('cs01')), 2)
        self.assertEqual(len(source.not_matching('cs01')), 1)

    def test_match_by_swarm_service(self):
        source = ContainerList([
            ED(id='1', labels={'com.docker.swarm.service.name': 'ss01'}),
            ED(id='2', labels={'com.docker.swarm.service.name': 'ss01'}),
            ED(id='3', labels={})
        ])

        self.assertEqual(len(source.matching('ss01')), 2)
        self.assertEqual(len(source.not_matching('ss01')), 1)

        source = ServiceList([
            ED(id='1', name='srv01', labels={}),
            ED(id='2', name='srv02', labels={}),
            ED(id='3', name='srv03', labels={})
        ])

        self.assertEqual(len(source.matching('srv01')), 1)
        self.assertEqual(len(source.not_matching('srv01')), 2)

    def test_match_by_swarm_stack_service(self):
        source = ContainerList([
            ED(id='1', labels={'com.docker.swarm.service.name': 'st01_srv01',
                               'com.docker.stack.namespace': 'st01'}),
            ED(id='2', labels={'com.docker.swarm.service.name': 'st01_srv01',
                               'com.docker.stack.namespace': 'st01'}),
            ED(id='3', labels={})
        ])

        self.assertEqual(len(source.matching('srv01')), 2)
        self.assertEqual(len(source.not_matching('srv01')), 1)

        source = ServiceList([
            ED(id='1', name='st01_srv01', labels={'com.docker.stack.namespace': 'st01'}),
            ED(id='2', name='srv02', labels={}),
            ED(id='3', name='srv03', labels={})
        ])

        self.assertEqual(len(source.matching('srv01')), 1)
        self.assertEqual(len(source.not_matching('srv01')), 2)

    def test_match_task_by_container_id(self):
        source = TaskList([
            ED(id='1', container_id='cc001', labels={}),
            ED(id='2', container_id='cc002', labels={}),
            ED(id='3', container_id='cc003', labels={})
        ])

        self.assertEqual(len(source.matching('cc002')), 1)
        self.assertEqual(len(source.not_matching('cc002')), 2)

    def test_match_task_by_service_id(self):
        source = TaskList([
            ED(id='1', service_id='srv001', labels={}),
            ED(id='2', service_id='srv002', labels={}),
            ED(id='3', service_id='srv003', labels={})
        ])

        self.assertEqual(len(source.matching('srv002')), 1)
        self.assertEqual(len(source.not_matching('srv002')), 2)

    def test_match_task_by_service_name(self):
        source = TaskList([
            ED(id='1', labels={'com.docker.swarm.service.name': 'srv001'}),
            ED(id='2', labels={'com.docker.swarm.service.name': 'srv002'}),
            ED(id='3', labels={'com.docker.swarm.service.name': 'srv003'})
        ])

        self.assertEqual(len(source.matching('srv002')), 1)
        self.assertEqual(len(source.not_matching('srv002')), 2)

    def test_match_task_by_stack_service_name(self):
        source = TaskList([
            ED(id='1', labels={'com.docker.swarm.service.name': 'st01_srv001',
                               'com.docker.stack.namespace': 'st01'}),
            ED(id='2', labels={'com.docker.swarm.service.name': 'st01_srv002',
                               'com.docker.stack.namespace': 'st01'}),
            ED(id='3', labels={'com.docker.swarm.service.name': 'st02_srv001',
                               'com.docker.stack.namespace': 'st02'}),
        ])

        self.assertEqual(len(source.matching('srv002')), 1)
        self.assertEqual(len(source.not_matching('srv002')), 2)

    def test_match_task_by_status(self):
        source = TaskList([
            ED(id='1', status='running', labels={}),
            ED(id='2', status='running', labels={}),
            ED(id='3', status='stopped', labels={})
        ])

        self.assertEqual(len(source.with_status('running')), 2)
        self.assertEqual(len(source.with_status('stopped')), 1)

    def test_match_network_against_container_networks(self):
        source = NetworkList([
            ED(id='n01'), ED(id='n02'), ED(id='n03')
        ])

        target = ED(raw=ED(attrs=ED(NetworkSettings=ED(Networks=ED(sample=ED(NetworkID='n01'))))))

        self.assertEqual(len(source.matching(target)), 1)
        self.assertEqual(next(iter(source.matching(target))).id, 'n01')
    
    def test_match_network_against_network(self):
        source = NetworkList([
            ED(id='n01'), ED(id='n02'), ED(id='n03')
        ])

        target = ED(id='n02')

        self.assertEqual(len(source.matching(target)), 1)
        self.assertEqual(next(iter(source.matching(target))).id, 'n02')

