from alpha_factory_v1.backend.services.metrics_service import MetricsExporter


def test_metrics_exporter_start(monkeypatch):
    called = []
    monkeypatch.setattr(
        "alpha_factory_v1.backend.services.metrics_service.init_metrics",
        lambda port: called.append(port),
    )
    exporter = MetricsExporter(9999)
    exporter.start()
    assert called == [9999]
