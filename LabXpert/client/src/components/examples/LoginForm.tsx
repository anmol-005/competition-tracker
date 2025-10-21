import LoginForm from '../LoginForm'

export default function LoginFormExample() {
  const handleLogin = (email: string, password: string) => {
    console.log('Login attempt:', { email, password })
  }

  return <LoginForm onLogin={handleLogin} />
}