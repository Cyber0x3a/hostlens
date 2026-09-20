"""Public exception hierarchy for HostLens"""


class HostLensError(Exception):
    """Base class for errors raised by HostLens"""


class ConfigurationError(HostLensError):
    """Configuration is invalid"""


class DiscoveryError(HostLensError):
    """Network discovery could not run"""


class PermissionDenied(DiscoveryError):
    """A network operation requires additional privileges"""


class InterfaceNotFound(DiscoveryError):
    """The selected network interface does not exist"""


class TargetUnreachable(HostLensError):
    """No useful evidence could be collected for a target"""


class CollectorError(HostLensError):
    """An evidence collector failed"""


class ResolverError(HostLensError):
    """An evidence resolver failed"""


class CloudResolverError(ResolverError):
    """A configured cloud resolver failed"""
