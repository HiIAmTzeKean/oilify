import React from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { toast } from 'react-toastify'
import LoginForm from '../components/LoginForm'
import { useAuth } from '../contexts/AuthContext'

const Login: React.FC = () => {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const { login, handleOAuthCallback: authHandleOAuth } = useAuth()
  const [oauthHandled, setOauthHandled] = React.useState(false)

  React.useEffect(() => {
    const token = searchParams.get('token')
    if (token && !oauthHandled) {
      // Handle OAuth callback
      setOauthHandled(true)
      handleOAuthCallback(token)
    }
  }, [searchParams, oauthHandled])

  async function handleOAuthCallback(token: string) {
    try {
      await authHandleOAuth(token)
      toast.success('Login successful')
      navigate('/')
    } catch (err) {
      toast.error('Failed to get user info')
      localStorage.removeItem('oilify_access_token')
    }
  }

  async function submitLogin(username: string, password: string) {
    try {
      await login(username, password)
      toast.success('Login is successful')
      navigate('/')
    } catch (err) {
      toast.error((err as Error).message || 'Login failed')
    }
  }

  return (
    <div className="max-w-md mx-auto mt-12">
      <h2 className="text-2xl font-semibold mb-4">Sign in to Oilify</h2>
      <div className="p-6 bg-slate-50 dark:bg-slate-900 rounded-md shadow">
        <LoginForm onSubmit={submitLogin} />
      </div>
    </div>
  )
}

export default Login
