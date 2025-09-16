from __future__ import annotations

import json
import os
from typing import Dict, List, Optional, Tuple

import pandas as pd
import plotly.express as px
import streamlit as st
from PIL import Image

from security import verify_password

# Configuración de la página
st.set_page_config(
    page_title="Dashboard Fondo Común de Inversión",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)


class FondoInversion:
    """Modelo de datos del fondo"""

    def __init__(self, archivo_datos: str = "fondo_datos.json") -> None:
        self.archivo_datos = archivo_datos
        self.datos = self.cargar_datos()

    def cargar_datos(self) -> Dict:
        """Carga los datos desde disco asegurando la estructura básica."""
        if os.path.exists(self.archivo_datos):
            try:
                with open(self.archivo_datos, "r", encoding="utf-8") as f:
                    datos = json.load(f)
            except Exception:
                datos = self.estructura_inicial()
        else:
            datos = self.estructura_inicial()

        estructura = self.estructura_inicial()
        for clave, valor_default in estructura.items():
            if clave not in datos:
                datos[clave] = valor_default
        return datos

    def estructura_inicial(self) -> Dict:
        return {
            "clientes": {},
            "transacciones": [],
            "balance_diario": [],
            "valor_cuotaparte": 1000.0,
            "total_cuotapartes": 0,
            "composicion_fondo": {},
            "distribucion_activos": {},
            "usuarios": {},
            "tipo_cambio": 0.0,
        }

    def guardar_datos(self) -> None:
        with open(self.archivo_datos, "w", encoding="utf-8") as f:
            json.dump(self.datos, f, indent=2, ensure_ascii=False)

    # ------------------------------------------------------------------
    # Métodos de consulta de datos
    # ------------------------------------------------------------------

    def get_usuario(self, username: str) -> Optional[Dict]:
        return self.datos.get("usuarios", {}).get(username)

    def get_clientes_filtrados(
        self, clientes_permitidos: Optional[List[str]]
    ) -> Dict[str, Dict]:
        clientes = self.datos.get("clientes", {})
        if clientes_permitidos is None:
            return dict(clientes)
        return {
            nombre: info
            for nombre, info in clientes.items()
            if nombre in clientes_permitidos
        }

    def get_transacciones_filtradas(
        self, clientes_permitidos: Optional[List[str]]
    ) -> List[Dict]:
        transacciones = self.datos.get("transacciones", [])
        if clientes_permitidos is None:
            return list(transacciones)
        return [
            t for t in transacciones if t.get("cliente") in clientes_permitidos
        ]

    def get_patrimonio_clientes(
        self, clientes_permitidos: Optional[List[str]]
    ) -> Dict[str, Dict]:
        clientes = self.get_clientes_filtrados(clientes_permitidos)
        if clientes_permitidos is None:
            total_para_porcentaje = self.datos.get("total_cuotapartes", 0)
        else:
            total_para_porcentaje = sum(
                datos.get("cuotapartes", 0) for datos in clientes.values()
            )

        patrimonio: Dict[str, Dict] = {}
        valor_cuotaparte = self.datos.get("valor_cuotaparte", 0)
        for nombre, datos in clientes.items():
            cuotapartes = datos.get("cuotapartes", 0)
            valor_actual = cuotapartes * valor_cuotaparte
            porcentaje = (
                (cuotapartes / total_para_porcentaje * 100)
                if total_para_porcentaje
                else 0
            )
            patrimonio[nombre] = {
                "cuotapartes": cuotapartes,
                "valor_actual": valor_actual,
                "porcentaje": porcentaje,
            }
        return patrimonio

    def get_total_cuotapartes_filtradas(
        self, clientes_permitidos: Optional[List[str]]
    ) -> float:
        if clientes_permitidos is None:
            return self.datos.get("total_cuotapartes", 0.0)
        clientes = self.get_clientes_filtrados(clientes_permitidos)
        return sum(datos.get("cuotapartes", 0.0) for datos in clientes.values())

    def get_balance_diario_df(self) -> pd.DataFrame:
        df = pd.DataFrame(self.datos.get("balance_diario", []))
        if df.empty:
            return df
        df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
        df = df.dropna(subset=["fecha"]).sort_values("fecha")
        return df

    def calcular_rendimiento_mensualizado(self) -> Tuple[float, float]:
        if len(self.datos.get("balance_diario", [])) < 2:
            return 0.0, 0.0

        df_balance = self.get_balance_diario_df()
        if df_balance.empty:
            return 0.0, 0.0

        balance_inicial = df_balance["balance"].iloc[0]
        balance_actual = df_balance["balance"].iloc[-1]
        if balance_inicial == 0:
            return 0.0, 0.0

        fecha_inicial = df_balance["fecha"].iloc[0]
        fecha_actual = df_balance["fecha"].iloc[-1]
        dias = (fecha_actual - fecha_inicial).days
        if dias <= 0:
            return 0.0, 0.0

        rendimiento_total = ((balance_actual - balance_inicial) / balance_inicial) * 100
        if dias >= 30:
            rendimiento_mensual = (
                (pow(balance_actual / balance_inicial, 30 / dias) - 1) * 100
            )
        else:
            rendimiento_mensual = (rendimiento_total / dias) * 30

        return rendimiento_total, rendimiento_mensual

    def get_balance_total_filtrado(
        self, clientes_permitidos: Optional[List[str]]
    ) -> float:
        patrimonio = self.get_patrimonio_clientes(clientes_permitidos)
        return sum(info["valor_actual"] for info in patrimonio.values())

    def get_tipo_cambio(self) -> float:
        tipo_cambio = self.datos.get("tipo_cambio", 0.0)
        try:
            tipo_cambio_float = float(tipo_cambio)
        except (TypeError, ValueError):
            return 0.0
        return tipo_cambio_float if tipo_cambio_float > 0 else 0.0

    def get_composicion_detallada(self) -> List[Dict]:
        composicion = self.datos.get("composicion_fondo", {})
        tipo_cambio = self.get_tipo_cambio()
        detalle: List[Dict] = []

        for instrumento, datos in composicion.items():
            moneda = str(datos.get("moneda", "ARS")).upper()
            monto_pesos = float(datos.get("monto", 0.0) or 0.0)
            monto_moneda = datos.get("monto_moneda")
            if monto_moneda is None:
                monto_moneda = datos.get("monto_original")

            if moneda == "ARS":
                if monto_moneda is None:
                    monto_moneda = monto_pesos
            elif moneda == "USD":
                if monto_moneda is None and tipo_cambio:
                    monto_moneda = monto_pesos / tipo_cambio
                if monto_moneda is not None and tipo_cambio:
                    monto_pesos = float(monto_moneda) * tipo_cambio
            else:
                if monto_moneda is None:
                    monto_moneda = monto_pesos

            detalle.append(
                {
                    "Instrumento": instrumento,
                    "Moneda": moneda,
                    "Monto_moneda": float(monto_moneda)
                    if monto_moneda is not None
                    else None,
                    "Monto_ARS": monto_pesos,
                }
            )

        total_en_pesos = sum(item["Monto_ARS"] for item in detalle)
        for item in detalle:
            item["Porcentaje"] = (
                (item["Monto_ARS"] / total_en_pesos * 100) if total_en_pesos else 0.0
            )

        return detalle


# ----------------------------------------------------------------------
# Utilidades de interfaz
# ----------------------------------------------------------------------


def cargar_logo() -> Optional[Image.Image]:
    logo_path = "Andes.png"
    if os.path.exists(logo_path):
        try:
            return Image.open(logo_path)
        except Exception:
            return None
    return None


def aplicar_estilos() -> None:
    st.markdown(
        """
        <style>
        .main-header {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            padding: 2rem;
            border-radius: 12px;
            color: white;
            text-align: center;
            margin-bottom: 2rem;
        }
        .metric-card {
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
        }
        .stAlert {
            border-radius: 10px;
        }
        .readonly-note {
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 12px 16px;
            margin-bottom: 16px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def verificar_autenticacion(fondo: FondoInversion) -> bool:
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.usuario = None
        st.session_state.rol = None
        st.session_state.clientes_permitidos = None

    if st.session_state.authenticated:
        return True

    st.markdown(
        """
        <div style="background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);\n                    padding: 2rem; border-radius: 12px; color: white; text-align: center;\n                    margin-bottom: 2rem;">
            <h1>🔒 Acceso restringido</h1>
            <p>Ingresa tus credenciales para consultar el fondo.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    usuarios_configurados = fondo.datos.get("usuarios", {})
    if not usuarios_configurados:
        st.warning(
            "No hay usuarios configurados. Usa `admin_console.py` para crear credenciales."
        )
        st.stop()

    with st.form("login_form"):
        st.subheader("Ingreso al panel")
        usuario = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        submitted = st.form_submit_button("Ingresar")

        if submitted:
            datos_usuario = fondo.get_usuario(usuario)
            if datos_usuario and verify_password(
                password, datos_usuario.get("salt", ""), datos_usuario.get("password_hash", "")
            ):
                st.session_state.authenticated = True
                st.session_state.usuario = usuario
                rol = datos_usuario.get("rol", "cliente")
                st.session_state.rol = rol
                if rol == "admin":
                    st.session_state.clientes_permitidos = None
                else:
                    st.session_state.clientes_permitidos = datos_usuario.get("clientes", [])
                st.success("✅ Acceso autorizado")
                st.rerun()
            else:
                st.error("❌ Usuario o contraseña incorrectos")

    st.stop()


def mostrar_logout(fondo: FondoInversion) -> None:
    with st.sidebar:
        st.markdown("### 👤 Sesión")
        st.write(f"**Usuario:** {st.session_state.usuario}")
        rol = st.session_state.get("rol", "cliente")
        rol_label = "Administrador" if rol == "admin" else "Inversor"
        st.write(f"**Rol:** {rol_label}")
        st.info(
            "Esta es una vista de solo lectura. Todas las modificaciones deben realizarse desde `admin_console.py`."
        )
        if st.button("🚪 Cerrar sesión", use_container_width=True):
            for key in ["authenticated", "usuario", "rol", "clientes_permitidos"]:
                st.session_state.pop(key, None)
            st.rerun()


# ----------------------------------------------------------------------
# Inicio de la aplicación
# ----------------------------------------------------------------------

aplicar_estilos()

if "fondo" not in st.session_state:
    st.session_state.fondo = FondoInversion()

fondo: FondoInversion = st.session_state.fondo

if not verificar_autenticacion(fondo):
    st.stop()

mostrar_logout(fondo)

logo = cargar_logo()

st.markdown("<div class='main-header'>", unsafe_allow_html=True)
if logo is not None:
    col_logo, col_text = st.columns([1, 3])
    with col_logo:
        st.image(logo, width=140)
    with col_text:
        st.markdown("<h1>Dashboard Fondo Común de Inversión</h1>", unsafe_allow_html=True)
        st.markdown(
            "<p>Panel de consulta - Datos en modo lectura</p>",
            unsafe_allow_html=True,
        )
else:
    st.markdown("<h1>Dashboard Fondo Común de Inversión</h1>", unsafe_allow_html=True)
    st.markdown(
        "<p>Panel de consulta - Datos en modo lectura</p>",
        unsafe_allow_html=True,
    )
st.markdown("</div>", unsafe_allow_html=True)

clientes_permitidos = st.session_state.get("clientes_permitidos")
patrimonio_clientes = fondo.get_patrimonio_clientes(clientes_permitidos)
transacciones_filtradas = fondo.get_transacciones_filtradas(clientes_permitidos)

balance_total = fondo.get_balance_total_filtrado(clientes_permitidos)
valor_cuotaparte = fondo.datos.get("valor_cuotaparte", 0.0)
tipo_cambio = fondo.get_tipo_cambio()
valor_total_usd = (balance_total / tipo_cambio) if tipo_cambio else None

clientes_filtrados = fondo.get_clientes_filtrados(clientes_permitidos)
numero_clientes = len(clientes_filtrados)

cuotapartes_totales = fondo.get_total_cuotapartes_filtradas(clientes_permitidos)
rendimiento_total, rendimiento_mensual = fondo.calcular_rendimiento_mensualizado()

col1, col2, col3, col4, col5, col6 = st.columns(6)
with col1:
    st.metric("Valor actual (ARS)", f"${balance_total:,.2f}")
with col2:
    if valor_total_usd is not None:
        st.metric("Valor actual (USD)", f"US$ {valor_total_usd:,.2f}")
    else:
        st.metric("Valor actual (USD)", "—")
with col3:
    if tipo_cambio:
        st.metric("Tipo de cambio (ARS/USD)", f"${tipo_cambio:,.2f}")
    else:
        st.metric("Tipo de cambio (ARS/USD)", "—")
with col4:
    st.metric("Clientes visibles", str(numero_clientes))
with col5:
    st.metric("Cuotapartes", f"{cuotapartes_totales:,.4f}")
with col6:
    st.metric("Valor de cuotaparte", f"${valor_cuotaparte:,.2f}")

col_r1, col_r2, col_r3 = st.columns([1, 2, 1])
with col_r2:
    color = "#28a745" if rendimiento_mensual >= 0 else "#dc3545"
    st.markdown(
        f"""
        <div class="metric-card" style="text-align: center;">
            <div style="font-size: 0.8em; color: #666;">Rendimiento mensualizado del fondo</div>
            <div style="font-size: 1.4em; font-weight: 700; color: {color};">
                {rendimiento_mensual:+.2f}%
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

if clientes_permitidos is not None and not clientes_filtrados:
    st.warning(
        "Tu usuario no tiene clientes asociados actualmente. Consulta al administrador si necesitas acceso."
    )


tab_resumen, tab_clientes, tab_graficos, tab_historial, tab_composicion = st.tabs(
    ["📈 Resumen", "👥 Clientes", "📊 Gráficos", "🔄 Historial", "📋 Composición"]
)

with tab_resumen:
    st.subheader("Resumen general")
    st.markdown(
        "<div class='readonly-note'>Los datos se actualizan desde la consola de administración. Esta vista solo permite consulta.</div>",
        unsafe_allow_html=True,
    )

    df_balance = fondo.get_balance_diario_df()
    if not df_balance.empty:
        fig_balance = px.line(
            df_balance,
            x="fecha",
            y="balance",
            title="Evolución del balance del fondo",
            markers=True,
        )
        fig_balance.update_layout(margin=dict(l=10, r=10, t=50, b=10))
        st.plotly_chart(fig_balance, use_container_width=True)
    else:
        st.info("No hay registros de balance diario disponibles.")

    if patrimonio_clientes:
        st.subheader("Detalle por cliente")
        for nombre, info in patrimonio_clientes.items():
            st.markdown(f"#### {nombre}")
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric("Cuotapartes", f"{info['cuotapartes']:,.4f}")
            with col_b:
                st.metric("Valor actual (ARS)", f"${info['valor_actual']:,.2f}")
                if tipo_cambio:
                    valor_usd_cliente = info["valor_actual"] / tipo_cambio
                    st.caption(f"Equivalente: US$ {valor_usd_cliente:,.2f}")
            with col_c:
                st.metric("Participación", f"{info['porcentaje']:.2f}%")
    else:
        st.info("No hay clientes disponibles para este usuario.")

with tab_clientes:
    st.subheader("Clientes habilitados")
    if patrimonio_clientes:
        df_clientes = pd.DataFrame(
            [
                {
                    "Cliente": nombre,
                    "Cuotapartes": datos["cuotapartes"],
                    "Valor actual": datos["valor_actual"],
                    "Participación (%)": datos["porcentaje"],
                }
                for nombre, datos in patrimonio_clientes.items()
            ]
        )
        if tipo_cambio:
            df_clientes["Valor actual (USD)"] = (
                df_clientes["Valor actual"] / tipo_cambio
            )
        df_clientes = df_clientes.sort_values("Valor actual", ascending=False)
        columnas = ["Cliente", "Cuotapartes", "Valor actual"]
        if "Valor actual (USD)" in df_clientes.columns:
            columnas.append("Valor actual (USD)")
        columnas.append("Participación (%)")
        df_clientes = df_clientes[columnas]
        formato_clientes = {
            "Cuotapartes": "{:.4f}",
            "Valor actual": "${:,.2f}",
            "Participación (%)": "{:.2f}",
        }
        if "Valor actual (USD)" in df_clientes.columns:
            formato_clientes["Valor actual (USD)"] = "US$ {:,.2f}"
        st.dataframe(
            df_clientes.style.format(formato_clientes),
            use_container_width=True,
        )
    else:
        st.info("No hay clientes asociados a tu usuario.")

with tab_graficos:
    st.subheader("Visualizaciones")

    df_clientes_plot = pd.DataFrame(
        [
            {"Cliente": nombre, "Valor actual": datos["valor_actual"]}
            for nombre, datos in patrimonio_clientes.items()
        ]
    )

    if not df_clientes_plot.empty:
        fig_pie = px.pie(
            df_clientes_plot,
            names="Cliente",
            values="Valor actual",
            title="Distribución por cliente",
        )
        fig_pie.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("No hay datos suficientes para generar gráficos de clientes.")

    df_transacciones = pd.DataFrame(transacciones_filtradas)
    if not df_transacciones.empty:
        df_transacciones["fecha"] = pd.to_datetime(df_transacciones["fecha"], errors="coerce")
        df_transacciones = df_transacciones.dropna(subset=["fecha"]).sort_values("fecha")
        fig_mov = px.bar(
            df_transacciones,
            x="fecha",
            y="monto",
            color="tipo",
            title="Movimientos registrados",
            labels={"monto": "Monto", "fecha": "Fecha", "tipo": "Tipo"},
        )
        fig_mov.update_layout(margin=dict(l=10, r=10, t=50, b=10))
        st.plotly_chart(fig_mov, use_container_width=True)
    else:
        st.info("No se registran transacciones para este usuario.")

with tab_historial:
    st.subheader("Historial de movimientos")
    df_historial = pd.DataFrame(transacciones_filtradas)
    if not df_historial.empty:
        df_historial["fecha"] = pd.to_datetime(df_historial["fecha"], errors="coerce")
        df_historial = df_historial.dropna(subset=["fecha"]).sort_values("fecha", ascending=False)
        df_historial["monto"] = df_historial["monto"].map(lambda x: f"${x:,.2f}")
        df_historial["cuotapartes"] = df_historial["cuotapartes"].map(lambda x: f"{x:,.4f}")
        df_historial["valor_cuotaparte"] = df_historial["valor_cuotaparte"].map(
            lambda x: f"${x:,.2f}"
        )
        df_historial.rename(columns={"fecha": "Fecha"}, inplace=True)
        st.dataframe(df_historial, use_container_width=True)
    else:
        st.info("No hay movimientos cargados para los clientes visibles.")

with tab_composicion:
    st.subheader("Composición del fondo")
    composicion_detallada = fondo.get_composicion_detallada()
    if composicion_detallada:
        df_composicion = pd.DataFrame(composicion_detallada)
        df_composicion = df_composicion.sort_values("Porcentaje", ascending=False)

        def formatear_monto_moneda(fila: pd.Series) -> str:
            valor = fila.get("Monto_moneda")
            if pd.isna(valor) or valor is None:
                return "—"
            simbolo = "US$" if fila.get("Moneda") == "USD" else "$"
            return f"{simbolo} {valor:,.2f}"

        df_composicion["Monto en moneda"] = df_composicion.apply(
            formatear_monto_moneda, axis=1
        )
        df_composicion["Monto (ARS)"] = df_composicion["Monto_ARS"]
        df_composicion["Participación (%)"] = df_composicion["Porcentaje"]

        columnas_mostrar = [
            "Instrumento",
            "Moneda",
            "Monto en moneda",
            "Monto (ARS)",
            "Participación (%)",
        ]
        st.dataframe(
            df_composicion[columnas_mostrar].style.format(
                {"Monto (ARS)": "${:,.2f}", "Participación (%)": "{:.2f}%"}
            ),
            use_container_width=True,
        )

        if tipo_cambio == 0 and (df_composicion["Moneda"] == "USD").any():
            st.warning(
                "Carga un tipo de cambio para valorizar correctamente las posiciones en USD."
            )

        fig_comp = px.pie(
            df_composicion,
            names="Instrumento",
            values="Monto_ARS",
            title="Participación por instrumento",
        )
        fig_comp.update_layout(margin=dict(l=10, r=10, t=50, b=10))
        st.plotly_chart(fig_comp, use_container_width=True)
    else:
        st.info("Todavía no se cargó la composición del fondo.")

    distribucion = fondo.datos.get("distribucion_activos", {})
    if distribucion:
        st.subheader("Distribución de activos")
        df_distribucion = pd.DataFrame(
            [
                {"Activo": activo, "Porcentaje": valor}
                for activo, valor in distribucion.items()
            ]
        )
        fig_dist = px.bar(
            df_distribucion,
            x="Activo",
            y="Porcentaje",
            title="Distribución por tipo de activo",
            labels={"Porcentaje": "%"},
        )
        fig_dist.update_layout(margin=dict(l=10, r=10, t=50, b=10))
        st.plotly_chart(fig_dist, use_container_width=True)
    else:
        st.caption("Carga la distribución de activos desde la consola para verla aquí.")

st.markdown("---")
st.caption(
    "📄 Panel en modo consulta. Para actualizar los datos utiliza el script `admin_console.py`."
)
