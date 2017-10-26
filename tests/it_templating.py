import time

from integrationtest_helper import BaseDockerIntegrationTest


class TemplatingIntegrationTest(BaseDockerIntegrationTest):
    def setUp(self):
        super(TemplatingIntegrationTest, self).setUp()
        self.build_project()
        self.prepare_images('alpine', 'pygen-build')

    def test_containers(self):
        c1 = self.remote_client.containers.run('alpine', command='sleep 3600',
                                               name='c1',
                                               labels={'pygen.target': 'T1'},
                                               detach=True)

        c2 = self.remote_client.containers.run('alpine', command='sleep 3600',
                                               name='c2',
                                               environment=['PYGEN_TARGET=T2'],
                                               ports={'9123': None, '9800/udp': None},
                                               detach=True)

        template = """
        {% for c in containers %}
          ID={{ c.id }} Name={{ c.name }}
        {% endfor %}

        {% set c1 = containers.matching('T1').first %}
        {% set c2 = containers.matching('T2').first %}
        
        T1={{ c1.name }} T2={{ c2.name }}
        Label={{ c1.labels['pygen.target'] }}
        Env={{ c2.env.PYGEN_TARGET }}
        Status={{ c1.status }}
        Image={{ c2.image }}
        Port/TCP={{ c2.ports.tcp.first_value }}
        Port/UDP={{ c2.ports.udp.first_value }}
        """

        self.dind_container.exec_run(['tee', '/tmp/template'], stdin=True, socket=True).sendall(template)

        command = [
            '--template /tmp/template',
            '--one-shot'
        ]

        output = self.remote_client.containers.run('pygen-build', command=' '.join(command), remove=True,
                                                   volumes=['/var/run/docker.sock:/var/run/docker.sock:ro',
                                                            '/tmp/template:/tmp/template:ro'])

        self.assertIn('ID=%s Name=c1' % c1.id, output)
        self.assertIn('ID=%s Name=c2' % c2.id, output)
        self.assertIn('T1=c1', output)
        self.assertIn('T2=c2', output)
        self.assertIn('Label=T1', output)
        self.assertIn('Env=T2', output)
        self.assertIn('Status=running', output)
        self.assertIn('Image=alpine', output)
        self.assertIn('Port/TCP=9123', output)
        self.assertIn('Port/UDP=9800', output)

    def test_services(self):
        command = self.init_swarm()

        with self.with_dind_container() as second_dind:

            with self.with_dind_container() as third_dind:

                self.prepare_images('alpine', client=self.dind_client(second_dind))
                self.prepare_images('alpine', client=self.dind_client(third_dind))

                second_dind.exec_run(command)
                third_dind.exec_run(command)

                endpoint_spec = {
                    'Ports':
                        [{
                            'Protocol': 'tcp',
                            'PublishedPort': 8080,
                            'TargetPort': 5000
                        }]
                }

                service = self.remote_client.services.create('alpine', 'sleep 3600', name='pygen_svc', mode='global',
                                                             labels={'test_label': '1234'},
                                                             env=['TEST_ENV=pygen_test'],
                                                             endpoint_spec=endpoint_spec)

                for _ in range(60):
                    if len(service.tasks()) >= 2:
                        if all(task['Status']['State'] == 'running' for task in service.tasks()):
                            break

                time.sleep(0.5)

                template = """
                {% for s in all_services %}
                S={{ s.id }}-{{ s.name }}
                S.image={{ s.image }}
                S.label={{ s.labels.test_label }}
                S.port={{ s.ports.tcp.first }}
                S.ingress={{ s.ingress.ports.tcp.first }}

                {% for t in s.tasks %}
                  T={{ t.id }}-{{ t.service_id }}
                  T.name={{ t.name }}
                  T.nodeId={{ t.node_id }}
                  T.state={{ t.desired_state }}/{{ t.status }}
                  T.image={{ t.image }}
                  T.serviceNameLabel={{ t.labels['com.docker.swarm.service.name'] }}
                  T.env={{ t.env.TEST_ENV }}
                {% endfor %}
                {% endfor %}
                """

                self.dind_container.exec_run(['tee', '/tmp/template'], stdin=True, socket=True).sendall(template)

                command = [
                    '--template /tmp/template',
                    '--one-shot'
                ]

                output = self.remote_client.containers.run('pygen-build', command=' '.join(command), remove=True,
                                                           volumes=['/var/run/docker.sock:/var/run/docker.sock:ro',
                                                                    '/tmp/template:/tmp/template:ro'])

                self.assertIn('S=%s-pygen_svc' % service.id, output)
                self.assertIn('S.image=alpine', output)
                self.assertIn('S.label=1234', output)
                self.assertIn('S.port=5000', output)
                self.assertIn('S.ingress=8080', output)

                for task in service.tasks():
                    self.assertIn('T=%s-%s' % (task['ID'], service.id), output)
                    self.assertIn('T.name=%s.%s.%s' % (service.name, task['NodeID'], task['ID']), output)
                    self.assertIn('T.nodeId=%s' % task['NodeID'], output)
                    self.assertIn('T.state=running/running', output)
                    self.assertIn('T.image=alpine', output)
                    self.assertIn('T.serviceNameLabel=pygen_svc', output)
                    self.assertIn('T.env=pygen_test', output)

    def test_networks(self):
        network = self.remote_client.networks.create('pygen-net')

        c1 = self.remote_client.containers.run('alpine', command='sleep 3600',
                                               network=network.name,
                                               detach=True)

        c2 = self.remote_client.containers.run('alpine', command='sleep 3600',
                                               network=network.name,
                                               detach=True)

        template = """
        {% set c1 = containers.matching('$c1').first %}
        {% set c2 = containers.matching('$c2').first %}
        N1={{ c1.networks.matching(c2).first.name }}
        N2={{ c1.networks.matching('$network_name').first.id }}
        N3={{ c2.networks.matching('$network_id').first.id }}
        """

        variables = {
            '$c1': c1.id,
            '$c2': c2.id,
            '$network_id': network.id,
            '$network_name': network.name
        }

        for key, value in variables.items():
            template = template.replace(key, value)

        self.dind_container.exec_run(['tee', '/tmp/template'], stdin=True, socket=True).sendall(template)

        command = [
            '--template /tmp/template',
            '--one-shot'
        ]

        output = self.remote_client.containers.run('pygen-build', command=' '.join(command), remove=True,
                                                   volumes=['/var/run/docker.sock:/var/run/docker.sock:ro',
                                                            '/tmp/template:/tmp/template:ro'])

        self.assertIn('N1=%s' % network.name, output)
        self.assertIn('N2=%s' % network.id, output)
        self.assertIn('N3=%s' % network.id, output)

    def test_nodes(self):
        command = self.init_swarm()

        with self.with_dind_container() as second_dind:

            with self.with_dind_container() as third_dind:

                second_dind.exec_run(command)
                third_dind.exec_run(command)

                template = """
                {% for n in nodes %}
                N={{ n.id }}-{{ n.role }}
                {% endfor %}
                """

                self.dind_container.exec_run(['tee', '/tmp/template'], stdin=True, socket=True).sendall(template)

                command = [
                    '--template /tmp/template',
                    '--one-shot'
                ]

                output = self.remote_client.containers.run('pygen-build', command=' '.join(command), remove=True,
                                                           volumes=['/var/run/docker.sock:/var/run/docker.sock:ro',
                                                                    '/tmp/template:/tmp/template:ro'])

                managers = self.remote_client.nodes.list(filters={'role': 'manager'})
                workers = self.remote_client.nodes.list(filters={'role': 'worker'})

                for node in managers:
                    self.assertIn('N=%s-manager' % node.id, output)

                for node in workers:
                    self.assertIn('N=%s-worker' % node.id, output)
    
    def x_test_compose(self):
        from compose.config.config import ConfigFile, ConfigDetails
        from compose.config.config import load as load_config
        from compose.project import Project
        
        composefile = """
        version: '2'
        services:
          first:
            image: alpine
            command: sleep 3600
          
          second:
            image: alpine
            command: sleep 3600
          
          pygen:
            image: pygen-build
            command: >
              --template '
                {% for c in containers %}
                  Name={{ c.name }}
                {% endfor %}

                1st={{ containers.matching('first')|length }}
                2nd={{ containers.matching('second')|length }}'
              --one-shot
            depends_on:
              - first
              - second
        """

        with open('/tmp/pygen-composefile.yml', 'w') as target:
            target.write(composefile)

        config = ConfigFile.from_filename('/tmp/pygen-composefile.yml'))
        details = ConfigDetails('/tmp', [config])
        project = Project.from_config('cmpse', load_config(details), self.docker_client.api)
        
        project.up(detached=True, scale_override={'second': 2})

        pygen = project.get_service('pygen')

