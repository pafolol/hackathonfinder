import { useRuns } from '../api/hooks'
import type { Run } from '../api/types'
import RunButton from '../components/RunButton'
import { formatDateTime } from '../lib/dates'

const STATUS_LABELS: Record<Run['status'], string> = { en_curso: 'En curso', ok: 'Completada', error: 'Falló' }

function duration(run: Run): string {
  if (!run.finished_at) return '—'
  const seconds = Math.round((new Date(run.finished_at).getTime() - new Date(run.started_at).getTime()) / 1000)
  return seconds < 60 ? `${seconds} s` : `${Math.floor(seconds / 60)} min ${seconds % 60} s`
}

export default function Busquedas() {
  const runs = useRuns()

  return (
    <>
      <header className="page-head">
        <div>
          <p className="eyebrow">Historial</p>
          <h1>Búsquedas</h1>
        </div>
        <RunButton />
      </header>

      {runs.isError && <p className="form-error">{runs.error.message}</p>}
      {runs.data?.length === 0 && (
        <div className="empty">
          <h2>Sin búsquedas todavía</h2>
          <p>Presiona «Buscar ahora» o programa una búsqueda en Contexto.</p>
        </div>
      )}
      {runs.data && runs.data.length > 0 && (
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>Inicio</th>
                <th>Origen</th>
                <th>Estado</th>
                <th className="num">Encontradas</th>
                <th className="num">Nuevas</th>
                <th className="num">Duración</th>
                <th className="num">Tokens</th>
              </tr>
            </thead>
            <tbody>
              {runs.data.map((run) => (
                <tr key={run.id}>
                  <td>{formatDateTime(run.started_at)}</td>
                  <td>{run.trigger === 'manual' ? 'Manual' : 'Programada'}</td>
                  <td>
                    <span className={`status status-${run.status}`}>{STATUS_LABELS[run.status]}</span>
                    {run.error && <div className="table-error">{run.error}</div>}
                  </td>
                  <td className="num">{run.status === 'ok' ? run.items_found : '—'}</td>
                  <td className="num">{run.status === 'ok' ? run.items_new : '—'}</td>
                  <td className="num">{duration(run)}</td>
                  <td className="num">{run.total_tokens?.toLocaleString('es-MX') ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  )
}
