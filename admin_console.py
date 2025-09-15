#!/usr/bin/env python3
"""
Script de administración del Fondo de Inversión
Permite actualizar datos desde la consola sin interfaz web
"""

import json
import os
from datetime import datetime, date
from typing import Dict, List
import argparse

class FondoAdminConsole:
    def __init__(self, archivo_datos='fondo_datos.json'):
        self.archivo_datos = archivo_datos
        self.datos = self.cargar_datos()
    
    def cargar_datos(self):
        """Carga los datos desde el archivo JSON"""
        if os.path.exists(self.archivo_datos):
            try:
                with open(self.archivo_datos, 'r', encoding='utf-8') as f:
                    datos = json.load(f)
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
            'distribucion_activos': {}
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
    
    def actualizar_composicion(self, composicion_input: str):
        """Actualiza la composición del fondo
        Formato: 'Instrumento1:monto1,Instrumento2:monto2,...'
        """
        try:
            composicion_nueva = {}
            items = composicion_input.split(',')
            
            for item in items:
                if ':' not in item:
                    print(f"❌ Formato incorrecto: {item}. Use 'Instrumento:monto'")
                    return False
                
                instrumento, monto_str = item.split(':', 1)
                instrumento = instrumento.strip()
                monto = float(monto_str.strip())
                
                if monto > 0:
                    composicion_nueva[instrumento] = monto
            
            if not composicion_nueva:
                print("❌ No se encontraron instrumentos válidos")
                return False
            
            # Calcular porcentajes
            total_monto = sum(composicion_nueva.values())
            composicion_completa = {}
            
            for instrumento, monto in composicion_nueva.items():
                porcentaje = (monto / total_monto * 100) if total_monto > 0 else 0
                composicion_completa[instrumento] = {
                    'monto': monto,
                    'porcentaje': porcentaje
                }
            
            self.datos['composicion_fondo'] = composicion_completa
            
            print("✅ Composición actualizada:")
            for instrumento, datos in composicion_completa.items():
                print(f"  • {instrumento}: ${datos['monto']:,.2f} ({datos['porcentaje']:.1f}%)")
            
            return True
            
        except ValueError as e:
            print(f"❌ Error en formato de montos: {e}")
            return False
        except Exception as e:
            print(f"❌ Error actualizando composición: {e}")
            return False
    
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
            print("7. 💾 Guardar datos")
            print("8. 🚪 Salir")
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
                    print("Formato: 'Instrumento1:monto1,Instrumento2:monto2,...'")
                    print("Ejemplo: 'Bonos:10000,Acciones:15000,FCI:5000'")
                    composicion = input("Composición: ").strip()
                    if composicion:
                        self.actualizar_composicion(composicion)
                
                elif opcion == '7':
                    self.guardar_datos()
                
                elif opcion == '8':
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
                       help='Actualizar composición: --composicion "Bonos:10000,Acciones:15000"')
    parser.add_argument('--estado', action='store_true',
                       help='Mostrar estado actual del fondo')
    
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
    
    if cambios_realizados:
        admin.guardar_datos()
    
    if args.estado or not any(vars(args).values()):
        admin.mostrar_estado()
    
    # Si no se pasaron argumentos específicos, abrir menú interactivo
    if not any([args.balance is not None, args.cliente, args.suscripcion, 
               args.rescate, args.composicion, args.estado]):
        admin.menu_interactivo()

if __name__ == "__main__":
    main()