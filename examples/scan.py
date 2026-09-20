import asyncio

from hostlens import HostLens


async def main() -> None:
    async for event in HostLens().scan_stream(mode="normal"):
        print(event)


asyncio.run(main())
