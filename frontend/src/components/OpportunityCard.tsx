import type { CSSProperties } from 'react'
import { Link } from 'react-router-dom'
import { useUpdateOpportunity } from '../api/hooks'
import type { Opportunity } from '../api/types'
import { countdown, daysUntil, monthAbbr, parseDay } from '../lib/dates'
import { CATEGORY_LABELS, MODALITY_LABELS, placeLabel, prizeLabel } from '../lib/labels'

export function DateStub({ deadline }: { deadline: string | null }) {
  if (!deadline) {
    return (
      <div className="stub is-open">
        <span className="stub-month">sin</span>
        <span className="stub-none">fecha</span>
      </div>
    )
  }
  const days = daysUntil(deadline)
  const tone = days < 0 ? ' is-closed' : days <= 7 ? ' is-urgent' : ''
  return (
    <div className={`stub${tone}`}>
      <span className="stub-month">{monthAbbr(deadline)}</span>
      <span className="stub-day">{parseDay(deadline).getDate()}</span>
    </div>
  )
}

export function Countdown({ deadline }: { deadline: string | null }) {
  if (!deadline) return <span className="countdown">Sin fecha límite publicada</span>
  const days = daysUntil(deadline)
  const tone = days < 0 ? ' is-closed' : days <= 7 ? ' is-urgent' : ''
  return <span className={`countdown${tone}`}>{countdown(days)}</span>
}

export default function OpportunityCard({ opportunity, index }: { opportunity: Opportunity; index: number }) {
  const update = useUpdateOpportunity()
  const prize = prizeLabel(opportunity)
  const place = placeLabel(opportunity)

  return (
    <article className="card" style={{ '--i': Math.min(index, 12) } as CSSProperties}>
      <DateStub deadline={opportunity.deadline} />
      <div className="card-body">
        <div className="card-meta">
          <span className={`category cat-${opportunity.category}`}>{CATEGORY_LABELS[opportunity.category]}</span>
          {opportunity.review_status === 'nueva' && <span className="badge-new">Nueva</span>}
          {opportunity.importance >= 4 && <span className="badge-priority">Prioritaria</span>}
          <Countdown deadline={opportunity.deadline} />
        </div>
        <h2 className="card-title">
          <Link to={`/oportunidades/${opportunity.id}`}>{opportunity.title}</Link>
        </h2>
        <p className="card-summary">{opportunity.summary}</p>
        <div className="chips">
          {prize && <span className="chip strong">{prize}</span>}
          {opportunity.modality && <span className="chip">{MODALITY_LABELS[opportunity.modality]}</span>}
          {place && <span className="chip">{place}</span>}
          {opportunity.cost && <span className="chip">{opportunity.cost}</span>}
        </div>
        {opportunity.fit_projects.length > 0 && (
          <p className="card-fits">
            <span>Encaja con</span> {opportunity.fit_projects.map((fit) => fit.name).join(' · ')}
          </p>
        )}
      </div>
      <button
        className={`save${opportunity.is_saved ? ' is-on' : ''}`}
        aria-pressed={opportunity.is_saved}
        title={opportunity.is_saved ? 'Quitar de guardadas' : 'Guardar'}
        onClick={() => update.mutate({ id: opportunity.id, is_saved: !opportunity.is_saved })}
      >
        {opportunity.is_saved ? '★' : '☆'}
      </button>
    </article>
  )
}
