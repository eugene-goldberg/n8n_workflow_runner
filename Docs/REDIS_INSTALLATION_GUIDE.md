# Redis Installation Guide for n8n Chat Memory

This guide will help you install Redis on your Hostinger VPS alongside n8n for use with the Redis Chat Memory node.

## Prerequisites

- Docker and Docker Compose installed on your VPS
- Access to your VPS via SSH
- Basic understanding of Docker networking

## Option 1: Quick Setup (Recommended for Development)

### Step 1: Run Redis with Docker

```bash
# Pull and run Redis
docker run -d \
  --name redis \
  --restart unless-stopped \
  -p 6379:6379 \
  redis:7-alpine
```

### Step 2: Verify Redis is Running

```bash
# Check if Redis container is running
docker ps | grep redis

# Test Redis connection
docker exec -it redis redis-cli ping
# Should return: PONG
```

## Option 2: Docker Compose Setup (Recommended for Production)

### Step 1: Create Redis Directory

```bash
# SSH into your VPS
ssh your-user@your-hostinger-vps-ip

# Create directory for Redis
mkdir -p ~/redis
cd ~/redis
```

### Step 2: Create Docker Compose File

```bash
nano docker-compose.yml
```

Add the following content:

```yaml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    container_name: redis
    restart: unless-stopped
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes --requirepass your_secure_password_here
    networks:
      - redis-network
      - n8n-network  # Connect to n8n's network

volumes:
  redis_data:

networks:
  redis-network:
    driver: bridge
  n8n-network:
    external: true
    name: root_default  # Update this to match your n8n network name
```

### Step 3: Update Configuration

1. **Set a password**: Replace `your_secure_password_here` with a strong password
2. **Network name**: Update `root_default` to match your n8n's Docker network name

To find your n8n network name:
```bash
docker network ls | grep n8n
# or
docker inspect n8n | grep NetworkMode
```

### Step 4: Start Redis

```bash
# Start Redis service
docker-compose up -d

# Check logs
docker-compose logs -f redis
```

## Option 3: Redis with Persistence and Security

For production environments, create a Redis configuration file:

### Step 1: Create Redis Config

```bash
nano redis.conf
```

Add the following:

```conf
# Enable persistence
appendonly yes
appendfilename "appendonly.aof"
appendfsync everysec

# Set max memory (adjust based on your VPS)
maxmemory 256mb
maxmemory-policy allkeys-lru

# Security
requirepass your_secure_password_here
protected-mode yes

# Networking
bind 0.0.0.0
port 6379

# Logging
loglevel notice
logfile /data/redis.log
```

### Step 2: Update Docker Compose

```yaml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    container_name: redis
    restart: unless-stopped
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
      - ./redis.conf:/usr/local/etc/redis/redis.conf
    command: redis-server /usr/local/etc/redis/redis.conf
    networks:
      - redis-network
      - n8n-network

volumes:
  redis_data:

networks:
  redis-network:
    driver: bridge
  n8n-network:
    external: true
    name: root_default
```

## Configure n8n to Use Redis

### Step 1: Create Redis Credentials in n8n

1. In n8n, go to **Credentials** → **Create New**
2. Search for "Redis" and select it
3. Configure:
   - **Host**: 
     - If n8n is in Docker: `redis` (container name)
     - If n8n is on host: `localhost` or `127.0.0.1`
   - **Port**: `6379`
   - **Database**: `0` (default)
   - **Password**: Your Redis password (if set)

### Step 2: Test the Connection

1. Click "Test Connection" in the credentials dialog
2. You should see "Connection successful!"

## Using Redis in Your Workflow

### Step 1: Import the Workflow

1. Import `n8n-intent-routing-workflow-v7-redis-memory.json`
2. Find the "Redis Chat Memory" node
3. Update the credentials to use your Redis connection

### Step 2: Configure Memory Node

The Redis Chat Memory node is already configured with:
- **Session ID**: Uses `user_id` from incoming messages
- **Context Window**: 10 messages (adjustable)

## Troubleshooting

### Connection Issues

1. **Check Redis is running**:
   ```bash
   docker ps | grep redis
   ```

2. **Test Redis connection**:
   ```bash
   # Without password
   docker exec -it redis redis-cli ping

   # With password
   docker exec -it redis redis-cli -a your_secure_password_here ping
   ```

3. **Check Redis logs**:
   ```bash
   docker logs redis
   ```

### Network Issues

1. **Verify networks**:
   ```bash
   # List all networks
   docker network ls

   # Inspect n8n container to find its network
   docker inspect n8n | grep -i network

   # Ensure Redis is on the same network
   docker network connect [n8n-network-name] redis
   ```

2. **Test connectivity from n8n container**:
   ```bash
   # If n8n is in Docker
   docker exec -it n8n ping redis
   ```

### Memory Issues

1. **Check Redis memory usage**:
   ```bash
   docker exec -it redis redis-cli -a your_password_here info memory
   ```

2. **Clear specific sessions if needed**:
   ```bash
   # Connect to Redis
   docker exec -it redis redis-cli -a your_password_here

   # List all keys
   KEYS *

   # Delete specific session
   DEL "langchain:memory:user_123"
   ```

## Maintenance

### Backup Redis Data

```bash
# Create backup
docker exec redis redis-cli -a your_password_here --rdb /data/backup.rdb

# Copy backup to host
docker cp redis:/data/backup.rdb ./redis_backup_$(date +%Y%m%d).rdb
```

### Monitor Redis

```bash
# Real-time monitoring
docker exec -it redis redis-cli -a your_password_here monitor

# Check memory usage
docker exec -it redis redis-cli -a your_password_here info memory

# Check connected clients
docker exec -it redis redis-cli -a your_password_here client list
```

### Update Redis

```bash
# Pull latest image
docker pull redis:7-alpine

# Stop and recreate container
docker-compose down
docker-compose up -d
```

## Security Best Practices

1. **Always set a password** in production
2. **Use SSL/TLS** for external connections (requires additional setup)
3. **Limit network exposure** - only expose Redis to n8n
4. **Regular backups** of Redis data
5. **Monitor memory usage** to prevent OOM issues

## Quick Commands Reference

```bash
# Start Redis
docker start redis

# Stop Redis
docker stop redis

# Restart Redis
docker restart redis

# View logs
docker logs -f redis

# Connect to Redis CLI
docker exec -it redis redis-cli -a your_password_here

# Check Redis info
docker exec -it redis redis-cli -a your_password_here info

# Flush all data (WARNING: Deletes everything)
docker exec -it redis redis-cli -a your_password_here FLUSHALL
```

## Next Steps

1. Import and test the Redis-enabled workflow
2. Send test messages to verify memory persistence
3. Monitor Redis memory usage during operation
4. Set up automated backups for production use

---

**Note**: Redis is an in-memory database. While it has persistence options, ensure you have adequate RAM on your VPS for your expected usage.