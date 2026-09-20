# Device profiles

Every identification path returns a `DeviceProfile`

It is a Pydantic model, so normal attribute access and Pydantic serialization both work

```python
device = await intel.identify("192.168.1.42")

print(device.ip)
print(device.best_name)
print(device.model_dump())
print(device.model_dump_json(indent=2))
```

## Main fields

| Field | Type | Meaning |
| --- | --- | --- |
| `ip` | `str` | Normalized IP address used for the scan |
| `mac` | `str \| None` | Normalized MAC address when discovery found one |
| `hostname` | `str \| None` | Selected hostname |
| `friendly_name` | `str \| None` | Device name reported by a local protocol |
| `manufacturer` | `str \| None` | Selected manufacturer |
| `device_type` | `str \| None` | Conservative device category |
| `model` | `str \| None` | Reported or resolved model |
| `os` | `str \| None` | Operating system when supported by evidence |
| `services` | `list[Service]` | Advertised or responsive services |
| `confidence` | `float` | Overall heuristic confidence from 0 to 1 |
| `fields` | `dict[str, FieldValue]` | Selected values with per-field confidence and sources |
| `evidence` | `list[Evidence]` | Facts and derived hints used to build the profile |

Unknown values stay `None`

## Best name

`best_name` picks the first useful value in this order

1. Friendly name
2. Meaningful hostname
3. Manufacturer and model
4. Model
5. Manufacturer and device type
6. Hostname
7. IP address
8. MAC address

Generated-looking hostnames such as `android-deadbeef` are kept in the profile but lose priority to a useful manufacturer and device type

## Evidence

An evidence item records where a value came from

```python
for item in device.evidence:
    print(item.source)
    print(item.field)
    print(item.value)
    print(item.confidence)
    print(item.observed_at)
```

Evidence may be a directly observed fact such as a UPnP model name or a derived hint from a local fingerprint rule

Derived sources use names such as `local:chromecast`

## Selected fields

The `fields` mapping explains which values won during fusion

```python
manufacturer = device.fields.get("manufacturer")

if manufacturer:
    print(manufacturer.value)
    print(manufacturer.confidence)
    print(manufacturer.sources)
```

HostLens groups evidence by field, removes exact duplicates, weighs source reliability, and selects one value

Supporting observations from independent sources raise the field confidence

Confidence values are ranking heuristics, not calibrated probabilities

## Explanation text

`explain()` produces text from the stored evidence

```python
print(device.explain())
```

```text
Samsung QN90C
Confidence: 94%

Evidence:
- MAC prefix matches Samsung Electronics
- UPnP modelName reports QN90C
```

The method does not invent details that are absent from `device.evidence`

## Services

Each `Service` can contain a name, transport protocol, port, service type, and string metadata

```python
for service in device.services:
    print(service.name, service.protocol, service.port)
```

mDNS advertisements usually use `service_type`

Deep TCP checks usually use `protocol="tcp"` and a port number
