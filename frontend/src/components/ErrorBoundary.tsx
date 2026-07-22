import { Component, ErrorInfo, ReactNode } from 'react'

interface Props {
  children: ReactNode
}

interface State {
  error: Error | null
}

export default class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null }

  static getDerivedStateFromError(error: Error): State {
    return { error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('Simulation dashboard failed to render', error, info)
  }

  render() {
    if (!this.state.error) return this.props.children
    return (
      <main className="min-h-screen grid place-items-center bg-slate-100 p-4">
        <div className="max-w-xl rounded-xl bg-white p-8 shadow">
          <h1 className="text-xl font-bold text-red-700">Dashboard display error</h1>
          <p className="mt-2 text-slate-600">The simulation is still running. Reload the dashboard after checking this message.</p>
          <pre className="mt-4 overflow-auto rounded bg-red-50 p-3 text-sm text-red-800">{this.state.error.message}</pre>
          <button onClick={() => window.location.reload()} className="mt-4 rounded bg-blue-600 px-4 py-2 font-semibold text-white">Reload dashboard</button>
        </div>
      </main>
    )
  }
}
