"""Built-in evidence collectors"""

from hostlens.collectors.base import Collector, collect_evidence
from hostlens.collectors.basic import HostnameCollector, OuiCollector
from hostlens.collectors.local_names import LlmnrCollector
from hostlens.collectors.mdns import MdnsCollector
from hostlens.collectors.netbios import NetbiosCollector
from hostlens.collectors.services import ServiceCollector
from hostlens.collectors.upnp import UpnpCollector

__all__ = [
    "Collector",
    "HostnameCollector",
    "LlmnrCollector",
    "MdnsCollector",
    "NetbiosCollector",
    "OuiCollector",
    "ServiceCollector",
    "UpnpCollector",
    "collect_evidence",
]
