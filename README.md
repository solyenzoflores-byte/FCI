# FCI - Panel del Fondo Común de Inversión

Este proyecto ofrece dos herramientas complementarias:

* **`main.py`**: panel web construido con Streamlit para consultar la
  información del fondo en modo **solo lectura**. Cada usuario debe iniciar sesión
  y solo ve los clientes que tenga asociados.
* **`admin_console.py`**: consola interactiva para administrar los datos del
  fondo (clientes, movimientos, composición) y gestionar los usuarios que pueden
  ingresar al panel web.

## Requisitos

* Python 3.8 o superior
* Dependencias listadas en `requirements.txt`

Instalación rápida de dependencias:

```bash
pip install -r requirements.txt
```

## Uso del panel web

Desde la carpeta del proyecto (`cd FCI`):

```bash
streamlit run main.py
```

Al ingresar se solicitará usuario y contraseña. Los datos visibles dependen del
rol asignado en la consola:

* **admin**: puede ver la información completa del fondo (aunque no puede editar
  desde la web).
* **cliente**: visualiza únicamente la información de los clientes asociados.

Todas las pestañas (resumen, clientes, gráficos, historial y composición)
aparecen en modo lectura. Para modificar datos es obligatorio utilizar la
consola de administración.

## Administración desde la consola

```bash
python admin_console.py
```

Desde el menú interactivo se pueden:

1. Consultar el estado general del fondo.
2. Actualizar el balance diario.
3. Agregar clientes y registrar suscripciones o rescates.
4. Cargar la composición del fondo (acepta montos en pesos y en USD).
5. **Gestionar usuarios del panel web** (crear, listar, cambiar contraseña o
   actualizar los clientes asociados).
6. Actualizar el tipo de cambio USD/ARS utilizado para las valuaciones.

También existen argumentos de línea de comandos para automatizar tareas. Algunos
 ejemplos:

```bash
# Crear un cliente con saldo inicial
python admin_console.py --cliente "Nuevo Cliente" --saldo 100000

# Registrar una suscripción
python admin_console.py --suscripcion "Enzo" 5000

# Actualizar el tipo de cambio (pesos por dólar)
python admin_console.py --tipo-cambio 1000

# Cargar una composición con instrumentos en pesos y dólares
python admin_console.py --composicion "Pesos:1000000,Dólar liquidez:5000:USD"

# Crear un usuario web asociado a un cliente
python admin_console.py --crear-usuario juan --clientes-usuario "Juan Perez" \
    --rol cliente

# Restablecer contraseña de un usuario existente
python admin_console.py --reset-password juan

# Listar usuarios registrados
python admin_console.py --listar-usuarios
```

> **Nota:** si no se indica la contraseña mediante `--password`, la consola la
> solicitará de forma interactiva para evitar que quede registrada en el
> historial.

## Usuarios de ejemplo

El archivo `fondo_datos.json` incluye usuarios iniciales a modo de ejemplo. Se
recomienda reemplazar sus contraseñas mediante la consola antes de usar el
sistema en producción.

| Usuario  | Rol       | Contraseña | Clientes visibles |
|----------|-----------|------------|-------------------|
| `admin`  | admin     | `admin123` | Todos             |
| `enzo`   | cliente   | `enzo2024` | Enzo              |
| `roberto`| cliente   | `roberto2024` | Roberto        |

## Estructura de datos

La información del fondo se almacena en `fondo_datos.json`. Las claves más
importantes son:

* `clientes`: detalle de cuotapartes por inversor.
* `transacciones`: historial de suscripciones y rescates.
* `balance_diario`: evolución del balance total del fondo.
* `composicion_fondo`: instrumentos que componen el fondo con montos y
  porcentajes. Cada instrumento puede incluir la moneda original (`moneda`) y
  el monto en esa divisa (`monto_moneda`).
* `tipo_cambio`: valor del dólar (ARS/USD) utilizado para convertir las
  posiciones en moneda extranjera.
* `usuarios`: credenciales y permisos para acceder al panel web.

Todos los cambios realizados desde la consola se guardan automáticamente en este
archivo.

## Seguridad

* Las contraseñas nunca se almacenan en texto plano, sino como hashes PBKDF2
  con una sal aleatoria.
* El panel web no ofrece controles para editar datos; todas las acciones de
  administración pasan por `admin_console.py`.
* Ante cualquier inconveniente con el acceso web, se puede restablecer la
  contraseña de un usuario desde la consola.
