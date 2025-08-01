# SpyroSolutions Agentic RAG - Production Deployment Guide

## Overview

This guide documents the production configuration for the SpyroSolutions Agentic RAG system deployed on Hostinger server (148.230.84.166).

## Production URLs

### API Endpoints
- **Direct API**: http://148.230.84.166:8058
- **Nginx Proxy**: http://srv928466.hstgr.cloud:8059
- **Health Check**: http://srv928466.hstgr.cloud:8059/health
- **API Docs**: http://srv928466.hstgr.cloud:8059/docs

### n8n Webhooks
- **Basic**: https://n8n.srv928466.hstgr.cloud/webhook/spyro-agentic-rag
- **Advanced**: https://n8n.srv928466.hstgr.cloud/webhook/spyro-rag-advanced
- **Stream Info**: https://n8n.srv928466.hstgr.cloud/webhook/spyro-agentic-rag-stream

### Monitoring
- **Prometheus**: http://srv928466.hstgr.cloud:9090
- **Grafana**: http://srv928466.hstgr.cloud:3000
  - Username: admin
  - Password: SpyroMonitor2025!

## Phase 7 Implementation Details

### 7.1 Nginx Reverse Proxy Configuration

**Location**: `/etc/nginx/sites-available/spyro-rag-api`

Key features:
- Upstream definition for load balancing readiness
- CORS headers for API access
- Special handling for Server-Sent Events
- Security headers (X-Frame-Options, X-XSS-Protection)
- Separate access/error logs

```nginx
upstream spyro_rag_api {
    server localhost:8058;
}

server {
    listen 8059;
    server_name srv928466.hstgr.cloud;
    
    # API proxy with CORS
    location / {
        proxy_pass http://spyro_rag_api;
        # ... full configuration in file
    }
}
```

### 7.2 SSL Configuration (Pending)

To enable HTTPS:
```bash
# Install Certbot
apt-get update
apt-get install certbot python3-certbot-nginx

# Get SSL certificate
certbot --nginx -d srv928466.hstgr.cloud

# Auto-renewal
certbot renew --dry-run
```

### 7.3 Monitoring Stack

#### Components Deployed:

1. **Prometheus** (Port 9090)
   - Scrapes metrics every 15 seconds
   - Monitors: Node, PostgreSQL, Neo4j, API
   - Data retention: 15 days (default)

2. **Grafana** (Port 3000)
   - Pre-configured datasource: Prometheus
   - Custom dashboard: SpyroSolutions Agentic RAG
   - Panels: CPU, Memory, Request Rate, Response Time

3. **Node Exporter** (Port 9100)
   - System metrics: CPU, Memory, Disk, Network

4. **PostgreSQL Exporter** (Port 9187)
   - Database metrics: Connections, queries, locks

#### Monitoring Configuration:
```yaml
# /root/spyro-monitoring/prometheus.yml
scrape_configs:
  - job_name: 'node'
    targets: ['node_exporter:9100']
  - job_name: 'postgres'
    targets: ['postgres_exporter:9187']
  - job_name: 'agentic-rag-api'
    targets: ['spyro_rag_api:8058']
```

### 7.4 Log Rotation

#### Nginx Logs
- Location: `/var/log/nginx/spyro-rag-*.log`
- Rotation: Daily, keep 14 days
- Compression: Enabled

#### Application Logs
- Location: `/root/spyro-agentic-rag/app/logs/*.log`
- Rotation: Daily or 50MB
- Retention: 30 days

#### Docker Logs
- Max size: 10MB per file
- Max files: 5
- Compression: Enabled

Configuration files:
- `/etc/logrotate.d/spyro-rag`
- `/etc/docker/daemon.json`

## Maintenance Tasks

### Daily Checks
1. Monitor Grafana dashboard for anomalies
2. Check API health endpoint
3. Review error logs

### Weekly Tasks
1. Review disk usage
2. Check log rotation
3. Update monitoring alerts

### Monthly Tasks
1. Security updates
2. Performance optimization review
3. Backup verification

## Troubleshooting

### Service Management
```bash
# Restart API
docker-compose -f /root/spyro-agentic-rag/docker-compose.yml restart

# Restart monitoring
docker-compose -f /root/spyro-monitoring/docker-compose.yml restart

# Check logs
docker logs spyro_rag_api -f
docker logs spyro_prometheus -f
docker logs spyro_grafana -f
```

### Common Issues

#### API Not Responding
1. Check container status: `docker ps`
2. Review logs: `docker logs spyro_rag_api`
3. Verify Nginx: `systemctl status nginx`

#### Monitoring Not Working
1. Check Prometheus targets: http://srv928466.hstgr.cloud:9090/targets
2. Verify network connectivity between containers
3. Check Grafana datasource configuration

#### High Memory Usage
1. Review container limits
2. Check for memory leaks in logs
3. Consider scaling horizontally

## Security Considerations

### Current Implementation
- Nginx security headers
- CORS configured for API access
- Monitoring behind authentication
- Log rotation to prevent disk fill

### Recommended Enhancements
1. Enable SSL/TLS (Certbot ready)
2. Implement API authentication
3. Set up firewall rules
4. Enable fail2ban for brute force protection
5. Regular security audits

## Backup Strategy

### What to Backup
1. PostgreSQL database: `spyro_rag_db`
2. Neo4j database: `/var/lib/neo4j/data`
3. Application configuration: `/root/spyro-agentic-rag/app/.env`
4. Nginx configurations
5. Monitoring dashboards

### Backup Commands
```bash
# PostgreSQL backup
docker exec n8n_postgres_memory pg_dump -U n8n_memory spyro_rag_db > backup.sql

# Neo4j backup
docker exec spyro_neo4j neo4j-admin database dump neo4j --to=/backups/

# Configuration backup
tar -czf config-backup.tar.gz /root/spyro-agentic-rag/app/.env /etc/nginx/sites-available/
```

## Performance Tuning

### PostgreSQL
- Connection pool: 20 (current)
- Shared buffers: Auto-configured
- Vector index: HNSW (optimized)

### API Service
- Workers: Auto (CPU count)
- Timeout: 300 seconds
- Keep-alive: 5 seconds

### Nginx
- Worker processes: Auto
- Worker connections: 1024
- Buffer sizes: Optimized for API

## Next Steps

1. **Enable SSL**: Run Certbot to secure API endpoints
2. **Set up Alerts**: Configure Prometheus alerting rules
3. **API Authentication**: Implement JWT or API key auth
4. **Horizontal Scaling**: Add load balancer for multiple API instances
5. **CDN Integration**: Cache static assets and API responses

## Support Contacts

- Server Admin: root@148.230.84.166
- Monitoring: http://srv928466.hstgr.cloud:3000
- API Health: http://srv928466.hstgr.cloud:8059/health