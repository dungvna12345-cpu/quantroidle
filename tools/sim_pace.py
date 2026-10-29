# -*- coding: utf-8 -*-
"""Mô phỏng nhịp game Quán Trọ Idle (không cần Godot).

Một bot "chơi đều tay": mua nâng cấp có hiệu quả cao nhất ngay khi đủ tiền, ưu tiên các mục tiêu chương.
Thời gian ra là CẬN DƯỚI (người thật chơi chậm hơn bot). Mô hình thông lượng là ước lượng
từ công thức trong autoload/GameState.gd, không phải mô phỏng từng nhân vật.

Chạy:
    python tools/sim_pace.py                          # đọc data/
    python tools/sim_pace.py --data tools/baseline_data
    python tools/sim_pace.py --compare tools/baseline_data data
"""
import argparse
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# ---- hằng số của mô hình (ước lượng quãng đường, tính bằng ô lưới)
EFF = 0.85                # hiệu suất thực tế (hàng đợi, nhân viên chờ nhau)
WAITER_TRIP = 28.0        # ô đi của bồi bàn cho một khách (dẫn khách + mang món + về chỗ)
WAITER_TO_DOOR = 7.5
WAITER_CARRY = 5.0
CUST_WALK_IN = 10.0
CHEF_TRIP = 5.0
LODGE_WALK = 12.0
EVENT_BONUS = 1.08        # lễ hội / giờ cao điểm trung bình
EVENING_SPAWN = 0.065     # thưởng giờ ăn tối trung bình theo thời gian
TYPE_FACTOR = 0.68 + 0.12 + 0.12 * 2 + 0.08 * 1.3
GOAL_PAYBACK = 900.0      # bot coi mục tiêu chương như khoản đầu tư hoàn vốn trong 15 phút
DT = 2.0


class Cfg:
    def __init__(self, d):
        d = Path(d)
        if not d.is_absolute():
            d = ROOT / d
        L = lambda n: json.loads((d / n).read_text(encoding="utf-8"))
        self.bal = L("balance.json")
        self.dishes = L("dishes.json")
        self.staff = L("staff.json")
        self.areas = L("areas.json")
        self.decor = L("decor.json")
        self.chapters = L("chapters.json")
        self.goals = L("goals.json")
        self.research = L("research.json")
        self.area = {a["id"]: a for a in self.areas}
        self.dish = {x["id"]: x for x in self.dishes}
        # gộp bàn / giường của phòng nối dài giống GameState._flatten_wings
        for a in self.areas:
            tables = list(a.get("tables", []))
            beds = list(a.get("beds", []))
            tw = [""] * len(tables)
            bw = [""] * len(beds)
            for w in a.get("wings", []):
                for t in w.get("tables", []):
                    tables.append(t)
                    tw.append(w["id"])
                for b in w.get("beds", []):
                    beds.append(b)
                    bw.append(w["id"])
            a["_tables"], a["_beds"], a["_tw"], a["_bw"] = tables, beds, tw, bw

    def apply(self, ov):
        """ov: {balance:{k:v}, chapter_fields:{field:[v...]}, goal_n:{type:[n per chapter]}, wing_build_scale:x}"""
        for k, v in ov.get("balance", {}).items():
            self.bal[k] = v
        for field, vals in ov.get("chapter_fields", {}).items():
            for i, v in enumerate(vals):
                self.chapters[i][field] = v
        for gtype, vals in ov.get("goal_n", {}).items():
            for ci, v in enumerate(vals):
                for g in self.goals["chapters"][ci]:
                    if g["type"] == gtype and "n" in g and v is not None:
                        g["n"] = v
        scale = float(ov.get("wing_build_scale", 1.0))
        for a in self.areas:
            for w in a.get("wings", []):
                w["build_seconds"] = float(w.get("build_seconds", 30)) * scale

    def b(self, k, default=0.0):
        return float(self.bal.get(k, default))


class State:
    def __init__(self, cfg):
        self.c = cfg
        self.t = 0.0
        self.rep = 0
        self.chapter = 0
        self.rp = 0
        self.res_income = 0
        self.stars_taken = {}
        self.new_run()

    # ---------- khởi tạo lượt chơi / chương
    def ch(self):
        return self.c.chapters[min(self.chapter, len(self.c.chapters) - 1)]

    def new_run(self):
        c = self.c
        self.gold = float(self.ch().get("start_gold", c.b("start_gold")))
        self.level = 1
        self.xp = 0.0
        self.run_gold = 0.0
        self.run_cust = 0.0
        self.dish_lv = {d["id"]: (1 if int(d["unlock_level"]) <= 1 else 0) for d in c.dishes}
        self.staff_n = {k: int(v["start_count"]) for k, v in c.staff.items() if k != "manager"}
        self.staff_lv = {k: 1 for k in self.staff_n}
        self.areas = {}
        for a in c.areas:
            self.areas[a["id"]] = {
                "unlocked": int(a["unlock_cost"]) == 0,
                "tables": [1 if i < int(a.get("start_tables", 0)) else 0 for i in range(len(a["_tables"]))],
                "rooms": [1 if i < int(a.get("start_rooms", 0)) else 0 for i in range(len(a["_beds"]))],
                "kitchen": 1, "cashier": 1, "decor": {}, "wings": {},
            }
        self.milestones = {}
        self.chapter_start = self.t

    # ---------- công thức giống GameState
    def cost_mult(self):
        return float(self.ch().get("cost_mult", 1.0))

    def cost_at(self, base, lv):
        return math.floor(base * self.cost_mult() * pow(self.c.b("cost_growth", 1.15), lv))

    def income_mult(self):
        m = (1.0 + self.c.b("prestige_bonus", 0.1) * self.rep) * float(self.ch().get("income_mult", 1))
        m *= 1.0 + 0.10 * self.res_income
        return m * EVENT_BONUS

    def exp_needed(self):
        return round(self.c.b("exp_base", 8) * pow(self.c.b("exp_growth", 1.3), self.level - 1))

    def dish_price(self, did):
        d = self.c.dish[did]
        lv = max(1, self.dish_lv[did])
        doubles = (lv - 1) // int(self.c.b("dish_double_every", 10))
        return float(d["price"]) * (1.0 + self.c.b("dish_mult_per_level", 0.25) * (lv - 1)) * (2.0 ** doubles)

    def staff_speed(self, sid):
        return 1.0 + float(self.c.staff[sid]["speed_per_level"]) * (self.staff_lv[sid] - 1)

    def table_mult(self, lv):
        return 1.0 + self.c.b("table_mult_per_level", 0.2) * max(0, lv - 1)

    def slot_open(self, aid, wid):
        if not wid:
            return True
        r = self.areas[aid]["wings"].get(wid)
        return r is not None and self.t >= r

    def tables_open_idx(self, aid):
        a = self.c.area[aid]
        st = self.areas[aid]
        return [i for i, lv in enumerate(st["tables"]) if lv > 0 and self.slot_open(aid, a["_tw"][i])]

    def rooms_open_idx(self, aid):
        a = self.c.area[aid]
        st = self.areas[aid]
        return [i for i, lv in enumerate(st["rooms"]) if lv > 0 and self.slot_open(aid, a["_bw"][i])]

    def satisfaction(self, aid):
        return sum(float(self.c.decor[k]["bonus"]) * n for k, n in self.areas[aid]["decor"].items())

    # ---------- thông lượng
    def dish_stats(self):
        unl = [d for d in self.c.dishes if self.dish_lv[d["id"]] > 0]
        n = len(unl)
        spec = str(self.ch().get("specialty", ""))
        sm = float(self.ch().get("specialty_mult", 1.5))
        mean_p = sum(self.dish_price(d["id"]) * (sm if d["id"] == spec else 1.0) for d in unl) / n
        p_special = self.c.b("special_order_chance", 0.3) + (1 - self.c.b("special_order_chance", 0.3)) / n
        sell = mean_p * (1.0 + p_special * (self.c.b("special_mult", 2.0) - 1.0))
        cook = sum(float(d["cook_time"]) for d in unl) / n
        exp = sum(float(d["exp"]) for d in unl) / n
        return sell, cook, exp

    def spawn_rate(self, aid):
        bonus = self.satisfaction(aid) + EVENING_SPAWN
        rc = self.staff_n.get("receptionist", 0)
        if rc > 0:
            bonus += float(self.c.staff["receptionist"]["spawn_bonus"]) * rc * self.staff_speed("receptionist")
        iv = max(self.c.b("min_spawn_interval", 0.5), self.c.b("base_spawn_interval", 3.0) / (1.0 + bonus))
        return 1.0 / iv

    def area_flow(self, aid, ds):
        """Trả về (khách/giây, vàng thô mỗi khách, exp mỗi khách) của một khu."""
        a = self.c.area[aid]
        st = self.areas[aid]
        if not st["unlocked"]:
            return 0.0, 0.0, 0.0
        b = self.c.b
        cw = b("walk_speed", 3.0)
        spawn = self.spawn_rate(aid)
        if a["kind"] == "lodging":
            idx = self.rooms_open_idx(aid)
            if not idx:
                return 0.0, 0.0, 0.0
            r = a["room"]
            cycle = float(r["sleep_time"]) + LODGE_WALK / cw
            rate = EFF * min(spawn, len(idx) / cycle)
            rents = [float(r["rent"]) * (1.0 + float(r["rent_per_level"]) * max(0, st["rooms"][i] - 1)) for i in idx]
            return rate, sum(rents) / len(rents), 1.0
        idx = self.tables_open_idx(aid)
        if not idx:
            return 0.0, 0.0, 0.0
        sell, cook, exp = ds
        sw = b("waiter_speed", 3.8) * self.staff_speed("waiter")
        nw = self.staff_n.get("waiter", 0)
        nc = min(self.staff_n.get("chef", 0), len(a["kitchen"]["stoves"]))
        if nw <= 0 or nc <= 0:
            return 0.0, 0.0, 0.0
        kspeed = 1.0 + b("kitchen_speed_per_level", 0.1) * (st["kitchen"] - 1)
        cook_eff = cook / (kspeed * self.staff_speed("chef"))
        chef_speed = cw * 1.2
        cap_c = nc / (cook_eff + CHEF_TRIP / chef_speed)
        cap_w = nw / (WAITER_TRIP / sw)
        t_table = WAITER_TO_DOOR / sw + CUST_WALK_IN / cw + cook_eff + 1.0 + WAITER_CARRY / sw + b("eat_time", 2.5) + 0.5
        cap_t = len(idx) / t_table
        cs = 1.0 + b("cashier_speed_per_level", 0.15) * (st["cashier"] - 1)
        crew = max(1, self.staff_n.get("cashier", 0))
        cap_cash = cs * self.staff_speed("cashier") * crew / b("pay_time", 1.4)
        rate = EFF * min(spawn, cap_t, cap_w, cap_c, cap_cash)
        mults = []
        for i in idx:
            wid = a["_tw"][i]
            wm = 1.0
            if wid:
                for w in a.get("wings", []):
                    if w["id"] == wid:
                        wm = float(w.get("price_mult", 1.0))
            mults.append(self.table_mult(st["tables"][i]) * wm)
        tip_chance = b("tip_chance", 0.25) + b("cashier_tip_per_level", 0.005) * (st["cashier"] - 1) + 0.12 * 0.4
        tip_f = 1.0 + tip_chance * b("tip_ratio", 0.5) * 1.24
        raw = sell * (sum(mults) / len(mults)) * float(a["price_mult"]) * TYPE_FACTOR * tip_f
        return rate, raw, exp

    def flows(self):
        ds = self.dish_stats()
        gold = cust = xp = 0.0
        im = self.income_mult()
        for aid in self.areas:
            r, raw, exp = self.area_flow(aid, ds)
            gold += r * raw * im
            cust += r
            xp += r * exp
        return gold, cust, xp

    # ---------- mục tiêu chương
    def goals(self):
        g = self.c.goals["chapters"]
        return g[min(self.chapter, len(g) - 1)]

    def goal_progress(self, g):
        t = g["type"]
        need = float(g.get("n", 1))
        if t == "level":
            return self.level, need
        if t == "tables":
            return sum(sum(1 for lv in s["tables"] if lv > 0) for s in self.areas.values()), need
        if t == "rooms":
            return sum(1 for lv in self.areas["lodging"]["rooms"] if lv > 0), need
        if t == "dish":
            return self.dish_lv[g["id"]], need
        if t == "customers":
            return self.run_cust, need
        if t == "staff":
            return self.staff_n.get(g["id"], 0), need
        if t == "area":
            return (1.0 if self.areas[g["id"]]["unlocked"] else 0.0), 1.0
        if t == "earn":
            return self.run_gold, need
        if t == "decor":
            return sum(sum(s["decor"].values()) for s in self.areas.values()), need
        return 0, 1

    def goals_done(self):
        return sum(1 for g in self.goals() if self.goal_progress(g)[0] >= self.goal_progress(g)[1])

    def stars(self):
        return min(3, self.goals_done() // int(self.c.goals.get("stars_per_goals", 2)))

    def goal_wants(self, kind, ident=""):
        for g in self.goals():
            p, n = self.goal_progress(g)
            if p >= n or g["type"] != kind:
                continue
            if kind in ("dish", "staff", "area") and g.get("id") != ident:
                continue
            return True
        return False

    # ---------- danh sách mua sắm: (chi phí, tên, thực hiện, hoàn tác, liên quan mục tiêu)
    def candidates(self):
        c = self.c
        b = c.b
        out = []

        def add(cost, name, do, undo, goal=False):
            out.append((cost, name, do, undo, goal))

        for d in c.dishes:
            did = d["id"]
            if self.dish_lv[did] > 0:
                cost = self.cost_at(float(d["upgrade_base"]), self.dish_lv[did] - 1)
                add(cost, "dish:" + did, lambda did=did: self.dish_lv.__setitem__(did, self.dish_lv[did] + 1),
                    lambda did=did: self.dish_lv.__setitem__(did, self.dish_lv[did] - 1),
                    self.goal_wants("dish", did))
        for sid, sd in c.staff.items():
            if sid == "manager" or self.level < int(sd["unlock_level"]):
                continue
            if self.staff_n[sid] < int(sd["max_count"]):
                extra = max(0, self.staff_n[sid] - int(sd["start_count"]))
                cost = math.floor(float(sd["hire_base"]) * self.cost_mult() * pow(float(sd["hire_mul"]), extra))
                add(cost, "hire:" + sid, lambda s=sid: self.staff_n.__setitem__(s, self.staff_n[s] + 1),
                    lambda s=sid: self.staff_n.__setitem__(s, self.staff_n[s] - 1), self.goal_wants("staff", sid))
            if self.staff_n[sid] > 0:
                cost = self.cost_at(float(sd["upgrade_base"]), self.staff_lv[sid])
                add(cost, "staff_up:" + sid, lambda s=sid: self.staff_lv.__setitem__(s, self.staff_lv[s] + 1),
                    lambda s=sid: self.staff_lv.__setitem__(s, self.staff_lv[s] - 1))
        for aid, st in self.areas.items():
            a = c.area[aid]
            if not st["unlocked"]:
                if self.level >= int(a["unlock_level"]):
                    cost = math.floor(float(a["unlock_cost"]) * self.cost_mult())
                    add(cost, "area:" + aid, lambda s=st: s.__setitem__("unlocked", True),
                        lambda s=st: s.__setitem__("unlocked", False),
                        self.goal_wants("area", aid) or (a["kind"] == "lodging" and self.goal_wants("rooms")))
                continue
            if a["kind"] == "dining":
                opened = [i for i in range(len(st["tables"])) if self.slot_open(aid, a["_tw"][i])]
                closed = [i for i in opened if st["tables"][i] == 0]
                if closed:
                    extra = max(0, sum(1 for lv in st["tables"] if lv > 0) - int(a["start_tables"]))
                    cost = math.floor(float(a["table_unlock_base"]) * self.cost_mult() * pow(float(a["table_unlock_mul"]), extra))
                    i = closed[0]
                    add(cost, "table_new:" + aid, lambda s=st, i=i: s["tables"].__setitem__(i, 1),
                        lambda s=st, i=i: s["tables"].__setitem__(i, 0), self.goal_wants("tables"))
                live = [i for i in opened if st["tables"][i] > 0]
                if live:
                    i = min(live, key=lambda k: st["tables"][k])
                    base = b("table_upgrade_base") * float(a["upgrade_mult"])
                    cost = self.cost_at(base, st["tables"][i])
                    add(cost, "table_up:" + aid, lambda s=st, i=i: s["tables"].__setitem__(i, s["tables"][i] + 1),
                        lambda s=st, i=i: s["tables"].__setitem__(i, s["tables"][i] - 1))
                add(self.cost_at(b("kitchen_upgrade_base") * float(a["upgrade_mult"]), st["kitchen"]), "kitchen:" + aid,
                    lambda s=st: s.__setitem__("kitchen", s["kitchen"] + 1), lambda s=st: s.__setitem__("kitchen", s["kitchen"] - 1))
                add(self.cost_at(b("cashier_upgrade_base") * float(a["upgrade_mult"]), st["cashier"]), "cashier:" + aid,
                    lambda s=st: s.__setitem__("cashier", s["cashier"] + 1), lambda s=st: s.__setitem__("cashier", s["cashier"] - 1))
            else:
                opened = [i for i in range(len(st["rooms"])) if self.slot_open(aid, a["_bw"][i])]
                closed = [i for i in opened if st["rooms"][i] == 0]
                r = a["room"]
                if closed:
                    extra = max(0, sum(1 for lv in st["rooms"] if lv > 0) - int(a["start_rooms"]))
                    cost = math.floor(float(r["unlock_base"]) * self.cost_mult() * pow(float(r["unlock_mul"]), extra))
                    i = closed[0]
                    add(cost, "room_new", lambda s=st, i=i: s["rooms"].__setitem__(i, 1),
                        lambda s=st, i=i: s["rooms"].__setitem__(i, 0), self.goal_wants("rooms"))
                live = [i for i in opened if st["rooms"][i] > 0]
                if live:
                    i = min(live, key=lambda k: st["rooms"][k])
                    cost = self.cost_at(b("room_upgrade_base"), st["rooms"][i])
                    add(cost, "room_up", lambda s=st, i=i: s["rooms"].__setitem__(i, s["rooms"][i] + 1),
                        lambda s=st, i=i: s["rooms"].__setitem__(i, s["rooms"][i] - 1))
            for w in a.get("wings", []):
                if w["id"] not in st["wings"] and self.level >= int(w["unlock_level"]):
                    cost = math.floor(float(w["cost"]) * self.cost_mult())
                    ready = self.t + float(w.get("build_seconds", 30))
                    add(cost, "wing:" + w["id"], lambda s=st, w=w, r=ready: s["wings"].__setitem__(w["id"], r),
                        lambda s=st, w=w: s["wings"].pop(w["id"], None))
            for k, n in a.get("decor_slots", {}).items():
                have = st["decor"].get(k, 0)
                if have < len(n):
                    d = c.decor[k]
                    cost = math.floor(float(d["cost"]) * float(a.get("decor_cost_mult", 1.0)) * self.cost_mult() * pow(float(d["cost_mul"]), have))
                    add(cost, "decor:" + k, lambda s=st, k=k: s["decor"].__setitem__(k, s["decor"].get(k, 0) + 1),
                        lambda s=st, k=k: s["decor"].__setitem__(k, s["decor"].get(k, 0) - 1), self.goal_wants("decor"))
        return out

    def choose(self):
        base = self.flows()[0]
        best = None
        afford = None
        for cost, name, do, undo, goal in self.candidates():
            if cost <= 0:
                continue
            do()
            g2 = self.flows()[0]
            undo()
            gain = g2 - base
            if goal:
                gain = max(gain, cost / GOAL_PAYBACK)
            ratio = gain / cost
            if ratio <= 0:
                continue
            item = (ratio, cost, name, do)
            if best is None or ratio > best[0]:
                best = item
            if cost <= self.gold and (afford is None or ratio > afford[0]):
                afford = item
        if best is None:
            return None
        if best[1] > self.gold and afford is not None and afford[0] >= 0.6 * best[0]:
            return afford
        return best


def run(cfg, max_hours=24.0, verbose=False):
    S = State(cfg)
    chapters = []
    target = None
    flows = S.flows()
    since_pick = 1e9
    last_level = S.level
    n_ch = len(cfg.chapters)
    while True:
        S.t += DT
        S.gold += flows[0] * DT
        S.run_gold += flows[0] * DT
        S.run_cust += flows[1] * DT
        S.xp += flows[2] * DT
        since_pick += DT
        dirty = False
        while S.xp >= S.exp_needed():
            S.xp -= S.exp_needed()
            S.level += 1
            for d in cfg.dishes:
                if int(d["unlock_level"]) <= S.level and S.dish_lv[d["id"]] == 0:
                    S.dish_lv[d["id"]] = 1
            if S.level in (5, 10, 15, 20, 25, 30):
                S.milestones[S.level] = S.t - S.chapter_start
            dirty = True
        for aid, st in S.areas.items():
            for wid, ready in list(st["wings"].items()):
                if abs(S.t - ready) < DT:
                    dirty = True
        if dirty or since_pick >= 20.0 or target is None:
            target = S.choose()
            since_pick = 0.0
        while target is not None and S.gold >= target[1]:
            S.gold -= target[1]
            target[3]()
            target = S.choose()
            since_pick = 0.0
            dirty = True
        # sao mục tiêu -> sách nghiên cứu
        st_now = S.stars()
        got = S.stars_taken.get(S.chapter, 0)
        while got < st_now:
            S.rp += [2, 3, 5][got]
            got += 1
            S.stars_taken[S.chapter] = got
        while S.rp >= 1 + S.res_income and S.res_income < 10:
            S.rp -= 1 + S.res_income
            S.res_income += 1
        if dirty or since_pick == 0.0:
            flows = S.flows()
        elapsed = S.t - S.chapter_start
        if S.stars() >= 3:
            chapters.append({"chapter": S.chapter + 1, "city": S.ch()["city"], "minutes": elapsed / 60.0,
                             "level": S.level, "milestones": dict(S.milestones), "customers": S.run_cust,
                             "gold": S.run_gold})
            if verbose:
                print("  xong chương %d sau %.0f phút" % (S.chapter + 1, elapsed / 60.0))
            if S.chapter >= n_ch - 1:
                break
            S.rep += max(1, int(math.sqrt(S.run_gold / cfg.b("prestige_divisor", 100000))))
            S.chapter += 1
            S.new_run()
            target = None
            flows = S.flows()
            since_pick = 1e9
        elif elapsed > max_hours * 3600.0:
            chapters.append({"chapter": S.chapter + 1, "city": S.ch()["city"], "minutes": float("inf"),
                             "level": S.level, "milestones": dict(S.milestones), "customers": S.run_cust,
                             "gold": S.run_gold, "stuck": S.goals_done(),
                             "unmet": ["%s %s %.0f/%.0f" % (g["type"], g.get("id", ""), *S.goal_progress(g)) for g in S.goals()
                                       if S.goal_progress(g)[0] < S.goal_progress(g)[1]]})
            break
    return chapters


def fmt(chs):
    lines = []
    total = 0.0
    for c in chs:
        m = c["minutes"]
        total += m if m != float("inf") else 0
        ms = " ".join("L%d=%dp" % (k, v / 60.0) for k, v in sorted(c["milestones"].items()))
        t = "chưa xong (%d/6 mục tiêu)" % c.get("stuck", 0) if m == float("inf") else "%6.0f phút (%.1f giờ)" % (m, m / 60.0)
        lines.append("  Chương %d %-8s %s | cấp %d | %s" % (c["chapter"], c["city"], t, c["level"], ms))
        if c.get("unmet"):
            lines.append("     chưa đạt: " + "; ".join(c["unmet"]))
    lines.append("  Tổng: %.1f giờ" % (total / 60.0))
    return "\n".join(lines)


def main():
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data")
    ap.add_argument("--compare", nargs=2, metavar=("A", "B"))
    ap.add_argument("--max-hours", type=float, default=24.0)
    ap.add_argument("--overrides", help="file JSON ghi đè số liệu để thử")
    ap.add_argument("-v", action="store_true")
    args = ap.parse_args()
    ov = json.loads(Path(args.overrides).read_text(encoding="utf-8")) if args.overrides else {}
    dirs = list(args.compare) if args.compare else [args.data]
    for d in dirs:
        print("== %s ==" % d)
        cfg = Cfg(d)
        if ov:
            cfg.apply(ov)
        print(fmt(run(cfg, args.max_hours, args.v)))


if __name__ == "__main__":
    main()
