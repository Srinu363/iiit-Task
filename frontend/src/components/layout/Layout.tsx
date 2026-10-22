/** Main layout wrapper — IQ Detect Dashboard. */
import { Outlet } from "react-router-dom";
import Navbar from "./Navbar";

export default function Layout() {
  return (
    <div className="flex min-h-screen flex-col bg-[#F7F9FC]">
      <Navbar />
      <main className="flex-1 w-full min-w-0">
        <div className="dashboard-content px-4 py-6 sm:py-8 sm:px-6 lg:px-10">
          <Outlet />
        </div>
      </main>
      <footer className="border-t border-[#E2E8F0] bg-white/80 backdrop-blur-sm py-5 mt-auto">
        <div className="dashboard-content px-4 sm:px-6 lg:px-10 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-500">
          <div className="flex items-center gap-2 font-medium text-slate-700">
            <span className="flex h-2 w-2 rounded-full bg-[#16A34A]" />
            IQDetect — AI Image Quality &amp; Defect Assessment
          </div>
          <p className="text-slate-400">
            Local Computer Vision &amp; Calibrated ML • Zero External APIs
          </p>
        </div>
      </footer>
    </div>
  );
}
