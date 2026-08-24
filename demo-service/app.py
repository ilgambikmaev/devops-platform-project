from flask import Flask, jsonify, request
import socket
import os
import json
import time

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor

resource = Resource(attributes={"service.name": "demo-service"})
provider = TracerProvider(resource=resource)
otlp_exporter = OTLPSpanExporter(
    endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://tempo.monitoring.svc.cluster.local:4318/v1/traces")
)
provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
trace.set_tracer_provider(provider)

app = Flask(__name__)
FlaskInstrumentor().instrument_app(app)

producer = None

def get_producer():
    global producer
    if producer is None:
        from kafka import KafkaProducer
        brokers = os.getenv("KAFKA_BROKERS", "my-cluster-kafka-bootstrap.kafka.svc.cluster.local:9092")
        producer = KafkaProducer(
            bootstrap_servers=brokers,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            request_timeout_ms=5000,
        )
    return producer

@app.route("/")
def home():
    return jsonify({
        "message": "Hello from DevOps Platform demo-service!",
        "hostname": socket.gethostname(),
        "version": os.getenv("APP_VERSION", "dev")
    })

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

@app.route("/event", methods=["POST"])
def send_event():
    try:
        p = get_producer()
        payload = {
            "hostname": socket.gethostname(),
            "timestamp": time.time(),
            "data": request.get_json(silent=True) or {},
        }
        p.send("demo-events", payload)
        p.flush(timeout=5)
        return jsonify({"status": "sent", "topic": "demo-events"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
