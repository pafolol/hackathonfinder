import { useState, type FormEvent } from 'react'
import { useDeleteProject, useProjects, useSaveProject } from '../api/hooks'
import type { Project, ProjectInput } from '../api/types'
import ChipInput from '../components/ChipInput'

const EMPTY: ProjectInput = {
  name: '',
  description: '',
  stage: null,
  sector: null,
  technologies: [],
  team: null,
  url: null,
  is_active: true,
}
const STAGES = ['Idea', 'Prototipo', 'MVP', 'Primeras ventas', 'En crecimiento']

export default function Proyectos() {
  const projects = useProjects()
  const save = useSaveProject()
  const remove = useDeleteProject()
  const [editingId, setEditingId] = useState<string | undefined>()
  const [form, setForm] = useState<ProjectInput>(EMPTY)

  const set = <K extends keyof ProjectInput>(key: K, value: ProjectInput[K]) => setForm((f) => ({ ...f, [key]: value }))

  function edit(project: Project) {
    const { id, created_at: _c, updated_at: _u, ...input } = project
    setEditingId(id)
    setForm(input)
    save.reset()
  }

  function reset() {
    setEditingId(undefined)
    setForm(EMPTY)
  }

  function submit(event: FormEvent) {
    event.preventDefault()
    save.mutate({ id: editingId, body: form }, { onSuccess: reset })
  }

  function onDelete(project: Project) {
    if (!window.confirm(`¿Eliminar «${project.name}»? También se quita de las oportunidades con las que encajaba.`)) return
    remove.mutate(project.id, { onSuccess: () => editingId === project.id && reset() })
  }

  return (
    <>
      <header className="page-head">
        <div>
          <p className="eyebrow">Contexto de búsqueda</p>
          <h1>Proyectos</h1>
          <p className="lead">Cada búsqueda cruza las oportunidades con estos proyectos. Entre mejor la descripción, mejor el cruce.</p>
        </div>
      </header>

      <div className="split">
        <section>
          {projects.isPending && <p className="muted">Cargando…</p>}
          {projects.isError && <p className="form-error">{projects.error.message}</p>}
          {projects.data?.length === 0 && (
            <div className="empty">
              <h2>Sin proyectos todavía</h2>
              <p>Agrega el primero con el formulario.</p>
            </div>
          )}
          <ul className="list">
            {projects.data?.map((project) => (
              <li key={project.id} className={`list-item${project.is_active ? '' : ' is-off'}${editingId === project.id ? ' is-editing' : ''}`}>
                <div>
                  <h3>
                    {project.name}
                    {!project.is_active && <span className="chip">Inactivo</span>}
                  </h3>
                  <p>{project.description || <em>Sin descripción</em>}</p>
                  <div className="chips">
                    {project.stage && <span className="chip strong">{project.stage}</span>}
                    {project.sector && <span className="chip">{project.sector}</span>}
                    {project.technologies.map((tech) => (
                      <span className="chip" key={tech}>
                        {tech}
                      </span>
                    ))}
                  </div>
                </div>
                <div className="list-actions">
                  <button className="link-button" onClick={() => edit(project)}>
                    Editar
                  </button>
                  <button className="link-button danger" onClick={() => onDelete(project)}>
                    Eliminar
                  </button>
                </div>
              </li>
            ))}
          </ul>
        </section>

        <form className="panel form" onSubmit={submit}>
          <h2>{editingId ? 'Editar proyecto' : 'Nuevo proyecto'}</h2>
          <label>
            Nombre
            <input required maxLength={200} value={form.name} onChange={(e) => set('name', e.target.value)} />
          </label>
          <label>
            Descripción
            <textarea rows={4} value={form.description} onChange={(e) => set('description', e.target.value)} placeholder="Qué problema resuelve, para quién y qué tiene construido." />
          </label>
          <div className="form-pair">
            <label>
              Etapa
              <select value={form.stage ?? ''} onChange={(e) => set('stage', e.target.value || null)}>
                <option value="">Sin definir</option>
                {STAGES.map((stage) => (
                  <option key={stage}>{stage}</option>
                ))}
              </select>
            </label>
            <label>
              Sector
              <input value={form.sector ?? ''} onChange={(e) => set('sector', e.target.value || null)} placeholder="Salud, fintech, agro…" />
            </label>
          </div>
          <label>
            Tecnologías
            <ChipInput value={form.technologies} onChange={(v) => set('technologies', v)} placeholder="Escribe y presiona Enter" />
          </label>
          <label>
            Equipo
            <input value={form.team ?? ''} onChange={(e) => set('team', e.target.value || null)} placeholder="3 estudiantes de ITC e IMT" />
          </label>
          <label>
            Sitio o repositorio
            <input type="url" value={form.url ?? ''} onChange={(e) => set('url', e.target.value || null)} placeholder="https://" />
          </label>
          <label className="check">
            <input type="checkbox" checked={form.is_active} onChange={(e) => set('is_active', e.target.checked)} /> Incluir en las búsquedas
          </label>
          {save.isError && <p className="form-error">{save.error.message}</p>}
          <div className="form-actions">
            <button className="button primary" disabled={save.isPending}>
              {editingId ? 'Guardar cambios' : 'Agregar proyecto'}
            </button>
            {editingId && (
              <button type="button" className="button quiet" onClick={reset}>
                Cancelar
              </button>
            )}
          </div>
        </form>
      </div>
    </>
  )
}
