from alpha_factory_v1.backend.services.kafka_service import KafkaService


def test_kafka_service_publish(monkeypatch):
    events = []

    class DummyBus:
        def __init__(self, *_a, **_k):
            pass

        def publish(self, topic, msg):
            events.append((topic, msg))

    monkeypatch.setattr(
        "alpha_factory_v1.backend.services.kafka_service.EventBus",
        DummyBus,
    )

    svc = KafkaService("broker", False)
    svc.publish("x", {"y": 1})
    assert events == [("x", {"y": 1})]
