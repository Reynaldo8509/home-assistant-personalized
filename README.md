# Home Assistant personalizado

![Logotipo oficial de Home Assistant](docs/assets/home-assistant-official-logo.png)

<sub>Imagen oficial de Home Assistant. La marca y el diseño pertenecen a Home Assistant y Open Home Foundation; este repositorio es una personalización independiente.</sub>

Configuración activa publicada desde el despliegue de Home Assistant en Docker del VPS. Incluye YAML activo, automatizaciones, scripts de Alexa y el helper ADB para Fire TV, con las credenciales, dispositivos y direcciones privadas sustituidos.

## Mapa visual de la integración

![Ilustración generada con IA del ecosistema de agentes, controles y hogar conectado](docs/assets/ai-architecture-map.png)

La ilustración resume visualmente el ecosistema. El diagrama Mermaid y las secciones siguientes describen los flujos implementados con etiquetas precisas.

## Integraciones documentadas

- Alexa enlazada con entidades y scripts de Home Assistant.
- Automatizaciones de presencia/detección basadas en sensores configurados localmente.
- Fire TV controlado mediante ADB por helper local: el emparejamiento y la clave privada se configuran en cada instalación.
- Hermes Agent se integra mediante sus plugins de Alexa/HA y puede solicitar acciones usando Home Assistant como capa de automatización.

```mermaid
flowchart LR
  TG[Telegram] --> H[Hermes Agent]
  H -->|plugin/acción autorizada| HA[Home Assistant]
  A[Alexa] -->|voz| HA
  HA --> AU[Automatizaciones y scripts]
  AU --> PR[Presencia y detección]
  AU --> TV[Helper ADB] --> FT[Fire TV]
```

Integración con [Hermes Agent Personalized](https://github.com/Reynaldo8509/hermes-agent-personalized) y [Hermy HQ Personalized](https://github.com/Reynaldo8509/hermy-hq-personalized).

Lee `INSTALL.md` para el despliegue y `SECURITY.md` para el límite de datos publicados. Reemplaza los valores ilustrativos y configura `secrets.yaml` localmente antes de arrancar.
