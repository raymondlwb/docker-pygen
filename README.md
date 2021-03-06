# docker-pygen

Configuration generator based on Docker containers state and parameters.

[![Travis](https://travis-ci.org/rycus86/docker-pygen.svg)](https://travis-ci.org/rycus86/docker-pygen)
[![Build Status](https://img.shields.io/docker/build/rycus86/docker-pygen.svg)](https://hub.docker.com/r/rycus86/docker-pygen)
[![Coverage Status](https://coveralls.io/repos/github/rycus86/docker-pygen/badge.svg?branch=master)](https://coveralls.io/github/rycus86/docker-pygen?branch=master)
[![Code Climate](https://codeclimate.com/github/rycus86/docker-pygen/badges/gpa.svg)](https://codeclimate.com/github/rycus86/docker-pygen)
[![Docker Image Layers](https://images.microbadger.com/badges/image/rycus86/arm-nginx.svg)](https://microbadger.com/images/rycus86/docker-pygen "Get your own image badge on microbadger.com")

## Motivation

As we break our applications down to individual microservices more and more
the harder it gets to configure the supporting infrastructure around them.
If we think about managing HTTP proxying to them with servers like *Nginx*
or configuring any other system that has to know about a set of (or all)
of the running services - that can become quite an overhead done manually.

If you're using Docker to run those microservices then this project could
provide an easy solution to the problem.
By inspecting the currently running containers and their settings it can
generate configuration files for basically anything that works with those.
It can also notify other services about the configuration change by
signalling or restarting them.

## Usage

To run it as a Python application (tested on versions 2.7, 3.4 and 3.6)
clone the project and install the dependencies:

```shell
pip install -r requirements.txt
```

Then run it as `python cli.py <args>` where the arguments are:

```text
usage: cli.py [-h] --template TEMPLATE [--target TARGET]
              [--restart <CONTAINER>] [--signal <CONTAINER> <SIGNAL>]
              [--interval <MIN> [<MAX> ...]] [--events <EVENT> [<EVENT> ...]]
              [--swarm-manager] [--workers <TARGET> [<TARGET> ...]]
              [--retries RETRIES] [--no-ssl-check] [--one-shot]
              [--docker-address <ADDRESS>] [--debug]

Template generator based on Docker runtime information

optional arguments:
  -h, --help            show this help message and exit
  --template TEMPLATE   The base Jinja2 template file or inline template as
                        string if it starts with "#"
  --target TARGET       The target to save the generated file (/dev/stdout by
                        default)
  --restart <CONTAINER>
                        Restart the target container, can be: ID, short ID,
                        name, Compose service name, label ["pygen.target"] or
                        environment variable ["PYGEN_TARGET"]
  --signal <CONTAINER> <SIGNAL>
                        Signal the target container, in <container> <signal>
                        format. The <container> argument can be one of the
                        attributes described in --restart
  --interval <MIN> [<MAX> ...]
                        Minimum and maximum intervals for sending
                        notifications. If there is only one argument it will
                        be used for both MIN and MAX. The defaults are: 0.5
                        and 2 seconds.
  --repeat <SECONDS>    Optional interval in seconds to re-run the target
                        generation after an event and execute the action if
                        the target has changed. Defaults to 0 meaning the
                        generation will not be repeated.
  --events <EVENT> [<EVENT> ...]
                        Docker events to watch and trigger updates for
                        (default: start, stop, die, health_status)
  --swarm-manager       Enable the Swarm manager HTTP endpoint on port 9411
  --workers <TARGET> [<TARGET> ...]
                        The target hostname of PyGen workers listening on port
                        9412 (use "tasks.service_name" for Swarm workers)
  --retries RETRIES     Number of retries for sending an action to a Swarm
                        worker
  --no-ssl-check        Disable SSL verification when loading templates over
                        HTTPS (not secure)
  --one-shot            Run the update once and exit, also execute actions if
                        the target changes
  --docker-address <ADDRESS>
                        Alternative address (URL) for the Docker daemon
                        connection
  --metrics <PORT>      HTTP port number for exposing Prometheus metrics
                        (default: 9413)
  --debug               Enable debug log messages
```

The application will need access to the Docker daemon too.

You can also run it as a Docker container to make things easier:

```shell
docker run -d --name config-generator                         \
              -v /var/run/docker.sock:/var/run/docker.sock:ro \
              -v shared-volume:/etc/share/config              \
              -v $PWD/template.conf:/etc/share/template.conf  \
              --template /etc/share/template.conf             \
              --target   /etc/share/config/auto.conf          \
              --restart  config-loader                        \
              --signal   web-server HUP                       \
              rycus86/docker-pygen
```

This command will:

- attach the Docker socket from `/var/run/docker.sock`
- attach a shared folder from the `shared-volume` to `/etc/share/config`
- attach the template file `template.conf` from the current host directory 
  to `/etc/share/template.conf`
- use the template (at `/etc/share/template.conf` inside the container)
- write to the `auto.conf` target file on the shared volume
  (at `/etc/share/config/auto.conf` inside the container)
- restart containers matching "config-loader" when the configuration file is updated
- send a *SIGHUP* signal to containers matching "web-server"

Matching containers can be based on container ID, short ID, name, Compose or Swarm service name.
You can also add it as the value of the `pygen.target` label or as the value of the 
`PYGEN_TARGET` environment variable.

The connection to the Docker daeamon can be overridden from the default
location to an alternative (for TCP for example) using the `--docker-address` flag.
For testing (or for other reasons) the app can also run in `--one-shot` mode
that generates the configuration using the template once and exits without
watching for events (this also executes any actions given if the target file changes).

The Docker image is available in three flavors:

- `amd64`: for *x86* hosts  
  [![Layers](https://images.microbadger.com/badges/image/rycus86/docker-pygen:amd64.svg)](https://microbadger.com/images/rycus86/docker-pygen:amd64 "Get your own image badge on microbadger.com")
- `armhf`: for *32-bits ARM* hosts  
  [![Layers](https://images.microbadger.com/badges/image/rycus86/docker-pygen:armhf.svg)](https://microbadger.com/images/rycus86/docker-pygen:armhf "Get your own image badge on microbadger.com")
- `aarch64`: for *64-bits ARM* hosts  
  [![Layers](https://images.microbadger.com/badges/image/rycus86/docker-pygen:aarch64.svg)](https://microbadger.com/images/rycus86/docker-pygen:aarch64 "Get your own image badge on microbadger.com")

All of these are built on and uploaded from [Travis](https://travis-ci.org/rycus86/docker-pygen)
while `latest` is a multi-arch manifest on [Docker Hub](https://hub.docker.com/r/rycus86/docker-pygen)
so using that would select the appropriate image based on the host's processor architecture.

The application exposes [Prometheus](https://prometheus.io/) metrics
about the number of calls and the execution times of certain actions.

## Templating

To generate the configuration files, the app uses [Jinja2 templates](http://jinja.pocoo.org/docs).
Templates have access to these variables:

- `containers` list containing a list of *running* Docker
  containers wrapped as `models.ContainerInfo` objects on a `resources.ContainerList`
- `services` list containing Swarm services with their running tasks (desired state)
  using `models.ServiceInfo` and `models.TaskInfo` objects wrapped in
  `resources.ServiceList` and `resources.TaskList` collections.
- `all_containers` *lazy-loaded* list of *all* Docker containers (even if not running)
- `all_services` *lazy-loaded* list of Swarm services with *all* their tasks
  (even if not in running desired state)
- `nodes` *lazy-loaded* list of Swarm nodes as `models.NodeInfo` objects wrapped
  in a `resources.ResourceList` list
- `own_container_id` that contains the ID of the container the app is running in
  or otherwise `None`
- `read_config` that helps reading configuration parameters from key-value files
  or environment variables and also full configuration files (certificates for example),
  see [docker_helper](https://github.com/rycus86/docker_helper) for more information and usage

Templates can be loaded from a file, from an HTTP/HTTPS address or can be given inline if
the `--template` parameters starts with a `#` sign.

A small example from a template could look like this:

```
{% set server_name = 'test.example.com' %}
upstream {{ server_name }} {
    {% for container in containers
          if  container.networks.first_value.ip_address
          and container.ports.tcp.first_value %}
        # {{ container.name }}
        server {{ container.networks.first_value.ip_address }}:{{ container.ports.tcp.first_value }};
    {% endfor %}
}
```

This example from the [nginx.example](https://github.com/rycus86/docker-pygen/blob/master/tests/templates/nginx.example)
file would output `server_name` as the value set on the first line then iterate
through the containers having an IP address and TCP port exposed to finally output
them prefixed with the container's name.

The available properties on a `models.ContainerInfo` object are:

- `raw`: The original container object from [docker-py](https://github.com/docker/docker-py)
- `id`: The container's ID
- `short_id`: The container's short ID
- `name`: The container's name
- `image`: The name of the image the container uses
- `status`: The current status of the container
- `health`: The health status of the container or `unknown` if it does not have health checking
- `labels`: The labels of the container (as `EnhancedDict` - see below)
- `env`: The environment variables of the container as `EnhancedDict`
- `networks`: The list of networks the container is attached to (as `NetworkList`)
- `ports`: The list of ports exposed by the container as `EnhancedDict` having
  `tcp` and `udp` ports as `EnhancedList`

The `utils.EnhancedDict` class is a Python dictionary extension to allow referring to
keys in it as properties - for example: `container.ports.tcp` instead of
`container['ports']['tcp']`. Property names are also case-insensitive.  
The `models.ContainerInfo` class extends `utils.EnhancedDict` to provide these features.

The `utils.EnhancedList` class is a Python list extension having additional properties
for getting the `first` or `last` element and the `first_value` - e.g. the first element
that is not `None` or empty.

The `resources.ResourceList` extends `EnhancedList` to provide a `matching(target)` method
that allows getting the first element of the list having a matching ID or name.
For convenience, a `not_matching` method is also available.

The `resources.ContainerList` extends the `matching` method to also match by Compose
or Swarm service name for containers.
It also supports the `healthy` property that filters the list for containers with healthy
state while the `with_health` method can be used to filter for a given health state.
The `self` property returns the `models.ContainerInfo` instance for the running
application itself, if appropriate.

Swarm services use the `models.ServiceInfo` class with these properties:

- `raw`: The original service object from the API
- `id`: The ID of the service
- `short_id`: The short ID of the service
- `name`: The name of the service
- `version`: The current Swarm version of the service
- `image`: The image used by the service
- `labels`: The labels attached to the service (not the tasks)
- `ports`: Contains two lists for `tcp` and `udp` ports for the published ports'
  targets used internally by the containers
- `networks`: The networks used by the service (except `ingress`)
- `ingress`: The Swarm ingress network's details
- `tasks`: The current Swarm tasks that belong to the service

Tasks use the `models.TaskInfo` class and have these properties available:

- `raw`: The original task attributes (`dict`-like) from the API
- `id`: The ID of the task
- `name`: The name of the task generated as `<service_name>.<slot>.<task_id>` for
  replicated services or `<service_name>.<node_id>.<task_id>` for global services.
- `node_id`: The ID of the Swarm node the task is scheduled on
- `service_id`: The ID of the service the task belongs to
- `slot`: The slot number for tasks in replicated services
- `container_id`: The ID of the container the task created
- `image`: The image the container of the task uses
- `status`: The status of the task
- `desired_state`: The desired state of the task
- `labels`: Labels assigned to the task and its containers, also including:
  - `com.docker.swarm.service.id`: The ID of the service the task belongs to
  - `com.docker.swarm.service.name`: The name of the service the task belongs to
  - `com.docker.swarm.task.id`: The ID of the task
  - `com.docker.swarm.task.name`: The name of the task
  - `com.docker.swarm.node.id`: The ID of the Swarm node the task is scheduled on
- `env`: Environment variables used on the container created by the task
- `networks`: The list of networks attached to the task

The `resources.ServiceList` extends `matching` by Swarm service name and the
`resources.TaskList` can also match by container ID, service ID or service name.
Tasks can also be filtered using their status and the `with_status` method.
Both of them support the `self` property, that returns the `models.ServiceInfo`
or the `models.TaskInfo` instance respectively,
where the current application is running, if appropriate.

The `resources.NetworkList` class adds matching by network ID
or network instance with an `id` property.
It also accept other objects with networking settings
(one that has a `networks` property, like `ContainerInfo`) and
matches the networks against its network list.
You can also pass another `resources.NetworkList` to it to give you
the common networks that are present on both lists.

The networks for __containers__ have the `id`, `name` and a single `ip_address` properties.
For __services__ the networks have a list of `ip_addresses` plus a `gateway` property.
__Task__ networks also include the network `labels` and an `is_ingress` flag as well.
Finally the __ingress__ network on services has a `port` property with lists of `tcp` and
`udp` ports published on the Swarm ingress.

An example for matching could be containers on the same network in a Compose project:
```
{% set reference = containers.matching('web').first %}
targets:
{% for container in containers %}
  - "http://{{ container.networks.matching(reference).first.ip_address }}:{{ container.ports.tcp.first_value }}/{{ container.name }}"
{% endfor %}
```

This would take the `web` container as a reference and list targets with
the IP address taken from the first matching network using the reference.
A Swarm example would be:

```
{% set own_service = services.self %}

Common networks:
{% for service in services %}
  {% for task in service.tasks %}
    {% if task.networks.not_matching('ingress').matching(own_service.networks).first_value %}
    - {{ task.name }} in {{ service.name }}
    {% endif %}
  {% endfor %}
{% endfor %}
```

The snippet above would print the name of the tasks (and the name of their services)
which share the same networks as the current *PyGen* app running in a container,
except for the network called `ingress`.
Note, that `task.networks.not_matching('ingress').matching(own_service)`
would also work for matching, but it is perhaps less readable or obvious.

Apart from the [built-in Jinja template filters](http://jinja.pocoo.org/docs/2.9/templates/#builtin-filters)
the `any` and `all` filters are also available to evaluate conditions using 
the Python built-in functions with the same name.

## Updating the target file

The application listens for Docker *start*, *stop*, *die* and *health_status* events by 
default from containers and schedules an update (can be configured by the `--events` flag).
If the generated content didn't change and the target already has the same content
then the process stops.

If the template and the runtime information produces changes in the target file's
content then a notification is scheduled according to the intervals set at startup.
If there is another notification scheduled before the minimum interval is reached
then it is being rescheduled unless the time since the first generation has passed
the maximum interval already.
This ensures batching notifications together in case many events arrive close to each other.
See the `timer.NotificationTimer` class for implementation details.

## Signalling others

When the contents of the target file have changed the application can either restart
containers or send UNIX signals to them to let them know about the change.
Matching containers is done as described on the help text of the `--restart` argument.

For example if we have a couple of containers running with the service name `nginx`
managed by a Compose project, a `--signal nginx HUP` command would send a *SIGHUP*
signal to each of them to get them to reload their configuration.

Both of these work with Swarm when target containers might be running on different
nodes than the app itself - using a Swarm *manager* and *workers* that alters the
behavior slightly.
For restarts, the manager app will restart matched Swarm services then stop if any of
them was found, otherwise the workers will execute the restarts against containers
matched locally.
Signalling tasks in Swarm is not supported as far as I know, so it is always done
using workers that will send the signal one-by-one to containers matched locally.

See how to configure the Swarm manager and workers below.

## Swarm support

To be able to execute actions as described above and to be notified of container
events happening on remote Swarm nodes the app can be run as a cooperating pair of
a Swarm manager and a number of Swarm workers.
The manager should be run as a single instance on a manager node
(the `node.role==manager` constraint can be used when scheduling the tasks) while
the workers should run in `global` mode so every node in the Swarm would have one
instance running.

Communication between the manager and the workers is done using HTTP requests.
The manager uses port `9411` to accept events from the workers and those use
port `9412` to accept action commands from the manager.
None of these ports have to be exposed externally, the instances will be able
to talk to each other as long as they are on the same overlay network.
If the app is not running from Docker containers then these ports
will have to be accessible though.

To enable the Swarm manager mode on the main app, use the `--swarm-manager` flag
along with the `--workers` parameter that contains the hostname(s) of the workers
to contact when executing actions.

The Swarm worker app is started using an alternative *cli* module:

```text
usage: swarm_worker.py [-h] --manager <HOSTNAME> [<HOSTNAME> ...]
                       [--retries RETRIES] [--events <EVENT> [<EVENT> ...]]
                       [--metrics <PORT>] [--debug]

PyGen cli to send HTTP updates on Docker events

optional arguments:
  -h, --help            show this help message and exit
  --manager <HOSTNAME> [<HOSTNAME> ...]
                        The target hostnames of the PyGen manager instances
                        listening on port 9411
  --retries RETRIES     Number of retries for sending an update to the manager
  --events <EVENT> [<EVENT> ...]
                        Docker events to watch and trigger updates for
                        (default: start, stop, die, health_status)
  --metrics <PORT>      HTTP port number for exposing Prometheus metrics
                        (default: 9414)
  --debug               Enable debug log messages
```

The only required parameter is the `--manager` containing the hostname
of the Swarm manager app listening for remote events.

My tests indicate that there can be a slight delay between a container
becoming healthy and the owning Swarm task changing to *running* state.
Because of this you might want to use the `--repeat` option of the manager
to retry the template generation after a few seconds which should give
some time for the task state to settle.

The worker app is available as a Docker image too using tags prefixed with
`worker`:

- `worker-amd64` for x86 architecture
- `worker-armhf` for 32-bits ARM
- `worker-aarch64` for 64-bits ARM

In a similar way to the main image, the `worker` tag is a multi-arch manifest that
will select the appropriate worker image based on the processor architecture of the host.

An example configuration for a Swarm manager and workers in a *Composefile*
could be:

```yaml
version: '3.4'
services:

  nginx:
    image: nginx
    deploy:
      replicas: 1
      placement:
        constraints:
          - node.role == manager
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/pygen/nginx-config:/etc/nginx/conf.d
  
  nginx-pygen:
    image: rycus86/docker-pygen
    command: >
      --template /etc/docker-pygen/templates/nginx.tmpl
      --target /etc/nginx/conf.d/default.conf
      --signal nginx HUP
      --interval 3 10
      --swarm-manager
      --workers tasks.mystack_nginx-pygen-worker
    deploy:
      replicas: 1
      placement:
        constraints:
          - node.role == manager
    volumes:
      - /var/pygen/nginx-config:/etc/nginx/conf.d
      - /var/pygen/nginx-pygen.tmpl:/etc/docker-pygen/templates/nginx.tmpl:ro
      - /var/run/docker.sock:/var/run/docker.sock:ro

  nginx-pygen-worker:
    image: rycus86/docker-pygen:worker
    command: --manager mystack_nginx-pygen
    read_only: true
    deploy:
      mode: global
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
```

When deployed using the `mystack` stack name the `nginx-pygen` manager app will
handle updates to the target configuration file while the `nginx-pygen-worker`
worker apps will collect Docker events and forward it to the manager.
They will also take care of signalling the `nginx` container on configuration
change, in particular the worker app running on the same node will, the others
will ignore the action.

## Testing

The project uses the built-in Python `unittest` library for testing.
The test files are in the `tests` folder and they use the `test_*.py` file name pattern.

The unit tests can be started with:

```text
PYTHONPATH=src python -m unittest discover -s tests -v
```

The integration tests are also written in Python and use
[Docker in Docker (dind)](https://hub.docker.com/_/docker/)
([more information](https://jpetazzo.github.io/2015/09/03/do-not-use-docker-in-docker-for-ci/)).
It will start containers having the Docker daemon and start containers
inside those to execute the tests and check the expected outcome.

The integration tests are in the same `tests` folder with the
`it_*.py` pattern and they can be executed using:

```text
PYTHONPATH=tests python -m unittest -v integrationtest_helper
```

## Acknowledgement

This tool was inspired by the awesome [jwilder/docker-gen](https://github.com/jwilder/docker-gen)
project that is written in Go and uses Go templates for configuration generation.
Many of the functionality here match or are related to what's available there.
