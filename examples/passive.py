import asyncio

from hostlens import HostLens


async def main() -> None:
    async for event in HostLens().watch_network():
        print(event)


asyncio.run(main())
