import { useState, type FormEvent } from 'react'
import { useCreateUser, useMe, useUpdateUser, useUsers } from '../api/hooks'
import type { Role, User } from '../api/types'

const EMPTY = { name: '', email: '', password: '', role: 'staff' as Role }

export default function Usuarios() {
  const me = useMe()
  const users = useUsers()
  const create = useCreateUser()
  const update = useUpdateUser()
  const [form, setForm] = useState(EMPTY)

  function submit(event: FormEvent) {
    event.preventDefault()
    create.mutate(form, { onSuccess: () => setForm(EMPTY) })
  }

  function resetPassword(user: User) {
    const password = window.prompt(`Nueva contraseña para ${user.name} (mínimo 8 caracteres)`)
    if (password) update.mutate({ id: user.id, password })
  }

  return (
    <>
      <header className="page-head">
        <div>
          <p className="eyebrow">Administración</p>
          <h1>Usuarios</h1>
        </div>
      </header>

      <div className="split">
        <section>
          {users.isError && <p className="form-error">{users.error.message}</p>}
          {update.isError && <p className="form-error">{update.error.message}</p>}
          <ul className="list">
            {users.data?.map((user) => {
              const isMe = user.id === me.data?.id
              return (
                <li key={user.id} className={`list-item${user.is_active ? '' : ' is-off'}`}>
                  <div>
                    <h3>
                      {user.name}
                      <span className={`chip${user.role === 'admin' ? ' strong' : ''}`}>{user.role === 'admin' ? 'Administrador' : 'Staff'}</span>
                      {!user.is_active && <span className="chip">Desactivado</span>}
                    </h3>
                    <p>{user.email}</p>
                  </div>
                  <div className="list-actions">
                    <button className="link-button" onClick={() => resetPassword(user)}>
                      Cambiar contraseña
                    </button>
                    {!isMe && (
                      <>
                        <button className="link-button" onClick={() => update.mutate({ id: user.id, role: user.role === 'admin' ? 'staff' : 'admin' })}>
                          {user.role === 'admin' ? 'Hacer staff' : 'Hacer administrador'}
                        </button>
                        <button className="link-button danger" onClick={() => update.mutate({ id: user.id, is_active: !user.is_active })}>
                          {user.is_active ? 'Desactivar' : 'Reactivar'}
                        </button>
                      </>
                    )}
                  </div>
                </li>
              )
            })}
          </ul>
        </section>

        <form className="panel form" onSubmit={submit}>
          <h2>Nueva cuenta</h2>
          <label>
            Nombre
            <input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          </label>
          <label>
            Correo
            <input type="email" required value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
          </label>
          <label>
            Contraseña inicial
            <input type="text" required minLength={8} value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
          </label>
          <label>
            Rol
            <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value as Role })}>
              <option value="staff">Staff</option>
              <option value="admin">Administrador</option>
            </select>
          </label>
          {create.isError && <p className="form-error">{create.error.message}</p>}
          <button className="button primary" disabled={create.isPending}>
            Crear cuenta
          </button>
        </form>
      </div>
    </>
  )
}
