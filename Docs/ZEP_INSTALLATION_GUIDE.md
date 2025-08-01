# Zep Memory Installation Guide for Hostinger VPS

This guide will help you install Zep Memory service on your Hostinger VPS alongside n8n using Docker.

## Prerequisites

- Docker and Docker Compose installed on your VPS
- Access to your VPS via SSH
- Sufficient disk space (Zep requires ~2GB for installation)

## Step 1: Create Zep Directory

```bash
# SSH into your VPS
ssh your-user@your-hostinger-vps-ip

# Create directory for Zep
mkdir -p ~/zep
cd ~/zep
```

## Step 2: Create Docker Compose File

Create a `docker-compose.yml` file for Zep:

```bash
nano docker-compose.yml
```

Add the following content:

```yaml
version: '3.8'

services:
  zep:
    image: ghcr.io/getzep/zep:latest
    container_name: zep
    restart: unless-stopped
    ports:
      - "8585:8000"  # Expose Zep on port 8585 (change if needed)
    environment:
      - ZEP_STORE_TYPE=postgres
      - ZEP_STORE_POSTGRES_DSN=postgres://zep_user:your_secure_password@zep-postgres:5432/zep?sslmode=disable
      - ZEP_NLP_SERVER_URL=http://zep-nlp:5557
      - ZEP_AUTH_REQUIRED=false  # Set to true for production
      - ZEP_AUTH_SECRET=your-secret-key-here  # Change this!
      - ZEP_LOG_LEVEL=info
    depends_on:
      - zep-postgres
      - zep-nlp
    networks:
      - zep-network
      - n8n-network  # Connect to n8n's network

  zep-postgres:
    image: postgres:15-alpine
    container_name: zep-postgres
    restart: unless-stopped
    environment:
      - POSTGRES_USER=zep_user
      - POSTGRES_PASSWORD=your_secure_password  # Change this!
      - POSTGRES_DB=zep
    volumes:
      - zep_postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U zep_user"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - zep-network

  zep-nlp:
    image: ghcr.io/getzep/zep-nlp:latest
    container_name: zep-nlp
    restart: unless-stopped
    environment:
      - ZEP_NLP_LOG_LEVEL=info
    networks:
      - zep-network

volumes:
  zep_postgres_data:

networks:
  zep-network:
    driver: bridge
  n8n-network:
    external: true  # Assumes n8n network already exists
    name: root_default  # Update this to match your n8n network name
```

## Step 3: Update Configuration

1. **Change passwords**: Replace `your_secure_password` with a strong password
2. **Set auth secret**: Replace `your-secret-key-here` with a secure random string
3. **Network name**: Update `root_default` to match your n8n's Docker network name

To find your n8n network name:
```bash
docker network ls | grep n8n
```

## Step 4: Start Zep Services

```bash
# Start Zep services
docker-compose up -d

# Check if services are running
docker-compose ps

# View logs
docker-compose logs -f
```

## Step 5: Verify Installation

1. Check if Zep is running:
```bash
curl http://localhost:8585/healthz
```

Expected response: `{"status":"ok"}`

2. Test the API:
```bash
curl http://localhost:8585/api/v1/sessions
```

## Step 6: Configure n8n to Use Zep

1. In n8n, go to **Credentials** → **Create New**
2. Search for "Zep" and select it
3. Configure:
   - **API URL**: `http://zep:8000` (if n8n is in Docker) or `http://localhost:8585` (if n8n is on host)
   - **API Key**: Leave empty if `ZEP_AUTH_REQUIRED=false`, otherwise use your configured key

## Step 7: Configure Firewall (if needed)

If you need to access Zep from outside your VPS:

```bash
# Allow port 8585 (only if needed for external access)
sudo ufw allow 8585/tcp
```

**Warning**: Only expose Zep externally if you've enabled authentication!

## Step 8: Production Considerations

For production use:

1. **Enable Authentication**:
   ```yaml
   ZEP_AUTH_REQUIRED=true
   ZEP_AUTH_SECRET=<generate-strong-secret>
   ```

2. **Use environment file** instead of hardcoding secrets:
   ```bash
   # Create .env file
   nano .env
   ```
   
   Add:
   ```
   POSTGRES_PASSWORD=your_secure_password
   ZEP_AUTH_SECRET=your_secret_key
   ```

3. **Configure SSL/TLS** with a reverse proxy (nginx/traefik)

4. **Resource Limits** (add to docker-compose.yml):
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '2'
         memory: 2G
   ```

## Troubleshooting

1. **Check logs**:
   ```bash
   docker-compose logs zep
   docker-compose logs zep-postgres
   docker-compose logs zep-nlp
   ```

2. **Restart services**:
   ```bash
   docker-compose restart
   ```

3. **Common issues**:
   - Port conflicts: Change `8585` to another port
   - Memory issues: Ensure sufficient RAM (minimum 2GB recommended)
   - Network issues: Verify n8n and Zep are on the same Docker network

## Testing Zep with n8n

1. Import the provided workflow (`n8n-intent-routing-workflow-v6-zep-memory.json`)
2. Configure the Zep Memory node with your credentials
3. Test with messages to verify memory persistence

## Maintenance

1. **Backup Zep data**:
   ```bash
   docker exec zep-postgres pg_dump -U zep_user zep > zep_backup_$(date +%Y%m%d).sql
   ```

2. **Update Zep**:
   ```bash
   docker-compose pull
   docker-compose up -d
   ```

3. **Monitor disk usage**:
   ```bash
   docker volume ls
   docker system df
   ```

## Additional Resources

- [Zep Documentation](https://docs.getzep.com/)
- [Zep GitHub Repository](https://github.com/getzep/zep)
- [n8n Zep Node Documentation](https://docs.n8n.io/integrations/builtin/cluster-nodes/sub-nodes/n8n-nodes-langchain.memoryZep/)

---

**Note**: This setup creates a basic Zep installation. For production environments, consider additional security measures, monitoring, and backup strategies.