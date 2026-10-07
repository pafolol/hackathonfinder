import { useQueryClient } from '@tanstack/react-query'
import { useEffect, useRef } from 'react'
import { useRuns, useStartRun } from '../api/hooks'
import { relativeTime } from '../lib/dates'

/** "Buscar ahora" plus the state of the latest search. Refreshes the feed when a search finishes. */
export default function RunButton() {
  const client = useQueryClient()
  const runs = useRuns()
  const start = useStartRun()
  const latest = runs.data?.[0]
  const running = latest?.status === 'en_curso' || start.isPending
  const wasRunning = useRef(false)

  useEffect(() => {
    if (wasRunning.current && !running) client.invalidateQueries({ queryKey: ['opportunities'] })
    wasRunning.current = running
  }, [running, client])

  let note = 'Aún no se ha hecho ninguna búsqueda'
  if (start.isError) note = start.error.message
  else if (running) note = 'Buscando en la web… puede tardar unos minutos'
  else if (latest?.status === 'error') note = `La última búsqueda falló ${relativeTime(latest.started_at)}`
  else if (latest) {
    note = `Última búsqueda ${relativeTime(latest.finished_at ?? latest.started_at)} · ${latest.items_new} nuevas`
  }

  return (
    <div className="run">
      <button className="button primary" disabled={running} onClick={() => start.mutate()}>
        {running && <span className="spinner" aria-hidden />}
        {running ? 'Buscando…' : 'Buscar ahora'}
      </button>
      <span className={`run-note${start.isError || (!running && latest?.status === 'error') ? ' is-error' : ''}`}>{note}</span>
    </div>
  )
}
