<div align="center">

[🇬🇧 English](README.md) · [🇪🇸 Español](README.es.md)

</div>

<div align="center">

# 🕯️ death-noticer

**Tus contenedores mueren a las 3 AM. Alguien debería notarlo.**

![Python](https://img.shields.io/badge/python-3.8%2B-blue?style=flat-square&logo=python&logoColor=white)
![Dependencies](https://img.shields.io/badge/dependencies-0-00A884?style=flat-square)
![Docker](https://img.shields.io/badge/lives%20in-docker-2496ED?style=flat-square&logo=docker&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-yellow?style=flat-square)

**Cero dependencias · Un archivo · AI First, con aprobación humana**

</div>

---

Tienes logs, tienes dashboards, tienes alertas. Y aun así, cuando un contenedor muere a las 3 AM, lo que recibes es un exit code gris en una terminal que nadie está mirando.

**death-noticer** es un sidecar diminuto siempre encendido que observa el stream de eventos de Docker. En el instante en que cualquier contenedor muere, escribe su **obituario**: quién era (nombre, imagen), cuánto vivió, la causa de muerte (reglas deterministas: exit codes, OOM, tormentas de restarts), sus últimas palabras (las últimas líneas de log) y, si quieres, un **epílogo de IA** de tu agente local.

Despliégalo una vez con `docker compose up -d` y cada muerte en tu host queda notada, documentada y (opcionalmente) anunciada.

## ⚡ Inicio rápido

```bash
git clone https://github.com/fernedy/death-noticer.git
cd death-noticer
docker compose up -d --build
# ...más tarde, un contenedor muere...
ls reports/
# my-api-20260914-030130.md
```

Un obituario se ve así:

```markdown
## 🕯️ Obituary — `my-api`

*my-api, beloved service behind `api:1.2`, left us at 2026-09-14 03:01:30
after 0:03:30 of uptime, surviving 3 restart(s).*

**Cause of death:** 🗡️ SIGKILL — kernel OOM killer or docker stop -f timeout
**Final words:** 🧠 memory pressure in logs

```
ERROR: Cannot allocate memory
```

*In lieu of flowers, raise the memory limit.* 🪦
```

O haz la autopsia puntual de un contenedor:

```bash
python death_noticer.py mi-contenedor-muerto
```

## 🔔 Anuncia las muertes

Apúntalo a cualquier webhook y cada obituario se publica en el momento en que se escribe:

```yaml
command: ["--reports-dir", "/reports",
          "--webhook", "https://discord.com/api/webhooks/XXX/YYY"]
```

Funciona con Discord (`content`), Slack-compatible (`text`) y webhooks genéricos — se envían ambas claves.

## 🤖 AI First, con aprobación humana

- **Determinista primero**: la causa de muerte sale de un motor de reglas (9 significados de exit code, 8 pistas de patrones de log) — misma evidencia, mismo veredicto, siempre.
- **IA segundo, opt-in y local**: con `--ai`, tu agent CLI local ([opencode](https://opencode.ai)) añade un epílogo de 3 líneas: causa raíz probable, un comando para confirmarla, un comando para corregirla. Sin API keys, sin nube, nada sale de tu máquina.
- **Human-in-the-loop**: death-noticer nunca reinicia, nunca «cura», nunca toca tus contenedores. Solo lee (`inspect`, `logs`, `events`) y escribe markdown. Tú decides qué hacer.

## 🧰 Todas las opciones

```bash
python death_noticer.py                      # vigila para siempre, obituarios en ./reports
python death_noticer.py --reports-dir /r     # carpeta personalizada
python death_noticer.py --webhook URL        # publica cada obituario en Slack/Discord
python death_noticer.py --tail 40            # recolecta más últimas palabras
python death_noticer.py --ai                 # epílogo de IA local en cada muerte
python death_noticer.py <contenedor>         # obituario puntual de un contenedor
```

## 🐳 Por qué vive en Docker

El noticer mismo es un contenedor (`python:3.12-alpine` + CLI de Docker) con tu docker socket montado. Ve cada muerte del host, sobrevive a reinicios (`restart: unless-stopped`) y no puede morir de las causas que documenta — no corre workload, no guarda estado, no envía tráfico salvo que configures un webhook.

## 🤝 Funciona genial con [container-autopsy](https://github.com/fernedy/container-autopsy)

death-noticer nota la muerte y escribe el obituario breve. Cuando necesitas el trabajo forense completo — tabla de evidencia, hallazgos contribuyentes, badge compartible — corre container-autopsy sobre el mismo contenedor.

## ✅ Tests

```bash
python -m unittest discover -v
```

La suite simula Docker por completo — el CI corre en Python 3.8, 3.10 y 3.12 sin daemon. Ver [`.github/workflows/ci.yml`](.github/workflows/ci.yml).

## 🤝 Contribuir

Ideas: versión para eventos de Kubernetes, muro de obituarios en HTML, feed RSS de muertes, anotación en Grafana por cada muerte. Ver [CONTRIBUTING.md](CONTRIBUTING.md). Regla de dogfooding: **los PRs no deben bajar el [Glow Score](https://github.com/fernedy/repo-glow) de este repo.**

## 📜 Licencia

MIT — ver [LICENSE](LICENSE).

---

<div align="center">

Construido AI-first por [Fernedy Arias](https://github.com/fernedy) · Tech Explorer

*Si death-noticer detectó una muerte a las 3 AM por ti, deja un ⭐.*

</div>
