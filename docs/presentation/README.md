# Material para presentación en Canva

## Contenido

- **`SLIDES.md`** — guión completo de las 12 diapositivas. Cada slide tiene:
  - Layout sugerido
  - Contenido visible (títulos, tablas, bullets)
  - Notas del orador (para el campo "speaker notes" de Canva)
- **`diagrams/`** — diagramas vectoriales (.svg) para subir a Canva
- **`screenshots/`** — (vacío, tú lo llenas) capturas del APK corriendo

## Diagramas incluidos

| Archivo | Para slide |
|---|---|
| `01_cover_graph.svg` | Slide 1 (portada decorativa) |
| `02_ecosystem.svg` | Slide 2 (deluxe-v2 ↔ deluxe-analyze) |
| `04_architecture_full.svg` | Slide 4 (arquitectura maestra) |
| `05_aws_pipeline.svg` | Slide 5 (pipeline AWS) |
| `06_gcp_pipeline.svg` | Slide 6 (pipeline GCP) |
| `07_neo4j_schema.svg` | Slide 7 (schema canónico) |
| `08_etl_flow.svg` | Slide 8 (ETL + algoritmos GDS) |
| `09_dashboard_arch.svg` | Slide 9 (Flutter + FastAPI) |
| `10_infra.svg` | Slide 10 (Terraform + CI/CD + WIF) |

Slides 3, 11 y 12 son texto/tabla — no requieren diagrama.

## Cómo armar en Canva

### Setup
1. Crear un nuevo "Pitch Deck" en Canva (16:9)
2. Tema: **dark mode**. Aplicar paleta personalizada:
   - Background: `#050605`
   - Surface: `#0c100e`
   - Primary: `#10b981` (emerald-500)
   - Primary light: `#34d399`
   - Gray: `#9ca3af`
   - Text: `#e8e8e8`
3. Tipografía: **Inter** (headings 700, body 400)

### Por cada slide

1. Abre `SLIDES.md` y ve a la sección de la slide que toca.
2. Crea una página nueva en Canva.
3. Copia el título.
4. Si hay diagrama: en Canva → **Uploads → upload media** → arrastra el `.svg` correspondiente desde `diagrams/`. SVG se renderiza vectorial, calidad perfecta.
5. Copia las tablas o listas. Canva tiene plantillas de tabla; el truco rápido es pegar como texto y dar formato.
6. Abre el panel de **speaker notes** (View → Show notes) y pega las "Notas del orador".

### Atajo: Magic Write (Canva Pro)
Si tienes Canva Pro, puedes pegar cada sección de `SLIDES.md` en el chat de Magic Design y te genera un layout automático. Después solo ajustas.

## Screenshots de la app

Para llenar `screenshots/`:

```
Slide 9 sugerencias de captura:
1. Home con las 5 feature cards
2. Q1 Promo reach con el KPI gigante "339"
3. Q2 Influencers con el bar chart
4. Q4 Comunidades con el treemap

En el teléfono Android (con el APK instalado):
- Volumen abajo + Power = screenshot
- Transfiere a esta carpeta
```

Estos screenshots se ven mejor en la slide 9 que cualquier diagrama
abstracto — son la prueba real de que el sistema funciona.

## Tiempo estimado

- Armar las 12 slides en Canva con los assets ya hechos: **1.5–2 horas**
- Si usas plantilla "Tech Startup Dark" pre-hecha: **45 min – 1h**

## Tips de presentación

- Total esperado con esta estructura: 18–22 minutos hablados
- Slide 4 (arquitectura) es el corazón — practica explicarla en 2 minutos
- Slide 11 (resultados) es donde el jurado conecta — destaca el "339 / 361"
- Ten lista la **demo del APK en tu teléfono** para mostrar al final si hay preguntas
