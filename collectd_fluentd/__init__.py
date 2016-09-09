version_info = (1, 0, 0)
__version__ = ".".join(map(str, version_info))

try:
    import collectd
    collectd_present = True
except (ImportError, AttributeError) as err:
    collectd_present = False

if collectd_present:
    from .plugin import FluentdCollectdPlugin
    FluentdCollectdPlugin.register(collectd)
