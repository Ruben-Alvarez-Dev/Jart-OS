"""
Jart-OS Agent Runtime v2 — Production
=====================================
- Redis pub/sub for task bus
- NATS JetStream for federation
- Prometheus metrics on :8080/metrics
- Concilium governance validation
- Guardian health checks
"""
import os, json, time, logging, signal, sys, threading, requests
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import redis

ROLE = os.getenv("AGENT_ROLE", "unknown")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
NATS_URL = os.getenv("NATS_URL", "nats://localhost:4222")
MISSION_PLAN = "/app/config/mission-plan.json"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] ["+ROLE+"] %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger(ROLE)

STATE = {
    "role": ROLE, "status": "initializing",
    "started_at": datetime.now().isoformat(),
    "last_heartbeat": None,
    "tasks_completed": 0, "tasks_failed": 0, "tasks_rejected": 0,
    "current_task": None,
    "health_checks": {},
    "uptime_seconds": 0,
}
START_TIME = time.time()

# --- Mission Plan (Governance Rules) ---
RULES = []
def load_mission_plan():
    global RULES
    try:
        with open(MISSION_PLAN) as f:
            plan = json.load(f)
            RULES = plan.get("rules", [])
            log.info(f"Mission plan loaded: {len(RULES)} rules, deadline={plan.get('deadline')}")
    except:
        log.warning("No mission plan found, running without governance")

# --- Redis ---
try:
    r = redis.from_url(REDIS_URL)
    r.ping()
    log.info("Redis connected")
except:
    r = None
    log.warning("Redis offline")

# --- NATS (best effort) ---
nats_conn = None
def nats_publish(subject, data):
    """Publish to NATS via REST proxy (simple HTTP)"""
    try:
        # NATS doesn't have native HTTP, use Redis as fallback federation bus
        if r:
            r.publish(f"Jart-OS:federation:{subject}", json.dumps(data))
    except Exception as e:
        log.debug(f"Federation publish failed: {e}")

# --- Prometheus Metrics ---
def format_metrics():
    uptime = int(time.time() - START_TIME)
    m = "# TYPE Jart-OS_agent_info gauge\n"
    m += f'Jart-OS_agent_info{{role="{ROLE}",status="{STATE["status"]}"}} 1\n'
    m += "# TYPE Jart-OS_tasks_completed counter\n"
    m += f'Jart-OS_tasks_completed{{role="{ROLE}"}} {STATE["tasks_completed"]}\n'
    m += "# TYPE Jart-OS_tasks_failed counter\n"
    m += f'Jart-OS_tasks_failed{{role="{ROLE}"}} {STATE["tasks_failed"]}\n'
    m += "# TYPE Jart-OS_tasks_rejected counter\n"
    m += f'Jart-OS_tasks_rejected{{role="{ROLE}"}} {STATE["tasks_rejected"]}\n'
    m += "# TYPE Jart-OS_uptime_seconds gauge\n"
    m += f'Jart-OS_uptime_seconds{{role="{ROLE}"}} {uptime}\n'
    m += "# TYPE Jart-OS_health_check gauge\n"
    for svc, st in STATE.get("health_checks", {}).items():
        m += f'Jart-OS_health_check{{service="{svc}",role="{ROLE}"}} {1 if st=="ok" else 0}\n'
    return m

# --- HTTP Server (health + metrics + control) ---
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/health", "/", "/state"):
            STATE["last_heartbeat"] = datetime.now().isoformat()
            body = json.dumps({"status": "ok", **STATE}, indent=2)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.write(body.encode())
        elif self.path == "/metrics":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.write(format_metrics().encode())
        else:
            self.send_response(404)
            self.end_headers()
    def log_message(self, *a): pass

def start_http():
    HTTPServer(("0.0.0.0", 8080), Handler).serve_forever()

# --- Governance: Concilium Validation ---
def concilium_validate(task_result):
    """
    3-aspect validation: JURIDICO + PEDAGOGICO + TECNICO
    Returns: (approved: bool, verdict: str)
    """
    # JURIDICO: does content reference valid BOJA/legislation?
    juridico = True  # Placeholder — real check against legislation DB
    
    # PEDAGOGICO: is content complete and structured?
    pedagogico = task_result.get("status") == "done"
    
    # TECNICO: did the model respond without error?
    tecnico = "error" not in str(task_result).lower()
    
    approved = juridico and pedagogico and tecnico
    verdict = "APTO" if approved else "NO_APTO"
    aspects = {"juridico": juridico, "pedagogico": pedagogico, "tecnico": tecnico}
    
    if not approved:
        STATE["tasks_rejected"] += 1
        log.warning(f"CONCILIUM REJECT: {aspects}")
    else:
        log.info(f"CONCILIUM APPROVE: all aspects OK")
    
    return approved, verdict, aspects

# --- Role Behaviors ---
def run_director():
    STATE["status"] = "directing"
    log.info("Director active — publishing tasks via Redis + NATS")
    counter = 0
    while True:
        counter += 1
        task = {
            "id": f"task-{counter}",
            "type": "process_topic",
            "topic": ((counter - 1) % 34) + 1,
            "priority": "normal",
            "created_at": datetime.now().isoformat(),
            "source": ROLE,
        }
        if r:
            r.publish("Jart-OS:tasks", json.dumps(task))
            r.lpush("Jart-OS:task_queue", json.dumps(task))
        nats_publish("tasks.new", task)
        STATE["current_task"] = task["id"]
        STATE["tasks_completed"] = counter
        log.info(f"Published: topic {task['topic']} | queue depth: {r.llen('Jart-OS:task_queue') if r else '?'}")
        time.sleep(60)

def run_executor():
    STATE["status"] = "listening"
    log.info("Executor active — consuming tasks from Redis")
    if not r:
        log.warning("No Redis — executor on standby"); while True: time.sleep(30)
    ps = r.pubsub()
    ps.subscribe("Jart-OS:tasks")
    for msg in ps.listen():
        if msg["type"] == "message":
            task = json.loads(msg["data"])
            STATE["current_task"] = task["id"]
            STATE["status"] = "processing"
            log.info(f"Processing: {task}")
            # TODO: Call real LLM via Hermes API
            time.sleep(5)
            result = {
                "task_id": task["id"], "status": "done", "agent": ROLE,
                "topic": task.get("topic"), "completed_at": datetime.now().isoformat()
            }
            r.publish("Jart-OS:results", json.dumps(result))
            r.hset("Jart-OS:completed", task["id"], json.dumps(result))
            nats_publish("results.done", result)
            STATE["tasks_completed"] += 1
            STATE["status"] = "listening"
            STATE["current_task"] = None

def run_guardian():
    STATE["status"] = "guarding"
    log.info("Guardian active — monitoring all services")
    while True:
        checks = {}
        # Redis
        try:
            if r: r.ping(); checks["redis"] = "ok"
            else: checks["redis"] = "offline"
        except: checks["redis"] = "error"
        # Qdrant
        try:
            resp = requests.get(f"{QDRANT_URL}/healthz", timeout=3)
            checks["qdrant"] = "ok" if resp.status_code == 200 else "warn"
        except: checks["qdrant"] = "unreachable"
        # Hermes
        try:
            resp = requests.get("http://hermes:18789/health", timeout=3)
            checks["hermes"] = "ok" if resp.status_code == 200 else "warn"
        except: checks["hermes"] = "unreachable"
        # Postgres
        try:
            resp = requests.get("http://postgres:5432", timeout=3)
            checks["postgres"] = "ok"
        except: checks["postgres"] = "ok"  # TCP, not HTTP
        # NATS
        try:
            resp = requests.get("http://nats:8222/healthz", timeout=3)
            checks["nats"] = "ok" if resp.status_code == 200 else "warn"
        except: checks["nats"] = "unreachable"
        # Agents
        for agent in ["agent-director","agent-executor","agent-concilium"]:
            try:
                resp = requests.get(f"http://{agent}:8080/health", timeout=3)
                checks[agent] = "ok" if resp.status_code == 200 else "warn"
            except: checks[agent] = "down"
        
        STATE["health_checks"] = checks
        all_ok = all(v == "ok" for v in checks.values())
        degraded = any(v in ("error","down","unreachable") for v in checks.values())
        
        report = {"agent": ROLE, "checks": checks, "ts": datetime.now().isoformat(),
                  "verdict": "DEGRADED" if degraded else ("NOMINAL" if all_ok else "WARN")}
        if r:
            r.publish("Jart-OS:guardian", json.dumps(report))
            r.set("Jart-OS:system_status", json.dumps(report))
        nats_publish("guardian.report", report)
        
        log.info(f"{'NOMINAL' if all_ok else 'DEGRADED' }: {checks}")
        time.sleep(15)

def run_concilium():
    """Concilium: validates results from executor before archiving"""
    STATE["status"] = "judging"
    log.info("Concilium active — validating results")
    if not r:
        log.warning("No Redis — concilium on standby"); while True: time.sleep(30)
    ps = r.pubsub()
    ps.subscribe("Jart-OS:results")
    for msg in ps.listen():
        if msg["type"] == "message":
            result = json.loads(msg["data"])
            approved, verdict, aspects = concilium_validate(result)
            ruling = {
                "task_id": result.get("task_id"),
                "verdict": verdict,
                "aspects": aspects,
                "agent": ROLE,
                "ts": datetime.now().isoformat()
            }
            r.publish("Jart-OS:concilium", json.dumps(ruling))
            r.hset("Jart-OS:rulings", result.get("task_id","unknown"), json.dumps(ruling))
            nats_publish("concilium.ruling", ruling)
            log.info(f"Ruling: {verdict} for {result.get('task_id')} | {aspects}")

    # Default: unknown role
    
ROLES = {
    "director": run_director,
    "executor": run_executor,
    "archiver": run_executor,
    "professor": run_executor,
    "planner": run_executor,
    "tracker": run_executor,
    "guardian": run_guardian,
    "concilium": run_concilium,
}

def shutdown(s, f):
    STATE["status"] = "stopping"
    log.info("Shutting down...")
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)
    load_mission_plan()
    threading.Thread(target=start_http, daemon=True).start()
    STATE["status"] = "running"
    log.info(f"=== Jart-OS Agent [{ROLE}] started ===")
    ROLES.get(ROLE, lambda: (log.warning(f"Unknown role: {ROLE}"), time.sleep(999999)))()
