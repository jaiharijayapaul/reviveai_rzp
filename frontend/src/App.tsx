import { NavLink, Outlet } from "react-router-dom";
import { Toaster } from "react-hot-toast";

const nav = [
  { to: "/", label: "Dashboard", end: true },
  { to: "/transactions", label: "Transactions" },
  { to: "/agent", label: "AI Agent" },
  { to: "/demo", label: "Demo" },
  { to: "/policy", label: "Policy Co-Pilot" },
];

export default function App() {
  return (
    <div className="min-h-screen flex">
      <aside className="w-60 shrink-0 border-r border-slate-800 p-5 flex flex-col gap-6">
        <div>
          <div className="text-lg font-semibold tracking-tight text-white">ReviveAI</div>
          <div className="text-xs text-slate-500 mt-0.5">Turn failed payments into recovered revenue.</div>
        </div>
        <nav className="flex flex-col gap-1">
          {nav.map((n) => (
            <NavLink
              key={n.to}
              to={n.to}
              end={n.end}
              className={({ isActive }) =>
                `px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isActive ? "bg-brand-600/20 text-brand-500" : "text-slate-400 hover:text-slate-100 hover:bg-slate-900"
                }`
              }
            >
              {n.label}
            </NavLink>
          ))}
        </nav>
        <div className="mt-auto text-[11px] text-slate-600">
          Razorpay TEST MODE · AI Buildathon 2026
        </div>
      </aside>
      <main className="flex-1 p-8 max-w-6xl mx-auto w-full">
        <Outlet />
      </main>
      <Toaster position="top-right" toastOptions={{ style: { background: '#1e293b', color: '#f8fafc', border: '1px solid #334155' } }} />
    </div>
  );
}
