# Antes que sea tarde

Tablero de alerta temprana para Permanencia y docentes MAIE. Recibe un Excel académico, calcula un riesgo de deserción con reglas visibles y entrega un listado priorizado con una acción por estudiante.

No usa un modelo opaco ni envía datos de estudiantes a un servicio externo.

## Qué cubre el reto

- Cargar un `.xlsx` desde la interfaz. No hay formulario para digitar estudiantes.
- Validar columnas, celdas vacías, textos donde va un número, promedios fuera de rango y documentos repetidos. Si algo falla, no se importa ninguna fila.
- Volver a cargar el archivo actualiza al mismo documento. No crea un duplicado.
- Tablero con registrados, en riesgo, sin riesgo activo y gráficas.
- PDF solo con quienes están en riesgo (Medio, Alto y Crítico), ordenados de mayor a menor puntaje.

## Cómo se calcula el riesgo

Puntaje de 0 a 100.

- Promedio: hasta 55 puntos. Por debajo de 3,0 es la parte más grande.
- Materias perdidas: hasta 18, con tope en 4.
- Inasistencias: hasta 15, con tope en 8.
- Evaluaciones no presentadas: hasta 7, con tope en 3.
- Semestre 1 o 2: 5 puntos más.

Niveles: Bajo 0–24, Medio 25–49, Alto 50–74, Crítico 75–100.

## Columnas del Excel

`documento`, `nombre`, `programa`, `semestre`, `promedio`, `materias_perdidas`, `inasistencias`, `evaluaciones_no_presentadas`.

La primera fila son los encabezados. También se aceptan con espacios y tildes, por ejemplo `Materias perdidas`. Hay una plantilla en `sample/estudiantes_ejemplo.xlsx` y dentro del tablero.

## Correrlo en el computador

Hace falta Docker Desktop abierto.

```bash
docker compose up -d
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
python scripts/make_sample.py
docker compose exec db psql -U antes -c "CREATE DATABASE antes_test"
pytest
gunicorn --bind 0.0.0.0:8000 --workers 1 wsgi:app

El puerto local de Postgres es el 55432, para no chocar con otras bases que ya usen el 5432.
```

En local el ingreso de ejemplo es `permanencia@uniminuto.local` / `cambia-esta-clave`. Cámbiala en `.env` antes de una demostración compartida. Ese archivo no se sube a GitHub.

Abre `http://127.0.0.1:8000`.

## Seguridad

- Contraseñas con Argon2id. La clave de demostración sale de `DEMO_PASSWORD`, no del código.
- Token CSRF en el ingreso, la carga y el cierre de sesión.
- Las plantillas escapan el HTML. Los nombres del Excel no se insertan sin escape.
- Cabeceras `Content-Security-Policy`, `X-Content-Type-Options` y `X-Frame-Options`. La cookie de sesión es `HttpOnly` y `SameSite=Lax`; en Render también `Secure`.
- PostgreSQL exige documento único, promedio entre 0 y 5, y conteos dentro de un rango. La carga entra en una sola transacción.
- Solo `.xlsx`, máximo 2 MB y 2000 filas. Se revisa que el archivo sea un libro Excel y se rechazan macros.
- Cinco intentos de ingreso fallidos bloquean la dirección durante 15 minutos.
- `SECRET_KEY` y `DATABASE_URL` vienen del entorno. Los registros no guardan documentos ni notas.

## Despliegue en Render

El repo incluye `render.yaml`: un servicio web gratuito y PostgreSQL. Hay que tener este proyecto en GitHub, GitLab o Bitbucket.

1. En Render, elige **New Blueprint** y conecta el repositorio.
2. Revisa que el servicio y la base queden en la misma región (`oregon`).
3. Al terminar, abre **Environment** del servicio web y copia `DEMO_PASSWORD`. El usuario es `permanencia@uniminuto.local`.
4. La base gratuita caduca a los 30 días. El servicio web gratuito se duerme a los 15 minutos sin visitas: ábrelo unos minutos antes de sustentar.

La app escucha en `0.0.0.0` y el puerto `PORT`. El chequeo de salud es `/healthz`. El Excel no se guarda en disco: Render borra el disco del servicio en cada despliegue, y los estudiantes quedan en PostgreSQL.

Si la cuenta no ofrece el plan gratuito de Postgres, usa el plan más pequeño y deja el resto del blueprint igual.
