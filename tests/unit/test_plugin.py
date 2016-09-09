from ..helpers import *

import json
import copy

from collectd_fluentd import plugin

class TestPlugin(object):
    def setup(self):
        self.collectd = MagicMock()
        self.modules = patch.dict('sys.modules', {'collectd': self.collectd})
        self.modules.start()

        self.plugin = plugin.FluentdCollectdPlugin(self.collectd)

    def teardown(self):
        self.modules.stop()

class TestCallbacks(TestPlugin):

    def test_register_callbacks(self):
        collectd = Mock()
        plugin.FluentdCollectdPlugin.register(collectd)
        assert collectd.register_config.called
        assert collectd.register_init.called
        assert collectd.register_read.called
        assert collectd.register_shutdown.called

    @patch.object(plugin.FluentdCollectdPlugin, 'log_message')
    def test_init_callback(self, mock_log_message):
        self.plugin.init()
        mock_log_message.assert_any_call("Initializing")

    @patch.object(plugin.FluentdCollectdPlugin, 'log_message')
    def test_shutdown_callback(self, mock_log_message):
        self.plugin.shutdown()
        mock_log_message.assert_any_call("Stopping")

    def test_config_callback(self):
        config = CollectdConfig('root', (), (
            ('host', '127.0.0.1', ()),
            ('port', '12345', ()),
            ('instance', 'example', ()),
            ('FluentdPlugin', 'kinesis', (
                ('stat_1', 'one', ()),
                ('stat_2', 'two', ()),
            )),
            ('FluentdPlugin', 'forward', (
                ('stat_1', 'one', ()),
                ('stat_2', 'two', ()),
            )),
        ))
        self.plugin.config(config)

        assert_items_equal(self.plugin.metrics.keys(), ['forward', 'kinesis'])

class TestParser(TestPlugin):
    def test_parser(self):
        desired_metrics = {
            'forward': {
                 'buffer_queue_length': 'gauge',
                 'buffer_total_queued_size': 'gauge'
            }
        }

        expected_result = {
            'forward': [
                {'name': 'buffer_queue_length', 'type': 'gauge', 'value': 20},
                {'name': 'buffer_total_queued_size', 'type': 'gauge', 'value': 10}
            ]
        }

        data = json.loads(fixture('api_response.json'))
        result = self.plugin.parse_metrics(desired_metrics, data)

        assert_items_equal(result, expected_result)

    @patch.object(plugin.FluentdCollectdPlugin, 'post_metric')
    def test_processor(self, mock_post_metric):
        result = {
            'forward': [
                {'name': 'buffer_queue_length', 'type': 'gauge', 'value': 20},
                {'name': 'buffer_total_queued_size', 'type': 'gauge', 'value': 10}
            ]
        }

        self.plugin.process_metrics(result)
        mock_post_metric.assert_any_call(20, "forward.buffer_queue_length", "gauge", None)
        mock_post_metric.assert_any_call(10, "forward.buffer_total_queued_size", "gauge", None)
