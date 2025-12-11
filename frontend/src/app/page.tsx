import Link from 'next/link';

export default function Home() {
  return (
    <main className="min-h-screen bg-black relative">
      {/* Background gradient overlay */}
      <div className="absolute inset-0 bg-gradient-to-b from-black/60 via-black/40 to-black" />

      {/* Hero background pattern */}
      <div className="absolute inset-0 opacity-20">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-red-900/20 via-transparent to-transparent" />
      </div>

      {/* Header */}
      <header className="relative z-10 flex items-center justify-between px-8 py-6">
        <div className="text-[#E50914] font-bold text-3xl tracking-tight">
          WSOPTV
        </div>
        <Link
          href="/login"
          className="bg-[#E50914] hover:bg-[#F40612] text-white px-4 py-1.5 rounded text-sm font-medium transition-colors"
        >
          Sign In
        </Link>
      </header>

      {/* Hero Content */}
      <div className="relative z-10 flex flex-col items-center justify-center min-h-[calc(100vh-200px)] px-4 text-center">
        <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-white mb-4 max-w-4xl leading-tight">
          Private Poker VOD
          <br />
          <span className="text-[#E50914]">Streaming Platform</span>
        </h1>
        <p className="text-lg md:text-xl text-gray-300 mb-8 max-w-2xl">
          Watch exclusive poker tournaments, cash games, and strategy tutorials.
          Premium content for serious players.
        </p>

        <div className="flex flex-col sm:flex-row gap-4">
          <Link
            href="/register"
            className="bg-[#E50914] hover:bg-[#F40612] text-white px-8 py-3 rounded text-lg font-semibold transition-colors flex items-center justify-center gap-2"
          >
            <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
              <path d="M8 5v14l11-7z" />
            </svg>
            Get Started
          </Link>
          <Link
            href="/login"
            className="bg-gray-600/80 hover:bg-gray-600 text-white px-8 py-3 rounded text-lg font-semibold transition-colors border border-gray-500"
          >
            Sign In
          </Link>
        </div>

        <p className="text-gray-500 text-sm mt-8">
          Members only. Admin approval required.
        </p>
      </div>

      {/* Features Section */}
      <div className="relative z-10 px-8 pb-16">
        <div className="max-w-6xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="bg-[#141414] rounded-lg p-6 border border-[#333]">
              <div className="w-12 h-12 bg-[#E50914]/20 rounded-lg flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-[#E50914]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
              </div>
              <h3 className="text-white font-semibold text-lg mb-2">Premium Content</h3>
              <p className="text-gray-400 text-sm">
                Access exclusive tournament recordings and high-stakes cash game sessions.
              </p>
            </div>

            <div className="bg-[#141414] rounded-lg p-6 border border-[#333]">
              <div className="w-12 h-12 bg-[#E50914]/20 rounded-lg flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-[#E50914]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              </div>
              <h3 className="text-white font-semibold text-lg mb-2">Private & Secure</h3>
              <p className="text-gray-400 text-sm">
                Members-only platform with admin approval for maximum privacy.
              </p>
            </div>

            <div className="bg-[#141414] rounded-lg p-6 border border-[#333]">
              <div className="w-12 h-12 bg-[#E50914]/20 rounded-lg flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-[#E50914]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
              </div>
              <h3 className="text-white font-semibold text-lg mb-2">Any Device</h3>
              <p className="text-gray-400 text-sm">
                Stream on desktop, tablet, or mobile. Watch anywhere, anytime.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="relative z-10 border-t border-[#333] py-8 px-8">
        <div className="max-w-6xl mx-auto text-center text-gray-500 text-sm">
          <p>&copy; 2024 WSOPTV. Private Poker VOD Streaming Platform.</p>
        </div>
      </footer>
    </main>
  );
}
