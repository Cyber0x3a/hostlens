# Platform notes

Network discovery is partly dependent on the operating system

HostLens handles unavailable collectors as missing evidence, so one unsupported method does not normally stop a scan

## Windows

The neighbor table reader uses `arp -a`

Active ARP uses Scapy and may need [Npcap](https://npcap.com/)

If active discovery returns no devices, try an elevated terminal once to separate a permission problem from a network problem

Windows interface names such as `Wi-Fi` can be passed to `HostLens(interface=...)`

NetBIOS checks in deep mode are useful mainly for Windows devices and older network appliances

## Linux

The neighbor table reader first tries `arp -a`, then `ip neigh show`

Scapy needs raw socket access for ARP discovery

Containers often lack both access to the physical LAN and the required network capability, even when the same command works on the host

## macOS

The neighbor table reader uses `arp -a`

Raw packet access may require elevation

Interface selection can use the system adapter name reported by the host

## IPv4 and IPv6

Targeted identification accepts an IPv4 or IPv6 address

Active subnet discovery currently accepts IPv4 CIDR ranges only

ARP is an IPv4 protocol

The current mDNS collector runs with `IPVersion.V4Only`

## Firewalls and client isolation

A local firewall can block replies to UDP discovery or TCP service checks

Wireless access points may isolate clients from each other

In either case, HostLens can only report facts that reach the machine running the scan

## Multiple adapters

Automatic selection follows the preferred IPv4 route

VPNs, virtual machines, and container adapters can change that route

Pass the desired interface when automatic selection chooses the wrong network

```python
intel = HostLens(interface="Wi-Fi")
```
