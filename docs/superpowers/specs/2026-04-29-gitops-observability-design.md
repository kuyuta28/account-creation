# GitOps + Observability Architecture Design

> **Spec Version:** 1.0
> **Date:** 2026-04-29
> **Status:** Draft

## 1. Executive Summary

Thiết kế kiến trúc enterprise cho hệ thống account-creation bao gồm:

1. **GitOps Configuration Management** — Config as Code, audit trail đầy đủ, rollback tức thì
2. **Full Observability Stack** — Distributed tracing, metrics, centralized logging, alerting

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              GIT REPOSITORY                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   config/   │  │  services/  │  │    k8s/    │  │  .github/   │         │
│  │   *.yaml    │  │   *.py      │  │  manifests │  │  workflows  │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
│         │                │                │                │                  │
│         └────────────────┼────────────────┼────────────────┘                  │
│                          ▼                                                    │
│               ┌─────────────────────┐                                          │
│               │   GitOps Pipeline   │                                          │
│               │   (GitHub Actions) │                                          │
│               └──────────┬──────────┘                                          │
│                          │                                                     │
│         ┌────────────────┼────────────────┐                                   │
│         ▼                ▼                ▼                                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                           │
│  │  Validator  │  │   Builder   │  │  Deployer   │                           │
│  │  - YAML     │  │  - Docker   │  │  - Compose  │                           │
│  │  - Schema   │  │  - Images   │  │  - Rolling  │                           │
│  │  - API keys │  │             │  │             │                           │
│  └─────────────┘  └─────────────┘  └─────────────┘                           │
│                                                                     │          │
└─────────────────────────────────────────────────────────────────────┼──────────┘
                                                                      │
                              ┌────────────────────────────────────────┐
                              │         DEPLOYMENT ENVIRONMENT         │
                              │                                         │
                              │  ┌───────────────────────────────────┐ │
                              │  │        SERVICE MESH LAYER         │ │
                              │  │                                   │ │
                              │  │  ┌─────────┐  ┌─────────┐       │ │
                              │  │  │ Traefik  │  │  Envoy  │       │ │
                              │  │  │ (proxy) │  │ (sidecar)│       │ │
                              │  │  └────┬────┘  └────┬────┘       │ │
                              │  └───────┼─────────────┼─────────────┘ │
                              │          │             │                │
                              │  ┌───────▼─────────────▼─────────────┐ │
                              │  │         SERVICES                  │ │
                              │  │                                   │ │
                              │  │  registrar  mail-service  aa-proxy│ │
                              │  │  tts-proxy   any-auto-reg         │ │
                              │  │                                   │ │
                              │  └───────────────┬───────────────────┘ │
                              │                  │                     │
                              │  ┌───────────────▼───────────────────┐ │
                              │  │      OPEN TELEMETRY COLLECTOR     │ │
                              │  │                                   │ │
                              │  │  traces ──► Jaeger                │ │
                              │  │  metrics ──► Prometheus           │ │
                              │  │  logs ──────► Loki                │ │
                              │  │                                   │ │
                              │  └───────────────┬───────────────────┘ │
                              │                  │                     │
                              │  ┌───────────────▼───────────────────┐ │
                              │  │         STORAGE & VISUALIZATION   │ │
                              │  │                                   │ │
                              │  │  Grafana (dashboards + alerting)   │ │
                              │  │  Jaeger (distributed traces)       │ │
                              │  │  Prometheus (metrics + alerting)   │ │
                              │  │  Loki (log aggregation)            │ │
                              │  │  AlertManager (routing alerts)     │ │
                              │  │                                   │ │
                              │  └───────────────────────────────────┘ │
                              │                                         │
                              └─────────────────────────────────────────┘
```

## 3. GitOps Configuration Management

### 3.1 Repository Structure

```
account-creation/
├── config/                          # ⭐ GitOps CONFIG REPO (TRUTH SOURCE)
│   ├── registrar/
│   │   ├── config.yaml              # Main config (validated)
│   │   ├── logging.yaml
│   │   ├── mail.yaml
│   │   ├── captcha.yaml
│   │   └── ... (all service configs)
│   ├── mail-service/
│   │   ├── config.yaml
│   │   └── providers.yaml
│   ├── aa-proxy/
│   │   └── config.yaml
│   ├── tts-proxy/
│   │   └── config.yaml
│   └── common/
│       └── defaults.yaml           # Shared default config
│
├── .github/
│   └── workflows/
│       ├── gitops-config.yml       # Config validation & deployment
│       ├── docker-build.yml        # Docker image builds
│       └── observability-alerts.yml # Alert rules
│
├── docker-compose.yml               # Main compose (reads from config/)
├── docker-compose.override.yml      # Local dev overrides
├── docker-compose.prod.yml          # Production overrides
│
└── services/                       # Service code
    ├── registrar/
    ├── mail-service/
    ├── aa-proxy/
    └── tts-proxy/
```

### 3.2 Config Validation Pipeline

```yaml
# .github/workflows/gitops-config.yml
name: GitOps Config Pipeline

on:
  push:
    paths:
      - 'config/**'
      - 'docker-compose*.yml'
  pull_request:
    paths:
      - 'config/**'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install validators
        run: |
          pip install pyyaml jsonschema

      - name: Validate YAML syntax
        run: |
          for f in config/**/*.yaml; do
            python -c "import yaml; yaml.safe_load(open('$f'))"
          done

      - name: Validate config schema
        run: |
          python .github/scripts/validate-config.py

      - name: Validate API keys format
        run: |
          python .github/scripts/validate-secrets.py

      - name: Check for secrets in config
        uses: trufflesecurity/trufflehog@main
        with:
          path: ./
          base64: false
```

### 3.3 Deployment Pipeline

```yaml
# .github/workflows/gitops-deploy.yml
name: GitOps Deployment

on:
  push:
    branches: [main]
    paths:
      - 'config/**'
      - 'docker-compose*.yml'
      - 'services/**'

env:
  REGISTRY: ghcr.io/${{ github.repository_owner }}
  DEPLOY_ENV: production

jobs:
  build:
    runs-on: ubuntu-latest
    outputs:
      images: ${{ steps.meta.outputs.images }}
    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/account-creation
          tags: |
            type=sha,prefix=
            type=ref,event=tag

      - name: Build and push registrar
        uses: docker/build-push-action@v5
        with:
          context: .
          file: ./registrar/Dockerfile
          push: true
          tags: ${{ env.REGISTRY }}/registrar:${{ github.sha }}

      # ... similar for other services

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Deploy to Server
        uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.PROD_HOST }}
          username: ${{ secrets.PROD_USER }}
          key: ${{ secrets.PROD_SSH_KEY }}
          script: |
            cd /opt/account-creation
            git pull origin main
            docker-compose -f docker-compose.prod.yml config
            docker-compose -f docker-compose.prod.yml pull
            docker-compose -f docker-compose.prod.yml up -d --no-deps
            docker system prune -f
```

### 3.4 Config File Schema

```python
# .github/scripts/config-schema.py
CONFIG_SCHEMA = {
    "type": "object",
    "required": ["version", "services"],
    "properties": {
        "version": {"type": "string", "pattern": "^\\d+\\.\\d+$"},
        "services": {
            "type": "object",
            "patternProperties": {
                "^[a-z-]+$": {
                    "type": "object",
                    "properties": {
                        "enabled": {"type": "boolean"},
                        "environment": {
                            "type": "object",
                            "patternProperties": {
                                "^[A-Z_]+$": {"type": "string"}
                            }
                        },
                        "replicas": {"type": "integer", "minimum": 1, "maximum": 10},
                        "health_check": {
                            "type": "object",
                            "properties": {
                                "path": {"type": "string"},
                                "interval": {"type": "string"},
                                "timeout": {"type": "string"}
                            }
                        }
                    }
                }
            }
        }
    }
}
```

## 4. Observability Stack

### 4.1 The Three Pillars

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           OBSERVABILITY STACK                               │
│                                                                             │
│    ┌──────────────┐     ┌──────────────┐     ┌──────────────┐              │
│    │   TRACES     │     │   METRICS    │     │    LOGS      │              │
│    │              │     │              │     │              │              │
│    │  OpenTelemetry│     │ Prometheus  │     │    Loki      │              │
│    │  + Jaeger    │     │  + Grafana   │     │  + Grafana   │              │
│    │              │     │              │     │              │              │
│    │  End-to-end  │     │  Time-series │     │  Aggregated  │              │
│    │  request     │     │  CPU, Mem,   │     │  application │              │
│    │  flow        │     │  Request/s   │     │  logs        │              │
│    └──────┬───────┘     └──────┬───────┘     └──────┬───────┘              │
│           │                    │                    │                      │
│           └────────────────────┼────────────────────┘                      │
│                                ▼                                           │
│                    ┌───────────────────────┐                               │
│                    │   GRAFANA UNIFIED    │                               │
│                    │      DASHBOARD       │                               │
│                    │                       │                               │
│                    │  - Service health    │                               │
│                    │  - Request latency   │                               │
│                    │  - Error rates       │                               │
│                    │  - Resource usage    │                               │
│                    │  - Log search        │                               │
│                    │  - Trace exploration │                               │
│                    └───────────────────────┘                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 OpenTelemetry Integration

```python
# common/src/common/telemetry.py
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes
import logging

class TelemetryManager:
    def __init__(self, service_name: str):
        self.service_name = service_name
        self._tracer = None
        self._meter = None

    def init_telemetry(self, otlp_endpoint: str):
        """Initialize OpenTelemetry with OTLP exporter."""
        resource = Resource.create({
            ResourceAttributes.SERVICE_NAME: self.service_name,
            ResourceAttributes.SERVICE_VERSION: "1.0.0",
            ResourceAttributes.DEPLOYMENT_ENVIRONMENT: os.getenv("APP_ENV", "dev"),
        })

        # Tracer setup
        trace_provider = TracerProvider(resource=resource)
        trace_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
        trace_provider.add_span_processor(
            BatchSpanProcessor(trace_exporter)
        )
        trace.set_tracer_provider(trace_provider)
        self._tracer = trace.get_tracer(self.service_name)

        # Meter setup
        metric_reader = PeriodicExportingMetricReader(
            OTLPMetricExporter(endpoint=otlp_endpoint),
            export_interval_millis=15000
        )
        meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
        metrics.set_meter_provider(meter_provider)
        self._meter = metrics.get_meter(self.service_name)

        # Logging integration
        logging.basicConfig(level=logging.INFO)
        handler = OTLPLogHandler(service_name=self.service_name, endpoint=otlp_endpoint)
        logging.root.handlers.append(handler)

    def create_span(self, name: str, attributes: dict = None):
        """Create a traced span."""
        return self._tracer.start_as_current_span(name, attributes=attributes)

    def record_metric(self, name: str, value: float, unit: str = "1"):
        """Record a metric."""
        counter = self._meter.create_counter(name, unit=unit)
        counter.add(value)

    def create_histogram(self, name: str, description: str, unit: str = "ms"):
        """Create a histogram for latency tracking."""
        return self._meter.create_histogram(name, description=description, unit=unit)
```

### 4.3 Service Instrumentation

```python
# Example: How each service uses telemetry
# registrar/src/api/routers/accounts.py

from common.telemetry import get_telemetry
from opentelemetry import trace

telemetry = get_telemetry()

@router.get("/accounts/{account_id}")
async def get_account(account_id: str):
    with telemetry.create_span("get_account", {"account_id": account_id}) as span:
        start = time.perf_counter()

        try:
            account = await account_service.get(account_id)
            span.set_attribute("account.found", True)

            # Record latency
            latency = (time.perf_counter() - start) * 1000
            telemetry.create_histogram(
                "account.get.latency",
                "Account fetch latency"
            ).record(latency)

            return ok(account)

        except Exception as e:
            span.record_exception(e)
            span.set_attribute("account.found", False)
            telemetry.record_metric("account.get.errors", 1)
            raise
```

### 4.4 Metrics to Collect

```python
# Standard metrics for all services
STANDARD_METRICS = {
    # HTTP metrics
    "http_requests_total": "Counter - Total HTTP requests",
    "http_request_duration_seconds": "Histogram - Request latency",
    "http_requests_in_flight": "Gauge - Concurrent requests",

    # Business metrics
    "account_creation_total": "Counter - Account creations",
    "account_creation_duration_seconds": "Histogram - Creation time",
    "mailbox_operations_total": "Counter - Mailbox operations",
    "image_lab_jobs_total": "Counter - Image lab jobs",
    "image_lab_job_duration_seconds": "Histogram - Job duration",

    # Health metrics
    "service_health_check": "Gauge - 1=healthy, 0=unhealthy",
    "dependency_health": "Gauge - External dependency health",

    # Resource metrics (auto-collected by Prometheus)
    "process_cpu_seconds_total": "Counter - CPU time",
    "process_memory_bytes": "Gauge - Memory usage",
    "process_open_fds": "Gauge - Open file descriptors",
}

# Service-specific metrics
SERVICE_METRICS = {
    "registrar": [
        "accounts_total",
        "accounts_by_status",
        "job_queue_size",
        "image_lab_pending_jobs",
        "image_lab_active_workers",
    ],
    "mail-service": [
        "mailbox_total",
        "email_sent_total",
        "email_received_total",
        "sms_sent_total",
        "circuit_breaker_state",
        "provider_latency",
    ],
    "aa-proxy": [
        "aa_sessions_total",
        "aa_requests_total",
        "aa_latency_seconds",
        "aa_errors_total",
    ],
    "tts-proxy": [
        "tts_requests_total",
        "tts_characters_processed",
        "tts_latency_seconds",
        "tts_errors_total",
    ],
}
```

### 4.5 Alert Rules

```yaml
# prometheus/alerts.yml
groups:
  - name: account_creation_alerts
    rules:
      # Service-level alerts
      - alert: ServiceDown
        expr: up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Service {{ $labels.instance }} is down"
          description: "{{ $labels.job }} has been down for more than 1 minute"

      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.01
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High error rate on {{ $labels.service }}"
          description: "Error rate is {{ $value | humanizePercentage }}"

      - alert: HighLatency
        expr: histogram_quantile(0.95, http_request_duration_seconds) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High latency on {{ $labels.service }}"
          description: "95th percentile latency is {{ $value }}s"

      # Business alerts
      - alert: AccountCreationFailureSpike
        expr: rate(account_creation_errors_total[5m]) > 0.1
        for: 3m
        labels:
          severity: critical
        annotations:
          summary: "Account creation failures detected"
          description: "More than 10% of account creations are failing"

      - alert: JobQueueBacklog
        expr: job_queue_size > 100
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Job queue backlog on {{ $labels.service }}"
          description: "{{ $value }} jobs pending for more than 10 minutes"

      # Resource alerts
      - alert: HighMemoryUsage
        expr: process_memory_bytes / process_memory_limit > 0.9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage on {{ $labels.instance }}"
          description: "Memory usage is at {{ $value | humanizePercentage }}"

      - alert: DiskSpaceLow
        expr: disk_free_bytes / disk_total_bytes < 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Low disk space on {{ $labels.instance }}"
          description: "Less than 10% disk space remaining"
```

### 4.6 Alert Routing

```yaml
# alertmanager/config.yml
global:
  smtp_smarthost: 'smtp.example.com:587'
  smtp_from: 'alerts@example.com'

route:
  group_by: ['alertname', 'severity']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  receiver: 'default'
  routes:
    - match:
        severity: critical
      receiver: 'pagerduty'
      continue: true

    - match:
        severity: warning
      receiver: 'slack'

    - match:
        service: registrar
      receiver: 'registrar-team'
      group_wait: 10s

receivers:
  - name: 'default'
    email_configs:
      - to: 'team@example.com'

  - name: 'slack'
    slack_configs:
      - channel: '#alerts'
        send_resolved: true
        api_url: 'https://hooks.slack.com/services/xxx'

  - name: 'pagerduty'
    pagerduty_configs:
      - service_key: 'PAGERDUTY_KEY'
        severity: critical

  - name: 'registrar-team'
    email_configs:
      - to: 'registrar-team@example.com'
```

## 5. Implementation Phases

### Phase 1: Infrastructure Setup (Week 1)
- [ ] Set up observability stack (Prometheus, Grafana, Loki, Jaeger)
- [ ] Configure Docker metrics export
- [ ] Set up GitHub Actions runners
- [ ] Create config validation pipeline

### Phase 2: Service Instrumentation (Week 2)
- [ ] Add OpenTelemetry to common library
- [ ] Instrument all services with tracing
- [ ] Add standard metrics to all endpoints
- [ ] Implement health check endpoints

### Phase 3: GitOps Pipeline (Week 3)
- [ ] Restructure repository for GitOps
- [ ] Implement config validation CI/CD
- [ ] Set up deployment pipeline
- [ ] Document workflow

### Phase 4: Alerting & Dashboards (Week 4)
- [ ] Create Grafana dashboards
- [ ] Configure alert rules
- [ ] Set up alert routing
- [ ] Runbooks documentation

## 6. Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Tracing | Jaeger + OpenTelemetry | Distributed request tracing |
| Metrics | Prometheus + Grafana | Time-series metrics & visualization |
| Logs | Loki + Grafana | Log aggregation |
| Alerting | AlertManager + PagerDuty | Alert routing |
| CI/CD | GitHub Actions | Automation |
| Container Registry | GHCR | Docker image storage |
| Service Mesh | Envoy (optional) | Sidecar proxy |

## 7. Cost Estimation

| Resource | Quantity | Monthly Cost |
|----------|----------|-------------|
| VMs (4x 4GB) | 4 | ~$80 |
| Object Storage (Loki) | 100GB | ~$5 |
| Container Registry | 10GB | ~$5 |
| Monitoring VMs | 2x 4GB | ~$40 |
| **Total** | | **~$130/month** |

## 8. Migration Strategy

### Incremental Migration (Zero Downtime)

1. **Week 1**: Add observability sidecar, no code changes
2. **Week 2**: Instrument new code paths only
3. **Week 3**: Backfill metrics for existing code
4. **Week 4**: GitOps migration (config-only change)

Each phase is independently deployable and reversible.
