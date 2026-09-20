# Cloud enrichment

Local scanning does not require an account or API key

Fingerbank support is opt in

```python
import os

from hostlens import HostLens

intel = HostLens(
    cloud=True,
    fingerbank_api_key=os.environ["FINGERBANK_API_KEY"],
)
```

Setting `cloud=True` without a key raises `ConfigurationError`

## What can be sent

The Fingerbank payload can contain these observed values

- MAC address
- Hostname
- DHCP fingerprint
- DHCP vendor class

Preview the exact payload before a request

```python
device = await intel.scan_host("192.168.1.42", mode="fast")
payload = intel.preview_cloud_payload(device)
print(payload)
```

When cloud support is disabled, `preview_cloud_payload` returns an empty dictionary

## When requests happen

Fingerbank may run in normal, deep, and passive identification

Fast mode skips it

The request uses HTTPS and includes the API key as required by the Fingerbank endpoint

HostLens does not place the API key in evidence or logs

## Failure behavior

A Fingerbank timeout, invalid response, or HTTP error does not discard local results

The client records a debug log and continues with evidence gathered on the LAN

Code that uses `FingerbankClient` directly receives `CloudResolverError` instead

## Practical handling of keys

Read the key from an environment variable or a secret manager

Do not commit it to an example, configuration file, test fixture, or shell history
