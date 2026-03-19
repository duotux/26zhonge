# ============================================================
#  数据库台账模块 — db/database.py
#  SQLite 存储违规事件、设备信息、操作日志
# ============================================================
import sqlite3
import os
import threading
from datetime import datetime, timedelta
from core.config import DB_PATH


class Database:
    def __init__(self, path: str = DB_PATH):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self._path = path
        self._local = threading.local()  # 每线程独立连接
        self._init_tables()

    # ── 连接管理 ──────────────────────────────────────────
    def _conn(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn") or self._local.conn is None:
            conn = sqlite3.connect(self._path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            self._local.conn = conn
        return self._local.conn

    def _init_tables(self):
        c = self._conn()
        c.executescript("""
        CREATE TABLE IF NOT EXISTS events (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            ts          TEXT    NOT NULL,
            device_ip   TEXT    NOT NULL,
            class_name  TEXT    NOT NULL,
            level       INTEGER NOT NULL,
            level_desc  TEXT,
            conf        REAL,
            img_path    TEXT,
            handled     INTEGER DEFAULT 0,
            handle_note TEXT,
            handle_ts   TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_events_ts ON events(ts);
        CREATE INDEX IF NOT EXISTS idx_events_level ON events(level);

        CREATE TABLE IF NOT EXISTS devices (
            ip          TEXT PRIMARY KEY,
            device_id   TEXT,
            location    TEXT,
            added_ts    TEXT
        );

        CREATE TABLE IF NOT EXISTS op_logs (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            ts       TEXT NOT NULL,
            user     TEXT,
            action   TEXT,
            detail   TEXT
        );
        """)
        c.commit()

    # ── 违规事件 ──────────────────────────────────────────
    def insert_event(self, event: dict) -> int:
        """插入违规事件记录（带事务保护和错误处理）"""
        try:
            c = self._conn()
            cur = c.execute(
                "INSERT INTO events(ts,device_ip,class_name,level,"
                "level_desc,conf,img_path) VALUES(?,?,?,?,?,?,?)",
                (event["ts"], event["device_ip"], event["class_name"],
                 event["level"], event.get("level_desc",""),
                 event.get("conf", 0.0), event.get("img_path",""))
            )
            c.commit()
            return cur.lastrowid
        except Exception as e:
            print(f"[Database] 插入事件失败：{e}")
            print(f"[Database] 事件数据：{event}")
            raise

    def mark_handled(self, event_id: int, note: str = "", user: str = ""):
        c = self._conn()
        c.execute(
            "UPDATE events SET handled=1, handle_note=?, handle_ts=? WHERE id=?",
            (note, datetime.now().isoformat(timespec="seconds"), event_id)
        )
        c.commit()
        self.log(user, "handle_event", f"event_id={event_id} note={note}")

    def query_events(self, days: int = 7, level: int = 0,
                     device_ip: str = "", unhandled_only: bool = False,
                     limit: int = 500) -> list:
        """查询违规事件，返回字典列表（增强错误处理）"""
        try:
            since = (datetime.now() - timedelta(days=days)).isoformat()
            sql   = "SELECT * FROM events WHERE ts>=?"
            args  = [since]
            if level > 0:
                sql += " AND level=?";  args.append(level)
            if device_ip:
                sql += " AND device_ip=?"; args.append(device_ip)
            if unhandled_only:
                sql += " AND handled=0"
            sql += f" ORDER BY ts DESC LIMIT {limit}"
            c = self._conn()
            rows = c.execute(sql, args).fetchall()
            return [dict(r) for r in rows]
        except Exception as e:
            print(f"[Database] 查询事件失败：{e}")
            return []

    def stats_by_class(self, days: int = 30) -> list:
        """按违规类别统计数量，用于柱状图（增强错误处理）"""
        try:
            since = (datetime.now() - timedelta(days=days)).isoformat()
            rows = self._conn().execute(
                "SELECT class_name, COUNT(*) AS cnt FROM events "
                "WHERE ts>=? GROUP BY class_name ORDER BY cnt DESC",
                (since,)
            ).fetchall()
            return [dict(r) for r in rows]
        except Exception as e:
            print(f"[Database] 统计类别失败：{e}")
            return []

    def stats_by_day(self, days: int = 14) -> list:
        """按日期统计事件数，用于折线图（增强错误处理）"""
        try:
            since = (datetime.now() - timedelta(days=days)).isoformat()
            rows = self._conn().execute(
                "SELECT substr(ts,1,10) AS day, COUNT(*) AS cnt "
                "FROM events WHERE ts>=? GROUP BY day ORDER BY day",
                (since,)
            ).fetchall()
            return [dict(r) for r in rows]
        except Exception as e:
            print(f"[Database] 统计日期失败：{e}")
            return []

    def stats_by_level(self, days: int = 30) -> dict:
        """按等级统计，用于饼图（增强错误处理）"""
        try:
            since = (datetime.now() - timedelta(days=days)).isoformat()
            rows = self._conn().execute(
                "SELECT level, COUNT(*) AS cnt FROM events "
                "WHERE ts>=? GROUP BY level",
                (since,)
            ).fetchall()
            return {r["level"]: r["cnt"] for r in rows}
        except Exception as e:
            print(f"[Database] 统计等级失败：{e}")
            return {}

    # ── 设备管理 ──────────────────────────────────────────
    def upsert_device(self, ip: str, device_id: str = "",
                      location: str = ""):
        c = self._conn()
        c.execute(
            "INSERT OR REPLACE INTO devices(ip,device_id,location,added_ts)"
            " VALUES(?,?,?,?)",
            (ip, device_id, location,
             datetime.now().isoformat(timespec="seconds"))
        )
        c.commit()

    def get_devices(self) -> list:
        rows = self._conn().execute("SELECT * FROM devices").fetchall()
        return [dict(r) for r in rows]

    # ── 操作日志 ──────────────────────────────────────────
    def log(self, user: str, action: str, detail: str = ""):
        c = self._conn()
        c.execute(
            "INSERT INTO op_logs(ts,user,action,detail) VALUES(?,?,?,?)",
            (datetime.now().isoformat(timespec="seconds"), user, action, detail)
        )
        c.commit()

    def query_logs(self, limit: int = 200) -> list:
        rows = self._conn().execute(
            "SELECT * FROM op_logs ORDER BY ts DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]
