# Juego millonario

Juego de preguntas inspirado en «¿Quién quiere ser millonario?». Incluye la interfaz web, una API en Flask y una base de datos SQLite local.

## Compartir y ejecutar en otro equipo

Comparte este enlace para que la otra persona descargue el proyecto:

**https://github.com/esneidermoo19/Juego-millonario**

Debe tener [Python 3](https://www.python.org/downloads/) instalado. Luego puede descargar el proyecto desde GitHub con **Code → Download ZIP** y descomprimirlo. También puede clonarlo con Git:

```bash
git clone https://github.com/esneidermoo19/Juego-millonario.git
cd Juego-millonario
```

Para iniciar:

- **Windows:** doble clic en `iniciar_juego.bat`.
- **macOS o Linux:** abrir una terminal en la carpeta del proyecto y ejecutar `./iniciar_juego.sh`.

El primer inicio crea un entorno de Python e instala las dependencias. En este equipo, abre **http://127.0.0.1:5000** en el navegador. Para compartirlo con alguien conectado a la misma red Wi-Fi, ambos deben usar este equipo como servidor y la otra persona debe abrir `http://IP-DEL-EQUIPO:5000`. En Fedora puedes ver la IP con `hostname -I` (por ejemplo, `192.168.1.42`). Para cerrar el juego, pulsa `Ctrl+C` en la ventana que lo inició.

La otra persona no necesita descargar nada. El equipo que ejecuta el juego debe permanecer encendido y conectado a la red. Este enlace funciona dentro de la misma red Wi-Fi, no desde Internet.

## Iniciar manualmente

Desde la carpeta del proyecto:

```bash
python -m venv .venv
```

Activa el entorno (`.venv\\Scripts\\activate` en Windows o `source .venv/bin/activate` en macOS/Linux), instala las dependencias y arranca el servidor:

```bash
python -m pip install -r backend/requirements.txt
python -m backend.app
```

La base de datos SQLite se crea en `backend/instance/millionaire.db` y se completa con preguntas de ejemplo al iniciar.

## Docker y Coolify

El archivo `compose.yaml` construye el contenedor, sirve el frontend y la API desde el mismo proceso y conserva SQLite en un volumen Docker. Para desplegar en Coolify:

1. Crea un recurso **Docker Compose** desde este repositorio y usa `compose.yaml` en la raíz.
2. Asigna el dominio al servicio `millionaire`, puerto interno **5000**.
3. Conserva el volumen Compose `millionaire-data`, montado en `/app/backend/instance`; ahí persiste la base SQLite entre despliegues.
4. En las variables de entorno de Coolify configura `DATABASE_URL=sqlite:///backend/instance/millionaire.db`. `PORT` ya queda fijado en `5000`; `WEB_CONCURRENCY` es opcional y por defecto vale `1`.

La imagen excluye la base local y los archivos `.env`; si el volumen está vacío, el backend crea el esquema e inserta preguntas iniciales al arrancar. Configura secretos desde las variables de entorno de Coolify. El archivo `.env.example` solo contiene la URL local de SQLite.

Coolify conecta su proxy al puerto expuesto del servicio; no hace falta publicar el puerto del contenedor directamente en el host.

## Pruebas

Las pruebas del backend están en `backend/tests/` y usan una base de datos temporal, así que no modifican la base real. Desde la carpeta del proyecto:

```bash
.venv/bin/python -m unittest discover -s backend/tests -t .
```

En Windows usa `.venv\Scripts\python.exe` en lugar de `.venv/bin/python`.

## Aviso legal

Este es un proyecto **educativo y sin fines de lucro**, creado con fines de aprendizaje. No se vende, no tiene publicidad y no genera ingresos.

- **Sin relación oficial:** este juego no está afiliado, patrocinado ni aprobado por ninguna de las personas, empresas o marcas que aparecen o se mencionan en él.
- **Formato del concurso:** «¿Quién quiere ser millonario?» (*Who Wants to Be a Millionaire?*) es una marca y un formato de televisión de sus respectivos dueños. Este proyecto solo se inspira en él; no usa su música ni sus logotipos oficiales.
- **Personajes:** los presentadores son caricaturas o referencias usadas como homenaje. Sus nombres e imágenes pertenecen a sus titulares:
  - Cristiano Ronaldo, «CR7» y James Rodríguez: derechos de imagen de cada persona.
  - Terminator: sus respectivos estudios de cine.
  - Master Chief y Halo: Microsoft.
- **Marcas en las ilustraciones:** los logotipos que aparecen en las camisetas, como Nike o los escudos de las federaciones de fútbol, son marcas registradas de sus dueños.
- **Voces:** las voces de los presentadores son sintéticas, generadas con [Piper](https://github.com/rhasspy/piper) o espeak-ng. No imitan ni reproducen la voz real de ninguna persona.

Si eres titular de alguno de estos derechos y quieres que se retire algún contenido, abre un *issue* en este repositorio y se retirará.
