"""Offline replay-copy isolation; no provider or workspace database access."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sqlite3

import pytest

spec = importlib.util.spec_from_file_location('limit_replay', Path(__file__).parents[1] / 'scripts/replay_limit_failures.py')
replay = importlib.util.module_from_spec(spec)
spec.loader.exec_module(replay)


@pytest.mark.parametrize('state,seq,version', [('negative', 19, 12), ('positive', 27, 18)])
def test_rewind_only_private_copy(tmp_path, state, seq, version):
    source = tmp_path / 'source.db'
    with sqlite3.connect(source) as db:
        db.executescript('''
        CREATE TABLE case_events(id TEXT,case_id TEXT,seq INT,type TEXT,occurred_at TEXT,payload TEXT);
        CREATE TABLE jobs(case_id TEXT);
        CREATE TABLE orchestration_runs(case_id TEXT);
        CREATE TABLE communications(id TEXT,case_id TEXT,started_at TEXT);
        CREATE TABLE mock_reservations(work_order_id TEXT,slot_id TEXT,status TEXT);
        CREATE TABLE contractor_reports(work_order_id TEXT);
        CREATE TABLE appointments(work_order_id TEXT);
        CREATE TABLE work_orders(id TEXT,status TEXT,contractor_id TEXT,quote_pence INT,completion_report_id TEXT,updated_at TEXT,created_at TEXT);
        CREATE TABLE action_records(case_id TEXT,created_at TEXT);
        CREATE TABLE mock_slots(slot_id TEXT,is_reserved INT);
        CREATE TABLE repair_cases(id TEXT,status TEXT,version INT,updated_at TEXT,last_decision_summary TEXT,next_follow_up_at TEXT);
        CREATE TABLE repair_issues(case_id TEXT,tenant_resolution_confirmed_at TEXT,unresolved_concerns TEXT);
        ''')
        for index in (19, 27, 30):
            db.execute('INSERT INTO case_events VALUES(?,?,?,?,?,?)', (str(index), replay.CASE, index, 'TENANT_CONFIRMATION_RECEIVED', f'2026-10-24T13:{index}:00', json.dumps({'communication_id': str(index)})))
            db.execute('INSERT INTO communications VALUES(?,?,?)', (str(index), replay.CASE, f'2026-10-24T13:{index}:00'))
        db.execute("INSERT INTO repair_cases VALUES(?,'RESOLVED',20,NULL,NULL,NULL)", (replay.CASE,))
        db.execute("INSERT INTO repair_issues VALUES(?,NULL,'[]')", (replay.CASE,))
        db.execute("INSERT INTO work_orders VALUES(?,'COMPLETED','contractor',100,'report','later','earlier')", (replay.FOLLOWUP,))
    digest = hashlib.sha256(source.read_bytes()).digest()
    destination = tmp_path / state / 'replay.db'
    assert replay.reconstruct(source, destination, state) == str(seq)
    assert hashlib.sha256(source.read_bytes()).digest() == digest
    assert destination.stat().st_mode & 0o777 == 0o600
    with sqlite3.connect(destination) as db:
        assert db.execute('SELECT MAX(seq) FROM case_events').fetchone()[0] == seq
        assert db.execute('SELECT version FROM repair_cases').fetchone()[0] == version
        assert db.execute('SELECT COUNT(*) FROM communications WHERE id="30"').fetchone()[0] == 0
        assert db.execute('SELECT status FROM work_orders').fetchone()[0] == ('READY' if state == 'negative' else 'COMPLETED')
    with pytest.raises(ValueError):
        replay.reconstruct(source, destination, state)
    with pytest.raises(ValueError):
        replay.reconstruct(source, source, state)
