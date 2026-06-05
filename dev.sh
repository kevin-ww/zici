#!/bin/bash
# dev.sh — Manage the Zici dev stack
# Usage:
#   ./dev.sh start|stop|restart|status
#   ./dev.sh frontend start|stop|restart|status
#   ./dev.sh backend  start|stop|restart|status
#   ./dev.sh db       start|stop|restart|status

set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"
BACKEND_LOG="/tmp/zici-backend.log"
FRONTEND_LOG="/tmp/zici-frontend.log"
BACKEND_PID_FILE="/tmp/zici-backend.pid"
FRONTEND_PID_FILE="/tmp/zici-frontend.pid"
SUPABASE_LOG="/tmp/zici-supabase.log"

# Required for Colima Docker socket
export DOCKER_HOST="unix:///var/run/docker.sock"
# Clear proxy so Supabase connections work
unset all_proxy http_proxy https_proxy SUPABASE_ACCESS_TOKEN

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

ok()   { echo -e "${GREEN}✓${NC} $1"; }
err()  { echo -e "${RED}✗${NC} $1"; }
info() { echo -e "${YELLOW}→${NC} $1"; }

# ── Supabase ──────────────────────────────────────────────────────────────────

start_supabase() {
  info "Starting local Supabase..."
  if supabase status 2>/dev/null | grep -q "54322"; then
    ok "Supabase already running (port 54322)"
  else
    supabase start --workdir "$BACKEND_DIR" > "$SUPABASE_LOG" 2>&1 &
    SUPABASE_PID=$!
    for i in $(seq 1 20); do
      if psql postgresql://postgres:postgres@127.0.0.1:54322/postgres -c "SELECT 1" > /dev/null 2>&1; then
        ok "Supabase started"
        return
      fi
      if ! kill -0 "$SUPABASE_PID" 2>/dev/null; then
        err "Supabase failed to start — check $SUPABASE_LOG"
        tail -10 "$SUPABASE_LOG"
        return 1
      fi
      sleep 1
    done
    err "Supabase did not become ready — check $SUPABASE_LOG"
    tail -10 "$SUPABASE_LOG"
  fi
}

stop_supabase() {
  info "Stopping Supabase..."
  supabase stop --workdir "$BACKEND_DIR" 2>/dev/null && ok "Supabase stopped" || true
}

# ── Backend ───────────────────────────────────────────────────────────────────

start_backend() {
  info "Starting FastAPI backend on :8000..."
  if [ -f "$BACKEND_PID_FILE" ] && kill -0 "$(cat $BACKEND_PID_FILE)" 2>/dev/null; then
    ok "Backend already running (PID $(cat $BACKEND_PID_FILE))"
    return
  fi
  cd "$BACKEND_DIR"
  uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload \
    > "$BACKEND_LOG" 2>&1 &
  echo $! > "$BACKEND_PID_FILE"
  sleep 2
  if curl -sf http://localhost:8000/health > /dev/null; then
    ok "Backend running — http://localhost:8000  (docs: http://localhost:8000/docs)"
  else
    err "Backend failed to start — check $BACKEND_LOG"
    cat "$BACKEND_LOG" | tail -10
  fi
}

stop_backend() {
  if [ -f "$BACKEND_PID_FILE" ]; then
    PID=$(cat "$BACKEND_PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
      kill "$PID" && ok "Backend stopped (PID $PID)"
    fi
    rm -f "$BACKEND_PID_FILE"
  else
    # fallback: kill by port
    lsof -ti :8000 | xargs kill -9 2>/dev/null && ok "Backend stopped" || true
  fi
}

# ── Frontend ──────────────────────────────────────────────────────────────────

start_frontend() {
  info "Starting Next.js frontend on :3000..."
  if [ -f "$FRONTEND_PID_FILE" ] && kill -0 "$(cat $FRONTEND_PID_FILE)" 2>/dev/null; then
    ok "Frontend already running (PID $(cat $FRONTEND_PID_FILE))"
    return
  fi
  # Kill anything squatting on 3000
  lsof -ti :3000 | xargs kill -9 2>/dev/null || true
  cd "$PROJECT_DIR"
  npm run dev > "$FRONTEND_LOG" 2>&1 &
  echo $! > "$FRONTEND_PID_FILE"
  # Wait up to 15s for Next.js to be ready
  for i in $(seq 1 15); do
    if curl -sf http://localhost:3000 > /dev/null; then
      ok "Frontend running — http://localhost:3000"
      return
    fi
    sleep 1
  done
  err "Frontend failed to start — check $FRONTEND_LOG"
  tail -10 "$FRONTEND_LOG"
}

stop_frontend() {
  if [ -f "$FRONTEND_PID_FILE" ]; then
    PID=$(cat "$FRONTEND_PID_FILE")
    # Kill the process group so child processes (Next.js workers) also die
    if kill -0 "$PID" 2>/dev/null; then
      kill -- -"$PID" 2>/dev/null || kill "$PID"
      ok "Frontend stopped (PID $PID)"
    fi
    rm -f "$FRONTEND_PID_FILE"
  else
    lsof -ti :3000 | xargs kill -9 2>/dev/null && ok "Frontend stopped" || true
  fi
}

# ── Status ────────────────────────────────────────────────────────────────────

status() {
  echo ""
  echo "── Zici Dev Stack Status ──────────────────────────"

  # Supabase
  if psql postgresql://postgres:postgres@127.0.0.1:54322/postgres \
       -c "SELECT 1" > /dev/null 2>&1; then
    ok "Supabase     postgresql://postgres:postgres@127.0.0.1:54322/postgres"
    info "Logs         $SUPABASE_LOG"
  else
    err "Supabase     not running"
    info "Logs         $SUPABASE_LOG"
  fi

  # Backend
  if curl -sf http://localhost:8000/health > /dev/null; then
    ok "Backend      http://localhost:8000  (docs: http://localhost:8000/docs)"
    info "Logs         $BACKEND_LOG"
  else
    err "Backend      not running"
    info "Logs         $BACKEND_LOG"
  fi

  # Frontend
  if curl -sf http://localhost:3000 > /dev/null; then
    ok "Frontend     http://localhost:3000"
    info "Logs         $FRONTEND_LOG"
  else
    err "Frontend     not running"
    info "Logs         $FRONTEND_LOG"
  fi

  echo "────────────────────────────────────────────────────"
  echo ""
  echo "  Logs:  tail -f $BACKEND_LOG"
  echo "         tail -f $FRONTEND_LOG"
  echo ""
}

status_supabase_only() {
  if psql postgresql://postgres:postgres@127.0.0.1:54322/postgres \
       -c "SELECT 1" > /dev/null 2>&1; then
    ok "Supabase     postgresql://postgres:postgres@127.0.0.1:54322/postgres"
    info "Logs         $SUPABASE_LOG"
  else
    err "Supabase     not running"
    info "Logs         $SUPABASE_LOG"
  fi
}

status_backend_only() {
  if curl -sf http://localhost:8000/health > /dev/null; then
    ok "Backend      http://localhost:8000  (docs: http://localhost:8000/docs)"
    info "Logs         $BACKEND_LOG"
  else
    err "Backend      not running"
    info "Logs         $BACKEND_LOG"
  fi
}

status_frontend_only() {
  if curl -sf http://localhost:3000 > /dev/null; then
    ok "Frontend     http://localhost:3000"
    info "Logs         $FRONTEND_LOG"
  else
    err "Frontend     not running"
    info "Logs         $FRONTEND_LOG"
  fi
}

# ── Commands ──────────────────────────────────────────────────────────────────

start_all() {
  echo ""
  echo "Starting Zici dev stack..."
  start_supabase
  start_backend
  start_frontend
  echo ""
  status
}

stop_all() {
  echo ""
  echo "Stopping Zici dev stack..."
  stop_frontend
  stop_backend
  stop_supabase
  echo ""
  ok "All services stopped"
}

service_cmd() {
  local service="$1"
  local action="$2"

  case "$service" in
    frontend)
      case "$action" in
        start) start_frontend ;;
        stop) stop_frontend ;;
        restart) stop_frontend; sleep 1; start_frontend ;;
        status) status_frontend_only ;;
        *) return 1 ;;
      esac
      ;;
    backend)
      case "$action" in
        start) start_backend ;;
        stop) stop_backend ;;
        restart) stop_backend; sleep 1; start_backend ;;
        status) status_backend_only ;;
        *) return 1 ;;
      esac
      ;;
    db|database|supabase)
      case "$action" in
        start) start_supabase ;;
        stop) stop_supabase ;;
        restart) stop_supabase; sleep 1; start_supabase ;;
        status) status_supabase_only ;;
        *) return 1 ;;
      esac
      ;;
    *)
      return 1
      ;;
  esac
}

case "${1:-}" in
  start)   start_all ;;
  stop)    stop_all ;;
  restart) stop_all; sleep 1; start_all ;;
  status)  status ;;
  frontend|backend|db|database|supabase)
    if [ -z "${2:-}" ]; then
      echo "Usage: ./dev.sh $1 start|stop|restart|status"
      exit 1
    fi
    service_cmd "$1" "$2"
    ;;
  *)
    echo "Usage: ./dev.sh start|stop|restart|status"
    echo "       ./dev.sh frontend start|stop|restart|status"
    echo "       ./dev.sh backend  start|stop|restart|status"
    echo "       ./dev.sh db       start|stop|restart|status"
    echo ""
    echo "  start    — Start Supabase, FastAPI backend, and Next.js frontend"
    echo "  stop     — Stop all three"
    echo "  restart  — Stop then start"
    echo "  status   — Check what's running"
    echo ""
    echo "  frontend — Manage only Next.js"
    echo "  backend  — Manage only FastAPI"
    echo "  db       — Manage only local Supabase"
    exit 1
    ;;
esac
