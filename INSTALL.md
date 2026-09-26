# Instalación

1. Instala Docker Engine y Docker Compose en el host elegido.
2. Copia `config/secrets.yaml.example` como `config/secrets.yaml` y completa los secretos localmente.
3. Revisa `config/configuration.yaml` y cambia las entidades/dispositivos de ejemplo por los de tu instalación.
4. Desde la raíz ejecuta `docker compose up -d`.
5. Comprueba Home Assistant en `http://localhost:8123` y revisa los registros con `docker compose logs --tail=100 homeassistant`.

El repositorio contiene las automatizaciones y scripts YAML activos publicados tras eliminar referencias a la red, equipos y secretos locales. No contiene `.storage`, credenciales de Alexa/ADB, base de datos ni historial privado. Los nombres y las direcciones reemplazadas requieren adaptación antes de instalar.

## Instalador

`HA_CONFIG_DIR=/path/to/ha/config ./install.sh` copia solo los YAML/helpers publicados. Si un archivo ya existe, se omite; `FORCE=1` permite reemplazarlo. El instalador no arranca ni reinicia el servicio y no instala credenciales.
