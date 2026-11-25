#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""三省六部（豆包版）旨意狀態 CLI：new / set / list"""
import argparse, json, os, datetime as dt

BASE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(BASE, "state.json")
STAGES = ["太子", "中書省", "門下省", "尚書省", "六部執行", "門下複審", "歸檔"]


def load():
    if os.path.exists(STATE):
        with open(STATE, encoding="utf-8") as f:
            return json.load(f)
    return {"updated": "", "edicts": []}


def save(d):
    d["updated"] = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("new")
    p.add_argument("title")
    p.add_argument("--note", default="")

    s = sub.add_parser("set")
    s.add_argument("eid")
    s.add_argument("--stage")
    s.add_argument("--dept")
    s.add_argument("--status")
    s.add_argument("--note", default="")

    sub.add_parser("list")
    a = ap.parse_args()
    d = load()

    if a.cmd == "new":
        n = len(d["edicts"]) + 1
        now = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
        d["edicts"].insert(0, {
            "id": f"E-{n:03d}", "title": a.title, "stage": "太子",
            "status": "已立案", "created": now, "updated": now,
            "depts": {}, "log": [{"t": dt.datetime.now().strftime("%H:%M"),
                                  "dept": "太子", "msg": a.note or "分揀立案"}]})
        save(d)
        print(d["edicts"][0]["id"])
        return

    if a.cmd == "list":
        for e in d["edicts"]:
            print(f"{e['id']}｜{e['stage']}｜{e['status']}｜{e['title']}")
        return

    for e in d["edicts"]:
        if e["id"] != a.eid:
            continue
        e["updated"] = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
        if a.stage:
            e["stage"] = a.stage
        if a.status:
            e["status"] = a.status
        if a.dept:
            e["depts"][a.dept] = a.status or e["status"]
            e.setdefault("log", []).insert(0, {
                "t": dt.datetime.now().strftime("%H:%M"), "dept": a.dept,
                "msg": a.note or a.status or ""})
        elif a.note:
            e.setdefault("log", []).insert(0, {
                "t": dt.datetime.now().strftime("%H:%M"), "dept": "尚書省", "msg": a.note})
        save(d)
        print(f"{e['id']} → {e['stage']} / {e['status']}")
        return
    print("找不到旨意", a.eid)


if __name__ == "__main__":
    main()
