# 3.14, la misma con la que se probó la app (constraints.txt). Todas las
# dependencias traen ruedas precompiladas para linux/amd64 en 3.14, así que la
# imagen se arma sin toolchain de C. Verificado con `pip download --only-binary`.
FROM python:3.14-slim

WORKDIR /app

# Las dependencias en su propia capa: cambiar una página no re-instala todo.
COPY requirements.txt constraints.txt ./
RUN pip install --no-cache-dir -r requirements.txt -c constraints.txt

# .dockerignore deja afuera .env y .streamlit/secrets.toml: en el servidor
# viven en el mismo directorio que el código y NO pueden quedar en la imagen.
COPY . .

EXPOSE 8501

# --server.address=0.0.0.0 para que Caddy lo alcance por la red de Docker. El
# puerto no se publica al host (ver docker-compose.yml): lo único expuesto a
# internet es Caddy, en el 443.
CMD ["streamlit", "run", "app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--server.fileWatcherType=none", \
     "--browser.gatherUsageStats=false"]
