import unittest
from unittest import mock

from alpha_factory_v1.backend import world_model as wm_mod


class DummyKafka:
    def produce(self, topic, payload):
        raise RuntimeError("boom")

    def poll(self, _):
        pass


class TestKafkaSend(unittest.TestCase):
    def test_exception_logged(self):
        saved = wm_mod._kafka
        wm_mod._kafka = DummyKafka()
        with mock.patch.object(wm_mod._LOG, "exception") as log_exc:
            wm_mod._kafka_send("test.topic", {"x": 1})
            log_exc.assert_called_once()
            msg, topic_arg = log_exc.call_args.args
            self.assertIn("Kafka emit failed", msg)
            self.assertEqual(topic_arg, "test.topic")
        wm_mod._kafka = saved


if __name__ == "__main__":
    unittest.main()
