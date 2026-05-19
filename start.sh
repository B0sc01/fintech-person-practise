#!/bin/bash
# Fintech Quant System - 一键启动脚本

set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

cleanup() {
    echo ""
    echo "正在停止所有服务..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    echo "已停止"
    exit 0
}
trap cleanup SIGINT SIGTERM

echo "========================================="
echo "  Fintech Quant - 量化交易学习系统"
echo "========================================="
echo ""

# Check Python dependencies
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "[!] Python 依赖未安装，正在安装..."
    cd "$PROJECT_DIR/backend"
    pip install -r requirements.txt
fi

# Check npm dependencies
if [ ! -d "$PROJECT_DIR/frontend/node_modules" ]; then
    echo "[!] npm 依赖未安装，正在安装..."
    cd "$PROJECT_DIR/frontend"
    npm install
fi

# Start backend
echo "[1/2] 启动后端服务 (port 8000)..."
cd "$PROJECT_DIR/backend"
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
sleep 2

# Verify backend
if curl -s http://localhost:8000/api/v1/health > /dev/null 2>&1; then
    echo "      后端已就绪: http://localhost:8000"
    echo "      API 文档:   http://localhost:8000/docs"
else
    echo "      [!] 后端启动失败，请检查错误信息"
    exit 1
fi

# Start frontend
echo "[2/2] 启动前端服务 (port 5173)..."
cd "$PROJECT_DIR/frontend"
npx vite --host 0.0.0.0 &
FRONTEND_PID=$!
sleep 2

echo ""
echo "========================================="
echo "  系统已启动!"
echo ""
echo "  前端页面: http://localhost:5173"
echo "  因子库:   http://localhost:5173/factors"
echo "  后端API:  http://localhost:8000/api/v1"
echo ""
echo "  按 Ctrl+C 停止所有服务"
echo "========================================="

wait
