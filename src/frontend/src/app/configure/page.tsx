"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Navbar from "@/components/Navbar";
import { MachineProfile, GenerationConfig } from "@/types";
import {
  Sliders,
  Database,
  Layers,
  Zap,
  Check,
  ArrowRight,
  AlertTriangle,
  RefreshCw,
  Info
} from "lucide-react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const DOMAINS = [
  "IoT / Manufacturing",
  "Logistics",
  "Finance",
  "Healthcare",
  "E-commerce"
];

const SCENARIOS = [
  "Boundary values",
  "Missing or corrupted data",
  "Combined equipment failure",
  "Network outage"
];

export default function ConfigurePage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const machineId = searchParams.get("machine");

  const [machine, setMachine] = useState<MachineProfile | null>(null);
  const [loadingMachine, setLoadingMachine] = useState(true);

  // Form State
  const [domain, setDomain] = useState("IoT / Manufacturing");
  const [numRecords, setNumRecords] = useState(10000);
  const [edgeCaseFreq, setEdgeCaseFreq] = useState(5);
  const [scenario, setScenario] = useState("Combined equipment failure");
  const [seed, setSeed] = useState(42);
  const [outputFormat, setOutputFormat] = useState<"csv" | "json" | "parquet">("csv");

  const [generating, setGenerating] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    if (!machineId) {
      setLoadingMachine(false);
      return;
    }

    fetch(`${API_BASE_URL}/api/machines/${machineId}`)
      .then((res) => {
        if (!res.ok) throw new Error("Machine profile not found");
        return res.json();
      })
      .then((data: MachineProfile) => {
        setMachine(data);
        if (data.suggested_domain) setDomain(data.suggested_domain);

        // Check if Combined Equipment Failure scenario should be disabled if < 2 number params
        const numCount = data.parameters.filter((p) => p.type === "number").length;
        if (numCount < 2) {
          setScenario("Boundary values");
        }
      })
      .catch((err) => setErrorMsg(err.message))
      .finally(() => setLoadingMachine(false));
  }, [machineId]);

  const numParamsCount = machine ? machine.parameters.filter((p) => p.type === "number").length : 0;
  const isCombinedFailureDisabled = numParamsCount < 2;

  // Proposed generation plan calculation
  const targetEdgeCaseRows = Math.round(numRecords * (edgeCaseFreq / 100.0));
  const normalRows = numRecords - targetEdgeCaseRows;

  const handleGenerate = async () => {
    if (!machineId) {
      setErrorMsg("No machine profile selected. Please define a machine first.");
      return;
    }

    setGenerating(true);
    setErrorMsg(null);

    try {
      const configPayload: GenerationConfig = {
        machine_id: machineId,
        num_records: numRecords,
        edge_case_frequency: edgeCaseFreq,
        scenario: scenario,
        seed: seed,
        output_format: outputFormat,
      };

      const res = await fetch(`${API_BASE_URL}/api/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(configPayload),
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Generation failed");
      }

      const result = await res.json();
      router.push(`/results/${result.run_id}`);
    } catch (err: any) {
      setErrorMsg(err.message || "Error generating dataset");
    } finally {
      setGenerating(false);
    }
  };

  if (loadingMachine) {
    return (
      <div className="min-h-screen bg-[#090d16] text-gray-100 flex flex-col font-sans">
        <Navbar />
        <div className="flex-grow flex items-center justify-center">
          <div className="flex items-center space-x-3 text-cyan-400">
            <RefreshCw className="h-6 w-6 animate-spin" />
            <span>Loading machine profile...</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#090d16] text-gray-100 flex flex-col font-sans">
      <Navbar />

      <main className="max-w-4xl mx-auto w-full px-6 py-10 flex-grow">
        {/* Step Indicator */}
        <div className="mb-8 border-b border-gray-800 pb-6">
          <div className="text-xs font-semibold text-cyan-400 uppercase tracking-wider mb-1">
            Step 3 of 4 • Configure Generator
          </div>
          <h1 className="text-3xl font-extrabold text-white">Generation Configuration</h1>
          {machine && (
            <p className="text-sm text-gray-400 mt-1">
              Machine: <strong className="text-white">{machine.name}</strong> ({machine.parameters.length} parameters)
            </p>
          )}
        </div>

        {errorMsg && (
          <div className="mb-6 p-4 rounded-xl bg-red-950/80 border border-red-800 text-red-200 text-sm flex items-start space-x-3">
            <AlertTriangle className="h-5 w-5 text-red-400 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold">Notice</p>
              <p className="mt-0.5 text-xs text-red-300">{errorMsg}</p>
            </div>
          </div>
        )}

        {/* Configuration Main Card */}
        <div className="bg-gray-900/80 border border-gray-800 rounded-3xl p-8 space-y-8 mb-8">
          <h2 className="text-lg font-bold text-white flex items-center space-x-2">
            <Sliders className="h-5 w-5 text-cyan-400" />
            <span>Example Generation Configuration</span>
          </h2>

          {/* 1. Domain Selection */}
          <div>
            <label className="block text-sm font-semibold text-white mb-3">Domain Template:</label>
            <div className="grid grid-cols-1 sm:grid-cols-3 lg:grid-cols-5 gap-3">
              {DOMAINS.map((d) => (
                <button
                  key={d}
                  type="button"
                  onClick={() => setDomain(d)}
                  className={`p-3 rounded-xl border text-xs font-semibold text-left transition-all ${
                    domain === d
                      ? "bg-cyan-950 text-cyan-400 border-cyan-500 shadow-sm shadow-cyan-500/20"
                      : "bg-gray-950 text-gray-400 border-gray-800 hover:border-gray-700"
                  }`}
                >
                  {d}
                </button>
              ))}
            </div>
          </div>

          {/* 2. Number of Records Slider */}
          <div>
            <div className="flex justify-between items-center mb-2">
              <label className="text-sm font-semibold text-white">Number of Records:</label>
              <span className="text-sm font-mono font-bold text-cyan-400 bg-gray-950 px-3 py-1 rounded-lg border border-gray-800">
                {numRecords.toLocaleString()} rows
              </span>
            </div>
            <input
              type="range"
              min="100"
              max="100000"
              step="100"
              value={numRecords}
              onChange={(e) => setNumRecords(parseInt(e.target.value))}
              className="w-full accent-cyan-500 h-2 bg-gray-950 rounded-lg cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-gray-500 font-mono mt-1">
              <span>100</span>
              <span>50,000</span>
              <span>100,000</span>
            </div>
          </div>

          {/* 3. Target Edge-case Frequency Slider */}
          <div>
            <div className="flex justify-between items-center mb-2">
              <label className="text-sm font-semibold text-white">Target Edge-Case Frequency:</label>
              <span className="text-sm font-mono font-bold text-red-400 bg-gray-950 px-3 py-1 rounded-lg border border-gray-800">
                {edgeCaseFreq}%
              </span>
            </div>
            <input
              type="range"
              min="1"
              max="20"
              step="1"
              value={edgeCaseFreq}
              onChange={(e) => setEdgeCaseFreq(parseInt(e.target.value))}
              className="w-full accent-red-500 h-2 bg-gray-950 rounded-lg cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-gray-500 font-mono mt-1">
              <span>1% (Low)</span>
              <span>10% (Medium)</span>
              <span>20% (Max)</span>
            </div>
          </div>

          {/* 4. Scenario to Inject */}
          <div>
            <label className="block text-sm font-semibold text-white mb-3">Scenario to Inject:</label>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {SCENARIOS.map((sc) => {
                const disabled = sc === "Combined equipment failure" && isCombinedFailureDisabled;
                return (
                  <button
                    key={sc}
                    type="button"
                    disabled={disabled}
                    onClick={() => setScenario(sc)}
                    className={`p-4 rounded-xl border text-xs font-semibold text-left transition-all flex flex-col justify-between ${
                      scenario === sc
                        ? "bg-red-950/40 text-red-300 border-red-500 shadow-sm"
                        : disabled
                        ? "bg-gray-950/40 text-gray-600 border-gray-900 cursor-not-allowed opacity-60"
                        : "bg-gray-950 text-gray-400 border-gray-800 hover:border-gray-700"
                    }`}
                  >
                    <span>{sc}</span>
                    {disabled && (
                      <span className="text-[10px] text-amber-500/80 mt-1 italic flex items-center space-x-1">
                        <Info className="h-3 w-3 shrink-0" />
                        <span>Requires at least 2 number parameters</span>
                      </span>
                    )}
                  </button>
                );
              })}
            </div>
          </div>

          {/* 5. Seed & Format */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-4 border-t border-gray-800/80">
            <div>
              <label className="block text-xs font-semibold text-gray-400 mb-1">Random Seed (Reproducible)</label>
              <input
                type="number"
                value={seed}
                onChange={(e) => setSeed(parseInt(e.target.value) || 42)}
                className="w-full bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm text-white font-mono focus:outline-none focus:border-cyan-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-400 mb-1">Output Export Format</label>
              <select
                value={outputFormat}
                onChange={(e) => setOutputFormat(e.target.value as any)}
                className="w-full bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500"
              >
                <option value="csv">CSV File (.csv)</option>
                <option value="json">JSON File (.json)</option>
                <option value="parquet">Apache Parquet (.parquet)</option>
              </select>
            </div>
          </div>

          {/* Proposed Generation Plan Box (LIVE UPDATING) */}
          <div className="bg-gray-950 border border-cyan-800/60 rounded-2xl p-6 shadow-md shadow-cyan-500/5">
            <h3 className="text-xs font-bold text-cyan-400 uppercase tracking-wider mb-4 flex items-center space-x-2">
              <Zap className="h-4 w-4" />
              <span>Proposed Generation Plan</span>
            </h3>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
              <div className="bg-gray-900/60 p-3 rounded-xl border border-gray-800">
                <span className="text-[10px] text-gray-400 block uppercase">Total Records</span>
                <span className="text-lg font-bold font-mono text-white">{numRecords.toLocaleString()}</span>
              </div>

              <div className="bg-gray-900/60 p-3 rounded-xl border border-gray-800">
                <span className="text-[10px] text-gray-400 block uppercase">Target Edge Cases</span>
                <span className="text-lg font-bold font-mono text-red-400">{targetEdgeCaseRows.toLocaleString()}</span>
              </div>

              <div className="bg-gray-900/60 p-3 rounded-xl border border-gray-800">
                <span className="text-[10px] text-gray-400 block uppercase">Normal Rows</span>
                <span className="text-lg font-bold font-mono text-emerald-400">{normalRows.toLocaleString()}</span>
              </div>

              <div className="bg-gray-900/60 p-3 rounded-xl border border-gray-800">
                <span className="text-[10px] text-gray-400 block uppercase">Domain</span>
                <span className="text-xs font-bold text-cyan-300 truncate block mt-1">{domain}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Full-width Button "Design this generator" */}
        <button
          type="button"
          disabled={generating}
          onClick={handleGenerate}
          className="w-full py-5 rounded-2xl bg-cyan-500 hover:bg-cyan-400 disabled:bg-gray-800 text-gray-950 disabled:text-gray-500 font-extrabold text-lg transition-all shadow-xl shadow-cyan-500/20 flex items-center justify-center space-x-3"
        >
          {generating ? (
            <>
              <RefreshCw className="h-6 w-6 animate-spin" />
              <span>Designing and generating dataset...</span>
            </>
          ) : (
            <>
              <span>Design this generator</span>
              <ArrowRight className="h-6 w-6" />
            </>
          )}
        </button>
      </main>
    </div>
  );
}
