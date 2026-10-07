import { useDeferredValue, useState } from 'react'
import { Link } from 'react-router-dom'
import { useOpportunities, useProjects } from '../api/hooks'
import type { Category, OpportunityFilters, ReviewStatus } from '../api/types'
import OpportunityCard from '../components/OpportunityCard'
import RunButton from '../components/RunButton'
import { CATEGORIES, CATEGORY_LABELS } from '../lib/labels'

export default function Oportunidades() {
  const [category, setCategory] = useState<Category | undefined>()
  const [status, setStatus] = useState<ReviewStatus | ''>('')
  const [projectId, setProjectId] = useState('')
  const [saved, setSaved] = useState(false)
  const [includeClosed, setIncludeClosed] = useState(false)
  const [sort, setSort] = useState<'deadline' | 'discovered'>('deadline')
  const [query, setQuery] = useState('')
  const q = useDeferredValue(query.trim())

  const filters: OpportunityFilters = {
    category,
    review_status: status || undefined,
    project_id: projectId || undefined,
    saved: saved || undefined,
    include_closed: includeClosed || undefined,
    sort,
    q: q || undefined,
  }
  const opportunities = useOpportunities(filters)
  const projects = useProjects()
  const filtered = Boolean(category || status || projectId || saved || q)
  const items = opportunities.data ?? []

  return (
    <>
      <header className="page-head">
        <div>
          <p className="eyebrow">Tablero</p>
          <h1>Oportunidades</h1>
        </div>
        <RunButton />
      </header>

      <div className="filters">
        <div className="pills" role="group" aria-label="Tipo">
          <button className={!category ? 'is-on' : ''} onClick={() => setCategory(undefined)}>
            Todas
          </button>
          {CATEGORIES.filter((c) => c !== 'otro').map((c) => (
            <button key={c} className={category === c ? 'is-on' : ''} onClick={() => setCategory(category === c ? undefined : c)}>
              {CATEGORY_LABELS[c]}
            </button>
          ))}
        </div>
        <div className="filter-row">
          <input className="search" type="search" placeholder="Buscar por título, fuente o ciudad" value={query} onChange={(e) => setQuery(e.target.value)} />
          <select value={projectId} onChange={(e) => setProjectId(e.target.value)} aria-label="Proyecto">
            <option value="">Todos los proyectos</option>
            {projects.data?.map((project) => (
              <option key={project.id} value={project.id}>
                {project.name}
              </option>
            ))}
          </select>
          <select value={status} onChange={(e) => setStatus(e.target.value as ReviewStatus | '')} aria-label="Estado">
            <option value="">Nuevas y revisadas</option>
            <option value="nueva">Solo nuevas</option>
            <option value="revisada">Solo revisadas</option>
            <option value="descartada">Descartadas</option>
          </select>
          <select value={sort} onChange={(e) => setSort(e.target.value as 'deadline' | 'discovered')} aria-label="Orden">
            <option value="deadline">Cierra primero</option>
            <option value="discovered">Más recientes</option>
          </select>
          <label className="check">
            <input type="checkbox" checked={saved} onChange={(e) => setSaved(e.target.checked)} /> Guardadas
          </label>
          <label className="check">
            <input type="checkbox" checked={includeClosed} onChange={(e) => setIncludeClosed(e.target.checked)} /> Incluir cerradas
          </label>
        </div>
      </div>

      {opportunities.isError && <p className="form-error">{opportunities.error.message}</p>}
      {opportunities.isPending && <p className="muted">Cargando oportunidades…</p>}

      {opportunities.isSuccess && items.length === 0 && (
        <div className="empty">
          {filtered ? (
            <>
              <h2>Nada coincide con estos filtros</h2>
              <p>Prueba quitando alguno o incluyendo las cerradas.</p>
            </>
          ) : (
            <>
              <h2>Todavía no hay oportunidades</h2>
              <p>
                Registra los <Link to="/proyectos">proyectos</Link> del área, describe el <Link to="/contexto">contexto</Link> y presiona
                «Buscar ahora».
              </p>
            </>
          )}
        </div>
      )}

      {items.length > 0 && (
        <>
          <p className="count">
            {items.length} {items.length === 1 ? 'oportunidad' : 'oportunidades'}
          </p>
          <div className="cards">
            {items.map((opportunity, index) => (
              <OpportunityCard key={opportunity.id} opportunity={opportunity} index={index} />
            ))}
          </div>
        </>
      )}
    </>
  )
}
