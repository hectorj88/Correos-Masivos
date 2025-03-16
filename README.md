# 📧 Enviador de Correos Masivos

Aplicación web para envío masivo de correos electrónicos personalizados usando Python y Streamlit.

## Características Principales
- ✅ Configuración automática para proveedores de correo populares (Gmail, Yandex, Yahoo, Outlook/Hotmail)
- 📊 Carga de destinatarios desde archivo Excel
- ✨ Editor HTML integrado con personalización dinámica
- 📨 Envío de correos de prueba previa verificación
- 📈 Panel de progreso y reporte de envíos
- 🔒 Configuración segura SMTP con SSL/TLS

Antes de enviar los correos, se verifica que no hallan cuentas duplicadas ni espacions en blanco entre el texto de los correos.

## Requisitos
- Python 3.7+
- Cuenta de correo electrónico con acceso SMTP
- Archivo Excel con estructura:
  | Nombre | Correo       |
  |--------|-------------|
  | Juan   | juan@mail.com|

## Prueba
Puedes realizar una prueba desde el siguiente link:

[https://correos-masivos-hector.streamlit.app/](https://correos-masivos-hector.streamlit.app/)

## Instalación
1. Clona el repositorio:
```bash
git clone https://github.com/bebegenial/Envio-de-Correos-Masivos.git
cd enviador-correos
```