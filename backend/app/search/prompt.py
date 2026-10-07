from datetime import date

from app.models import Opportunity, Project
from app.schemas import Preferences

CATEGORY_LABELS = {
    "hackathon": "hackathones",
    "convocatoria": "convocatorias",
    "aceleradora": "aceleradoras e incubadoras",
    "competencia": "competencias y concursos de emprendimiento",
    "fondo": "fondos, becas y grants",
    "otro": "otras oportunidades relevantes",
}
MODALITY_LABELS = {"presencial": "presencial", "en_linea": "en línea", "hibrido": "híbrido"}

INSTRUCTIONS = """\
Eres el analista de oportunidades del área de Emprendimiento del Tecnológico de Monterrey, campus Guadalajara.
Tu trabajo es buscar en la web oportunidades vigentes (hackathones, convocatorias, competencias, aceleradoras, \
fondos) a las que puedan aplicar los estudiantes, equipos y startups del área.

Reglas:
- Usa la búsqueda web. Solo incluye oportunidades que hayas verificado en una página real; nunca inventes \
fechas, premios ni enlaces. Si un dato no aparece en la fuente, déjalo en null.
- `url` debe ser la página oficial de la oportunidad (o la fuente más directa), no un buscador ni un agregador \
genérico cuando exista la página oficial.
- Solo oportunidades con registro abierto o por abrir. Descarta las que ya cerraron.
- Fechas en formato AAAA-MM-DD. Si no hay fecha límite publicada, deja `deadline` en null y explica en \
`deadline_note`.
- `prize_text` describe el premio como lo publica la fuente; `prize_amount_usd` es el premio máximo aproximado \
en dólares, o null si no es monetario o no se conoce.
- `importance` va de 1 a 5: 5 = encaja muy bien con el perfil y los proyectos, y la fecha o el premio la hacen \
prioritaria; 1 = relevancia marginal.
- En `fit_projects` relaciona cada oportunidad con los proyectos de la lista que realmente podrían aplicar, \
usando su número (`project_ref`) y una nota breve de por qué encaja. Lista vacía si ninguno encaja.
- Escribe `title`, `summary`, `content`, `eligibility`, `requirements`, las notas y las etiquetas en español, \
aunque la fuente esté en otro idioma. `summary` de 1 a 3 frases; `content` con más detalle si lo hay.
- No repitas oportunidades de la lista "ya registradas", salvo que hayan cambiado datos importantes \
(fecha límite, premio).
"""


def _bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def build_input(
    profile_text: str,
    prefs: Preferences,
    projects: list[Project],
    known: list[Opportunity],
    today: date,
) -> tuple[str, dict[int, Project]]:
    """Return the user message and the project_ref -> Project map used in it."""
    refs = {i: p for i, p in enumerate(projects, start=1)}
    sections = [f"Fecha de hoy: {today.isoformat()}."]

    sections.append(
        "## Perfil del área\n"
        + (profile_text.strip() or "Área de Emprendimiento del Tecnológico de Monterrey, campus Guadalajara.")
    )

    criteria = [
        "Tipos de oportunidad: " + ", ".join(CATEGORY_LABELS[t] for t in prefs.types) + ".",
        "Regiones: " + ", ".join(prefs.regions) + "." if prefs.regions else "Regiones: sin restricción.",
        "Modalidades aceptadas: " + ", ".join(MODALITY_LABELS[m] for m in prefs.modalities) + ".",
        f"Fecha límite dentro de los próximos {prefs.deadline_window_days} días (o sin fecha publicada).",
        f"Devuelve como máximo {prefs.max_results} oportunidades, las más relevantes primero.",
    ]
    if prefs.min_prize_usd:
        criteria.append(
            f"Si el premio es monetario, que sea de al menos {prefs.min_prize_usd} USD; "
            "las oportunidades sin premio monetario siguen siendo válidas si aportan valor."
        )
    if prefs.keywords:
        criteria.append("Temas y palabras clave de interés: " + ", ".join(prefs.keywords) + ".")
    if prefs.priority_sources:
        criteria.append("Revisa primero estas fuentes: " + ", ".join(prefs.priority_sources) + ".")
    if prefs.excluded_sources:
        criteria.append("No uses estas fuentes: " + ", ".join(prefs.excluded_sources) + ".")
    sections.append("## Criterios de búsqueda\n" + _bullets(criteria))

    if refs:
        lines = []
        for ref, p in refs.items():
            details = [p.description.strip()] if p.description.strip() else []
            if p.stage:
                details.append(f"Etapa: {p.stage}")
            if p.sector:
                details.append(f"Sector: {p.sector}")
            if p.technologies:
                details.append("Tecnologías: " + ", ".join(p.technologies))
            if p.team:
                details.append(f"Equipo: {p.team}")
            lines.append(f"{ref}. {p.name}" + (" — " + ". ".join(details) if details else ""))
        sections.append("## Proyectos del área\n" + "\n".join(lines))
    else:
        sections.append("## Proyectos del área\nAún no hay proyectos registrados; deja `fit_projects` vacío.")

    if known:
        sections.append(
            "## Oportunidades ya registradas (no repetir)\n"
            + _bullets([f"{o.title} — {o.url}" for o in known])
        )

    sections.append("Busca ahora y devuelve las oportunidades encontradas.")
    return "\n\n".join(sections), refs
