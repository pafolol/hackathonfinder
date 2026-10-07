import type { ReactNode } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useOpportunity, useUpdateOpportunity } from '../api/hooks'
import { Countdown, DateStub } from '../components/OpportunityCard'
import { formatDay, relativeTime } from '../lib/dates'
import { CATEGORY_LABELS, MODALITY_LABELS, placeLabel, REVIEW_LABELS } from '../lib/labels'

function Row({ label, children }: { label: string; children: ReactNode }) {
  if (!children) return null
  return (
    <div className="row">
      <dt>{label}</dt>
      <dd>{children}</dd>
    </div>
  )
}

export default function OportunidadDetalle() {
  const { id = '' } = useParams()
  const query = useOpportunity(id)
  const update = useUpdateOpportunity()

  if (query.isPending) return <p className="muted">Cargando…</p>
  if (query.isError) return <p className="form-error">{query.error.message}</p>
  const o = query.data
  const place = placeLabel(o)

  return (
    <article className="detail">
      <Link className="back" to="/">
        ← Oportunidades
      </Link>

      <header className="detail-head">
        <DateStub deadline={o.deadline} />
        <div>
          <div className="card-meta">
            <span className={`category cat-${o.category}`}>{CATEGORY_LABELS[o.category]}</span>
            <span className="chip">{REVIEW_LABELS[o.review_status]}</span>
            {o.importance >= 4 && <span className="badge-priority">Prioritaria</span>}
            <Countdown deadline={o.deadline} />
          </div>
          <h1>{o.title}</h1>
          <p className="lead">{o.summary}</p>
        </div>
      </header>

      <div className="actions">
        <a className="button primary" href={o.registration_url ?? o.url} target="_blank" rel="noreferrer">
          {o.registration_url ? 'Ir al registro' : 'Ver la convocatoria'} ↗
        </a>
        {o.registration_url && (
          <a className="button" href={o.url} target="_blank" rel="noreferrer">
            Página oficial ↗
          </a>
        )}
        <button className="button" onClick={() => update.mutate({ id: o.id, is_saved: !o.is_saved })}>
          {o.is_saved ? '★ Guardada' : '☆ Guardar'}
        </button>
        {o.review_status !== 'revisada' && (
          <button className="button" onClick={() => update.mutate({ id: o.id, review_status: 'revisada' })}>
            Marcar como revisada
          </button>
        )}
        {o.review_status !== 'descartada' ? (
          <button className="button quiet" onClick={() => update.mutate({ id: o.id, review_status: 'descartada' })}>
            Descartar
          </button>
        ) : (
          <button className="button quiet" onClick={() => update.mutate({ id: o.id, review_status: 'nueva' })}>
            Restaurar
          </button>
        )}
      </div>
      {update.isError && <p className="form-error">{update.error.message}</p>}

      <div className="detail-grid">
        <section className="panel">
          <h2>Fechas clave</h2>
          <dl>
            <Row label="Fecha límite">{o.deadline ? formatDay(o.deadline) : (o.deadline_note ?? 'No publicada')}</Row>
            {o.deadline && <Row label="Nota">{o.deadline_note}</Row>}
            <Row label="Inicio del evento">{o.event_start && formatDay(o.event_start)}</Row>
            <Row label="Fin del evento">{o.event_end && formatDay(o.event_end)}</Row>
          </dl>
        </section>

        <section className="panel">
          <h2>Datos</h2>
          <dl>
            <Row label="Registro">{o.registration_status}</Row>
            <Row label="Modalidad">{o.modality && MODALITY_LABELS[o.modality]}</Row>
            <Row label="Sede">{place}</Row>
            <Row label="Costo">{o.cost}</Row>
            <Row label="Premio">{o.prize_text ?? (o.prize_amount_usd ? `US$${o.prize_amount_usd.toLocaleString('en-US')}` : null)}</Row>
          </dl>
        </section>

        <section className="panel fits">
          <h2>Proyectos que encajan</h2>
          {o.fit_projects.length === 0 ? (
            <p className="muted">La búsqueda no relacionó esta oportunidad con ningún proyecto registrado.</p>
          ) : (
            <ul>
              {o.fit_projects.map((fit) => (
                <li key={fit.project_id}>
                  <strong>{fit.name}</strong>
                  {fit.note && <span>{fit.note}</span>}
                </li>
              ))}
            </ul>
          )}
        </section>

        {(o.eligibility || o.requirements.length > 0) && (
          <section className="panel">
            <h2>Quién puede aplicar</h2>
            {o.eligibility && <p>{o.eligibility}</p>}
            {o.requirements.length > 0 && (
              <ul className="bullets">
                {o.requirements.map((requirement) => (
                  <li key={requirement}>{requirement}</li>
                ))}
              </ul>
            )}
          </section>
        )}

        {o.content && (
          <section className="panel wide">
            <h2>Detalle</h2>
            <p className="prose">{o.content}</p>
          </section>
        )}
      </div>

      <footer className="detail-foot">
        {o.tags.length > 0 && (
          <div className="chips">
            {o.tags.map((tag) => (
              <span className="chip" key={tag}>
                #{tag}
              </span>
            ))}
          </div>
        )}
        <p className="muted">
          {o.source_name && <>Fuente: {o.source_name} · </>}
          Encontrada {relativeTime(o.discovered_at)} · Importancia {o.importance} de 5
        </p>
      </footer>
    </article>
  )
}
