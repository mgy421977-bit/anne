"""Fractal episodic memory backed by SQLite."""

from __future__ import annotations

import json
import re
import sqlite3
import uuid
from datetime import datetime
from typing import Any

from anne.core.cognitive_state import Consciousness, EthicScore, Hypothesis


class FractalMemory:
    """Persistent memory with additive multi-scale coordinates.

    Existing databases are migrated without destructive schema changes.
    """

    def __init__(self, db_path: str = "anne.db") -> None:
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._init_tables()

    def _ensure_columns(self, table: str, columns: dict[str, str]) -> None:
        existing = {row[1] for row in self.conn.execute(f"PRAGMA table_info({table})")}
        for name, definition in columns.items():
            if name not in existing:
                self.conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")

    def _init_tables(self) -> None:
        cur = self.conn.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS hypotheses (
            id TEXT PRIMARY KEY, topic TEXT, claim TEXT, probability REAL,
            iteration INTEGER, tested INTEGER, result TEXT, confidence_delta REAL,
            source TEXT, created_at TEXT)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS decisions (
            id TEXT PRIMARY KEY, hypothesis_id TEXT, goodness REAL, equality REAL,
            harm REAL, total REAL, verdict TEXT, reasoning TEXT, consciousnesses TEXT,
            cognitive_stage TEXT, created_at TEXT)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS dream_patterns (
            id TEXT PRIMARY KEY, pattern TEXT UNIQUE, frequency INTEGER DEFAULT 1,
            avg_score REAL DEFAULT 0.0, last_verdict TEXT, last_seen TEXT)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS learned_rules (
            id TEXT PRIMARY KEY, rule TEXT, confidence REAL,
            support_count INTEGER DEFAULT 1, created_at TEXT)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS empathy_map (
            id TEXT PRIMARY KEY, consciousness_a TEXT, consciousness_b TEXT,
            relation_strength REAL DEFAULT 0.5, conflict_count INTEGER DEFAULT 0,
            resolution_count INTEGER DEFAULT 0, updated_at TEXT)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS failure_traces (
            id TEXT PRIMARY KEY, cycle_id TEXT, stage TEXT, raw_input TEXT,
            reason TEXT, meta_tag TEXT, hypothesis_id TEXT, ethic_total REAL,
            created_at TEXT)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS scale_events (
            cycle_id TEXT PRIMARY KEY, parent_cycle_id TEXT, depth INTEGER NOT NULL DEFAULT 0,
            scale_role TEXT NOT NULL, task_mode TEXT NOT NULL DEFAULT 'general',
            question TEXT NOT NULL, selected_claim TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'started', stage_reached TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL)""")
        self._ensure_columns("hypotheses", {
            "depth": "INTEGER NOT NULL DEFAULT 0", "parent_cycle_id": "TEXT",
            "task_mode": "TEXT NOT NULL DEFAULT 'general'"})
        self._ensure_columns("decisions", {
            "depth": "INTEGER NOT NULL DEFAULT 0", "parent_cycle_id": "TEXT",
            "task_mode": "TEXT NOT NULL DEFAULT 'general'"})
        self._ensure_columns("failure_traces", {
            "depth": "INTEGER NOT NULL DEFAULT 0", "parent_cycle_id": "TEXT",
            "task_mode": "TEXT NOT NULL DEFAULT 'general'", "scale_role": "TEXT NOT NULL DEFAULT 'frame'"})
        self.conn.commit()

    @staticmethod
    def _normalize_token(token: str) -> str:
        """Normalize common Turkish inflections for lightweight memory recall.

        This is intentionally conservative: it only strips common grammatical
        endings and preserves the resulting lexical stem for prefix matching.
        """
        token = token.casefold().strip(".,!?;:()[]{}\"'")
        if not token:
            return token
        suffixes = (
            "larından", "lerinden", "larına", "lerine", "ların", "lerin",
            "lardan", "lerden", "ların", "lerin", "lara", "lere",
            "dan", "den", "tan", "ten", "dır", "dir", "dur", "dür",
            "tır", "tir", "tur", "tür", "ın", "in", "un", "ün",
            "ım", "im", "um", "üm", "ı", "i", "u", "ü",
        )
        for suffix in suffixes:
            if token.endswith(suffix) and len(token) - len(suffix) >= 3:
                return token[:-len(suffix)]
        return token

    @classmethod
    def _normalized_terms(cls, text: str) -> list[str]:
        raw_terms = re.findall(r"[\wçğıöşüÇĞİÖŞÜ]+", text.casefold(), flags=re.UNICODE)
        return [term for term in (cls._normalize_token(t) for t in raw_terms) if term]

    def save_hypothesis(self, h: Hypothesis, *, depth: int = 0,
                        parent_cycle_id: str | None = None, task_mode: str = "general") -> None:
        self.conn.execute("""INSERT OR REPLACE INTO hypotheses
            (id,topic,claim,probability,iteration,tested,result,confidence_delta,source,created_at,
             depth,parent_cycle_id,task_mode) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (h.id,h.topic,h.claim,h.probability,h.iteration,int(h.tested),h.result,
             h.confidence_delta,h.source,datetime.now().isoformat(),depth,parent_cycle_id,task_mode))
        self.conn.commit()

    def save_decision(self, decision_id: str, hyp_id: str, score: EthicScore,
                      consciousnesses: list[Consciousness], stage: str = "YAP", *,
                      depth: int = 0, parent_cycle_id: str | None = None,
                      task_mode: str = "general") -> None:
        self.conn.execute("""INSERT OR REPLACE INTO decisions
            (id,hypothesis_id,goodness,equality,harm,total,verdict,reasoning,consciousnesses,
             cognitive_stage,created_at,depth,parent_cycle_id,task_mode) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (decision_id,hyp_id,score.goodness,score.equality,score.harm,score.total,score.verdict,
             score.reasoning,json.dumps([c.id for c in consciousnesses]),stage,
             datetime.now().isoformat(),depth,parent_cycle_id,task_mode))
        self.conn.commit()

    def save_dream_pattern(self, pattern: str, score: float, verdict: str) -> None:
        cur = self.conn.cursor()
        existing = cur.execute("SELECT id,frequency,avg_score FROM dream_patterns WHERE pattern=?", (pattern,)).fetchone()
        if existing:
            nf = existing[1] + 1
            na = (existing[2] * existing[1] + score) / nf
            cur.execute("UPDATE dream_patterns SET frequency=?,avg_score=?,last_verdict=?,last_seen=? WHERE id=?",
                        (nf, round(na,3), verdict, datetime.now().isoformat(), existing[0]))
        else:
            cur.execute("INSERT INTO dream_patterns VALUES (?,?,?,?,?,?)",
                        (f"dp_{uuid.uuid4().hex[:12]}",pattern,1,score,verdict,datetime.now().isoformat()))
        self.conn.commit()

    def save_learned_rule(self, rule: str, confidence: float) -> None:
        cur = self.conn.cursor()
        existing = cur.execute("SELECT id,support_count FROM learned_rules WHERE rule=?", (rule,)).fetchone()
        if existing:
            cur.execute("UPDATE learned_rules SET confidence=?,support_count=? WHERE id=?",
                        (min(confidence + 0.05,1.0),existing[1]+1,existing[0]))
        else:
            cur.execute("INSERT INTO learned_rules VALUES (?,?,?,?,?)",
                        (f"rule_{uuid.uuid4().hex[:12]}",rule,confidence,1,datetime.now().isoformat()))
        self.conn.commit()

    def update_empathy(self, id_a: str, id_b: str, conflict: bool = False, resolved: bool = False) -> None:
        key = f"{min(id_a,id_b)}_{max(id_a,id_b)}"
        cur = self.conn.cursor()
        existing = cur.execute("SELECT id,relation_strength,conflict_count,resolution_count FROM empathy_map WHERE id=?", (key,)).fetchone()
        if existing:
            s = min(1.0, existing[1] + (0.05 if resolved else -0.02))
            cur.execute("UPDATE empathy_map SET relation_strength=?,conflict_count=?,resolution_count=?,updated_at=? WHERE id=?",
                        (round(s,3),existing[2]+(1 if conflict else 0),existing[3]+(1 if resolved else 0),datetime.now().isoformat(),key))
        else:
            cur.execute("INSERT INTO empathy_map VALUES (?,?,?,?,?,?,?)",
                        (key,id_a,id_b,0.5,1 if conflict else 0,1 if resolved else 0,datetime.now().isoformat()))
        self.conn.commit()

    def get_similar_decisions(self, topic: str, limit: int = 3) -> list[tuple[Any,...]]:
        cur = self.conn.cursor()
        results: list[tuple[Any,...]] = []
        terms = self._normalized_terms(topic)
        for term in terms:
            rows = cur.execute("""SELECT d.verdict,d.total,d.reasoning,h.topic
                FROM decisions d JOIN hypotheses h ON d.hypothesis_id=h.id
                WHERE h.topic LIKE ? ORDER BY d.created_at DESC LIMIT ?""", (f"%{term}%",limit)).fetchall()
            results.extend(rows)
        deduped: list[tuple[Any,...]] = []
        seen: set[tuple[Any,...]] = set()
        for row in results:
            if row not in seen:
                seen.add(row)
                deduped.append(row)
        return deduped[:limit]

    def get_top_patterns(self, limit: int = 5) -> list[tuple[Any,...]]:
        return self.conn.cursor().execute("SELECT pattern,frequency,avg_score,last_verdict FROM dream_patterns ORDER BY frequency DESC LIMIT ?", (limit,)).fetchall()

    def get_strong_rules(self, limit: int = 5) -> list[tuple[Any,...]]:
        return self.conn.cursor().execute("SELECT rule,confidence,support_count FROM learned_rules WHERE confidence > 0.6 ORDER BY confidence DESC LIMIT ?", (limit,)).fetchall()

    def get_empathy_strength(self, id_a: str, id_b: str) -> float:
        key = f"{min(id_a,id_b)}_{max(id_a,id_b)}"
        row = self.conn.cursor().execute("SELECT relation_strength FROM empathy_map WHERE id=?", (key,)).fetchone()
        return float(row[0]) if row else 0.5

    def save_failure_trace(self, cycle_id: str, stage: str, raw_input: str, reason: str,
                           meta_tag: str = "", hypothesis_id: str = "", ethic_total: float = 0.0,
                           *, depth: int = 0, parent_cycle_id: str | None = None,
                           task_mode: str = "general", scale_role: str = "frame") -> str:
        trace_id = f"ft_{uuid.uuid4().hex}"
        self.conn.execute("""INSERT INTO failure_traces
            (id,cycle_id,stage,raw_input,reason,meta_tag,hypothesis_id,ethic_total,created_at,
             depth,parent_cycle_id,task_mode,scale_role) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (trace_id,cycle_id,stage,raw_input,reason,meta_tag,hypothesis_id,ethic_total,
             datetime.now().isoformat(),depth,parent_cycle_id,task_mode,scale_role))
        self.conn.commit()
        return trace_id

    def get_recent_failures(self, limit: int = 5) -> list[tuple[Any,...]]:
        return self.conn.cursor().execute("""SELECT id,cycle_id,stage,reason,meta_tag,ethic_total,created_at
            FROM failure_traces ORDER BY created_at DESC,rowid DESC LIMIT ?""", (limit,)).fetchall()

    def get_failures_at_depth(self, depth: int, limit: int = 20) -> list[tuple[Any,...]]:
        return self.conn.cursor().execute("""SELECT id,cycle_id,parent_cycle_id,depth,task_mode,scale_role,stage,reason,created_at
            FROM failure_traces WHERE depth=? ORDER BY created_at DESC,rowid DESC LIMIT ?""", (depth,limit)).fetchall()

    def save_scale_event(self, *, cycle_id: str, parent_cycle_id: str | None, depth: int,
                         scale_role: str, task_mode: str, question: str, selected_claim: str = "",
                         status: str = "started", stage_reached: str = "") -> str:
        self.conn.execute("""INSERT OR REPLACE INTO scale_events
            (cycle_id,parent_cycle_id,depth,scale_role,task_mode,question,selected_claim,status,stage_reached,created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (cycle_id,parent_cycle_id,depth,scale_role,task_mode,question,selected_claim,status,stage_reached,datetime.now().isoformat()))
        self.conn.commit()
        return cycle_id

    def get_scale_events(self, cycle_id: str | None = None, parent_cycle_id: str | None = None,
                         limit: int = 50) -> list[tuple[Any,...]]:
        clauses: list[str] = []
        params: list[Any] = []
        if cycle_id is not None:
            clauses.append("cycle_id=?"); params.append(cycle_id)
        if parent_cycle_id is not None:
            clauses.append("parent_cycle_id=?"); params.append(parent_cycle_id)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        params.append(limit)
        return self.conn.cursor().execute(f"""SELECT cycle_id,parent_cycle_id,depth,scale_role,task_mode,
            question,selected_claim,status,stage_reached,created_at FROM scale_events {where}
            ORDER BY depth ASC,created_at ASC LIMIT ?""", params).fetchall()
