# Guía de despliegue: backend de tracking de correos en el VPS

Por Héctor Rosas · backend Solutions · Noviembre 2026

Esta guía lleva el backend FastAPI desde tu equipo hasta producción en el VPS, en este orden: subir los archivos, construir la imagen sin credenciales, publicarla en Docker Hub (opcional) y levantar los contenedores uno a uno.

## 0. Antes de empezar

Estructura recomendada en el VPS. Cada carpeta es un proyecto Compose independiente:

```
/opt/backend/
├── traefik/    # docker-compose-traefik.yml, .env (ACME_EMAIL), acme/acme.json
├── postgres/   # docker-compose-postgres.yml, .env
└── api/        # código del backend, Dockerfile, docker-compose.yml, .env
```

Requisitos:

- Docker Engine y Docker Compose v2 instalados (`docker compose version`).
- Registro DNS tipo A del subdominio (por ejemplo `track.mi-dominio-web.com`) apuntando a la IP del VPS.
- Puertos 80 y 443 abiertos en el firewall.
- Cuenta de Docker Hub, necesaria para descargar las imágenes de `dhi.io`.
- Orden de arranque obligatorio: **Traefik, luego Postgres, luego la API**.

## 1. Dejar los archivos del backend en el VPS

### 1.1 Crear las carpetas

```bash
ssh usuario@IP_DEL_VPS
sudo mkdir -p /opt/backend/api /opt/backend/postgres /opt/backend/traefik
sudo chown -R $USER:$USER /opt/backend
exit
```

### 1.2 Subir el proyecto desde tu equipo

**Opción A (la más simple): enviar el .zip.** Desde la carpeta de tu equipo donde está `tracking_api.zip`:

```bash
scp tracking_api.zip usuario@IP_DEL_VPS:/tmp/
```

Luego, en el VPS:

```bash
ssh usuario@IP_DEL_VPS
sudo apt-get install -y unzip
unzip /tmp/tracking_api.zip -d /tmp
cp -a /tmp/tracking_api/. /opt/backend/api/
rm -rf /tmp/tracking_api /tmp/tracking_api.zip
```

El `cp -a origen/. destino/` copia también los archivos ocultos (`.dockerignore`, `.env.example`).

**Opción B: rsync** (Linux, macOS o WSL), desde la carpeta que contiene `tracking_api/`:

```bash
rsync -av --exclude '.env' --exclude '__pycache__' tracking_api/ usuario@IP_DEL_VPS:/opt/backend/api/
```

### 1.3 Reemplazar por los archivos corregidos

El zip original trae un Dockerfile y un compose anteriores. Sobrescríbelos con los corregidos desde tu equipo:

```bash
scp Dockerfile docker-compose.yml .dockerignore .env.example usuario@IP_DEL_VPS:/opt/backend/api/
scp docker-compose-postgres.yml usuario@IP_DEL_VPS:/opt/backend/postgres/
scp docker-compose-traefik.yml usuario@IP_DEL_VPS:/opt/backend/traefik/
```

El de Traefik solo hace falta si aún no lo tienes en esa carpeta o quieres actualizarlo.

### 1.4 Verificar la carpeta

```bash
cd /opt/backend/api
ls -a
```

Debes ver: `.dockerignore`, `.env.example`, `Dockerfile`, `docker-compose.yml`, `main.py`, `requirements.txt` y las carpetas `core`, `models`, `routers`, `schemas`, `services` (y `scripts`, que se ignora al construir). **Todavía no debe existir un `.env`.**

### 1.5 Crear el .env en el VPS

Genera los valores secretos:

```bash
# Clave Fernet (cifra los tokens del píxel)
openssl rand -base64 32 | tr '+/' '-_'

# Clave de administración de la API
openssl rand -hex 32

# Contraseña de PostgreSQL
openssl rand -hex 24
```

Crea y protege el archivo:

```bash
cd /opt/backend/api
cp .env.example .env
nano .env
chmod 600 .env
```

Completa estos campos:

- `API_DOMAIN` y `ALLOWED_HOSTS`: el mismo dominio en ambos.
- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`: idénticos a los del `.env` de Postgres.
- `FERNET_KEY` y `ADMIN_API_KEY`: los valores que acabas de generar.

Importante:

- Guarda `FERNET_KEY` y `ADMIN_API_KEY` en un gestor de contraseñas. Las mismas claves deben estar como variables de entorno en el equipo donde corre tu script de envío (`sender_helper.py`).
- Si cambias `FERNET_KEY` después de enviar correos, las aperturas de esos correos ya no se registrarán.
- El `.env` nunca se sube a Git ni a Docker Hub.

## 2. Crear la imagen desde el VPS (sin credenciales dentro)

### 2.1 Cómo se garantiza que no entren credenciales

Hay tres capas de protección:

1. El `.dockerignore` excluye `.env` del contexto de construcción.
2. El Dockerfile copia solo `main.py` y las carpetas de código; no usa `COPY . .`.
3. Las variables llegan en tiempo de ejecución mediante `env_file` y `environment` del compose, nunca durante el build.

### 2.2 Iniciar sesión en el registro de imágenes endurecidas

```bash
docker login dhi.io
```

Usa tu usuario de Docker Hub y, como contraseña, un token de acceso personal (Docker Hub, Account settings, Personal access tokens). Un token de solo lectura suele bastar para descargar imágenes.

### 2.3 Construir la imagen

```bash
cd /opt/backend/api
docker build --pull -t backend-api:1.0 .
```

- `--pull` descarga la versión más reciente de la imagen base.
- `-t backend-api:1.0` es el nombre y la versión de tu imagen.
- El punto final es el contexto: la carpeta actual.

La primera vez tarda unos minutos. También puedes usar `docker compose build`, que genera la misma etiqueta porque el compose declara `image: backend-api:1.0`.

### 2.4 Verificar que la imagen está limpia

**a) La imagen existe:**

```bash
docker images backend-api
```

**b) Sin variables sensibles.** Solo deben aparecer variables como `PATH`, `PYTHONUNBUFFERED`; nunca `FERNET_KEY`, `POSTGRES_PASSWORD` ni similares:

```bash
docker image inspect backend-api:1.0 --format '{{json .Config.Env}}'
```

**c) Sin archivo .env dentro.** La imagen final no tiene shell, así que se inspecciona exportando su contenido:

```bash
docker create --name inspeccion backend-api:1.0
docker export inspeccion | tar -tf - | grep -F 'app/.env' || echo 'OK: no hay .env en la imagen'
docker export inspeccion | tar -tf - | grep '^app/' | grep -v '^app/venv'
docker rm inspeccion
```

El segundo listado debe mostrar únicamente `main.py` y las carpetas `core`, `models`, `routers`, `schemas` y `services`.

**d) Historial sin secretos.** Si no hay coincidencias, está bien:

```bash
docker history --no-trunc backend-api:1.0 | grep -iE 'password|secret|fernet|api_key' || echo 'OK'
```

**e) Usuario sin privilegios:**

```bash
docker image inspect backend-api:1.0 --format '{{.Config.User}}'
```

Debe mostrar un usuario no root (por ejemplo `nonroot` o `65532`).

### 2.5 Versionado

Cada vez que cambies el código, construye una nueva versión (`backend-api:1.1`), actualiza el `image:` del compose y reinicia el contenedor. La versión anterior queda disponible para volver atrás.

## 3. Subir la imagen a Docker Hub (opcional)

**¿Es necesario?** No. Si construyes en el VPS, la imagen ya está ahí. Sirve para tener un respaldo, desplegar en otro servidor sin reconstruir, o construir en tu equipo y solo descargar en el VPS.

1. **Crea un repositorio privado.** En hub.docker.com, Repositories, Create repository, nombre `backend-api`, visibilidad **Private**. La imagen no contiene credenciales, pero es código tuyo.
2. **Crea un token** en Account settings, Personal access tokens, con permisos Read & Write.
3. **Inicia sesión:**

   ```bash
   docker login -u TU_USUARIO
   ```

   Pega el token cuando pida la contraseña.
4. **Etiqueta la imagen con tu usuario:**

   ```bash
   docker tag backend-api:1.0 TU_USUARIO/backend-api:1.0
   ```
5. **Súbela:**

   ```bash
   docker push TU_USUARIO/backend-api:1.0
   ```
6. **Para usarla desde otro servidor:** haz `docker login -u TU_USUARIO` y `docker pull TU_USUARIO/backend-api:1.0`. En el compose cambia el bloque `build` por `image: TU_USUARIO/backend-api:1.0`. Para ejecutarla ya no necesitas iniciar sesión en `dhi.io`; eso solo se requiere para construir.
7. **Al terminar, cierra sesión:**

   ```bash
   docker logout
   ```

   Las credenciales quedan guardadas en `~/.docker/config.json`; si el VPS es compartido, elimina el token cuando ya no lo uses.

## 4. Levantar los contenedores uno a uno

### 4.1 Traefik

Si ya está funcionando, solo verifica:

```bash
docker ps --filter name=traefik
docker network ls | grep proxy
```

Si todavía no lo has levantado:

```bash
cd /opt/backend/traefik
mkdir -p acme
touch acme/acme.json
chmod 600 acme/acme.json
echo 'ACME_EMAIL=tu_correo@tudominio.com' > .env
docker compose -f docker-compose-traefik.yml up -d
docker compose -f docker-compose-traefik.yml logs --tail 50
```

**No borres ni recrees `acme/acme.json` si ya existe**: ahí están tus certificados. Si solo actualizas el compose, `up -d` recrea el contenedor conservando ese archivo.

### 4.2 PostgreSQL

```bash
cd /opt/backend/postgres
nano .env
chmod 600 .env
```

El `.env` de esta carpeta debe contener `POSTGRES_USER`, `POSTGRES_PASSWORD` y `POSTGRES_DB`, con los mismos valores del `.env` de la API. Luego:

```bash
docker compose -f docker-compose-postgres.yml up -d
docker compose -f docker-compose-postgres.yml logs --tail 50
```

Verifica (puede tardar unos 20 segundos en marcarse como saludable):

```bash
docker ps --filter name=postgres
docker network ls | grep db_network
docker exec postgres pg_isready -U TU_POSTGRES_USER -d TU_POSTGRES_DB
```

Debe responder `accepting connections`.

**Ojo:** la contraseña solo se aplica la primera vez que se crea el volumen. Si cambias `POSTGRES_PASSWORD` después, la base de datos no se entera; tendrías que cambiarla con `ALTER USER` o recrear el volumen (lo que borra los datos).

### 4.3 API

```bash
cd /opt/backend/api
docker compose up -d
docker compose logs --tail 50
```

Busca estas líneas: `Uvicorn running on http://0.0.0.0:8000` y `Application startup complete`. Comprueba que se crearon las tablas:

```bash
docker exec postgres psql -U TU_POSTGRES_USER -d TU_POSTGRES_DB -c '\\dt'
```

Deben aparecer `campaigns` y `email_opens`.

### 4.4 Probar de punta a punta

**Pruebas básicas (desde cualquier equipo):**

```bash
# Debe responder 200 y content-type: image/gif (aunque el token sea inválido)
curl -I https://track.mi-dominio-web.com/t/prueba.gif

# Debe responder 401 (sin clave)
curl -i https://track.mi-dominio-web.com/admin/campaigns/x/stats

# Debe responder 404 (campaña inexistente, con la clave correcta)
curl -i -H 'X-API-Key: TU_CLAVE' https://track.mi-dominio-web.com/admin/campaigns/x/stats
```

**Prueba real con un token válido (desde tu equipo, junto a `sender_helper.py`):**

```bash
export FERNET_KEY='TU_FERNET_KEY'
export ADMIN_API_KEY='TU_ADMIN_API_KEY'
export TRACKING_BASE_URL='https://track.mi-dominio-web.com'
python -c "from sender_helper import build_pixel_url; print(build_pixel_url('prueba', 'tu_correo@ejemplo.com'))"
```

En Windows PowerShell las variables se definen con `$env:FERNET_KEY='...'`. Los comandos `curl` con comillas simples funcionan en PowerShell moderno, WSL, macOS o Linux. Luego:

```bash
# 1. Simula la apertura con la URL generada
curl -I URL_GENERADA

# 2. Registra la campaña con 1 envío
curl -X POST https://track.mi-dominio-web.com/admin/campaigns -H 'X-API-Key: TU_ADMIN_API_KEY' -H 'Content-Type: application/json' -d '{"id":"prueba","name":"Prueba","total_sent":1}'

# 3. Consulta las estadísticas
curl -H 'X-API-Key: TU_ADMIN_API_KEY' https://track.mi-dominio-web.com/admin/campaigns/prueba/stats
```

Si todo está bien, verás `unique_opens: 1` y `open_rate_percent: 100.0`. Para limpiar los datos de prueba:

```bash
docker exec postgres psql -U TU_POSTGRES_USER -d TU_POSTGRES_DB -c "DELETE FROM email_opens WHERE campaign_id='prueba'; DELETE FROM campaigns WHERE id='prueba';"
```

## 5. Operación diaria

| Tarea | Comando |
| --- | --- |
| Ver contenedores | `docker ps` |
| Ver logs de la API | `cd /opt/backend/api && docker compose logs -f api` |
| Reiniciar la API | `docker compose restart api` |
| Actualizar a una versión nueva | Cambia el tag en `image:`, luego `docker compose build` y `docker compose up -d` |
| Volver a la versión anterior | Restaura el tag anterior en `image:` y `docker compose up -d` |
| Apagar la API | `docker compose down` |
| Respaldo de la base de datos | `docker exec postgres pg_dump -U TU_POSTGRES_USER TU_POSTGRES_DB > respaldo_$(date +%F).sql` |

**Nunca ejecutes `docker compose down -v` en la carpeta de Postgres:** borraría el volumen con todos los datos.

## 6. Solución de problemas

| Síntoma | Causa probable | Solución |
| --- | --- | --- |
| `unauthorized` o `pull access denied` al construir | No has iniciado sesión en dhi.io | `docker login dhi.io` |
| `pip install` falla compilando paquetes | Versión de Python sin paquetes precompilados para Alpine | Cambia a `3.12` en ambas etapas del Dockerfile |
| `network proxy declared as external, but could not be found` | Traefik no está levantado | Levanta Traefik primero (4.1) |
| `network db_network declared as external, but could not be found` | Postgres no está levantado | Levanta Postgres primero (4.2) |
| La API reinicia en bucle con `password authentication failed` | Credenciales distintas entre los `.env` | Iguala `POSTGRES_*`; recuerda que la contraseña solo se aplica al crear el volumen |
| La API reinicia con `could not translate host name postgres` | Postgres apagado o fuera de `db_network` | Revisa `docker ps` y la red |
| Traefik responde 404 | Falta `API_DOMAIN` o el DNS no apunta al VPS | Revisa el `.env` y el registro A |
| `Invalid host header` | `ALLOWED_HOSTS` no coincide con el dominio | Haz que sean idénticos |
| El certificado no se emite | DNS sin propagar o puerto 80 cerrado | Revisa los logs de Traefik y el firewall |
| `/admin` responde 401 | `X-API-Key` incorrecta | Usa el valor exacto de `ADMIN_API_KEY` |
| Una apertura no se registra | `FERNET_KEY` distinta entre script y servidor, o abriste dos veces en menos de 30 s | Revisa la clave; el filtro anti-duplicados ignora repeticiones rápidas |

## 7. Lista de verificación final

- [ ] DNS apunta al VPS y los puertos 80 y 443 están abiertos.
- [ ] Archivos del backend en `/opt/backend/api`, sin `.env` hasta el paso 1.5.
- [ ] `.env` creado con `chmod 600` y claves guardadas en un gestor de contraseñas.
- [ ] Imagen construida y verificada sin `.env` ni variables sensibles.
- [ ] Traefik, Postgres y API arriba, en ese orden.
- [ ] Pruebas básicas y prueba real con token superadas.
- [ ] Datos de prueba eliminados.
- [ ] Claves y variables copiadas al equipo desde donde enviarás los correos.
