#!/bin/bash

# AI English Teaching System - Backend Services Verification Script
# 此脚本用于验证 Docker 服务的运行状态

echo "===================================="
echo "AI 英语教学系统 - 服务验证脚本"
echo "===================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查 Docker 是否运行
echo -n "检查 Docker 守护进程... "
if docker info > /dev/null 2>&1; then
    echo -e "${GREEN}[运行中]${NC}"
else
    echo -e "${RED}[未运行]${NC}"
    echo "错误: Docker 守护进程未运行，请先启动 Docker Desktop"
    exit 1
fi

echo ""
echo "检查 Docker 服务状态..."
echo ""

# 检查服务函数
check_service() {
    local service_name=$1
    local container_name=$2
    local health_check=$3

    echo -n "  $service_name... "

    if docker ps --format '{{.Names}}' | grep -q "^${container_name}$"; then
        status=$(docker inspect --format='{{.State.Health.Status}}' ${container_name} 2>/dev/null)
        if [ "$status" == "healthy" ] || [ -z "$status" ]; then
            echo -e "${GREEN}[运行中]${NC}"
            return 0
        else
            echo -e "${YELLOW}[健康检查: $status]${NC}"
            return 1
        fi
    else
        echo -e "${RED}[未运行]${NC}"
        return 2
    fi
}

# 检查 PostgreSQL
if check_service "PostgreSQL 15" "english_teaching_postgres"; then
    echo "    连接字符串: postgresql://postgres:postgres@localhost:5432/english_teaching"
    echo "    管理界面 (PgAdmin): http://localhost:5050 (需要启动 tools profile)"
fi
echo ""

# 检查 Redis
if check_service "Redis 7" "english_teaching_redis"; then
    echo "    连接字符串: redis://localhost:6379"
    echo "    管理界面 (Redis Commander): http://localhost:8081 (需要启动 tools profile)"
fi
echo ""

# 检查 Qdrant
if check_service "Qdrant" "english_teaching_qdrant"; then
    echo "    HTTP API: http://localhost:6333"
    echo "    gRPC API: localhost:6334"
    echo "    Web UI: http://localhost:6333/dashboard"
fi
echo ""

# 检查端口占用
echo "检查端口占用情况..."
check_port() {
    local port=$1
    local service=$2
    echo -n "  端口 $port ($service)... "
    if lsof -i :$port > /dev/null 2>&1; then
        echo -e "${GREEN}[已使用]${NC}"
    else
        echo -e "${YELLOW}[空闲]${NC}"
    fi
}

check_port 5432 "PostgreSQL"
check_port 6379 "Redis"
check_port 6333 "Qdrant HTTP"
check_port 6334 "Qdrant gRPC"

echo ""
echo "===================================="
echo "服务验证完成"
echo "===================================="
echo ""
echo "快速命令:"
echo "  查看所有服务状态: docker-compose ps"
echo "  查看服务日志: docker-compose logs -f"
echo "  停止所有服务: docker-compose down"
echo "  启动管理工具: docker-compose --profile tools up -d"
echo ""
