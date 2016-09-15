# collectd_fluentd

[![Build Status](https://travis-ci.org/acquia/collectd_fluentd.svg?branch=master)](https://travis-ci.org/acquia/collectd_fluentd)

A plugin for [collectd](http://www.collectd.org) to gather metrics from a [fluentd](http://www.fluentd.org) instance, with a
focus on easy installation and configuration.

### Configuration
To configure the plugin:

```xml
LoadPlugin "python"

<Plugin python>
  Import "collectd_fluentd"

  <Module fluentd>
    Instance "example"
    Host     "127.0.0.1"
    Port     "24220"
    Username "user"
    Password "password"

    <FluentdPlugin "kinesis">
      buffer_queue_length "gauge"
      buffer_total_queued_size "gauge"
      retry_count "counter"
    </FluentdPlugin>
  </Module>
</Plugin>
```

License
-------
Except as otherwise noted this software is licensed under the [Apache License, Version 2.0](http://www.apache.org/licenses/LICENSE-2.0.html).

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
