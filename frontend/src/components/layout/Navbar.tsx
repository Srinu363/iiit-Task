/** Navigation bar component — IQ Detect Premium White Analytics SaaS. */
import { Link, useLocation } from "react-router-dom";

export default function Navbar() {
  const location = useLocation();

  const isCurrent = (path: string) => location.pathname === path;

  const linkClass = (path: string) =>
    `relative px-3.5 py-1.5 rounded-xl text-xs sm:text-sm font-semibold transition-all duration-150 focus:outline-none focus-visible:ring-2 focus-visible:ring-[#5145FF]/40 ${
      isCurrent(path)
        ? "bg-[#EEF0FF] text-[#5145FF] border border-[#D7DCFF] shadow-2xs"
        : "text-slate-600 hover:text-gray-900 hover:bg-slate-100/70 border border-transparent"
    }`;

  return (
    <nav className="sticky top-0 z-50 border-b border-[#E2E8F0] bg-white/90 backdrop-blur-md shadow-[0_1px_3px_0_rgba(17,24,39,0.02)]">
      <div className="dashboard-content flex h-16 items-center justify-between px-4 sm:px-6 lg:px-10">
        {/* Brand Shield & Logo */}
        <Link
          to="/"
          className="flex items-center gap-3 group focus:outline-none focus-visible:ring-2 focus-visible:ring-[#5145FF] rounded-xl"
        >
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-[#5145FF] to-[#4335E6] text-white shadow-sm shadow-[#5145FF]/25 transition-transform duration-200 group-hover:scale-105">
            {/* Shield Vision Icon */}
            <svg className="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-lg font-extrabold text-gray-900 tracking-tight">
              IQ<span className="text-[#5145FF]">Detect</span>
            </span>
            <span className="inline-flex items-center gap-1 rounded-full bg-[#EEF0FF] px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-[#5145FF] border border-[#D7DCFF]">
              <span className="h-1.5 w-1.5 rounded-full bg-[#10B981]" />
              AI Vision
            </span>
          </div>
        </Link>

        {/* Navigation Actions */}
        <div className="flex items-center gap-1.5 sm:gap-2">
          <Link to="/" className={linkClass("/")}>
            Analyze
          </Link>
          <Link to="/history" className={linkClass("/history")}>
            History
          </Link>
        </div>
      </div>
    </nav>
  );
}
