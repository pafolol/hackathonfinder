import { useState, type FormEvent } from 'react'
import { useLogin } from '../api/hooks'
import Brand from '../components/Brand'

export default function Login() {
  const login = useLogin()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  function submit(event: FormEvent) {
    event.preventDefault()
    login.mutate({ email, password })
  }

  return (
    <div className="login">
      <form className="login-form" onSubmit={submit}>
        <Brand />
        <h2>Iniciar sesión</h2>
        <label>
          Correo
          <input type="email" autoComplete="username" required value={email} onChange={(e) => setEmail(e.target.value)} />
        </label>
        <label>
          Contraseña
          <input type="password" autoComplete="current-password" required value={password} onChange={(e) => setPassword(e.target.value)} />
        </label>
        {login.isError && <p className="form-error">{login.error.message}</p>}
        <button className="button primary" disabled={login.isPending}>
          {login.isPending ? 'Entrando…' : 'Entrar'}
        </button>
        <p className="hint">¿No tienes cuenta? Pídela a un administrador del área.</p>
      </form>
    </div>
  )
}
