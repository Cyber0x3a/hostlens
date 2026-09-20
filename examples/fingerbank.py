import asyncio
import os

from hostlens import HostLens


async def main() -> None:
    intel = HostLens(cloud=True, fingerbank_api_key=os.environ["FINGERBANK_API_KEY"])
    print(await intel.identify("192.168.1.42"))


asyncio.run(main())
