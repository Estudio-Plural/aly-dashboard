#!/bin/bash
# Despliega el panel en plural-aly (https://aly-panel.estudio-plural.co).
# Se corre DESDE EL MAC, después de mergear a main:
#
#   bash deploy.sh
#
# El servidor baja `main` de GitHub (el repo es público: no necesita llave),
# queda idéntico a origin/main, reconstruye la imagen y espera a que el panel
# responda por HTTPS. Los secretos (.env y .streamlit/secrets.toml) están en
# .gitignore, así que git no los toca.
#
# No hay runner ni nada escuchando a GitHub en el servidor del bot: el
# despliegue solo pasa cuando alguien corre esto.
set -euo pipefail

H="${ALY_PANEL_HOST:-plural-aly}"

ssh "$H" 'bash -s' <<'EOF'
set -euo pipefail
DOM=aly-panel.estudio-plural.co
REPO_URL=https://github.com/Estudio-Plural/aly-dashboard.git
cd /opt/aly-dashboard

command -v git >/dev/null || { apt-get update -qq && apt-get install -y -qq git >/dev/null; }

# La primera vez la carpeta viene de un rsync, sin .git: se vuelve un clon en
# el sitio (los archivos ya están; el reset los deja iguales a main).
if [ ! -d .git ]; then
  git init -q -b main
  git remote add origin "$REPO_URL"
fi

git fetch -q origin main
# Sin docker-compose.yml en main no hay con qué levantar el panel: mejor no
# tocar nada que dejar el servidor con código que no arranca.
git cat-file -e origin/main:docker-compose.yml 2>/dev/null \
  || { echo "❌ main no tiene docker-compose.yml. ¿Ya se mergeó el PR #9?"; exit 1; }

ANTES=$(git rev-parse -q --short --verify HEAD || echo "-------")
git reset -q --hard origin/main
# reset --hard no borra archivos sin seguimiento: lo que main ya no tiene (o
# lo que quedó del rsync del primer despliegue) seguiría en la carpeta y Docker
# lo copiaría a la imagen. clean -fd los borra; SIN -x, así que respeta
# .gitignore y no toca .env ni .streamlit/secrets.toml.
git clean -q -fd
echo "== main: $ANTES → $(git rev-parse --short HEAD)  $(git log -1 --format=%s)"

# Una carpeta pages/ hace que Streamlit corra cada página sin pasar por el
# login (ver CLAUDE.md, «Navegación»). Si aparece, no se despliega.
[ ! -d pages ] || { echo "❌ Hay una carpeta pages/ en el servidor: las páginas se abrirían sin login. Despliegue detenido."; exit 1; }

chmod 600 .env .streamlit/secrets.toml

# Validar el Caddyfile ANTES de levantar: si cambió y está mal, Caddy no
# arrancaría al recrearse y el panel quedaría caído. Así falla acá y el que
# está corriendo sigue.
docker run --rm -v /opt/aly-dashboard/caddy:/etc/caddy:ro caddy:2.11.2 \
  caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile >/dev/null 2>&1 \
  || { echo "❌ El Caddyfile no es válido. No se desplegó nada:"; \
       docker run --rm -v /opt/aly-dashboard/caddy:/etc/caddy:ro caddy:2.11.2 \
         caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile 2>&1 | tail -3; exit 1; }

docker compose -p aly-dashboard up -d --build 2>&1 | tail -4
# Si cambió el Caddyfile, `up` no reinicia Caddy (su contenedor no cambió);
# reload aplica la config nueva sin cortar conexiones.
docker exec aly-dashboard-caddy caddy reload --config /etc/caddy/Caddyfile --adapter caddyfile 2>&1 | tail -1
# Solo las imágenes viejas de este proyecto, nada del bot.
docker image prune -f --filter label=com.docker.compose.project=aly-dashboard >/dev/null

for i in $(seq 1 40); do
  if curl -fsS --max-time 5 --resolve "$DOM:443:127.0.0.1" "https://$DOM/_stcore/health" >/dev/null 2>&1; then
    echo "✅ https://$DOM responde"
    docker ps --filter name=aly-dashboard --format "{{.Names}}\t{{.Status}}"
    exit 0
  fi
  sleep 3
done
echo "❌ El panel no respondió por HTTPS en 2 minutos"
docker ps -a --filter name=aly-dashboard --format "{{.Names}}\t{{.Status}}"
docker logs --tail=30 aly-dashboard-caddy
docker logs --tail=50 aly-dashboard
exit 1
EOF
