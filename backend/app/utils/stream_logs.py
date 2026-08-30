from collections import deque
from datetime import datetime

# Keep the last 100 logs
SYSTEM_LOGS = deque(maxlen=100)

def add_log(level: str, system: str, message: str):
    log_entry = {
        "id": f"{datetime.utcnow().timestamp()}-{len(SYSTEM_LOGS)}",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "level": level,    # INFO, WARN, ERROR, SUCCESS
        "system": system,  # RAZORPAY, REVIVE-AI, POLICY, SYSTEM
        "message": message
    }
    SYSTEM_LOGS.append(log_entry)

def get_logs(since_id: str = None) -> list[dict]:
    logs = list(SYSTEM_LOGS)
    if not since_id:
        return logs
    
    # Find the index of the since_id
    for i, log in enumerate(logs):
        if log["id"] == since_id:
            return logs[i+1:]
    
    return logs
