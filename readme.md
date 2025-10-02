# Pool Pad Sizing & Quote App (MVP)

This is a lightweight internal tool built with **Streamlit, Python, Pandas, and NumPy**.  
It helps estimate pool pad renovation and repair jobs by calculating hydraulics, equipment sizing, and labor.

---

## 🚀 Features (MVP)
- Calculates **required GPM** based on pool gallons & turnover rate.
- Computes **Total Dynamic Head (TDH)** using Hazen–Williams equation.
- Recommends **filter size**, **heater BTU rating**, and **salt cell capacity**.
- Advises on **wire size (AWG)** for pump circuits (preliminary).
- Estimates **labor hours & cost** at a fixed $150/hr.
- Matches specs against **sample pump curves** (demo data).
- Exports results as **CSV summary**.

---

## 📦 Requirements
See `requirements.txt` for package versions:
- Streamlit
- Pandas
- NumPy

---

## ▶️ Run Locally
Clone the repo and install dependencies:

```bash
git clone https://github.com/SteveWardAustin/pool-quote-app.git
cd pool-quote-app
pip install -r requirements.txt
streamlit run app.py
