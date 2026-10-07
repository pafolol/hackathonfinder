import { useEffect, useState, type FormEvent } from 'react'
import { useContextConfig, useSaveContext } from '../api/hooks'
import type { ContextInput, Preferences, Schedule } from '../api/types'
import ChipInput from '../components/ChipInput'
import { formatDateTime } from '../lib/dates'
import { CATEGORIES, CATEGORY_LABELS, MODALITIES, MODALITY_LABELS, WEEKDAYS } from '../lib/labels'

function toggle<T>(list: T[], item: T): T[] {
  return list.includes(item) ? list.filter((value) => value !== item) : [...list, item]
}

export default function Contexto() {
  const context = useContextConfig()
  const save = useSaveContext()
  const [form, setForm] = useState<ContextInput | null>(null)

  useEffect(() => {
    if (context.data && !form) {
      const { profile_text, preferences, schedule } = context.data
      setForm({ profile_text, preferences, schedule })
    }
  }, [context.data, form])

  if (context.isError) return <p className="form-error">{context.error.message}</p>
  if (!form) return <p className="muted">Cargando…</p>

  const prefs = form.preferences
  const schedule = form.schedule
  const setPrefs = (patch: Partial<Preferences>) => setForm({ ...form, preferences: { ...prefs, ...patch } })
  const setSchedule = (patch: Partial<Schedule>) => setForm({ ...form, schedule: { ...schedule, ...patch } })

  function submit(event: FormEvent) {
    event.preventDefault()
    if (form) save.mutate(form)
  }

  return (
    <form onSubmit={submit}>
      <header className="page-head">
        <div>
          <p className="eyebrow">Contexto de búsqueda</p>
          <h1>Contexto</h1>
          <p className="lead">Lo que el buscador sabe del área. Se envía en cada búsqueda junto con los proyectos activos.</p>
        </div>
        <div className="run">
          <button className="button primary" disabled={save.isPending}>
            {save.isPending ? 'Guardando…' : 'Guardar contexto'}
          </button>
          {save.isError && <span className="run-note is-error">{save.error.message}</span>}
          {save.isSuccess && !save.isPending && <span className="run-note">Guardado</span>}
        </div>
      </header>

      <div className="stack">
        <section className="panel form">
          <h2>Perfil del área</h2>
          <label>
            ¿Quiénes son y qué buscan?
            <textarea
              rows={8}
              value={form.profile_text}
              onChange={(e) => setForm({ ...form, profile_text: e.target.value })}
              placeholder="Ej. Área de emprendimiento universitario. Acompañamos a estudiantes de profesional y posgrado con proyectos en etapa temprana. Nos interesan oportunidades abiertas a estudiantes universitarios en México, en español o inglés…"
            />
          </label>
        </section>

        <section className="panel form">
          <h2>Preferencias de búsqueda</h2>
          <fieldset>
            <legend>Tipos de oportunidad</legend>
            <div className="checks">
              {CATEGORIES.map((category) => (
                <label className="check" key={category}>
                  <input type="checkbox" checked={prefs.types.includes(category)} onChange={() => setPrefs({ types: toggle(prefs.types, category) })} />
                  {CATEGORY_LABELS[category]}
                </label>
              ))}
            </div>
          </fieldset>
          <fieldset>
            <legend>Modalidades</legend>
            <div className="checks">
              {MODALITIES.map((modality) => (
                <label className="check" key={modality}>
                  <input type="checkbox" checked={prefs.modalities.includes(modality)} onChange={() => setPrefs({ modalities: toggle(prefs.modalities, modality) })} />
                  {MODALITY_LABELS[modality]}
                </label>
              ))}
            </div>
          </fieldset>
          <label>
            Regiones
            <ChipInput value={prefs.regions} onChange={(regions) => setPrefs({ regions })} placeholder="México, Latinoamérica…" />
          </label>
          <label>
            Temas y palabras clave
            <ChipInput value={prefs.keywords} onChange={(keywords) => setPrefs({ keywords })} placeholder="IA, salud, sostenibilidad…" />
          </label>
          <div className="form-pair">
            <label>
              Fuentes prioritarias
              <ChipInput value={prefs.priority_sources} onChange={(priority_sources) => setPrefs({ priority_sources })} placeholder="devpost.com, mlh.io…" />
            </label>
            <label>
              Fuentes excluidas
              <ChipInput value={prefs.excluded_sources} onChange={(excluded_sources) => setPrefs({ excluded_sources })} placeholder="Sitios que no quieres ver" />
            </label>
          </div>
          <div className="form-trio">
            <label>
              Premio mínimo (USD)
              <input
                type="number"
                min={0}
                value={prefs.min_prize_usd ?? ''}
                onChange={(e) => setPrefs({ min_prize_usd: e.target.value ? Number(e.target.value) : null })}
                placeholder="Sin mínimo"
              />
            </label>
            <label>
              Cierre dentro de (días)
              <input type="number" min={7} max={730} required value={prefs.deadline_window_days} onChange={(e) => setPrefs({ deadline_window_days: Number(e.target.value) })} />
            </label>
            <label>
              Máximo por búsqueda
              <input type="number" min={1} max={40} required value={prefs.max_results} onChange={(e) => setPrefs({ max_results: Number(e.target.value) })} />
            </label>
          </div>
        </section>

        <section className="panel form">
          <h2>Búsqueda programada</h2>
          <label className="check">
            <input type="checkbox" checked={schedule.enabled} onChange={(e) => setSchedule({ enabled: e.target.checked })} /> Buscar automáticamente
          </label>
          <div className="form-trio">
            <label>
              Frecuencia
              <select value={schedule.frequency} disabled={!schedule.enabled} onChange={(e) => setSchedule({ frequency: e.target.value as Schedule['frequency'] })}>
                <option value="daily">Todos los días</option>
                <option value="weekly">Cada semana</option>
              </select>
            </label>
            <label>
              Día
              <select value={schedule.weekday} disabled={!schedule.enabled || schedule.frequency === 'daily'} onChange={(e) => setSchedule({ weekday: Number(e.target.value) })}>
                {WEEKDAYS.map((day, index) => (
                  <option key={day} value={index}>
                    {day}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Hora (Guadalajara)
              <select value={schedule.hour} disabled={!schedule.enabled} onChange={(e) => setSchedule({ hour: Number(e.target.value) })}>
                {Array.from({ length: 24 }, (_, hour) => (
                  <option key={hour} value={hour}>
                    {String(hour).padStart(2, '0')}:00
                  </option>
                ))}
              </select>
            </label>
          </div>
          <p className="hint">
            {context.data?.next_run_at
              ? `Próxima búsqueda: ${formatDateTime(context.data.next_run_at)}.`
              : 'No hay ninguna búsqueda programada.'}{' '}
            Solo se ejecuta mientras el servidor esté encendido.
          </p>
        </section>
      </div>
    </form>
  )
}
