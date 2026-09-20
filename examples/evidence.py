import asyncio

from hostlens import HostLens


async def main() -> None:
    device = await HostLens().identify("192.168.1.42")
    for evidence in device.evidence:
        print(evidence.source, evidence.field, evidence.value, evidence.confidence)


asyncio.run(main())
