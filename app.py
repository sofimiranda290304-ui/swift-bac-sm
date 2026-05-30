import streamlit as st
import pandas as pd
from amplpy import AMPL

st.set_page_config(page_title="BAC SSC - Operaciones SWIFT", layout="wide")

st.markdown("""
<style>
h1 { color: #C8102E; }
h2 { color: #1A1A2E; }
.stButton>button {
    background-color: #C8102E;
    color: white;
    font-weight: bold;
    border-radius: 8px;
    padding: 0.5em 2em;
}
.stButton>button:hover { background-color: #9B0D23; }
</style>
""", unsafe_allow_html=True)

st.title("🏦 BAC SSC — Operaciones SWIFT")
st.markdown("**Ejercicio 3 · Programación Entera Mixta · II-1122**")

ANALISTAS   = ["Andrea", "Beatriz", "Carlos", "Daniel", "Esteban"]
OPERACIONES = ["MT103", "MT202", "MT700", "MT760", "MT940"]

tiempos_raw = {
    "Andrea":  [25, 30,  0,  0, 20],
    "Beatriz": [35, 28, 40, 45, 22],
    "Carlos":  [40, 45, 35, 30, 25],
    "Daniel":  [30, 32, 50,  0, 18],
    "Esteban": [ 0,  0, 30, 28, 30],
}

df_tiempos = pd.DataFrame(tiempos_raw, index=OPERACIONES).T
df_tiempos.index.name   = "Analista"
df_tiempos.columns.name = "Operación"

tab1, tab2, tab3 = st.tabs(["📋 Problema", "📐 Modelo AMPL", "⚙️ Resolución"])

with tab1:
    st.header("Contexto del problema")
    st.info(
        "El Centro de Servicios Compartidos (SSC) de BAC Credomatic procesa cada mañana "
        "un lote de operaciones SWIFT urgentes provenientes de Costa Rica, Guatemala, "
        "Honduras y Panamá. Como Subgerente de Operaciones Internacionales, usted asigna "
        "las operaciones del lote entre los analistas del equipo de Comercio Exterior."
    )

    st.subheader("Lote del día — 5 operaciones SWIFT urgentes (cierre a las 11:00 a.m.)")
    col1, col2, col3, col4, col5 = st.columns(5)
    ops_info = [
        ("MT103", "Transferencia cliente",      "→ Panamá"),
        ("MT202", "Transferencia interbancaria", "→ Guatemala"),
        ("MT700", "Carta de crédito (LC)",       "→ Honduras"),
        ("MT760", "Garantía bancaria",           ""),
        ("MT940", "Reporte de cuenta",           ""),
    ]
    for col, (code, desc, origen) in zip([col1, col2, col3, col4, col5], ops_info):
        col.markdown(f"""
        <div style='background:#C8102E;color:white;text-align:center;
                    padding:10px;border-radius:6px 6px 0 0;font-weight:bold'>
            {code}
        </div>
        <div style='border:1px solid #ddd;text-align:center;
                    padding:10px;border-radius:0 0 6px 6px;'>
            {desc}<br><small>{origen}</small>
        </div>""", unsafe_allow_html=True)

    st.subheader("Tiempos de procesamiento (minutos)")
    st.caption("🔴 = bloqueado por compliance Bridger")

    def color_celdas(val):
        return "background-color:#ffcccc; color:#cc0000; font-weight:bold" if val == 0 else ""

    st.dataframe(
        df_tiempos.style.map(color_celdas),
        use_container_width=True
    )

    st.subheader("🚫 Restricciones de compliance Bridger")
    restricciones = [
        ("Andrea",  "No puede ejecutar MT700 (LC) ni MT760 (Garantía)"),
        ("Daniel",  "No puede ejecutar MT760 (Garantía)"),
        ("Esteban", "No puede ejecutar MT103 ni MT202 (en re-certificación)"),
    ]
    for analista, restriccion in restricciones:
        st.markdown(f"- **{analista}**: {restriccion}")

    st.subheader("🎯 El reto")
    st.warning(
        "Asignar UNA operación a CADA uno de los 5 analistas del turno minimizando "
        "el tiempo TOTAL de procesamiento del lote."
    )

with tab2:
    st.header("Modelo Matemático")

    col_izq, col_der = st.columns([1, 1])

    with col_izq:
        st.subheader("Formulación")
        st.markdown("""
**Variable de decisión**

$x_{ij} = 1$ si el analista $i$ realiza la operación $j$; 0 en caso contrario.

**Función objetivo**

$$\\min Z = \\sum_{i}\\sum_{j} t_{ij} \\cdot x_{ij}$$

**Restricciones**

- Cada operación la realiza exactamente 1 analista:
$$\\sum_i x_{ij} = 1 \\quad \\forall j$$

- Cada analista realiza exactamente 1 operación:
$$\\sum_j x_{ij} = 1 \\quad \\forall i$$

- Compliance (celdas bloqueadas):
$$x_{ij} = 0 \\quad \\text{si } t_{ij} = 0$$

- Integralidad:
$$x_{ij} \\in \\{0,1\\}$$
        """)

    with col_der:
        st.subheader("Archivo .mod")
        mod_code = """\
set ANALISTAS;
set OPERACIONES;

param tiempo{i in ANALISTAS,
             j in OPERACIONES} >= 0;
param disponible{i in ANALISTAS,
                 j in OPERACIONES} binary;

var x{i in ANALISTAS,
      j in OPERACIONES} binary;

minimize Tiempo_total:
  sum {i in ANALISTAS,
       j in OPERACIONES}
  tiempo[i,j] * x[i,j];

s.t. Op{j in OPERACIONES}:
  sum {i in ANALISTAS} x[i,j] = 1;

s.t. An{i in ANALISTAS}:
  sum {j in OPERACIONES} x[i,j] = 1;

s.t. Comp{i in ANALISTAS,
          j in OPERACIONES}:
  x[i,j] <= disponible[i,j];"""
        st.code(mod_code, language="text")

        st.subheader("Archivo .dat")
        dat_code = """\
set ANALISTAS := Andrea Beatriz Carlos Daniel Esteban;
set OPERACIONES := MT103 MT202 MT700 MT760 MT940;

param tiempo :
           MT103  MT202  MT700  MT760  MT940 :=
Andrea       25     30      0      0     20
Beatriz      35     28     40     45     22
Carlos       40     45     35     30     25
Daniel       30     32     50      0     18
Esteban       0      0     30     28     30 ;

param disponible :
           MT103  MT202  MT700  MT760  MT940 :=
Andrea       1      1      0      0      1
Beatriz      1      1      1      1      1
Carlos       1      1      1      1      1
Daniel       1      1      1      0      1
Esteban      0      0      1      1      1 ;"""
        st.code(dat_code, language="text")

with tab3:
    st.header("Resolución con AMPL")

    MOD = """\
set ANALISTAS;
set OPERACIONES;

param tiempo{i in ANALISTAS, j in OPERACIONES} >= 0;
param disponible{i in ANALISTAS, j in OPERACIONES} binary;

var x{i in ANALISTAS, j in OPERACIONES} binary;

minimize Tiempo_total:
  sum {i in ANALISTAS, j in OPERACIONES} tiempo[i,j] * x[i,j];

s.t. Op{j in OPERACIONES}: sum {i in ANALISTAS} x[i,j] = 1;
s.t. An{i in ANALISTAS}:   sum {j in OPERACIONES} x[i,j] = 1;
s.t. Comp{i in ANALIST
