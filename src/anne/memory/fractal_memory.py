"""Fractal episodic memory backed by SQLite."""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime
from typing import Any

from anne.core.cognitive_state import Consciousness, EthicScore, Hypothesis


class FractalMemory:
    """Persistent episodic memory with pattern accumulation.

    Stores hypotheses, decisions, dream patterns, learned rules,
    inter-consciousness empathy relations, and ANLA failure traces (SFT).
    """

    def __init__(self, db_path: str = "anne.db") -> None:
        self.conn = sqlite3.connect(db_path)
        self._init_tables()

    def _init_tables(self) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS hypotheses (
                id TEXT PRIMARY KEY,
                topic TEXT,
                claim TEXT,
                probability REAL,
                iteration INTEGER,
                tested INTEGER,
                result TEXT,
                confidence_delta REAL,
                source TEXT,
                created_at TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS decisions (
                id TEXT PRIMARY KEY,
                hypothesis_id TEXT,
                goodness REAL,
                equality REAL,
                harm REAL,
                total REAL,
                verdict TEXT,
                reasoning TEXT,
                consciousnesses TEXT,
                cognitive_stage TEXT,
                created_at TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS dream_patterns (
                id TEXT PRIMARY KEY,
                pattern TEXT UNIQUE,
                frequency INTEGER DEFAULT 1,
                avg_score REAL DEFAULT 0.0,
                last_verdict TEXT,
                last_seen TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS learned_rules (
                id TEXT PRIMARY KEY,
                rule TEXT,
                confidence REAL,
                support_count INTEGER DEFAULT 1,
                created_at TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS empathy_map (
                id TEXT PRIMARY KEY,
                consciousness_a TEXT,
                consciousness_b TEXT,
                relation_strength REAL DEFAULT 0.5,
                conflict_count INTEGER DEFAULT 0,
                resolution_count INTEGER DEFAULT 0,
                updated_at TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS failure_traces (
                id TEXT PRIMARY KEY,
                cycle_id TEXT,
                stage TEXT,
                raw_input TEXT,
                reason TEXT,
                meta_tag TEXT,
                hypothesis_id TEXT,
                ethic_total REAL,
                created_at TEXT
            )
            """
        )
        self.conn.commit()

    def save_hypothesis(self, h: Hypothesis) -> None:
        cur = self.conn.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO hypotheses VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                h.id,
                h.topic,
                h.claim,
                h.probability,
                h.iteration,
                int(h.tested),
                h.result,
                h.confidence_delta,
                h.source,
                datetime.now().isoformat(),
            ),
        )
        self.conn.commit()

    def save_decision(
        self,
        decision_id: str,
        hyp_id: str,
        score: EthicScore,
        consciousnesses: list[Consciousness],
        stage: str = "YAP",
    ) -> None:
        cur = self.conn.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO decisions VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (
                decision_id,
                hyp_id,
                score.goodness,
                score.equality,
                score.harm,
                score.total,
                score.verdict,
                score.reasoning,
                json.dumps([c.id for c in consciousnesses]),
                stage,
                datetime.now().isoformat(),
            ),
        )
        self.conn.commit()

    def save_dream_pattern(self, pattern: str, score: float, verdict: str) -> None:
        cur = self.conn.cursor()
        existing = cur.execute(
            "SELECT id, frequency, avg_score FROM dream_patterns WHERE pattern=?",
            (pattern,),
        ).fetchone()
        if existing:
            nf = existing[1] + 1
            na = (existing[2] * existing[1] + score) / nf
            cur.execute(
                """
                UPDATE dream_patterns
                SET frequency=?, avg_score=?, last_verdict=?, last_seen=?
                WHERE id=?
                """,
                (nf, round(na, 3), verdict, datetime.now().isoformat(), existing[0]),
            )
        else:
            pid = f"dp_{uuid.uuid4().hex[:12]}"
            cur.execute(
                "INSERT INTO dream_patterns VALUES (?,?,?,?,?,?)",
                (pid, pattern, 1, score, verdict, datetime.now().isoformat()),
            )
        self.conn.commit()

    def save_learned_rule(self, rule: str, confidence: float) -> None:
        cur = self.conn.cursor()
        existing = cur.execute(
            "SELECT id, support_count FROM learned_rules WHERE rule=?", (rule,)
        ).fetchone()
        if existing:
            cur.execute(
                "UPDATE learned_rules SET confidence=?, support_count=? WHERE id=?",
                (min(confidence + 0.05, 1.0), existing[1] + 1, existing[0]),
            )
        else:
            rid = f"rule_{uuid.uuid4().hex[:12]}"
            cur.execute(
                "INSERT INTO learned_rules VALUES (?,?,?,?,?)",
                (rid, rule, confidence, 1, datetime.now().isoformat()),
            )
        self.conn.commit()

    def update_empathy(
        self,
        id_a: str,
        id_b: str,
        conflict: bool = False,
        resolved: bool = False,
    ) -> None:
        key = f"{min(id_a, id_b)}_{max(id_a, id_b)}"
        cur = self.conn.cursor()
        existing = cur.execute(
            """
            SELECT id, relation_strength, conflict_count, resolution_count
            FROM empathy_map WHERE id=?
            """,
            (key,),
        ).fetchone()
        if existing:
            s = min(1.0, existing[1] + (0.05 if resolved else -0.02))
            cur.execute(
                """
                UPDATE empathy_map
                SET relation_strength=?, conflict_count=?, resolution_count=?, updated_at=?
                WHERE id=?
                """,
                (
                    round(s, 3),
                    existing[2] + (1 if conflict else 0),
                    existing[3] + (1 if resolved else 0),
                    datetime.now().isoformat(),
                    key,
                ),
            )
        else:
            cur.execute(
                "INSERT INTO empathy_map VALUES (?,?,?,?,?,?,?)",
                (
                    key,
                    id_a,
                    id_b,
                    0.5,
                    1 if conflict else 0,
                    1 if resolved else 0,
                    datetime.now().isoformat(),
                ),
            )
        self.conn.commit()

    def get_similar_decisions(
        self, topic: str, limit: int = 3
    ) -> list[tuple[Any, ...]]:
        cur = self.conn.cursor()
        results: list[tuple[Any, ...]] = []
        for word in topic.lower().split():
            rows = cur.execute(
                """
                SELECT d.verdict, d.total, d.reasoning, h.topic
                FROM decisions d JOIN hypotheses h ON d.hypothesis_id = h.id
                WHERE h.topic LIKE ? ORDER BY d.created_at DESC LIMIT ?
                """,
                (f"%{word}%", limit),
            ).fetchall()
            results.extend(rows)
        return results[:limit]

    def get_top_patterns(self, limit: int = 5) -> list[tuple[Any, ...]]:
        return self.conn.cursor().execute(
            """
            SELECT pattern, frequency, avg_score, last_verdict
            FROM dream_patterns ORDER BY frequency DESC LIMIT ?
            """,
            (limit,),
        ).fetchall()

    def get_strong_rules(self, limit: int = 5) -> list[tuple[Any, ...]]:
        return self.conn.cursor().execute(
            """
            SELECT rule, confidence, support_count FROM learned_rules
            WHERE confidence > 0.6 ORDER BY confidence DESC LIMIT ?
            """,
            (limit,),
        ).fetchall()

    def get_empathy_strength(self, id_a: str, id_b: str) -> float:
        key = f"{min(id_a, id_b)}_{max(id_a, id_b)}"
        row = self.conn.cursor().execute(
            "SELECT relation_strength FROM empathy_map WHERE id=?", (key,)
        ).fetchone()
        return float(row[0]) if row else 0.5

    def save_failure_trace(
        self,
        cycle_id: str,
        stage: str,
        raw_input: str,
        reason: str,
        meta_tag: str = "",
        hypothesis_id: str = "",
        ethic_total: float = 0.0,
    ) -> str:
        """Persist a Structured Failure Trace (SFT) for ANLA retry support."""
        trace_id = f"ft_{uuid.uuid4().hex}"
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO failure_traces
            VALUES (?,?,?,?,?,?,?,?,?)
            """,
            (
                trace_id,
                cycle_id,
                stage,
                raw_input,
                reason,
                meta_tag,
                hypothesis_id,
                ethic_total,
                datetime.now().isoformat(),
            ),
        )
        self.conn.commit()
        return trace_id

    def get_recent_failures(self, limit: int = 5) -> list[tuple[Any, ...]]:
        """Return most recent failure traces (newest first)."""
        return self.conn.cursor().execute(
            """
            SELECT id, cycle_id, stage, reason, meta_tag, ethic_total, created_at
            FROM failure_traces
            ORDER BY created_at DESC, rowid DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
