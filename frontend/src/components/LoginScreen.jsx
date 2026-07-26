import { useState } from "react";
import { Brain, Lock, User, Terminal } from "lucide-react";
import toast from "react-hot-toast";

export default function LoginScreen({ onLoginSuccess }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!username.trim() || !password.trim()) {
      toast.error("Please enter both username and password.");
      return;
    }

    setIsLoading(true);
    try {
      const formData = new URLSearchParams();
      formData.append("username", username);
      formData.append("password", password);

      const res = await fetch("/token", {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: formData.toString(),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || "Authentication failed. Invalid username or password.");
      }

      const data = await res.json();
      localStorage.setItem("token", data.access_token);
      toast.success("Welcome back to NeuraSearch!");
      onLoginSuccess();
    } catch (err) {
      toast.error(err.message || "Could not connect to backend server.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[var(--bg-primary)] text-[var(--text-primary)] flex items-center justify-center relative overflow-hidden font-inter transition-colors duration-300">
      {/* Background Lavender & White Atmospheric Glows */}
      <div className="absolute top-[-20%] left-[-20%] w-[65%] h-[65%] rounded-full bg-lavender-400/15 blur-[160px] pointer-events-none" />
      <div className="absolute bottom-[-20%] right-[-20%] w-[65%] h-[65%] rounded-full bg-lavender-300/15 blur-[160px] pointer-events-none" />
      <div className="absolute top-[40%] left-[35%] w-[40%] h-[40%] rounded-full bg-white/10 blur-[140px] pointer-events-none" />

      {/* Login Card */}
      <div className="w-full max-w-md p-8 rounded-2xl glass border border-lavender-300/20 shadow-2xl shadow-lavender-500/10 relative z-10 animate-slide-up mx-4 backdrop-blur-2xl">
        {/* Logo */}
        <div className="flex flex-col items-center mb-8">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-lavender-400 via-white to-lavender-300 p-0.5 shadow-xl shadow-lavender-400/25 flex items-center justify-center mb-4">
            <div className="w-full h-full bg-[var(--bg-secondary)] rounded-[14px] flex items-center justify-center">
              <Brain className="w-8 h-8 text-lavender-300 animate-pulse" />
            </div>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-[var(--text-primary)] flex items-center gap-2">
            NeuraSearch <span className="text-[10px] bg-lavender-400/20 border border-lavender-300/40 text-lavender-300 px-2 py-0.5 rounded-full uppercase font-semibold">v2.1</span>
          </h1>
          <p className="text-xs text-[var(--text-secondary)] mt-1">Lavender & White AI Research Workspace</p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider mb-2">
              Username
            </label>
            <div className="relative">
              <User className="absolute left-3.5 top-3 w-4 h-4 text-lavender-300/70" />
              <input
                type="text"
                placeholder="Enter username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full bg-[var(--bg-secondary)] border border-lavender-300/20 rounded-xl py-2.5 pl-10 pr-4 text-sm text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:border-lavender-400 focus:ring-1 focus:ring-lavender-400 transition-all"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider mb-2">
              Password
            </label>
            <div className="relative">
              <Lock className="absolute left-3.5 top-3 w-4 h-4 text-lavender-300/70" />
              <input
                type="password"
                placeholder="Enter password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-[var(--bg-secondary)] border border-lavender-300/20 rounded-xl py-2.5 pl-10 pr-4 text-sm text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:border-lavender-400 focus:ring-1 focus:ring-lavender-400 transition-all"
                required
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full mt-2 py-3 rounded-xl bg-gradient-to-r from-lavender-500 via-lavender-400 to-white text-white font-semibold text-sm shadow-lg shadow-lavender-500/25 hover:shadow-lavender-400/40 hover:opacity-95 transition-all flex items-center justify-center gap-2 disabled:opacity-50 active:scale-[0.99]"
          >
            {isLoading ? (
              <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              <>
                <Terminal className="w-4 h-4 text-white" />
                <span>Initialize Session</span>
              </>
            )}
          </button>
        </form>

        {/* Demo Hint */}
        <div className="mt-6 pt-6 border-t border-lavender-300/10 text-center">
          <p className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider mb-1">Local Seeding Details</p>
          <code className="text-xs bg-lavender-400/10 border border-lavender-300/20 text-lavender-300 px-2.5 py-1 rounded-lg font-mono">
            admin / password123
          </code>
        </div>
      </div>
    </div>
  );
}
