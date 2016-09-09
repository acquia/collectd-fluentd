#!/usr/bin/env python

#  Licensed to the Apache Software Foundation (ASF) under one or more
#  contributor license agreements.  See the NOTICE file distributed with this
#  work for additional information regarding copyright ownership.  The ASF
#  licenses this file to you under the Apache License, Version 2.0 (the
#  "License"); you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.

"""
Fluentd Collectd plugin
"""

import logging
import requests
import requests.auth
import sys

class FluentdCollectdPlugin(object):

    PLUGIN_NAME = "fluentd"

    def __init__(self, collectd=None):
        self.collectd = collectd
        self.metrics = {}
        self.configs = []

    @classmethod
    def register(cls, collectd):
        """
        Registers the plugin's callbacks with the given collectd module.
        Since the collectd module is only available when the plugin is running
        in collectd's python process we use some dependency injection here.
        :param collectd: The collectd module.
        :type collectd: module
        """
        instance = cls(collectd)

        collectd.register_config(instance.config, name=cls.PLUGIN_NAME)
        collectd.register_init(instance.init, name=cls.PLUGIN_NAME)
        collectd.register_read(instance.read, name=cls.PLUGIN_NAME)
        collectd.register_shutdown(instance.shutdown, name=cls.PLUGIN_NAME)

    def log_message(self, msg, log_level=logging.INFO):
        """
        Log Message
        """
        try:
            if log_level == logging.INFO:
                self.collectd.info("{} plugin: {}".format(self.PLUGIN_NAME, msg))
            elif log_level == logging.ERROR:
                self.collectd.error("{} plugin: {}".format(self.PLUGIN_NAME, msg))
            elif log_level == logging.WARNING:
                self.collectd.warning("{} plugin: {}".format(self.PLUGIN_NAME, msg))
            elif log_level == logging.DEBUG:
                self.collectd.debug("{} plugin: {}".format(self.PLUGIN_NAME, msg))
        except Exception as e:
            sys.stderr.write(
                "{} plugin: unable to write log message due to '{}'".format(
                    self.PLUGIN_NAME, e.message
                )
            )

    def get_metrics(self, conf):
        """
        Get Metrics
        """
        result = None
        try:
            auth = None
            if conf['username'] and conf['password']:
                auth = requests.auth.HTTPBasicAuth(
                        username=conf['username'], password=conf['password']
                    )

            request_uri = "{scheme}://{host}:{port}{path}".format(
                scheme=conf['scheme'],
                host=conf['host'],
                port=conf['port'],
                path=conf['path']
            )

            response = requests.get(request_uri, auth=auth)
            result = response.json()
        except Exception as exc:
            self.log_message(exc.message, logging.ERROR)
            result = None

        return result

    def post_metric(self, value, name, type, instance=None):
        """
        Post Metric
        """
        try:
            val = self.collectd.Values()
            val.plugin = self.PLUGIN_NAME
            val.type = type
            val.type_instance = name
            val.plugin_instance = instance
            val.values = [value]
            val.dispatch()
        except Exception as exc:
            self.log_message(
                "{plugin} plugin: Error, unable to post metric {instance}.{name}={type}({value}) due to {err}".format(
                    plugin=self.PLUGIN_NAME, instance=instance, name=name, value=value, type=type, err=exc.message
                ),
                logging.ERROR
            )

    def process_metrics(self, result, instance=None):
        if not result:
            return

        for name, plugin_metrics in result.iteritems():
            for metric in plugin_metrics:
                metric_name = metric['name']
                metric_type = metric['type']
                metric_value = metric['value']
                metric_namespaced_name = ".".join([name, metric_name])

                self.post_metric(metric_value, metric_namespaced_name, metric_type, instance)

    def parse_metrics(self, desired_metrics=None, data=None):
        """
        Parse metrics
        """
        if not any(desired_metrics) or data is None:
            return

        plugins = data.get('plugins')
        if plugins is None:
            return None

        result = {}
        # Loop over all returned plugins available from the api call
        for plugin in plugins:
            # Check to see if the plugin type is in the configured list
            if plugin['type'] in desired_metrics.keys():
                plugin_type = plugin['type']
                desired_metrics_list = desired_metrics[plugin_type]
                # Loop over all the configured metrics for the given plugin
                result[plugin_type] = []
                for metric_name, metric_type in desired_metrics_list.iteritems():
                    if metric_name in plugin:
                        metric_value = plugin[metric_name]
                        result[plugin_type].append({
                            'name': metric_name,
                            'type': metric_type,
                            'value': metric_value
                        })
        return result

    def read(self):
        """
        Read callback for collectd
        """
        for conf in self.configs:
            # Lookup stats from Fluentd
            result = self.get_metrics(conf)
            instance = conf['instance']

            # Parse out each configured plugins metrics
            if result:
                parsed_result = self.parse_metrics(self.metrics, result)
                if parsed_result is not None:
                    if any(parsed_result):
                        self.process_metrics(parsed_result, instance)

    def config(self, conf):
        """
        Configuration callback for collectd
        """

        # Reset any previously configured metrics.
        self.metrics = {}
        self.configs = []

        host = 'localhost'
        port = 24220
        path = '/api/plugins.json'
        scheme = 'http'
        username = None
        password = None
        instance = None

        for node in conf.children:
            key = node.key.lower()
            val = node.values[0]

            if key == 'host':
                host = val
            elif key == 'port':
                port = int(val)
            elif key == 'path':
                path = val
            elif key == 'scheme':
                scheme = val
            elif key == 'username':
                username = val
            elif key == 'password':
                password = val
            elif key == 'instance':
                instance = val
            elif key == 'fluentdplugin':
                fluentd_name = val

                self.metrics[fluentd_name] = {}

                for node_child in node.children:
                    fluentd_plugin_metric_name = node_child.key.lower()
                    fluentd_plugin_metric_type = node_child.values[0]

                    self.log_message("{} plugin: Fluentd plugin {} metric key: {} - value: {}".format(
                        self.PLUGIN_NAME, fluentd_name, fluentd_plugin_metric_name, fluentd_plugin_metric_type
                        )
                    )

                    self.metrics[fluentd_name].update(
                        {fluentd_plugin_metric_name: fluentd_plugin_metric_type}
                    )
            else:
                self.log_message(
                    "{} plugin: Unknown config key: {}".format(self.PLUGIN_NAME, key),
                    logging.WARNING
                )
                continue

            self.log_message(
                "Adding configuration: host={host}, port={port}, scheme={scheme}, username={username}, with password={password}, instance name={instance}, path={path}".format(
                    host=host, port=port, scheme=scheme, username=username, password=bool(password), instance=instance, path=path
                 )
            )

            self.configs.append({
                'host': host,
                'port': port,
                'path': path,
                'scheme': scheme,
                'username': username,
                'password': password,
                'instance': instance,
            })

    def init(self):
        """
        Initialization callback for collectd
        """
        self.log_message("Initializing")

    def shutdown(self):
        """
        Shutdown callback for collectd
        """
        self.log_message("Stopping")
