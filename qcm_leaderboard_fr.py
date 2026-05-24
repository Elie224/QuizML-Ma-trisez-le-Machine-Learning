import json
import csv
from io import StringIO
from datetime import datetime, timezone
from pathlib import Path


LEADERBOARD_PATH = Path("data/qcm/leaderboard.json")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read() -> list[dict]:
    if not LEADERBOARD_PATH.exists():
        return []
    try:
        payload = json.loads(LEADERBOARD_PATH.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            return payload
    except Exception:
        return []
    return []


def _write(rows: list[dict]) -> None:
    LEADERBOARD_PATH.parent.mkdir(parents=True, exist_ok=True)
    LEADERBOARD_PATH.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")


def submit_score(player: str, score: int, total: int) -> dict:
    name = (player or "joueur").strip()
    if not name:
        name = "joueur"

    score_value = max(0, int(score))
    total_value = max(1, int(total))
    ratio = round(score_value / total_value, 4)

    rows = _read()
    entry = {
        "player": name[:40],
        "score": score_value,
        "total": total_value,
        "ratio": ratio,
        "submitted_at": _now_iso(),
    }
    rows.append(entry)

    rows.sort(key=lambda x: (-float(x.get("ratio", 0.0)), -int(x.get("score", 0)), str(x.get("submitted_at", ""))))
    rows = rows[:100]
    _write(rows)
    return entry


def top(limit: int = 10) -> list[dict]:
    rows = _read()
    pick = max(1, min(100, int(limit)))
    return rows[:pick]


def to_csv(limit: int = 100) -> str:
    rows = top(limit=limit)
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=["rank", "player", "score", "total", "ratio", "submitted_at"])
    writer.writeheader()
    for idx, item in enumerate(rows, start=1):
        writer.writerow(
            {
                "rank": idx,
                "player": item.get("player", ""),
                "score": item.get("score", 0),
                "total": item.get("total", 0),
                "ratio": item.get("ratio", 0.0),
                "submitted_at": item.get("submitted_at", ""),
            }
        )
    return output.getvalue()
