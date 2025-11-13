# storage.py
# Lightweight SQLite helper for bins, readings, and metadata.

import sqlite3
import time
from typing import Dict, Any
from config import DB_PATH

def _get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = _get_conn()
    cur = conn.cursor()
    cur.executescript("""
    PRAGMA foreign_keys = ON;
    CREATE TABLE IF NOT EXISTS bins (
        bin_id INTEGER PRIMARY KEY AUTOINCREMENT,
        bin_code TEXT UNIQUE,
        name TEXT,
        latitude REAL,
        longitude REAL,
        height_cm REAL,
        created_at REAL DEFAULT (strftime('%s','now'))
    );

    CREATE TABLE IF NOT EXISTS readings (
        reading_id INTEGER PRIMARY KEY AUTOINCREMENT,
        bin_id INTEGER REFERENCES bins(bin_id) ON DELETE CASCADE,
        fill_percent REAL,
        distance_cm REAL,
        recorded_at REAL DEFAULT (strftime('%s','now'))
    );

    CREATE TABLE IF NOT EXISTS alerts (
        alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
        bin_id INTEGER REFERENCES bins(bin_id) ON DELETE CASCADE,
        alert_type TEXT,
        message TEXT,
        triggered_at REAL DEFAULT (strftime('%s','now')),
        acknowledged INTEGER DEFAULT 0
    );
    """)
    conn.commit()
    conn.close()

def add_or_update_bin(bin_code: str, name: str=None, latitude: float=None, longitude: float=None, height_cm: float=None):
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT bin_id FROM bins WHERE bin_code = ?", (bin_code,))
    row = cur.fetchone()
    if row:
        cur.execute("""
            UPDATE bins SET name=?, latitude=?, longitude=?, height_cm=?
            WHERE bin_code=?
        """, (name, latitude, longitude, height_cm, bin_code))
        bin_id = row["bin_id"]
    else:
        cur.execute("""
            INSERT INTO bins(bin_code,name,latitude,longitude,height_cm)
            VALUES(?,?,?,?,?)
        """, (bin_code, name, latitude, longitude, height_cm))
        bin_id = cur.lastrowid
    conn.commit()
    conn.close()
    return bin_id

def get_bins():
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM bins")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def get_bin(bin_id):
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM bins WHERE bin_id=?", (bin_id,))
    r = cur.fetchone()
    conn.close()
    return dict(r) if r else None

def insert_reading(bin_id: int, fill_percent: float, distance_cm: float):
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO readings(bin_id, fill_percent, distance_cm, recorded_at) VALUES(?,?,?,?)",
                (bin_id, fill_percent, distance_cm, time.time()))
    conn.commit()
    conn.close()

def get_latest_reading(bin_id: int):
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM readings WHERE bin_id=? ORDER BY recorded_at DESC LIMIT 1", (bin_id,))
    r = cur.fetchone()
    conn.close()
    return dict(r) if r else None

def log_alert(bin_id: int, alert_type: str, message: str):
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO alerts(bin_id, alert_type, message, triggered_at) VALUES(?,?,?,?)",
                (bin_id, alert_type, message, time.time()))
    conn.commit()
    conn.close()
