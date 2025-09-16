#!/usr/bin/env python3
"""
Script de administración del Fondo de Inversión
Permite actualizar datos desde la consola sin interfaz web
"""

import json
import os
from datetime import datetime, date
from typing import Dict, List, Optional
import argparse
import getpass

from security import generate_salt, hash_password

class FondoAdminConsole:
    def __init__(self, archivo_datos='fondo_datos.json'):
        if not os.path.isabs(archivo_datos):
            base_dir = os.path.dirname(os.path.abspath(__file__))
            archivo_datos = os.path.join(base_dir, archivo_datos)
        self.archivo_datos = archivo_datos
        self.datos = self.cargar_datos()
    
    def cargar_datos(self):
        """Carga los datos desde el archivo JSON"""
        if os.path.exists(self.archivo_datos):
            try:
                with open(self.archivo_datos, 'r', encoding='utf-8') as f:
                    datos = json.load(f)
                estructura = self.estructura_inicial()
                for clave, valor_default in estructura.items():
                    if clave not in datos:
                        datos[clave] = valor_default
                return datos
            except Exception as e:
                print(f"❌ Error cargando datos: {e}")
                return self.estructura_inicial()
        else:
            print("⚠️  Archivo de datos no encontrado, creando estructura inicial")
            return self.estructura_inicial()
    
    def estructura_inicial(self):
        """Estructura inicial de datos"""
        return {
            'clientes': {},
            'transacciones': [],
            'balance_diario': [],
            'valor_cuotaparte': 1000.0,
            'total_cuotapartes': 0,
            'composicion_fondo': {},
            'distribucion_activos': {},
            'usuarios': {},
            'tipo_cambio': 0.0
        }
    
    def guardar_datos(self):
        """Guarda los datos en el archivo JSON"""
        try:
            with open(self.archivo_datos, 'w', encoding='utf-8') as f:
                json.dump(self.datos, f, indent=2, ensure_ascii=False)
            print("✅ Datos guardados correctamente")
            return True
        except Exception as e:
            print(f"❌ Error guardando datos: {e}")
            return False
    
    def mostrar_estado(self):
        """Muestra el estado actual del fondo"""
        print("\n" + "="*50)
        print("📊 ESTADO ACTUAL DEL FONDO")
        print("="*50)
        
        balance_total = self.get_balance_total()
        print(f"💰 Balance Total: ${balance_total:,.2f}")
        print(f"👥 Total Clientes: {len(self.datos['clientes'])}")
        print(f"📋 Total Cuotapartes: {self.datos['total_cuotapartes']:,.2f}")
        print(f"💵 Valor Cuotaparte: ${self.datos['valor_cuotaparte']:,.2f}")
        if self.datos.get('tipo_cambio', 0):
            print(f"💱 Tipo de cambio USD/ARS: ${self.datos['tipo_cambio']:,.2f}")
        else:
            print("💱 Tipo de cambio USD/ARS: no definido")
        
        if self.datos['clientes']:
            print(f"\n👥 CLIENTES:")
            for nombre, datos in self.datos['clientes'].items():
                valor_actual = datos['cuotapartes'] * self.datos['valor_cuotaparte']
                print(f"  • {nombre}: {datos['cuotapartes']:,.2f} cuotapartes (${valor_actual:,.2f})")
        
        if self.datos['composicion_fondo']:
            print(f"\n📈 COMPOSICIÓN DEL FONDO:")
            for instrumento, datos in self.datos['composicion_fondo'].items():
                print(f"  • {instrumento}: ${datos['monto']:,.2f} ({datos['porcentaje']:.1f}%)")
        
        print("="*50)
    
    def get_balance_total(self):
        """Obtiene el balance total actual"""
        if self.datos['balance_diario']:
            return self.datos['balance_diario'][-1]['balance']
        return 0
    
    def actualizar_balance(self, nuevo_balance: float):
        """Actualiza el balance diario"""
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
        
        print(f"✅ Balance actualizado a ${nuevo_balance:,.2f}")
        print(f"📊 Nuevo valor cuotaparte: ${self.datos['valor_cuotaparte']:,.2f}")
    
    def agregar_cliente(self, nombre: str, saldo_inicial: float = 0):
        """Agrega un nuevo cliente"""
        if nombre in self.datos['clientes']:
            print(f"❌ El cliente {nombre} ya existe")
            return False
        
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
        
        print(f"✅ Cliente {nombre} agregado con {cuotapartes:.2f} cuotapartes")
        return True
    
    def suscripcion(self, cliente: str, monto: float):
        """Registra una suscripción"""
        if cliente not in self.datos['clientes']:
            print(f"❌ Cliente {cliente} no existe")
            return False
        
        if monto <= 0:
            print("❌ El monto debe ser mayor a 0")
            return False
        
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
        
        print(f"✅ Suscripción registrada: {cliente} - ${monto:,.2f} ({cuotapartes_nuevas:.4f} cuotapartes)")
        return True
    
    def rescate(self, cliente: str, monto: float):
        """Registra un rescate"""
        if cliente not in self.datos['clientes']:
            print(f"❌ Cliente {cliente} no existe")
            return False
        
        if monto <= 0:
            print("❌ El monto debe ser mayor a 0")
            return False
        
        cuotapartes_a_retirar = monto / self.datos['valor_cuotaparte']
        
        if self.datos['clientes'][cliente]['cuotapartes'] < cuotapartes_a_retirar:
            print(f"❌ Fondos insuficientes. Cliente tiene {self.datos['clientes'][cliente]['cuotapartes']:.4f} cuotapartes")
            return False
        
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
        
        print(f"✅ Rescate registrado: {cliente} - ${monto:,.2f} ({cuotapartes_a_retirar:.4f} cuotapartes)")
        return True

    # -------------------------------------------------------------
    # Gestión de usuarios para acceso web
    # -------------------------------------------------------------

    def crear_usuario(self, username: str, password: str, rol: str = 'cliente',
                      clientes: Optional[List[str]] = None) -> bool:
        """Crea un nuevo usuario de acceso web."""
        clientes = clientes or []

        rol = rol.lower()
        if rol not in {'admin', 'cliente'}:
            print("❌ Rol inválido. Use 'admin' o 'cliente'")
            return False

        if username in self.datos['usuarios']:
            print(f"❌ El usuario {username} ya existe")
            return False

        if rol != 'admin':
            if not clientes:
                print("❌ Debe asociar al menos un cliente al usuario")
                return False
            clientes_validos = [c for c in clientes if c in self.datos['clientes']]
            if len(clientes_validos) != len(clientes):
                print("❌ Algunos clientes no existen en el fondo")
                print(f"   Clientes válidos: {', '.join(self.datos['clientes'].keys())}")
                return False
        else:
            clientes_validos = []

        salt = generate_salt()
        password_hash = hash_password(password, salt)

        self.datos['usuarios'][username] = {
            'rol': rol,
            'salt': salt,
            'password_hash': password_hash,
            'clientes': clientes_validos,
        }

        print(f"✅ Usuario {username} creado correctamente")
        if rol == 'admin':
            print("   • Rol administrador (acceso a todos los clientes)")
        else:
            print(f"   • Clientes asociados: {', '.join(clientes_validos)}")
        return True

    def listar_usuarios(self):
        """Muestra la lista de usuarios configurados"""
        usuarios = self.datos.get('usuarios', {})
        if not usuarios:
            print("⚠️  No hay usuarios configurados")
            return

        print("\n👥 USUARIOS REGISTRADOS:")
        for username, info in usuarios.items():
            rol = info.get('rol', 'cliente')
            if rol == 'admin':
                print(f"  • {username} (admin)")
            else:
                clientes = info.get('clientes', [])
                clientes_txt = ', '.join(clientes) if clientes else 'Sin clientes asociados'
                print(f"  • {username} (cliente) -> {clientes_txt}")

    def actualizar_password(self, username: str, nuevo_password: str) -> bool:
        """Actualiza la contraseña de un usuario"""
        usuario = self.datos['usuarios'].get(username)
        if not usuario:
            print(f"❌ Usuario {username} no existe")
            return False

        salt = generate_salt()
        usuario['salt'] = salt
        usuario['password_hash'] = hash_password(nuevo_password, salt)
        print(f"✅ Contraseña actualizada para {username}")
        return True

    def actualizar_clientes_usuario(self, username: str, clientes: List[str]) -> bool:
        """Actualiza la lista de clientes asociados a un usuario"""
        usuario = self.datos['usuarios'].get(username)
        if not usuario:
            print(f"❌ Usuario {username} no existe")
            return False

        if usuario.get('rol') == 'admin':
            print("⚠️  El usuario es administrador y ya tiene acceso total")
            return False

        clientes_validos = [c for c in clientes if c in self.datos['clientes']]
        if len(clientes_validos) != len(clientes):
            print("❌ Algunos clientes no existen. No se realizaron cambios")
            print(f"   Clientes válidos: {', '.join(self.datos['clientes'].keys())}")
            return False

        usuario['clientes'] = clientes_validos
        print(f"✅ Clientes actualizados para {username}: {', '.join(clientes_validos)}")
        return True

    def menu_usuarios(self):
        """Menú interactivo para administrar usuarios"""
        while True:
            print("\n" + "-"*40)
            print("👤 ADMINISTRACIÓN DE USUARIOS")
            print("-"*40)
            print("1. Crear usuario")
            print("2. Listar usuarios")
            print("3. Actualizar contraseña")
            print("4. Actualizar clientes asociados")
            print("5. Volver")

            opcion = input("Seleccione una opción: ").strip()

            if opcion == '1':
                username = input("Nombre de usuario: ").strip()
                rol = input("Rol (admin/cliente) [cliente]: ").strip() or 'cliente'
                clientes = []
                if rol.lower() != 'admin':
                    if not self.datos['clientes']:
                        print("❌ No hay clientes cargados. Cree el cliente antes de asignarlo")
                        continue
                    print("Clientes disponibles:", ', '.join(self.datos['clientes'].keys()))
                    clientes_input = input("Clientes asociados (separados por coma): ").strip()
                    clientes = [c.strip() for c in clientes_input.split(',') if c.strip()]
                password = getpass.getpass("Contraseña: ")
                confirmacion = getpass.getpass("Confirmar contraseña: ")
                if password != confirmacion:
                    print("❌ Las contraseñas no coinciden")
                    continue
                if self.crear_usuario(username, password, rol, clientes):
                    self.guardar_datos()

            elif opcion == '2':
                self.listar_usuarios()

            elif opcion == '3':
                username = input("Usuario: ").strip()
                nuevo_password = getpass.getpass("Nueva contraseña: ")
                confirmacion = getpass.getpass("Confirmar contraseña: ")
                if nuevo_password != confirmacion:
                    print("❌ Las contraseñas no coinciden")
                    continue
                if self.actualizar_password(username, nuevo_password):
                    self.guardar_datos()

            elif opcion == '4':
                username = input("Usuario: ").strip()
                if username not in self.datos['usuarios']:
                    print("❌ Usuario no encontrado")
                    continue
                if self.datos['usuarios'][username].get('rol') == 'admin':
                    print("⚠️  El usuario es admin y no necesita clientes asociados")
                    continue
                if not self.datos['clientes']:
                    print("❌ No hay clientes cargados")
                    continue
                print("Clientes disponibles:", ', '.join(self.datos['clientes'].keys()))
                clientes_input = input("Clientes asociados (separados por coma): ").strip()
                clientes = [c.strip() for c in clientes_input.split(',') if c.strip()]
                if self.actualizar_clientes_usuario(username, clientes):
                    self.guardar_datos()

            elif opcion == '5':
                break
            else:
                print("❌ Opción inválida")
    
    def actualizar_composicion(self, composicion_input: str):
        """Actualiza la composición del fondo
        Formato: 'Instrumento1:monto1,Instrumento2:monto2,...'
        """
        try:
            composicion_procesada = []
            items = [item.strip() for item in composicion_input.split(',') if item.strip()]

            for item in items:
                partes = [p.strip() for p in item.split(':')]
                if len(partes) < 2:
                    print(f"❌ Formato incorrecto: {item}. Use 'Instrumento:monto[:moneda]'")
                    return False
                if len(partes) > 3:
                    print(f"❌ Formato incorrecto: {item}. Máximo tres componentes 'Instrumento:monto:moneda'")
                    return False

                instrumento = partes[0]
                monto = float(partes[1])
                moneda = partes[2].upper() if len(partes) == 3 and partes[2] else 'ARS'

                if monto <= 0:
                    continue

                if moneda not in {'ARS', 'USD'}:
                    print(f"⚠️  Moneda '{moneda}' no reconocida. Se asumirá en pesos (ARS).")
                    moneda = 'ARS'

                composicion_procesada.append((instrumento, monto, moneda))

            if not composicion_procesada:
                print("❌ No se encontraron instrumentos válidos")
                return False

            tipo_cambio = self.datos.get('tipo_cambio', 0.0) or 0.0
            composicion_completa = {}
            total_en_pesos = 0.0
            composicion_intermedia = []

            for instrumento, monto, moneda in composicion_procesada:
                if moneda == 'USD':
                    if tipo_cambio <= 0:
                        print("❌ Debe configurar el tipo de cambio (💱) antes de cargar montos en USD.")
                        return False
                    monto_en_pesos = monto * tipo_cambio
                    composicion_intermedia.append((instrumento, monto_en_pesos, moneda, monto))
                else:
                    monto_en_pesos = monto
                    composicion_intermedia.append((instrumento, monto_en_pesos, moneda, None))
                total_en_pesos += monto_en_pesos

            if total_en_pesos <= 0:
                print("❌ El total de la composición debe ser mayor a 0")
                return False

            for instrumento, monto_en_pesos, moneda, monto_moneda in composicion_intermedia:
                porcentaje = (monto_en_pesos / total_en_pesos * 100) if total_en_pesos else 0
                registro = {
                    'monto': monto_en_pesos,
                    'porcentaje': porcentaje,
                    'moneda': moneda
                }
                if moneda == 'USD' and monto_moneda is not None:
                    registro['monto_moneda'] = monto_moneda
                composicion_completa[instrumento] = registro

            self.datos['composicion_fondo'] = composicion_completa

            print("✅ Composición actualizada:")
            for instrumento, datos in composicion_completa.items():
                moneda = datos.get('moneda', 'ARS')
                porcentaje = datos.get('porcentaje', 0.0)
                monto_pesos = datos.get('monto', 0.0)
                if moneda == 'USD' and 'monto_moneda' in datos:
                    monto_moneda = datos['monto_moneda']
                    print(f"  • {instrumento}: US$ {monto_moneda:,.2f} (=${monto_pesos:,.2f}) ({porcentaje:.1f}%)")
                else:
                    print(f"  • {instrumento}: ${monto_pesos:,.2f} ({porcentaje:.1f}%)")

            return True

        except ValueError as e:
            print(f"❌ Error en formato de montos: {e}")
            return False
        except Exception as e:
            print(f"❌ Error actualizando composición: {e}")
            return False

    def actualizar_tipo_cambio(self, tipo_cambio: float):
        """Actualiza el valor del tipo de cambio USD/ARS"""
        try:
            tipo_cambio = float(tipo_cambio)
        except (TypeError, ValueError):
            print("❌ Tipo de cambio inválido")
            return False

        if tipo_cambio <= 0:
            print("❌ El tipo de cambio debe ser mayor a 0")
            return False

        self.datos['tipo_cambio'] = tipo_cambio
        print(f"✅ Tipo de cambio actualizado a ${tipo_cambio:,.2f} (ARS por USD)")
        return True

    def menu_interactivo(self):
        """Menu interactivo para operaciones"""
        while True:
            print("\n" + "="*40)
            print("🔧 ADMINISTRACIÓN DEL FONDO")
            print("="*40)
            print("1. 📊 Ver estado actual")
            print("2. 💰 Actualizar balance")
            print("3. 👤 Agregar cliente")
            print("4. ⬆️  Registrar suscripción")
            print("5. ⬇️  Registrar rescate")
            print("6. 📈 Actualizar composición")
            print("7. 👤 Administrar usuarios")
            print("8. 💱 Actualizar tipo de cambio")
            print("9. 💾 Guardar datos")
            print("10. 🚪 Salir")
            print("="*40)
            
            try:
                opcion = input("Seleccione una opción: ").strip()
                
                if opcion == '1':
                    self.mostrar_estado()
                
                elif opcion == '2':
                    balance_actual = self.get_balance_total()
                    print(f"Balance actual: ${balance_actual:,.2f}")
                    nuevo_balance = float(input("Nuevo balance: $"))
                    self.actualizar_balance(nuevo_balance)
                
                elif opcion == '3':
                    nombre = input("Nombre del cliente: ").strip()
                    saldo_str = input("Saldo inicial (0 si no tiene): $").strip()
                    saldo = float(saldo_str) if saldo_str else 0
                    self.agregar_cliente(nombre, saldo)
                
                elif opcion == '4':
                    if not self.datos['clientes']:
                        print("❌ No hay clientes registrados")
                        continue
                    print("Clientes disponibles:", ", ".join(self.datos['clientes'].keys()))
                    cliente = input("Cliente: ").strip()
                    monto = float(input("Monto de suscripción: $"))
                    self.suscripcion(cliente, monto)
                
                elif opcion == '5':
                    if not self.datos['clientes']:
                        print("❌ No hay clientes registrados")
                        continue
                    print("Clientes disponibles:", ", ".join(self.datos['clientes'].keys()))
                    cliente = input("Cliente: ").strip()
                    monto = float(input("Monto de rescate: $"))
                    self.rescate(cliente, monto)
                
                elif opcion == '6':
                    print("Formato: 'Instrumento1:monto1[:moneda1],Instrumento2:monto2[:moneda2],...'")
                    print("Ejemplo: 'Bonos:10000,Acciones:15000,USD Liquidez:10:USD'")
                    print("Si no se indica moneda se asume pesos (ARS).")
                    composicion = input("Composición: ").strip()
                    if composicion:
                        self.actualizar_composicion(composicion)

                elif opcion == '7':
                    self.menu_usuarios()

                elif opcion == '8':
                    valor = float(input("Nuevo tipo de cambio (ARS por USD): "))
                    self.actualizar_tipo_cambio(valor)

                elif opcion == '9':
                    self.guardar_datos()

                elif opcion == '10':
                    print("👋 ¡Hasta luego!")
                    break

                else:
                    print("❌ Opción inválida")
            
            except ValueError:
                print("❌ Error: Ingrese un valor numérico válido")
            except KeyboardInterrupt:
                print("\n👋 Operación cancelada")
                break
            except Exception as e:
                print(f"❌ Error inesperado: {e}")

def main():
    """Función principal con argumentos de línea de comandos"""
    parser = argparse.ArgumentParser(description='Administrador del Fondo de Inversión')
    parser.add_argument('--archivo', '-f', default='fondo_datos.json', 
                       help='Archivo de datos JSON (default: fondo_datos.json)')
    parser.add_argument('--balance', '-b', type=float,
                       help='Actualizar balance directamente')
    parser.add_argument('--cliente', '-c', 
                       help='Agregar cliente (usar con --saldo)')
    parser.add_argument('--saldo', '-s', type=float, default=0,
                       help='Saldo inicial para nuevo cliente')
    parser.add_argument('--suscripcion', nargs=2, metavar=('CLIENTE', 'MONTO'),
                       help='Registrar suscripción: --suscripcion "Juan Perez" 5000')
    parser.add_argument('--rescate', nargs=2, metavar=('CLIENTE', 'MONTO'),
                       help='Registrar rescate: --rescate "Juan Perez" 2000')
    parser.add_argument('--composicion',
                       help="Actualizar composición (formato 'Instrumento:monto[:moneda]'). Ej: --composicion \"Bonos:10000,USD Liquidez:10:USD\"")
    parser.add_argument('--tipo-cambio', type=float,
                       help='Actualizar tipo de cambio (ARS por USD)')
    parser.add_argument('--estado', action='store_true',
                       help='Mostrar estado actual del fondo')
    parser.add_argument('--crear-usuario', metavar='USUARIO',
                        help='Crear usuario de acceso web')
    parser.add_argument('--rol', choices=['admin', 'cliente'], default='cliente',
                        help='Rol del usuario creado (default: cliente)')
    parser.add_argument('--clientes-usuario',
                        help='Clientes asociados al usuario (separados por comas)')
    parser.add_argument('--password',
                        help='Contraseña para crear o actualizar usuarios (si no se proporciona se solicitará)')
    parser.add_argument('--reset-password', metavar='USUARIO',
                        help='Restablecer la contraseña de un usuario existente')
    parser.add_argument('--listar-usuarios', action='store_true',
                        help='Mostrar usuarios registrados')
    
    args = parser.parse_args()
    
    # Inicializar administrador
    admin = FondoAdminConsole(args.archivo)
    
    # Procesar argumentos
    cambios_realizados = False
    
    if args.balance is not None:
        admin.actualizar_balance(args.balance)
        cambios_realizados = True
    
    if args.cliente:
        admin.agregar_cliente(args.cliente, args.saldo)
        cambios_realizados = True
    
    if args.suscripcion:
        cliente, monto = args.suscripcion
        admin.suscripcion(cliente, float(monto))
        cambios_realizados = True
    
    if args.rescate:
        cliente, monto = args.rescate
        admin.rescate(cliente, float(monto))
        cambios_realizados = True

    if args.composicion:
        admin.actualizar_composicion(args.composicion)
        cambios_realizados = True

    if args.tipo_cambio is not None:
        if admin.actualizar_tipo_cambio(args.tipo_cambio):
            cambios_realizados = True

    if args.crear_usuario:
        password = args.password
        if not password:
            password = getpass.getpass("Contraseña para el nuevo usuario: ")
        if not password:
            print("❌ Debe proporcionar una contraseña")
        else:
            clientes_usuario = []
            if args.rol != 'admin':
                if args.clientes_usuario:
                    clientes_usuario = [c.strip() for c in args.clientes_usuario.split(',') if c.strip()]
                if not clientes_usuario:
                    print("❌ Debe indicar clientes asociados con --clientes-usuario")
                else:
                    if admin.crear_usuario(args.crear_usuario, password, args.rol, clientes_usuario):
                        cambios_realizados = True
            else:
                if admin.crear_usuario(args.crear_usuario, password, args.rol, []):
                    cambios_realizados = True

    if args.reset_password:
        nuevo_password = args.password
        if not nuevo_password:
            nuevo_password = getpass.getpass("Nueva contraseña: ")
        if not nuevo_password:
            print("❌ Debe proporcionar una contraseña para actualizar")
        else:
            if admin.actualizar_password(args.reset_password, nuevo_password):
                cambios_realizados = True

    if args.listar_usuarios:
        admin.listar_usuarios()

    if cambios_realizados:
        admin.guardar_datos()

    if args.estado or not any(vars(args).values()):
        admin.mostrar_estado()
    
    # Si no se pasaron argumentos específicos, abrir menú interactivo
    if not any([
        args.balance is not None,
        args.cliente,
        args.suscripcion,
        args.rescate,
        args.composicion,
        args.tipo_cambio is not None,
        args.estado,
        args.crear_usuario,
        args.reset_password,
        args.listar_usuarios,
    ]):
        admin.menu_interactivo()

if __name__ == "__main__":
    main()