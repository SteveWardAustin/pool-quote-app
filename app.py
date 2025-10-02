# app.py
import math
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Pool Pad Sizing & Quote MVP", layout="wide")

# ---------- Constants ----------
PVC_C = 140  # Hazen–Williams for new PVC
PSI_TO_FT = 2.31

INTERNAL_DIAMETERS_IN = {
    1.5: 1.61,  # approx IDs in inches (sch40)
    2.0: 2.07,
    2.5: 2.47,
    3.0: 3.07,
}

EQUIV_LENGTH_PER_FITTING_FT = {"90": 6, "45": 3, "tee": 12}

FILTER_MAX_LOADING = {"Cartridge": 0.5, "Sand": 15.0, "DE": 2.0}

COMMON_HEATER_SIZES = [200_000, 300_000, 400_000]

AWG_TABLE = pd.DataFrame({
    "AWG": [12, 10, 8, 6, 4],
    "Copper_Ohms_per_1000ft": [1.588, 0.999, 0.628, 0.395, 0.249],
    "Est_Ampacity_60C": [20, 30, 40, 55, 70],
})

# ---------- Demo Pump Curves ----------
pump_data = pd.DataFrame({
    "Pump": ["Pentair_IntelliFlo"]*5 + ["Hayward_TriStar"]*5 + ["Jandy_ePump"]*5,
    "Head_ft": [10,20,30,40,50]*3,
    "Flow_gpm": [
        120,110,95,80,65,   # Pentair
        100,90,75,60,45,    # Hayward
        130,115,100,85,70   # Jandy
    ]
})

# ---------- Helper Functions ----------
def required_gpm(gallons: float, turnover_hours: float) -> float:
    return gallons / (turnover_hours * 60.0)

def hazen_williams_head_ft(q_gpm: float, c: float, d_in: float, length_ft: float) -> float:
    if q_gpm <= 0 or d_in <= 0 or length_ft <= 0:
        return 0.0
    return 4.52 * (q_gpm**1.85) / (c**1.85 * d_in**4.87) * length_ft

def equiv_length_total(ft_straight: float, n90: int, n45: int, ntee: int) -> float:
    return ft_straight + n90*EQUIV_LENGTH_PER_FITTING_FT["90"] + n45*EQUIV_LENGTH_PER_FITTING_FT["45"] + ntee*EQUIV_LENGTH_PER_FITTING_FT["tee"]

def filter_area_required(gpm: float, filter_type: str) -> float:
    loading = FILTER_MAX_LOADING[filter_type]
    return gpm / loading if loading > 0 else 0.0

def heater_btu(gallons: float, delta_f: float, hours: float) -> float:
    if hours <= 0: return 0.0
    return 8.34 * gallons * delta_f / hours

def nearest_common_heater(btu_required: float) -> int:
    return min(COMMON_HEATER_SIZES, key=lambda s: abs(s - btu_required))

def suggest_awg(amps: float, length_ft: float, voltage: int = 240, max_drop_pct: float = 3.0):
    if amps <= 0 or length_ft <= 0: return None, None
    max_drop_volts = voltage * (max_drop_pct / 100.0)
    for _, row in AWG_TABLE.iterrows():
        r_total = row["Copper_Ohms_per_1000ft"] * (2 * length_ft / 1000.0)
        vdrop = amps * r_total
        if vdrop <= max_drop_volts and amps <= row["Est_Ampacity_60C"]:
            return int(row["AWG"]), vdrop
    return int(AWG_TABLE.iloc[-1]["AWG"]), amps * (AWG_TABLE.iloc[-1]["Copper_Ohms_per_1000ft"] * (2 * length_ft / 1000.0))

def pump_matcher(required_flow, required_head):
    valid = []
    for pump in pump_data["Pump"].unique():
        curve = pump_data[pump_data["Pump"] == pump]
        flow_at_head = np.interp(required_head, curve["Head_ft"], curve["Flow_gpm"])
        if flow_at_head >= required_flow:
            margin = flow_at_head - required_flow
            valid.append((pump, flow_at_head, margin))
    return valid

# ---------- UI ----------
st.title("Pool Pad Sizing & Quote — MVP (Internal)")

with st.sidebar:
    st.header("Project & Pool")
    customer = st.text_input("Customer", "")
    gallons = st.number_input("Pool gallons", 1000, 200000, value=20000, step=500)
    turnover_hours = st.number_input("Desired turnover hours", 2.0, 24.0, value=8.0, step=0.5)

    st.header("Hydraulics")
    pipe_size = st.selectbox("Pipe size (nominal)", [1.5, 2.0, 2.5, 3.0], index=1)
    suction_len = st.number_input("Suction run length (ft)", 0.0, 400.0, value=60.0, step=5.0)
    return_len = st.number_input("Return run length (ft)", 0.0, 400.0, value=80.0, step=5.0)
    n90 = st.number_input("90° elbows (count)", 0, 40, value=6)
    n45 = st.number_input("45° elbows (count)", 0, 40, value=4)
    ntee = st.number_input("Tees (count)", 0, 20, value=2)
    elevation = st.number_input("Elevation gain (ft)", 0.0, 30.0, value=4.0, step=0.5)
    equip_loss_psi = st.slider("Equipment loss (clean) psi", 0.0, 15.0, value=6.0, step=0.5)

    st.header("Equipment Targets")
    filter_type = st.selectbox("Filter type", ["Cartridge", "Sand", "DE"])
    want_heater = st.checkbox("Include heater sizing?", value=False)
    if want_heater:
        deltaT = st.number_input("Temp rise (°F)", 1.0, 40.0, value=10.0, step=1.0)
        heat_hours = st.number_input("Heat-up time (hrs)", 1.0, 24.0, value=6.0, step=1.0)
    want_salt = st.checkbox("Salt system?", value=True)

    st.header("Electrical (Advisory)")
    pump_amps = st.number_input("Pump amps (nameplate)", 0.0, 60.0, value=12.0, step=0.5)
    distance = st.number_input("Run distance one-way (ft)", 0.0, 400.0, value=75.0, step=5.0)

    st.header("Labor")
    complexity = st.selectbox("Install complexity", ["Basic", "Medium", "Complex"], index=1)
    base_hours = {"Basic": 6, "Medium": 10, "Complex": 16}[complexity]
    extras_hours = st.number_input("Extra hours", 0.0, 40.0, value=2.0, step=1.0)
    labor_rate = 150.0

# ---------- Calculations ----------
gpm = required_gpm(gallons, turnover_hours)
id_in = INTERNAL_DIAMETERS_IN[pipe_size]

suction_L = equiv_length_total(suction_len, n90//2, n45//2, ntee//2)
return_L = equiv_length_total(return_len, n90 - n90//2, n45 - n45//2, ntee - ntee//2)

suction_head = hazen_williams_head_ft(gpm, PVC_C, id_in, suction_L)
return_head = hazen_williams_head_ft(gpm, PVC_C, id_in, return_L)
equip_head = equip_loss_psi * PSI_TO_FT
tdh = suction_head + return_head + elevation + equip_head

filter_area = filter_area_required(gpm, filter_type)
salt_cell_min_gal = math.ceil(gallons * 1.5)

heater_req, heater_pick = None, None
if want_heater:
    heater_req = heater_btu(gallons, deltaT, heat_hours)
    heater_pick = nearest_common_heater(heater_req)

awg, vdrop = suggest_awg(pump_amps, distance, voltage=240)
labor_hours = base_hours + extras_hours + (2 if want_heater else 0) + (1 if want_salt else 0)
labor_total = labor_hours * labor_rate

# ---------- Display ----------
st.subheader("Sizing Results (Specs)")
st.metric("Required Flow (GPM)", f"{gpm:.1f}")
st.metric("Total Dynamic Head (ft)", f"{tdh:.0f}")
st.write(f"**Pump Spec Needed:** ~{gpm:.0f} gpm @ {tdh:.0f} ft TDH")

st.write(f"**Filter Type:** {filter_type} → Min Area ~{filter_area:.0f} sq ft")
if want_heater:
    st.write(f"**Heater:** ~{heater_req:,.0f} BTU/hr → Suggest {heater_pick:,} BTU")
if want_salt:
    st.write(f"**Salt Cell:** ≥ {salt_cell_min_gal:,} gallons")

st.caption("Notes: Hazen–Williams C=140, 1 psi ≈ 2.31 ft. Conservative defaults.")

st.subheader("Pump Curve Matches (Demo Data)")
matches = pump_matcher(gpm, tdh)
if matches:
    df_matches = pd.DataFrame(matches, columns=["Pump", f"Flow @ {tdh:.0f} ft", "Margin (GPM)"])
    st.table(df_matches)
else:
    st.warning("No pump in demo dataset meets required flow/head.")

st.subheader("Electrical Advisory")
if awg:
    st.write(f"Run {distance:.0f} ft • {pump_amps:.1f} A")
    st.write(f"Suggested AWG: #{awg} Cu (V-drop ≈ {vdrop:.2f} V)")
st.caption("Confirm conductor size & breaker with NEC & licensed electrician.")

st.subheader("Labor Estimate")
st.write(f"Hours: {labor_hours:.1f} • Rate: ${labor_rate:.0f}/hr")
st.metric("Labor Total", f"${labor_total:,.0f}")

df_summary = pd.DataFrame([{
    "Customer": customer,
    "Gallons": gallons,
    "Turnover_hrs": turnover_hours,
    "GPM_req": round(gpm,1),
    "TDH_ft": round(tdh,0),
    "Filter_Type": filter_type,
    "Filter_Min_Area_sqft": round(filter_area,0),
    "Heater_BTU_calc": round(heater_req,0) if heater_req else None,
    "Heater_Suggested": heater_pick if heater_pick else None,
    "SaltCell_Min_Gal": salt_cell_min_gal if want_salt else None,
    "Advisory_AWG": awg,
    "Labor_Hours": labor_hours,
    "Labor_Total": labor_total
}])
st.download_button("Download summary (CSV)", df_summary.to_csv(index=False), file_name="pool_quote_summary.csv")
