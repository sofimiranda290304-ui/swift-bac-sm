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

# ── Datos del problema ────────────────────────────────────────────────
ANALISTAS   = ["Andrea", "Beatriz", "Carlos", "Daniel", "Esteban"]
OPERACIONES = ["MT103", "MT202", "MT700", "MT760", "MT940"]

# Tiempo en minutos; 0 = bloqueado por compliance
tiempos_raw = {
    #         MT103  MT202  MT700  MT760  MT940
    "Andrea":  [ 25,   30,    0,    0,    20],
    "Beatriz": [ 35,   28,   40,   45,    22],
    "Carlos":  [ 40,   45,   35,   30,    25],
    "Daniel":  [ 30,   32,   50,    0,    18],
    "Esteban": [  0,    0,   30,   28,    30],
}

df_tiempos = pd.DataFrame(tiempos_raw, index=OPERACIONES).T
df_tiempos.index.name   = "Analista"
df_tiempos.columns.name = "Operación"

# ── Tabs ──────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📋 Problema", "📐 Modelo AMPL", "⚙️ Resolución"])

# ── TAB 1: Problema ───────────────────────────────────────────────────
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
        ("MT103", "Transferencia cliente", "→ Panamá"),
        ("MT202", "Transferencia interbancaria", "→ Guatemala"),
        ("MT700", "Carta de crédito (LC)", "→ Honduras"),
        ("MT760", "Garantía bancaria", ""),
        ("MT940", "Reporte de cuenta", ""),
    ]
    for col, (code, desc, origen) in zip([col1,col2,col3,col4,col5], ops_info):
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
        df_tiempos.style.applymap(color_celdas),
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

# ── TAB 2: Modelo AMPL ────────────────────────────────────────────────
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
  sum_i x[i,j] = 1;

s.t. An{i in ANALISTAS}:
  sum_j x[i,j] = 1;

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

# ── TAB 3: Resolución ─────────────────────────────────────────────────
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
s.t. Comp{i in ANALISTAS, j in OPERACIONES}: x[i,j] <= disponible[i,j];
"""

    DAT_VALUES = {
        ("Andrea",  "MT103"): 25, ("Andrea",  "MT202"): 30,
        ("Andrea",  "MT700"):  0, ("Andrea",  "MT760"):  0,
        ("Andrea",  "MT940"): 20,
        ("Beatriz", "MT103"): 35, ("Beatriz", "MT202"): 28,
        ("Beatriz", "MT700"): 40, ("Beatriz", "MT760"): 45,
        ("Beatriz", "MT940"): 22,
        ("Carlos",  "MT103"): 40, ("Carlos",  "MT202"): 45,
        ("Carlos",  "MT700"): 35, ("Carlos",  "MT760"): 30,
        ("Carlos",  "MT940"): 25,
        ("Daniel",  "MT103"): 30, ("Daniel",  "MT202"): 32,
        ("Daniel",  "MT700"): 50, ("Daniel",  "MT760"):  0,
        ("Daniel",  "MT940"): 18,
        ("Esteban", "MT103"):  0, ("Esteban", "MT202"):  0,
        ("Esteban", "MT700"): 30, ("Esteban", "MT760"): 28,
        ("Esteban", "MT940"): 30,
    }

    if st.button("🚀 Resolver ahora"):
        with st.spinner("Resolviendo con AMPL + HiGHS..."):
            try:
                ampl = AMPL()
                ampl.eval(MOD)

                ampl.set["ANALISTAS"]   = ANALISTAS
                ampl.set["OPERACIONES"] = OPERACIONES

                t_param = ampl.param["tiempo"]
                d_param = ampl.param["disponible"]
                for i in ANALISTAS:
                    for j in OPERACIONES:
                        t_param[i, j] = DAT_VALUES[(i, j)]
                        d_param[i, j] = 0 if DAT_VALUES[(i, j)] == 0 else 1

                ampl.option["solver"] = "highs"
                ampl.solve()

                status = ampl.solve_result
                if status in ("solved", "optimal"):
                    z = ampl.obj["Tiempo_total"].value()
                    x = ampl.var["x"]

                    asignaciones = []
                    for i in ANALISTAS:
                        for j in OPERACIONES:
                            if round(x[i, j].value()) == 1:
                                asignaciones.append({
                                    "Analista": i,
                                    "Operación": j,
                                    "Tiempo (min)": DAT_VALUES[(i, j)]
                                })

                    df_res = pd.DataFrame(asignaciones)

                    st.success(f"✅ Solución óptima encontrada — Z = **{int(z)} minutos**")

                    st.subheader("📊 Asignación óptima")
                    st.dataframe(df_res, use_container_width=True, hide_index=True)

                    st.subheader("📈 Tiempo por analista")
                    st.bar_chart(df_res.set_index("Analista")["Tiempo (min)"])

                    st.subheader("🗺️ Matriz de asignación")
                    matriz = pd.DataFrame(0, index=ANALISTAS, columns=OPERACIONES)
                    for _, row in df_res.iterrows():
                        matriz.loc[row["Analista"], row["Operación"]] = row["Tiempo (min)"]

                    def highlight_assigned(val):
                        return "background-color:#d4edda; font-weight:bold" if val > 0 else ""

                    st.dataframe(
                        matriz.style.applymap(highlight_assigned),
                        use_container_width=True
                    )
                else:
                    st.error(f"El solver no encontró solución óptima. Estado: {status}")

            except Exception as e:
                st.error(f"Error al resolver: {e}")
                st.info("Verifica que `amplpy` esté instalado y el solver HiGHS disponible.")
