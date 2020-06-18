from json import dumps

from redis import StrictRedis
from redis_cache import RedisCache

from loggers.logger import Logger


class Cache():
    def __init__(
        self,
        host: str = 'localhost',
        port: int = 6379
    ) -> None:
        self.__client = StrictRedis(host, port=port, decode_responses=True)
        self.__client.config_set('maxmemory', '256mb')
        self.__cache = RedisCache(redis_client=self.__client)
        self.__logger = Logger().getLogger(__file__)
        self.__logger.info("Initialize Cache.")

    def key_exists(self, *args):
        serialized_data = dumps([args[1:], {}])
        key = f'rc:{args[0]}:{serialized_data}'
        return self.__client.exists(key) >= 1

    def __call__(self, ttl=60 * 10, limit=100, namespace=None):
        return self.__cache.cache(ttl, limit, namespace)


if __name__ == "__main__":
    # connect to redis
    cache = Cache()

    @cache(ttl=60 * 1, limit=10)
    def yeah_man(x, y):
        return x + y

    for i in range(10):
        print(yeah_man(i, i))

    print(cache.key_exists('__main__.yeah_man', 7, 7))
