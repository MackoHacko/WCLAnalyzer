import os
import time

from testcontainers.compose import DockerCompose

from cache import Cache

REDIS_PORT = 6379

TEST_INPUT = {
    "first": "sugar",
    "second": "threat",
    "third": 1337
}


def get_cache_key(namespace, func_input):
    return f"rc:{namespace}:[{func_input}, {{}}]"


def assert_and_get_host_port(compose, port):
    host = compose.get_service_host("redis-cache-test", REDIS_PORT)
    port = compose.get_service_port("redis-cache-test", REDIS_PORT)
    assert host == "0.0.0.0" and port == "6380"
    return host, port


def assert_key_exists(cache, namespace, test_input, exists):
    assert cache.key_exists(
        namespace,
        *test_input
    ) is exists


def test_should_insert_key_after_call():
    with DockerCompose(
        os.getcwd() + "/test",
        compose_file_name="docker-compose.yml",
        pull=True
    ) as compose:
        (host, port) = assert_and_get_host_port(compose, REDIS_PORT)

        cache = Cache(host, port)

        namespace = "insert-key-test"

        @cache(namespace=namespace)
        def test_func(first: str, second: str, third: int):
            return f"first second {third}"

        assert_key_exists(cache, namespace, list(TEST_INPUT.values()), exists = False)

        test_func(TEST_INPUT["first"], TEST_INPUT["second"], TEST_INPUT["third"])

        assert_key_exists(cache, namespace, list(TEST_INPUT.values()), exists = True)


def test_should_remove_key_after_ttl():
    with DockerCompose(
        os.getcwd() + "/test",
        compose_file_name="docker-compose.yml",
        pull=True
    ) as compose:
        (host, port) = assert_and_get_host_port(compose, REDIS_PORT)

        cache = Cache(host, port)

        namespace = "remove-key-test"

        @cache(namespace=namespace, ttl=1)
        def test_func(first: str, second: str, third: int):
            return f"first second {third}"

        test_func(TEST_INPUT["first"], TEST_INPUT["second"], TEST_INPUT["third"])

        assert_key_exists(cache, namespace, list(TEST_INPUT.values()), exists = True)

        time.sleep(1.1)

        assert_key_exists(cache, namespace, list(TEST_INPUT.values()), exists = False)


def test_should_respect_key_limit():
    with DockerCompose(
        os.getcwd() + "/test",
        compose_file_name="docker-compose.yml",
        pull=True
    ) as compose:
        (host, port) = assert_and_get_host_port(compose, REDIS_PORT)

        cache = Cache(host, port)

        namespace = "respect_key_limit"

        @cache(namespace=namespace, limit = 1)
        def test_func(test_input: int):
            return test_input

        assert cache.get_key_count() == 0

        test_func(1)

        # First call gives two keys. One for the base function and one for the inputs
        assert cache.get_key_count() == 2

        [test_func(i) for i in range(50)]

        assert cache.get_key_count() == 2


def test_should_evict_least_accessed():
    with DockerCompose(
        os.getcwd() + "/test",
        compose_file_name="docker-compose.yml",
        pull=True
    ) as compose:
        (host, port) = assert_and_get_host_port(compose, REDIS_PORT)

        cache = Cache(host, port)

        namespace = "evict-least-accessed"

        @cache(namespace=namespace, limit = 3)
        def test_func(test_input: int):
            return test_input

        func_input = range(3)
        keys = []

        # Create three keys
        [test_func(i) for i in func_input]
        [keys.append(get_cache_key(namespace, [i])) for i in func_input]
        keys.append(f'rc:{namespace}:keys')  # base function

        assert set(cache.get_all_keys()) == set(keys)

        # Access all except first input
        [test_func(i) for i in func_input[1:]]

        # Add new input
        test_func(3)
        keys.append(get_cache_key(namespace, [3]))

        diff = set(keys) - set(cache.get_all_keys())
        assert diff == set([keys[0]])
