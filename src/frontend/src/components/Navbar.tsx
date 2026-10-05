"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Layers, BarChart3, Database } from "lucide-react";

export default function Navbar() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-50 w-full border-b border-gray-800 bg-[#090d16]/90 backdrop-blur-md">
      <div className="mx-auto flex max-w-7xl items-center justify-end px-6 py-4">
        {/* Navigation links & workflow step indicator */}
        <nav className="flex items-center space-x-1 sm:space-x-6 text-sm font-medium">
          <Link
            href="/"
            className={`px-3 py-1.5 rounded-md transition-colors ${
              pathname === "/" ? "bg-slate-800 text-cyan-400 font-semibold" : "text-gray-400 hover:text-white"
            }`}
          >
            Overview
          </Link>

          <Link
            href="/define"
            className={`px-3 py-1.5 rounded-md flex items-center space-x-1.5 transition-colors ${
              pathname === "/define" ? "bg-slate-800 text-cyan-400 font-semibold" : "text-gray-400 hover:text-white"
            }`}
          >
            <Layers className="h-4 w-4" />
            <span>1. Define Machine</span>
          </Link>

          <Link
            href="/configure"
            className={`px-3 py-1.5 rounded-md flex items-center space-x-1.5 transition-colors ${
              pathname?.startsWith("/configure") ? "bg-slate-800 text-cyan-400 font-semibold" : "text-gray-400 hover:text-white"
            }`}
          >
            <Database className="h-4 w-4" />
            <span>2. Configure</span>
          </Link>

          <span className="text-gray-400 flex items-center space-x-1.5 px-3 py-1.5">
            <BarChart3 className="h-4 w-4 text-gray-500" />
            <span>3. Results</span>
          </span>
        </nav>
      </div>
    </header>
  );
}
