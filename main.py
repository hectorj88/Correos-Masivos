import streamlit as st
import pandas as pd
import funciones as fc
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
#from dotenv import load_dotenv
import tempfile
#streamlit run main.py
#pip freeze > requirements.txt
# Configuración de la página
st.set_page_config(
    page_title="Enviador de Correos",
    page_icon="📧",
    layout="wide"
)

# Título y descripción
st.title("📧 Enviador de Correos Masivos")
st.markdown("Esta aplicación te permite enviar correos masivos personalizados utilizando un archivo Excel y una plantilla HTML.")

# Cargar variables de entorno (opcional)
#load_dotenv()

# Crear tabs para organizar la interfaz
tab1, tab2, tab3 = st.tabs(["Configuración", "Contenido", "Enviar"])

with tab1:
    st.header("Configuración De la Cuenta de Email")
    
    # Campo para editar el nombre asociado al correo
    nombre_remitente = st.text_input(
        "Nombre asociado al correo remitente",
        #value="Valor por defecto",  # Valor predeterminado
        placeholder="Ej: Juan Perez",
        help="Este nombre se mostrará como el remitente en el correo que reciba el cliente."
    )
    
    # Diccionario de servidores SMTP populares
    SMTP_SERVERS = {
        "Yandex": {"server": "smtp.yandex.com", "port": 465},
        "Gmail": {"server": "smtp.gmail.com", "port": 465},
        "Yahoo": {"server": "smtp.mail.yahoo.com", "port": 465},
        "Outlook/Hotmail": {"server": "smtp-mail.outlook.com", "port": 587}
    }

    # Selección de proveedor de correo
    proveedor_seleccionado = st.selectbox(
        "Selecciona tu proveedor de correo",
        options=list(SMTP_SERVERS.keys()),
        index=0,  # Yandex como opción por defecto
        help="Selecciona tu proveedor de correo electrónico para configuración automática"
    )

    # Mostrar advertencia para Gmail
    if proveedor_seleccionado == "Gmail":
        st.info("Debes tener activa la Clave de Aplicaciones para poder enviar correos por Gmail")
    
    # Configurar automáticamente servidor y puerto según selección
    smtp_config = SMTP_SERVERS[proveedor_seleccionado]
    
    # Configuración del servidor SMTP
    col1, col2 = st.columns(2)
    with col1:
        #smtp_server = st.text_input("Servidor SMTP", value="smtp.yandex.com")
        #smtp_port = st.number_input("Puerto SMTP", value=465, min_value=1, max_value=65535)
        remitente = st.text_input("Correo Remitente", placeholder="ejemplo@dominio.com")
    
    with col2:
        #remitente = st.text_input("Correo Remitente", placeholder="ejemplo@dominio.com")
        password = st.text_input("Contraseña", type="password")

    # Cargar archivo Excel
    st.header("Archivo de Destinatarios")
    uploaded_excel = st.file_uploader("Sube tu archivo Excel con los destinatarios", type=["xlsx", "xls"])
    
    if uploaded_excel is not None:
        try:
            df = pd.read_excel(uploaded_excel)
            
            st.success(f"✅ Archivo cargado correctamente con {len(df)} registros")
            st.dataframe(df, height=200)
            
            # Seleccionar columnas
            st.subheader("Selecciona las columnas")
            col_nombre = st.selectbox("Columna para Nombre", options=df.columns.tolist())
            col_correo = st.selectbox("Columna para Correo", options=df.columns.tolist())            
            
        except Exception as e:
            st.error(f"Error al cargar el archivo: {str(e)}")

with tab2:
    st.header("Contenido del Correo")
    
    # Configuración del asunto y preheader
    col1, col2 = st.columns(2)
    with col1:
        asunto = st.text_input(
            "Asunto del correo", 
            value=f"¡Regístrate al encuentro sobre inclusión y tecnología en la educación infantil!"
        )
    with col2:
        preheader = st.text_input("Preheader", value="Asegura tu cupo GRATIS ahora")
    
    # Opciones para el cuerpo HTML
    option = st.radio("¿Cómo quieres definir el cuerpo del correo?", ["Subir archivo HTML", "Editar directamente"])
    
    if option == "Subir archivo HTML":
        uploaded_html = st.file_uploader("Sube tu archivo HTML con el cuerpo del correo", type=["html"])
        if uploaded_html is not None:
            html_content = uploaded_html.getvalue().decode("utf-8")
            st.session_state.html_content = html_content  # Almacenar en st.session_state
            st.success("✅ Archivo HTML cargado correctamente")
            st.code(html_content[:500] + "..." if len(html_content) > 500 else html_content, language="html")
    else:
        default_html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Correo</title>
</head>
<body>
    <h1>Hola {{NOMBRE}}!</h1>
    <p>Este es un mensaje personalizado. Puedes usar la etiqueta {{NOMBRE}} para personalizar el mensaje.</p>
</body>
</html>"""
        html_content = st.text_area("Contenido HTML", value=default_html, height=300)
########################################################################
with tab3:
    st.header("Enviar Correo de Prueba")
    
        # Columna para enviar correo de prueba
    col1, col2 = st.columns(2)
    with col1:
        correo_prueba = st.text_input(
            "Correo de prueba",
            placeholder="ejemplo@dominio.com",
            help="Ingresa el correo al que deseas enviar una prueba."
        )
    with col2:
        st.write("")  # Espacio para alinear el botón
        st.write("")  # Espacio para alinear el botón
        if st.button("Enviar Prueba", type="primary"):
            if not correo_prueba:
                st.error("❌ Debes ingresar un correo de prueba")
            elif 'html_content' not in st.session_state:
                st.error("❌ No se ha definido el contenido HTML")
            else:
                try:
                    with st.spinner("Enviando correo de prueba..."):
                        # Conectar al servidor SMTP
                        #smtp_server = 'smtp.yandex.com'
                        smtp_server = smtp_config["server"]
                        #smtp_port = 465
                        smtp_port = smtp_config["port"]
                        server = smtplib.SMTP_SSL(smtp_server, smtp_port)
                        server.login(remitente, password)
                        st.success("✅ Conexión al servidor SMTP establecida")
                        
                        # Crear el mensaje de prueba
                        mensaje_prueba = MIMEMultipart()
                        mensaje_prueba["From"] = f"{nombre_remitente} <{remitente}>"
                        mensaje_prueba["To"] = correo_prueba
                        mensaje_prueba["Subject"] = asunto.replace("{{NOMBRE}}", str(col_nombre))
                        mensaje_prueba["X-Preheader"] = preheader
                        
                        # Personalizar el contenido HTML para la prueba
                        contenido_prueba = st.session_state.html_content.replace("{{NOMBRE}}", "Usuario de Prueba")
                        
                        # Adjuntar el cuerpo HTML
                        mensaje_prueba.attach(MIMEText(contenido_prueba, "html"))
                        
                        # Enviar el correo de prueba
                        server.sendmail(remitente, correo_prueba, mensaje_prueba.as_string())
                        st.success(f"✅ Correo de prueba enviado a {correo_prueba}")
                        
                        # Cerrar la conexión
                        server.quit()
                except Exception as e:
                    st.error(f"❌ Error al enviar correo de prueba: {e}")
    
    st.header("Enviar Correos")
    
    # Función para enviar correos
    def enviar_correos():
        if 'df' not in st.session_state:
            st.error("❌ No se ha cargado ningún archivo Excel")
            return
        
        if not remitente or not password:
            st.error("❌ Debes ingresar el correo remitente y la contraseña")
            return
        
        if 'html_content' not in st.session_state:
            st.error("❌ No se ha definido el contenido HTML")
            return
        
        # Guardar configuración temporalmente
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Conectar al servidor SMTP
            smtp_server = 'smtp.yandex.com'
            smtp_port = 465
            server = smtplib.SMTP_SSL(smtp_server, smtp_port)
            server.login(remitente, password)
            st.success("✅ Conexión al servidor SMTP establecida")
            
            # Limpiar el DataFrame antes de enviar los correos
            df = fc.limpiar_correos(st.session_state.df, col_correo)
            
            # Obtener el primer nombre de la columna de nombres
            df = fc.obtener_primer_nombre(df, col_nombre)
            
            # Enviar correos a cada destinatario
            enviados = 0
            errores = 0
            total = len(df)
            # Lista para almacenar correos no enviados
            correos_no_enviados = []
            
            for index, row in df.iterrows():
                nombre = row.get(col_nombre, "Estimado/a")
                correo = row.get(col_correo)
                
                if pd.isna(correo) or not correo:
                    status_text.text(f"Fila {index+1}: Correo electrónico no válido, se omite")
                    errores += 1
                    continue
                
                # Crear el mensaje personalizado
                mensaje = MIMEMultipart()
                #mensaje["From"] = remitente
                mensaje["From"] = f"{nombre_remitente} <{remitente}>"
                mensaje["To"] = correo
                mensaje["Subject"] = asunto.replace("{{NOMBRE}}", str(nombre))
                mensaje["X-Preheader"] = preheader
                
                # Personalizar el contenido HTML
                contenido_personalizado = html_content.replace("{{NOMBRE}}", str(nombre))
                
                # Adjuntar el cuerpo HTML
                mensaje.attach(MIMEText(contenido_personalizado, "html"))
                
                try:
                    # Convertir el objeto mensaje a string
                    mensaje_texto = mensaje.as_string()
                    server.sendmail(remitente, correo, mensaje_texto)
                    enviados += 1
                    status_text.text(f"✅ Correo enviado a {nombre} ({correo})")
                except Exception as e:
                    status_text.text(f"❌ Error al enviar correo a {correo}: {e}")
                    errores += 1
                
                # Actualizar la barra de progreso
                progress_bar.progress(min((index + 1) / total, 1.0))
            
            # Cerrar la conexión
            server.quit()
            
            # Resumen final
            st.success(f"""
            ### Resumen de envío:
            - Total de correos enviados: {enviados}
            - Total de errores: {errores}
            """)

            # Mostrar correos no enviados
            if correos_no_enviados:
                st.warning("Correos no enviados:")
                st.write(correos_no_enviados)

                # Guardar correos no enviados en un archivo y permitir descarga
                with open("correos_no_enviados.txt", "w") as file:
                    for correo in correos_no_enviados:
                        file.write(correo + "\n")

                with open("correos_no_enviados.txt", "r") as file:
                    st.download_button(
                        label="Descargar correos no enviados",
                        data=file,
                        file_name="correos_no_enviados.txt",
                        mime="text/plain"
                    )
            else:
                st.success("Todos los correos fueron enviados correctamente.")
            
        except Exception as e:
            st.error(f"Error general: {str(e)}")
    
    if st.button("Enviar Correos", type="primary"):
        if 'df' in st.session_state and (df is not None):
            if 'html_content' in st.session_state and html_content:
                with st.spinner("Enviando correos..."):
                    enviar_correos()
            else:
                st.error("❌ Debes definir el contenido HTML primero")
        else:
            st.error("❌ Debes cargar el archivo Excel primero")
    
    st.info("⚠️ Asegúrate de haber configurado correctamente todos los parámetros antes de enviar")

# Información del pie de página
st.markdown("---")
st.caption("Desarrollado por Hector")