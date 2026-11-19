# Enviador de correos masivos

Aplicación web desarrollada con Python y Streamlit para crear y enviar correos electrónicos personalizados a partir de una lista de destinatarios en Excel. Incluye una opción de seguimiento de aperturas mediante un backend FastAPI.

## Funcionalidades

- Envío mediante SMTP con configuración para Gmail, Yandex, Yahoo y Outlook/Hotmail.
- Personalización del asunto y del contenido HTML con el nombre de cada destinatario.
- Carga de contactos desde archivos Excel (`.xlsx` o `.xls`) y selección de las columnas de nombre y correo.
- Envío de prueba, seguimiento del progreso y resumen de resultados.
- Limpieza de direcciones: elimina espacios al inicio y al final, filas sin correo y direcciones duplicadas.
- Seguimiento de aperturas opcional, administrado por un backend FastAPI y PostgreSQL.

## Probar la aplicación

Puedes usar la versión publicada en Streamlit:

[Abrir Enviador de Correos Masivos](https://correos-masivos-hector.streamlit.app/)

## Requisitos

- Python 3.10 o superior.
- `pip`.
- Una cuenta de correo con acceso SMTP. Algunos proveedores requieren una contraseña de aplicación.
- Para ejecutar la aplicación localmente, configura las variables del backend de tracking indicadas en [Configuración del seguimiento](#configuración-del-seguimiento).

## Instalación y ejecución local

Clona el repositorio y entra en su carpeta:

```bash
git clone https://github.com/hectorj88/Correos-Masivos.git
cd Correos-Masivos
```

Crea y activa un entorno virtual. En Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

En macOS o Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Instala las dependencias e inicia la aplicación:

```bash
python -m pip install -r requirements.txt
python -m streamlit run main.py
```

Streamlit mostrará en la terminal la dirección local para abrir en el navegador.

## Configuración del seguimiento

La aplicación necesita las variables de tracking para iniciar, aunque el backend esté alojado en otro servidor. En la raíz del proyecto, crea un archivo `.env` con los valores de tu backend:

```dotenv
FERNET_KEY=tu_clave_fernet
ADMIN_API_KEY=tu_clave_de_administracion
TRACKING_BASE_URL=https://track.tudominio.com
```

`FERNET_KEY` y `ADMIN_API_KEY` deben coincidir con las configuradas en el backend. `TRACKING_BASE_URL` debe ser la URL pública del servicio, sin una barra final. No publiques ni compartas el archivo `.env`; está excluido de Git.

Para desplegar el backend FastAPI en un VPS, sigue la guía detallada: [Guía de despliegue del backend de tracking en el VPS](Guía%20de%20despliegue%20backend%20de%20tracking%20de%20correos%20en%20el%20VPS.md). La guía cubre la configuración de Docker, Traefik, PostgreSQL, secretos, verificación y operación.

## Preparar y enviar una campaña

1. Prepara un archivo Excel con una fila por destinatario. La aplicación te permite elegir las columnas; por ejemplo:

   | Nombre | Correo |
   | --- | --- |
   | Ana Pérez | ana@ejemplo.com |

2. Ejecuta la aplicación y completa la configuración del remitente: nombre, proveedor, correo y contraseña SMTP.
3. Carga el Excel y selecciona sus columnas de nombre y correo.
4. Define el asunto, el contenido HTML y un identificador para la campaña. Puedes usar `{{NOMBRE}}` en el asunto y en el cuerpo para insertar el nombre del destinatario.
5. Envía un correo de prueba y revisa que se vea correctamente.
6. Cuando todo esté listo, inicia el envío y revisa el progreso y el resumen final.

Para registrar aperturas, incluye `{{tracking_pixel_url}}` en el HTML donde quieras insertar el píxel de seguimiento. El cliente de correo debe cargar imágenes para que se registre la apertura; por eso, las métricas pueden no reflejar todas las lecturas con exactitud.

## Estructura del proyecto

```text
.
├── main.py                   # Interfaz Streamlit y proceso de envío
├── funciones.py              # Limpieza y preparación de destinatarios
├── requirements.txt          # Dependencias de la aplicación
├── backend/
│   ├── main.py               # API FastAPI de tracking
│   ├── scripts/sender_helper.py
│   ├── docker-compose.yml
│   ├── docker-compose-postgres.yml
│   └── docker-compose-traefik.yml
└── Guía de despliegue backend de tracking de correos en el VPS.md
```

## Seguridad y privacidad

- No guardes contraseñas SMTP ni claves de tracking en el código fuente.
- Protege el archivo `.env` y guarda una copia segura de las claves. La `FERNET_KEY` debe mantenerse estable para poder procesar los píxeles ya enviados.
- Usa el seguimiento de aperturas de forma transparente y de acuerdo con las normas de privacidad aplicables.
