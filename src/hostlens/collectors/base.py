"""Shared collector runner"""

import asyncio
import logging
from collections.abc import Sequence
from typing import Protocol

from hostlens.models import Evidence, Target

logger = logging.getLogger(__name__)


class Collector(Protocol):
    name: str

    async def collect(self, target: Target, timeout: float) -> list[Evidence]: ...


async def collect_evidence(
    collectors: Sequence[Collector],
    target: Target,
    timeout: float,
) -> list[Evidence]:
    """Run independent collectors together and isolate their failures"""
    results = await asyncio.gather(
        *(_collect_safely(collector, target, timeout) for collector in collectors)
    )
    return [item for result in results for item in result]


async def _collect_safely(
    collector: Collector,
    target: Target,
    timeout: float,
) -> list[Evidence]:
    try:
        async with asyncio.timeout(timeout):
            return await collector.collect(target, timeout)
    except Exception as error:
        logger.debug("Collector %s failed for %s: %s", collector.name, target.ip, error)
        return []
