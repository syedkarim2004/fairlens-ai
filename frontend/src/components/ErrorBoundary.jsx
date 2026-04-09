import React from 'react'

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, errorInfo) {
    console.error('[FairLens Error]', error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-[60vh] flex flex-col items-center justify-center p-12 text-center bg-red-50/30 rounded-[3rem] border border-red-100">
          <div className="text-6xl mb-6">🏜️</div>
          <h2 className="text-3xl font-black text-dark mb-4">Something went wrong</h2>
          <p className="text-gray-500 font-medium mb-8 max-w-md">
            Our fairness engine encountered an unexpected rendering error. This usually happens when data is misaligned with the visual components.
          </p>
          <div className="bg-white p-4 rounded-xl border border-red-100 text-red-500 font-mono text-xs mb-8 max-w-full overflow-auto">
            {this.state.error?.toString()}
          </div>
          <button
            onClick={() => window.location.reload()}
            className="bg-dark text-white px-10 py-4 rounded-2xl font-black hover:bg-black transition-all shadow-xl shadow-dark/10"
          >
            Reload Platform
          </button>
        </div>
      )
    }

    return this.props.children
  }
}

export default ErrorBoundary
