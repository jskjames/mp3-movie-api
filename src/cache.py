import json
import logging

import fakeredis

logger = logging.getLogger(__name__)


class MovieCache:
    def __init__(self):
        self.client = fakeredis.FakeRedis(decode_responses=True)

    def make_key(self, limit):
        return f"movies:limit:{limit}"

    def get(self, limit):
        """Return the cached response, or None on a miss."""
        key = self.make_key(limit)
        value = self.client.get(key)
        if value is None:
            logger.debug("Cache MISS: %s", key)
            return None
        logger.debug("Cache HIT: %s", key)
        return json.loads(value)

    def set(self, limit, response):
        """Cache the complete response for 90 seconds."""
        self.client.set(self.make_key(limit), json.dumps(response), ex=90)

    def invalidate(self):
        """Clear all retrievals from this dedicated cache."""
        self.client.flushdb()
        logger.debug("Invalidated movie cache")
