
import math
from dataclasses import dataclass
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="메이플키우기 종결 계산기", page_icon="📈", layout="wide")

@dataclass
class Settings:
    balance_ratio: float = 90.0
    target_spread: float = 20.0
    d_crit_chance: float = 1.0
    d_crit_dmg: float = 1.0
    d_damage: float = 1.0
    d_main_stat: float = 1000.0
    d_min_mult: float = 1.0
    d_max_mult: float = 1.0
    d_final_dmg: float = 1.0

@dataclass
class Stats:
    crit_chance: float
    crit_dmg: float
    damage: float
    main_stat: float
    min_mult: float
    max_mult: float
    final_dmg: float
    ancient_on: bool
    ancient_awaken: int

ANCIENT_COEF = {0:0.30, 1:0.36, 2:0.42, 3:0.48, 4:0.54, 5:0.60}

def clamp(x, lo, hi):
    return max(lo, min(hi, x))

def ancient_coef(on: bool, awaken: int) -> float:
    if not on:
        return 0.0
    awaken = int(clamp(awaken, 0, 5))
    return ANCIENT_COEF[awaken]

def effective_crit_dmg(s: Stats) -> float:
    coef = ancient_coef(s.ancient_on, s.ancient_awaken)
    return s.crit_dmg + s.crit_chance * coef

def crit_expected_multiplier(s: Stats) -> float:
    cc = clamp(s.crit_chance, 0.0, 100.0) / 100.0
    cd = effective_crit_dmg(s) / 100.0
    return (1.0 - cc) + cc * (1.0 + cd)

def damage_multiplier(s: Stats) -> float:
    return 1.0 + s.damage / 100.0

def final_multiplier(s: Stats) -> float:
    return 1.0 + s.final_dmg / 100.0

def avg_minmax_multiplier(s: Stats) -> float:
    return ((s.min_mult + s.max_mult) / 2.0) / 100.0

def dps_index(s: Stats) -> float:
    return s.main_stat * crit_expected_multiplier(s) * damage_multiplier(s) * final_multiplier(s) * avg_minmax_multiplier(s)

def pct_gain(base: float, new: float) -> float:
    return (new / base - 1.0) * 100.0

def efficiencies(s: Stats, stt: Settings):
    base = dps_index(s)
    out = {}

    s1 = Stats(**{**s.__dict__, "crit_chance": s.crit_chance + stt.d_crit_chance})
    out["크확"] = pct_gain(base, dps_index(s1))

    s2 = Stats(**{**s.__dict__, "crit_dmg": s.crit_dmg + stt.d_crit_dmg})
    out["크뎀"] = pct_gain(base, dps_index(s2))

    s3 = Stats(**{**s.__dict__, "damage": s.damage + stt.d_damage})
    out["데미지"] = pct_gain(base, dps_index(s3))

    s4 = Stats(**{**s.__dict__, "main_stat": s.main_stat + stt.d_main_stat})
    out["주스텟"] = pct_gain(base, dps_index(s4))

    s5 = Stats(**{**s.__dict__, "min_mult": s.min_mult + stt.d_min_mult})
    out["최소배율"] = pct_gain(base, dps_index(s5))

    s6 = Stats(**{**s.__dict__, "max_mult": s.max_mult + stt.d_max_mult})
    out["최대배율"] = pct_gain(base, dps_index(s6))

    s7 = Stats(**{**s.__dict__, "final_dmg": s.final_dmg + stt.d_final_dmg})
    out["최종데미지"] = pct_gain(base, dps_index(s7))

    return out

def balance_and_goals(s: Stats, stt: Settings):
    target_stat = s.damage * stt.balance_ratio
    stat_diff = target_stat - s.main_stat  # + 부족, - 과다

    target_damage = s.main_stat / stt.balance_ratio
    damage_diff = target_damage - s.damage  # + 부족, - 과다

    spread = s.max_mult - s.min_mult
    target_min = s.max_mult - stt.target_spread
    min_need = target_min - s.min_mult  # + 필요

    steps_damage = max(0.0, damage_diff) / max(1e-9, stt.d_damage)
    steps_stat = max(0.0, stat_diff) / max(1e-9, stt.d_main_stat)
    steps_min = max(0.0, min_need) / max(1e-9, stt.d_min_mult)

    return {
        "목표주스텟": target_stat,
        "주스텟차이": stat_diff,
        "목표데미지": target_damage,
        "데미지차이": damage_diff,
        "현재편차": spread,
        "목표최소": target_min,
        "최소필요": min_need,
        "주스텟필요스텝": steps_stat,
        "데미지필요스텝": steps_damage,
        "최소필요스텝": steps_min,
    }

def recommendation(s: Stats, stt: Settings):
    g = balance_and_goals(s, stt)
    if s.crit_chance < 100:
        return "크확 100% 먼저"
    if g["최소필요"] > 0:
        return f"최소배율 +{g['최소필요']:.1f}%p (편차 {stt.target_spread:g} 목표)"
    if g["데미지차이"] > 0:
        return f"데미지 +{g['데미지차이']:.1f}%p (주스텟 대비 부족)"
    if g["주스텟차이"] > 0:
        return f"주스텟 +{g['주스텟차이']:.0f} (데미지 대비 부족)"
    return "미세최적화(크뎀/최종뎀/최소) 단계"

st.title("📈 메이플키우기 계산기")
st.caption("Hyedan 69섭 테토클럽 전용")

with st.sidebar:
    st.header("입력")
    crit_chance = st.number_input("크확(%)", min_value=0.0, max_value=200.0, value=100.0, step=1.0)
    crit_dmg = st.number_input("크뎀(%)", min_value=0.0, max_value=9999.0, value=150.0, step=1.0)
    damage = st.number_input("데미지(%)", min_value=0.0, max_value=9999.0, value=545.0, step=1.0)
    main_stat = st.number_input("주스텟", min_value=0.0, max_value=10_000_000.0, value=46406.0, step=100.0)
    min_mult = st.number_input("최소배율(%)", min_value=0.0, max_value=9999.0, value=155.6, step=0.1)
    max_mult = st.number_input("최대배율(%)", min_value=0.0, max_value=9999.0, value=185.0, step=0.1)
    final_dmg = st.number_input("최종데미지(%)", min_value=0.0, max_value=9999.0, value=0.0, step=0.1)

    st.divider()
    st.subheader("고대책")
    ancient_on = st.toggle("고대책 적용", value=True)
    ancient_awaken = st.slider("각성(0~5)", min_value=0, max_value=5, value=0, disabled=not ancient_on)

    st.divider()
    st.subheader("설정")
    balance_ratio = st.number_input("균형비율(데미지:주스텟)", min_value=1.0, max_value=300.0, value=90.0, step=1.0)
    target_spread = st.number_input("목표 편차(최대-최소)", min_value=0.0, max_value=200.0, value=20.0, step=1.0)

    with st.expander("효율 계산 증분(선택)"):
        d_cc = st.number_input("크확 증분(%p)", min_value=0.1, max_value=50.0, value=1.0, step=0.1)
        d_cd = st.number_input("크뎀 증분(%p)", min_value=0.1, max_value=200.0, value=1.0, step=0.1)
        d_dmg = st.number_input("데미지 증분(%p)", min_value=0.1, max_value=200.0, value=1.0, step=0.1)
        d_stat = st.number_input("주스텟 증분(+)", min_value=1.0, max_value=1_000_000.0, value=1000.0, step=100.0)
        d_min = st.number_input("최소배율 증분(%p)", min_value=0.1, max_value=200.0, value=1.0, step=0.1)
        d_max = st.number_input("최대배율 증분(%p)", min_value=0.1, max_value=200.0, value=1.0, step=0.1)
        d_final = st.number_input("최종뎀 증분(%p)", min_value=0.1, max_value=200.0, value=1.0, step=0.1)

settings = Settings(
    balance_ratio=float(balance_ratio),
    target_spread=float(target_spread),
    d_crit_chance=float(d_cc),
    d_crit_dmg=float(d_cd),
    d_damage=float(d_dmg),
    d_main_stat=float(d_stat),
    d_min_mult=float(d_min),
    d_max_mult=float(d_max),
    d_final_dmg=float(d_final),
)

stats = Stats(
    crit_chance=float(crit_chance),
    crit_dmg=float(crit_dmg),
    damage=float(damage),
    main_stat=float(main_stat),
    min_mult=float(min_mult),
    max_mult=float(max_mult),
    final_dmg=float(final_dmg),
    ancient_on=bool(ancient_on),
    ancient_awaken=int(ancient_awaken),
)

coef = ancient_coef(stats.ancient_on, stats.ancient_awaken)
applied_cd = effective_crit_dmg(stats)
base_index = dps_index(stats)
goals = balance_and_goals(stats, settings)
eff = efficiencies(stats, settings)

col1, col2, col3, col4 = st.columns(4)
col1.metric("현재 딜지수", f"{base_index:,.2f}")
col2.metric("고대책 계수", f"{coef:.2f}")
col3.metric("적용 크뎀(%)", f"{applied_cd:.1f}")
col4.metric("최소/최대 편차", f"{(stats.max_mult-stats.min_mult):.1f}")

st.info("추천: " + recommendation(stats, settings))

st.subheader("균형 진단 + 목표치/필요량")
gdf = pd.DataFrame([
    ["목표 주스텟(=데미지×비율)", goals["목표주스텟"]],
    ["주스텟 차이(+부족 / -과다)", goals["주스텟차이"]],
    ["목표 데미지(=주스텟/비율)", goals["목표데미지"]],
    ["데미지 차이(+부족 / -과다)", goals["데미지차이"]],
    ["목표 최소(=최대-목표편차)", goals["목표최소"]],
    ["최소 필요(+필요 / -여유)", goals["최소필요"]],
    ["주스텟 필요 스텝(증분 기준)", goals["주스텟필요스텝"]],
    ["데미지 필요 스텝(증분 기준)", goals["데미지필요스텝"]],
    ["최소 필요 스텝(증분 기준)", goals["최소필요스텝"]],
], columns=["항목", "값"])
st.dataframe(gdf, use_container_width=True, hide_index=True)

st.subheader("효율(증분 기준 딜 상승률 %)")
edf = pd.DataFrame([{"항목": k, "효율(%)": v} for k, v in eff.items()]).sort_values("효율(%)", ascending=False)
st.dataframe(edf, use_container_width=True, hide_index=True)

with st.expander("계산 방식(요약)"):
    st.write("""
- 딜지수 = 주스텟 × 치명타기대배율 × (1+데미지%) × (1+최종뎀%) × 평균배율(최소/최대)
- 치명타기대배율 = (1-크확)×1 + (크확)×(1+적용크뎀)
- 고대책 적용 크뎀 = 기본 크뎀 + 크확×계수(0각~5각)
""")
