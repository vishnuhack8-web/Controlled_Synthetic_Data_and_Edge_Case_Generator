"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import whatsNewData from "@/data/whats_new.json";
import {
  Sparkles,
  ArrowRight,
  ShieldCheck,
  Zap,
  Sliders,
  CheckCircle2,
  FileSpreadsheet,
  Cpu,
  Layers,
  HelpCircle,
  Github,
  BookOpen
} from "lucide-react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function LandingPage() {
  const [configSpec, setConfigSpec] = useState<any>(null);

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/config-spec`)
      .then((res) => res.json())
      .then((data) => setConfigSpec(data))
      .catch((err) => console.error("Error fetching config spec:", err));
  }, []);

  return (
    <div className="min-h-screen bg-[#090d16] text-gray-100 flex flex-col font-sans">
      <Navbar />

      {/* a) HERO SECTION */}
      <section className="relative py-20 px-6 max-w-7xl mx-auto w-full text-center flex flex-col items-center">
        <div className="inline-flex items-center space-x-2 px-3 py-1.5 rounded-full bg-cyan-950/80 border border-cyan-800 text-cyan-400 text-xs font-semibold mb-6">
          <Sparkles className="h-3.5 w-3.5 text-cyan-400" />
          <span>Local Offline AI Data & Anomaly Generator</span>
        </div>

        <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight text-white max-w-4xl leading-tight">
          AI Synthetic Data & <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-500">Edge-Case Generation</span> Platform
        </h1>

        <p className="mt-6 text-lg text-gray-400 max-w-2xl leading-relaxed">
          Create realistic, privacy-preserving synthetic datasets with automatically produced rare edge cases, failure scenarios, and statistical validation for ML models and software testing.
        </p>

        <div className="mt-10 flex flex-wrap gap-4 justify-center">
          <Link
            href="/define"
            className="inline-flex items-center space-x-2 px-8 py-4 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-gray-950 font-bold shadow-lg shadow-cyan-500/25 transition-all text-base"
          >
            <span>Start configuring</span>
            <ArrowRight className="h-5 w-5" />
          </Link>
        </div>
      </section>

      {/* b) WHAT THIS PLATFORM DOES (4 CARDS) */}
      <section className="py-12 px-6 max-w-7xl mx-auto w-full">
        <h2 className="text-2xl font-bold text-center text-white mb-10">What This Platform Does</h2>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-gray-900/60 border border-gray-800 p-6 rounded-2xl flex flex-col hover:border-cyan-500/40 transition-colors">
            <div className="p-3 bg-cyan-950/60 rounded-xl text-cyan-400 w-fit mb-4">
              <Sliders className="h-6 w-6" />
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">Controlled Generation</h3>
            <p className="text-sm text-gray-400 leading-relaxed">
              Deterministic, schema-driven dataset creation matching user distributions, parameter ranges, and business rules.
            </p>
          </div>

          <div className="bg-gray-900/60 border border-gray-800 p-6 rounded-2xl flex flex-col hover:border-cyan-500/40 transition-colors">
            <div className="p-3 bg-red-950/60 rounded-xl text-red-400 w-fit mb-4">
              <Zap className="h-6 w-6" />
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">Edge-Case Engine</h3>
            <p className="text-sm text-gray-400 leading-relaxed">
              Inject rare events, boundary values, equipment failure modes, corruptions, and network outages into datasets.
            </p>
          </div>

          <div className="bg-gray-900/60 border border-gray-800 p-6 rounded-2xl flex flex-col hover:border-cyan-500/40 transition-colors">
            <div className="p-3 bg-emerald-950/60 rounded-xl text-emerald-400 w-fit mb-4">
              <ShieldCheck className="h-6 w-6" />
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">Privacy Safe</h3>
            <p className="text-sm text-gray-400 leading-relaxed">
              Zero real records copied. Performs nearest-neighbor distance and PII pattern scans with fake text tokens.
            </p>
          </div>

          <div className="bg-gray-900/60 border border-gray-800 p-6 rounded-2xl flex flex-col hover:border-cyan-500/40 transition-colors">
            <div className="p-3 bg-purple-950/60 rounded-xl text-purple-400 w-fit mb-4">
              <CheckCircle2 className="h-6 w-6" />
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">Quality Checks</h3>
            <p className="text-sm text-gray-400 leading-relaxed">
              Statistical KS goodness-of-fit testing, range compliance, and predictive ML anomaly detection evaluation.
            </p>
          </div>
        </div>
      </section>

      {/* c) WHAT'S NEW (CHANGELOG) */}
      <section className="py-12 px-6 max-w-7xl mx-auto w-full">
        <div className="bg-gray-900/80 border border-gray-800 rounded-3xl p-8">
          <div className="flex items-center space-x-3 mb-6">
            <Sparkles className="h-5 w-5 text-cyan-400" />
            <h2 className="text-xl font-bold text-white">What's New</h2>
          </div>

          <div className="space-y-4">
            {whatsNewData.map((item) => (
              <div key={item.id} className="flex flex-col sm:flex-row sm:items-center justify-between p-4 rounded-xl bg-gray-950/60 border border-gray-800/80 gap-3">
                <div className="flex items-start space-x-3">
                  <span
                    className={`mt-0.5 px-2.5 py-0.5 text-xs font-bold rounded-full ${
                      item.badge === "New" ? "bg-cyan-500/20 text-cyan-400 border border-cyan-500/40" : "bg-purple-500/20 text-purple-400 border border-purple-500/40"
                    }`}
                  >
                    {item.badge}
                  </span>
                  <div>
                    <h3 className="text-sm font-semibold text-white">{item.title}</h3>
                    <p className="text-xs text-gray-400 mt-1">{item.description}</p>
                  </div>
                </div>
                <span className="text-xs text-gray-500 font-mono shrink-0">{item.date}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* d) TOTAL INPUTS YOU CAN PROVIDE */}
      <section className="py-12 px-6 max-w-7xl mx-auto w-full">
        <h2 className="text-2xl font-bold text-white mb-4">Total Inputs You Can Provide</h2>
        <p className="text-sm text-gray-400 mb-8">
          Full specification of configurable parameters served directly from single source of truth <code className="text-cyan-400 font-mono bg-slate-900 px-2 py-1 rounded">/api/config-spec</code>.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-gray-900/50 border border-gray-800 p-6 rounded-2xl">
            <h3 className="text-sm font-bold uppercase tracking-wider text-cyan-400 mb-3">1. Domain Templates (5)</h3>
            <ul className="space-y-2 text-xs text-gray-300">
              {configSpec?.domains ? (
                configSpec.domains.map((d: string) => <li key={d} className="flex items-center space-x-2"><span>•</span><span>{d}</span></li>)
              ) : (
                <li>IoT / Manufacturing (default), Logistics, Finance, Healthcare, E-commerce</li>
              )}
            </ul>
          </div>

          <div className="bg-gray-900/50 border border-gray-800 p-6 rounded-2xl">
            <h3 className="text-sm font-bold uppercase tracking-wider text-cyan-400 mb-3">2. Schema & Types (5)</h3>
            <ul className="space-y-2 text-xs text-gray-300">
              <li>• <strong>Number:</strong> min, max, unit</li>
              <li>• <strong>Category:</strong> values[], weights[]</li>
              <li>• <strong>Boolean:</strong> true_share (0-100%)</li>
              <li>• <strong>Text:</strong> fake token note</li>
              <li>• <strong>Datetime:</strong> interval frequency</li>
            </ul>
          </div>

          <div className="bg-gray-900/50 border border-gray-800 p-6 rounded-2xl">
            <h3 className="text-sm font-bold uppercase tracking-wider text-cyan-400 mb-3">3. Volume & Frequency</h3>
            <ul className="space-y-2 text-xs text-gray-300">
              <li>• <strong>Record count:</strong> 100 to 100,000 (default 10,000)</li>
              <li>• <strong>Edge-case freq:</strong> 1% to 20% (default 5%)</li>
              <li>• <strong>Seed:</strong> reproducible integer</li>
              <li>• <strong>Export formats:</strong> CSV, JSON, Parquet</li>
            </ul>
          </div>

          <div className="bg-gray-900/50 border border-gray-800 p-6 rounded-2xl">
            <h3 className="text-sm font-bold uppercase tracking-wider text-cyan-400 mb-3">4. Failure Scenarios (4)</h3>
            <ul className="space-y-2 text-xs text-gray-300">
              {configSpec?.scenarios ? (
                configSpec.scenarios.map((s: string) => <li key={s} className="flex items-center space-x-2"><span>•</span><span>{s}</span></li>)
              ) : (
                <li>Boundary values, Missing/Corrupted data, Combined equipment failure, Network outage</li>
              )}
            </ul>
          </div>
        </div>
      </section>

      {/* e) HOW IT WORKS */}
      <section className="py-12 px-6 max-w-7xl mx-auto w-full">
        <h2 className="text-2xl font-bold text-center text-white mb-10">How It Works</h2>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 text-center">
          <div className="bg-gray-900/40 p-6 rounded-2xl border border-gray-800 flex flex-col items-center">
            <div className="w-10 h-10 rounded-full bg-cyan-500/20 text-cyan-400 font-bold flex items-center justify-center mb-4">1</div>
            <h3 className="font-semibold text-white mb-1">Define</h3>
            <p className="text-xs text-gray-400">Describe your machine paragraph; local Ollama extracts parameter schema.</p>
          </div>

          <div className="bg-gray-900/40 p-6 rounded-2xl border border-gray-800 flex flex-col items-center">
            <div className="w-10 h-10 rounded-full bg-cyan-500/20 text-cyan-400 font-bold flex items-center justify-center mb-4">2</div>
            <h3 className="font-semibold text-white mb-1">Configure</h3>
            <p className="text-xs text-gray-400">Select volume, edge-case frequency, failure scenario, and seed.</p>
          </div>

          <div className="bg-gray-900/40 p-6 rounded-2xl border border-gray-800 flex flex-col items-center">
            <div className="w-10 h-10 rounded-full bg-cyan-500/20 text-cyan-400 font-bold flex items-center justify-center mb-4">3</div>
            <h3 className="font-semibold text-white mb-1">Validate</h3>
            <p className="text-xs text-gray-400">Review privacy scores, quality reports, and predictive ML evaluation.</p>
          </div>

          <div className="bg-gray-900/40 p-6 rounded-2xl border border-gray-800 flex flex-col items-center">
            <div className="w-10 h-10 rounded-full bg-cyan-500/20 text-cyan-400 font-bold flex items-center justify-center mb-4">4</div>
            <h3 className="font-semibold text-white mb-1">Download</h3>
            <p className="text-xs text-gray-400">Export privacy-preserved synthetic datasets as CSV, JSON, or Parquet.</p>
          </div>
        </div>
      </section>

      {/* f) FOOTER */}
      <footer className="mt-auto border-t border-gray-800/80 py-8 px-6 bg-gray-950/80">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-gray-400">
          <p>© 2026 SynthEdge AI Synthetic Data & Edge-Case Generation Platform</p>
          <div className="flex items-center space-x-6">
            <a href="https://github.com" target="_blank" rel="noreferrer" className="flex items-center space-x-1 hover:text-cyan-400 transition-colors">
              <Github className="h-4 w-4" />
              <span>GitHub</span>
            </a>
            <a href="/docs" className="flex items-center space-x-1 hover:text-cyan-400 transition-colors">
              <BookOpen className="h-4 w-4" />
              <span>Documentation</span>
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
}
