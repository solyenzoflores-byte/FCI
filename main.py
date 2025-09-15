import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import json
import os
from typing import Dict, List
import numpy as np
from PIL import Image
import base64
import hashlib

# Configuración de la página
st.set_page_config(
    page_title="Dashboard Fondo Común de Inversión",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CONFIGURACIÓN DE SEGURIDAD
# Opción 1: Usuario y contraseña (cambiar estos valores)
ADMIN_USER = "Enzo"  # Cambiar por tu usuario
ADMIN_PASSWORD = "Enzo123"  # Cambiar por tu contraseña

# Opción 2: Solo contraseña maestra
MASTER_PASSWORD = "Godeto"  # Cambiar por tu contraseña maestra

# Función de autenticación
def verificar_autenticacion():
    """Verifica si el usuario está autenticado"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        st.markdown("""
        <div style="background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); padding: 2rem; border-radius: 10px; color: white; text-align: center; margin-bottom: 2rem;">
            <h1>🔒 Acceso Restringido</h1>
            <p>Esta es una vista de solo lectura. Ingresa la contraseña para administrar.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Formulario de login
        with st.form("login_form"):
            st.subheader("🔑 Autenticación de Administrador")
            
            # Opción 1: Usuario y contraseña
            usuario = st.text_input("Usuario:", placeholder="Ingresa tu usuario")
            password = st.text_input("Contraseña:", type="password", placeholder="Ingresa tu contraseña")
            
            # Opción 2: Solo contraseña maestra (comentar la línea anterior y descomentar esta)
            # password = st.text_input("Contraseña Maestra:", type="password", placeholder="Ingresa la contraseña maestra")
            
            submitted = st.form_submit_button("🚀 Ingresar")
            
            if submitted:
                # Verificación con usuario y contraseña
                if usuario == ADMIN_USER and password == ADMIN_PASSWORD:
                    st.session_state.authenticated = True
                    st.success("✅ Acceso autorizado")
                    st.rerun()
                
                # Verificación solo con contraseña maestra (comentar el bloque anterior y descomentar este)
                # if password == MASTER_PASSWORD:
                #     st.session_state.authenticated = True
                #     st.success("✅ Acceso autorizado")
                #     st.rerun()
                else:
                    st.error("❌ Credenciales incorrectas")
        
        return False
    return True

# Función para mostrar el botón de cerrar sesión
def mostrar_logout():
    """Muestra el botón para cerrar sesión"""
    if st.session_state.get('authenticated', False):
        with st.sidebar:
            st.markdown("---")
            if st.button("🚪 Cerrar Sesión", type="secondary"):
                st.session_state.authenticated = False
                st.rerun()

# Función para cargar logo
def cargar_logo():
    """Carga el logo si existe"""
    logo_path = "Andes.png"  # Coloca tu logo con este nombre
    if os.path.exists(logo_path):
        try:
            logo = Image.open(logo_path)
            return logo
        except:
            return None
    return None

# Estilos CSS personalizados
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        border-left: 4px solid #667eea;
    }
    .rendimiento-positivo {
        color: #28a745;
        font-weight: bold;
        font-size: 1.2em;
    }
    .rendimiento-negativo {
        color: #dc3545;
        font-weight: bold;
        font-size: 1.2em;
    }
    .logo-container {
        display: flex;
        justify-content: center;
        margin-bottom: 1rem;
    }
    .stAlert {
        border-radius: 10px;
    }
    .readonly-mode {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 5px;
        padding: 10px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

class FondoInversion:
    def __init__(self):
        self.archivo_datos = 'fondo_datos.json'
        self.datos = self.cargar_datos()
    
    def cargar_datos(self):
        """Carga los datos desde el archivo JSON o crea estructura inicial"""
        if os.path.exists(self.archivo_datos):
            try:
                with open(self.archivo_datos, 'r', encoding='utf-8') as f:
                    datos = json.load(f)
                
                # Asegurar que existen todas las claves necesarias (migración de datos)
                estructura_completa = self.estructura_inicial()
                for clave, valor_default in estructura_completa.items():
                    if clave not in datos:
                        datos[clave] = valor_default
                
                return datos
            except:
                return self.estructura_inicial()
        else:
            return self.estructura_inicial()
    
    def estructura_inicial(self):
        """Estructura inicial de datos"""
        return {
            'clientes': {},
            'transacciones': [],
            'balance_diario': [],
            'valor_cuotaparte': 1000.0,  # Valor inicial en pesos
            'total_cuotapartes': 0,
            'composicion_fondo': {},  # Cambio: ahora guarda montos y porcentajes
            'distribucion_activos': {}  # Nuevo: distribución de activos
        }
    
    def guardar_datos(self):
        """Guarda los datos en el archivo JSON"""
        with open(self.archivo_datos, 'w', encoding='utf-8') as f:
            json.dump(self.datos, f, indent=2, ensure_ascii=False)
    
    def agregar_cliente(self, nombre: str, saldo_inicial: float = 0):
        """Agrega un nuevo cliente al fondo"""
        if nombre not in self.datos['clientes']:
            cuotapartes = 0
            if saldo_inicial > 0 and self.datos['valor_cuotaparte'] > 0:
                cuotapartes = saldo_inicial / self.datos['valor_cuotaparte']
                self.datos['total_cuotapartes'] += cuotapartes
                
                # Registrar transacción inicial
                transaccion = {
                    'fecha': datetime.now().isoformat(),
                    'cliente': nombre,
                    'tipo': 'suscripcion',
                    'monto': saldo_inicial,
                    'cuotapartes': cuotapartes,
                    'valor_cuotaparte': self.datos['valor_cuotaparte']
                }
                self.datos['transacciones'].append(transaccion)
            
            self.datos['clientes'][nombre] = {
                'cuotapartes': cuotapartes,
                'fecha_ingreso': datetime.now().isoformat()
            }
            return True
        return False
    
    def suscripcion(self, cliente: str, monto: float):
        """Registra una suscripción (aporte) de un cliente"""
        if cliente in self.datos['clientes'] and monto > 0:
            cuotapartes_nuevas = monto / self.datos['valor_cuotaparte']
            self.datos['clientes'][cliente]['cuotapartes'] += cuotapartes_nuevas
            self.datos['total_cuotapartes'] += cuotapartes_nuevas
            
            transaccion = {
                'fecha': datetime.now().isoformat(),
                'cliente': cliente,
                'tipo': 'suscripcion',
                'monto': monto,
                'cuotapartes': cuotapartes_nuevas,
                'valor_cuotaparte': self.datos['valor_cuotaparte']
            }
            self.datos['transacciones'].append(transaccion)
            return True
        return False
    
    def rescate(self, cliente: str, monto: float):
        """Registra un rescate (retiro) de un cliente"""
        if cliente in self.datos['clientes']:
            cuotapartes_a_retirar = monto / self.datos['valor_cuotaparte']
            
            if self.datos['clientes'][cliente]['cuotapartes'] >= cuotapartes_a_retirar:
                self.datos['clientes'][cliente]['cuotapartes'] -= cuotapartes_a_retirar
                self.datos['total_cuotapartes'] -= cuotapartes_a_retirar
                
                transaccion = {
                    'fecha': datetime.now().isoformat(),
                    'cliente': cliente,
                    'tipo': 'rescate',
                    'monto': -monto,
                    'cuotapartes': -cuotapartes_a_retirar,
                    'valor_cuotaparte': self.datos['valor_cuotaparte']
                }
                self.datos['transacciones'].append(transaccion)
                return True
        return False
    
    def actualizar_balance_diario(self, nuevo_balance: float):
        """Actualiza el balance total del fondo y recalcula valor de cuotaparte"""
        fecha_hoy = date.today().isoformat()
        
        # Remover entrada del mismo día si existe
        self.datos['balance_diario'] = [
            b for b in self.datos['balance_diario'] 
            if b['fecha'] != fecha_hoy
        ]
        
        # Agregar nuevo balance
        balance_entry = {
            'fecha': fecha_hoy,
            'balance': nuevo_balance
        }
        self.datos['balance_diario'].append(balance_entry)
        
        # Recalcular valor de cuotaparte
        if self.datos['total_cuotapartes'] > 0:
            self.datos['valor_cuotaparte'] = nuevo_balance / self.datos['total_cuotapartes']
        
        # Mantener solo los últimos 365 días
        self.datos['balance_diario'] = self.datos['balance_diario'][-365:]
    
    def actualizar_composicion_fondo(self, composicion_montos: dict):
        """Actualiza la composición del fondo con montos y calcula porcentajes"""
        total_monto = sum(composicion_montos.values())
        
        composicion_completa = {}
        for instrumento, monto in composicion_montos.items():
            porcentaje = (monto / total_monto * 100) if total_monto > 0 else 0
            composicion_completa[instrumento] = {
                'monto': monto,
                'porcentaje': porcentaje
            }
        
        self.datos['composicion_fondo'] = composicion_completa
    
    def get_composicion_para_graficos(self):
        """Retorna la composición en formato para gráficos (solo porcentajes)"""
        if not self.datos['composicion_fondo']:
            return {}
        
        return {instrumento: datos['porcentaje'] 
                for instrumento, datos in self.datos['composicion_fondo'].items()}
    
    def get_total_monto_composicion(self):
        """Calcula el monto total de la composición"""
        if not self.datos['composicion_fondo']:
            return 0
        
        return sum(datos['monto'] for datos in self.datos['composicion_fondo'].values())
    
    def actualizar_distribucion_activos(self, distribucion: dict):
        """Actualiza la distribución de activos"""
        self.datos['distribucion_activos'] = distribucion
    
    def calcular_rendimiento_mensualizado(self):
        """Calcula el rendimiento mensualizado del fondo"""
        if len(self.datos['balance_diario']) < 2:
            return 0, 0
        
        df_balance = pd.DataFrame(self.datos['balance_diario'])
        df_balance['fecha'] = pd.to_datetime(df_balance['fecha'])
        df_balance = df_balance.sort_values('fecha')
        
        # Rendimiento del período completo
        balance_inicial = df_balance['balance'].iloc[0]
        balance_actual = df_balance['balance'].iloc[-1]
        
        if balance_inicial == 0:
            return 0, 0
        
        # Calcular días transcurridos
        fecha_inicial = df_balance['fecha'].iloc[0]
        fecha_actual = df_balance['fecha'].iloc[-1]
        dias_transcurridos = (fecha_actual - fecha_inicial).days
        
        if dias_transcurridos == 0:
            return 0, 0
        
        # Rendimiento total
        rendimiento_total = ((balance_actual - balance_inicial) / balance_inicial) * 100
        
        # Rendimiento mensualizado (30 días)
        if dias_transcurridos >= 30:
            rendimiento_mensual = (pow(balance_actual / balance_inicial, 30 / dias_transcurridos) - 1) * 100
        else:
            # Si no hay 30 días, extrapolamos
            rendimiento_mensual = (rendimiento_total / dias_transcurridos) * 30
        
        return rendimiento_total, rendimiento_mensual
    
    def get_patrimonio_clientes(self):
        """Obtiene el patrimonio actual de cada cliente"""
        patrimonio = {}
        for cliente, datos in self.datos['clientes'].items():
            valor_actual = datos['cuotapartes'] * self.datos['valor_cuotaparte']
            patrimonio[cliente] = {
                'cuotapartes': datos['cuotapartes'],
                'valor_actual': valor_actual,
                'porcentaje': (datos['cuotapartes'] / self.datos['total_cuotapartes'] * 100) if self.datos['total_cuotapartes'] > 0 else 0
            }
        return patrimonio
    
    def get_balance_total(self):
        """Obtiene el balance total actual"""
        if self.datos['balance_diario']:
            return self.datos['balance_diario'][-1]['balance']
        return 0

# Inicializar el fondo
if 'fondo' not in st.session_state:
    st.session_state.fondo = FondoInversion()

fondo = st.session_state.fondo

# VERIFICAR AUTENTICACIÓN
is_admin = verificar_autenticacion()

# Si no está autenticado, mostrar solo vista de lectura
if not is_admin:
    # Vista de solo lectura - solo mostrar datos
    logo = cargar_logo()
    
    st.markdown("""
    <div class="main-header">
    """, unsafe_allow_html=True)
    
    if logo:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image(logo, width=150)
    
    st.markdown("""
        <h1>💰 Dashboard Fondo Común de Inversión</h1>
        <p>📊 Vista de Solo Lectura</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Métricas principales (solo lectura)
    balance_total = fondo.get_balance_total()
    patrimonio_clientes = fondo.get_patrimonio_clientes()
    total_clientes = len(fondo.datos['clientes'])
    rendimiento_total, rendimiento_mensual = fondo.calcular_rendimiento_mensualizado()
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            label="Balance Total",
            value=f"${balance_total:,.2f}",
            delta=None
        )
    
    with col2:
        st.metric(
            label="Total Clientes",
            value=str(total_clientes),
            delta=None
        )
    
    with col3:
        st.metric(
            label="Total Cuotapartes",
            value=f"{fondo.datos['total_cuotapartes']:,.2f}",
            delta=None
        )
    
    with col4:
        st.metric(
            label="Valor Cuotaparte",
            value=f"${fondo.datos['valor_cuotaparte']:,.2f}",
            delta=None
        )
    
    with col5:
        # Rendimiento mensualizado con color condicional
        color_class = "rendimiento-positivo" if rendimiento_mensual >= 0 else "rendimiento-negativo"
        st.markdown(f"""
        <div style="text-align: center; padding: 10px; background: white; border-radius: 10px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
            <div style="font-size: 0.8em; color: #666; margin-bottom: 5px;">Rendimiento Mensual</div>
            <div class="{color_class}">{rendimiento_mensual:+.2f}%</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Tabs de solo lectura
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📈 Resumen", "👥 Clientes", "📊 Gráficos", "🔄 Historial", "📋 Composición"])
    
    # [El resto del código de las tabs se mantiene igual, pero sin controles de edición]
    # ... (código de las tabs de visualización)
    
    st.stop()  # Detener ejecución aquí si no está autenticado

# A partir de aquí, solo se ejecuta si está autenticado
mostrar_logout()

# Header principal con logo
logo = cargar_logo()

st.markdown("""
<div class="main-header">
""", unsafe_allow_html=True)

if logo:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image(logo, width=150)

st.markdown("""
    <h1>💰 Dashboard Fondo Común de Inversión</h1>
    <p>🔓 Modo Administrador - Control Total</p>
</div>
""", unsafe_allow_html=True)

# Métricas principales
balance_total = fondo.get_balance_total()
patrimonio_clientes = fondo.get_patrimonio_clientes()
total_clientes = len(fondo.datos['clientes'])
rendimiento_total, rendimiento_mensual = fondo.calcular_rendimiento_mensualizado()

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        label="Balance Total",
        value=f"${balance_total:,.2f}",
        delta=None
    )

with col2:
    st.metric(
        label="Total Clientes",
        value=str(total_clientes),
        delta=None
    )

with col3:
    st.metric(
        label="Total Cuotapartes",
        value=f"{fondo.datos['total_cuotapartes']:,.2f}",
        delta=None
    )

with col4:
    st.metric(
        label="Valor Cuotaparte",
        value=f"${fondo.datos['valor_cuotaparte']:,.2f}",
        delta=None
    )

with col5:
    # Rendimiento mensualizado con color condicional
    color_class = "rendimiento-positivo" if rendimiento_mensual >= 0 else "rendimiento-negativo"
    st.markdown(f"""
    <div style="text-align: center; padding: 10px; background: white; border-radius: 10px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
        <div style="font-size: 0.8em; color: #666; margin-bottom: 5px;">Rendimiento Mensual</div>
        <div class="{color_class}">{rendimiento_mensual:+.2f}%</div>
    </div>
    """, unsafe_allow_html=True)

# Sidebar para operaciones (solo para administradores)
st.sidebar.header("⚙️ Operaciones de Administrador")
st.sidebar.success("✅ Modo Administrador Activado")

# Actualizar balance diario
st.sidebar.subheader("📊 Balance Diario")
nuevo_balance = st.sidebar.number_input(
    "Nuevo balance total:",
    min_value=0.0,
    value=float(balance_total) if balance_total > 0 else 0.0,
    format="%.2f"
)

if st.sidebar.button("🔄 Actualizar Balance", type="primary"):
    fondo.actualizar_balance_diario(nuevo_balance)
    fondo.guardar_datos()
    st.sidebar.success("Balance actualizado correctamente")
    st.rerun()

st.sidebar.divider()

# [Resto del código del sidebar para administradores...]
# Composición del fondo - MODIFICADO PARA USAR MONTOS
st.sidebar.subheader("📈 Composición del Fondo")
with st.sidebar.expander("Actualizar Composición"):
    st.write("Ingresa los instrumentos del fondo y sus montos:")
    
    # Número de instrumentos
    num_instrumentos = st.number_input("Número de instrumentos:", min_value=1, max_value=20, value=5)
    
    composicion_nueva = {}
    total_monto = 0
    
    for i in range(num_instrumentos):
        col1, col2 = st.columns(2)
        with col1:
            instrumento = st.text_input(f"Instrumento {i+1}:", key=f"instr_{i}")
        with col2:
            monto = st.number_input(f"Monto {i+1}:", min_value=0.0, value=0.0, format="%.2f", key=f"monto_{i}")
        
        if instrumento and monto > 0:
            composicion_nueva[instrumento] = monto
            total_monto += monto
    
    # Mostrar total y porcentajes calculados
    st.write(f"**Total:** ${total_monto:,.2f}")
    
    if composicion_nueva and total_monto > 0:
        st.write("**Porcentajes calculados:**")
        for instrumento, monto in composicion_nueva.items():
            porcentaje = (monto / total_monto * 100)
            st.write(f"• {instrumento}: ${monto:,.2f} ({porcentaje:.1f}%)")
    
    if st.button("💾 Guardar Composición"):
        if composicion_nueva:
            fondo.actualizar_composicion_fondo(composicion_nueva)
            fondo.guardar_datos()
            st.success("Composición actualizada")
            st.rerun()
        else:
            st.error("Ingrese al menos un instrumento con monto")

# [Resto del código para las operaciones de administrador...]

# Tabs completas con funcionalidad de administrador
# [Aquí va todo el código de las tabs que ya tenías]

# Footer
st.markdown("---")
st.markdown("**🔐 Modo Administrador Activo - Control Total Habilitado**")
st.markdown("**💡 Instrucciones de uso:**")
st.markdown("""
1. **Balance Diario**: Actualiza el balance total del fondo desde el sidebar
2. **Nuevos Clientes**: Agrega clientes con saldo inicial opcional
3. **Suscripciones**: Registra aportes de los clientes
4. **Rescates**: Registra retiros (verifica fondos suficientes)
5. **Composición**: Define los instrumentos que componen el fondo **ingresando montos** (los porcentajes se calculan automáticamente)
6. **Distribución**: Establece la distribución por tipo de activo
7. **Logo**: Coloca tu logo como 'logo_empresa.png' en la carpeta del proyecto
8. **Análisis**: Revisa gráficos, rendimientos y evolución en las diferentes pestañas
""")

st.info("💾 **Todos los datos se guardan automáticamente en 'fondo_datos.json'**")