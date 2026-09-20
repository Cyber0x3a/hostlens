import asyncio

from hostlens import HostLens


async def main() -> None:
    for device in await HostLens().discover():
        print(device.ip, device.best_name)


asyncio.run(main())
