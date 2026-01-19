import os
import unittest

from alpha_factory_v1.backend.agents import base as base_mod

class TestPromMetrics(unittest.TestCase):
    def test_prom_metrics_none(self):
        orig_counter = base_mod.Counter
        orig_gauge = base_mod.Gauge
        base_mod.Counter = None
        base_mod.Gauge = None
        run, err, lat = base_mod._prom_metrics("x")
        self.assertIsNone(run)
        self.assertIsNone(err)
        self.assertIsNone(lat)
        base_mod.Counter = orig_counter
        base_mod.Gauge = orig_gauge

    def test_prom_metrics_stub(self):
        class Dummy:
            def __init__(self, *_, **__):
                self.label_arg = None
            def labels(self, name):
                self.label_arg = name
                return self
            def inc(self):
                pass
            def set(self, v):
                self.value = v
        orig_counter = base_mod.Counter
        orig_gauge = base_mod.Gauge
        base_mod.Counter = Dummy
        base_mod.Gauge = Dummy
        run, err, lat = base_mod._prom_metrics("test")
        self.assertIsInstance(run, Dummy)
        self.assertEqual(run.label_arg, "test")
        self.assertIsInstance(err, Dummy)
        self.assertIsInstance(lat, Dummy)
        base_mod.Counter = orig_counter
        base_mod.Gauge = orig_gauge

class TestKafkaProducer(unittest.TestCase):
    def test_no_broker(self):
        os.environ.pop("ALPHA_KAFKA_BROKER", None)
        orig = base_mod.KafkaProducer
        base_mod.KafkaProducer = object  # dummy
        self.assertIsNone(base_mod._kafka_producer())
        base_mod.KafkaProducer = orig

    def test_none_library(self):
        os.environ["ALPHA_KAFKA_BROKER"] = "localhost:9092"
        orig = base_mod.KafkaProducer
        base_mod.KafkaProducer = None
        self.assertIsNone(base_mod._kafka_producer())
        base_mod.KafkaProducer = orig
        os.environ.pop("ALPHA_KAFKA_BROKER", None)

    def test_stub_producer(self):
        class Stub:
            def __init__(self, bootstrap_servers=None, value_serializer=None, linger_ms=None):
                self.args = (bootstrap_servers, value_serializer, linger_ms)
        os.environ["ALPHA_KAFKA_BROKER"] = "a:1,b:2 ,"
        orig = base_mod.KafkaProducer
        base_mod.KafkaProducer = Stub
        prod = base_mod._kafka_producer()
        self.assertIsInstance(prod, Stub)
        self.assertEqual(prod.args[0], ["a:1", "b:2"])
        base_mod.KafkaProducer = orig
        os.environ.pop("ALPHA_KAFKA_BROKER", None)

class TestEnvSeconds(unittest.TestCase):
    def test_env_seconds(self):
        from alpha_factory_v1.backend.agents.ping_agent import _env_seconds, _MIN_INTERVAL
        os.environ.pop("X_INT", None)
        self.assertEqual(_env_seconds("X_INT", 42), 42)
        os.environ["X_INT"] = "2"
        self.assertEqual(_env_seconds("X_INT", 10), _MIN_INTERVAL)
        os.environ["X_INT"] = "15"
        self.assertEqual(_env_seconds("X_INT", 1), 15)
        os.environ["X_INT"] = "bad"
        self.assertEqual(_env_seconds("X_INT", 7), 7)
        os.environ.pop("X_INT", None)

if __name__ == "__main__":
    unittest.main()
