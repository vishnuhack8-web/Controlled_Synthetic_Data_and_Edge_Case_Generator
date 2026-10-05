"use client";

import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import Navbar from "@/components/Navbar";
import { Parameter, MachineProfile, LLMStatus } from "@/types";
import {
  Cpu,
  Plus,
  Trash2,
  RefreshCw,
  ArrowRight,
  AlertCircle,
  Sparkles,
  Layers,
  Check
} from "lucide-react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const WATER_PUMP_EXAMPLE =
  "A high-capacity industrial water pump station that monitors temperature (0-100 °C), pressure (1-10 bar), flow rate (0-500 L/min), operational mode (idle, running, error), emergency stop button state, and records timestamps every 5 seconds.";

const VENDING_MACHINE_EXAMPLE =
  "A smart vending machine that tracks item inventory stock level (0-100 items), internal temperature (2-10 °C), payment method (cash, credit_card, mobile_pay), network connectivity status (online, offline), and door sensor.";

export default function DefineMachinePage() {
  const router = useRouter();

  // State
  const [llmStatus, setLlmStatus] = useState<LLMStatus | null>(null);
  const [description, setDescription] = useState("");
  const [machineName, setMachineName] = useState("My Industrial Machine");
  const [suggestedDomain, setSuggestedDomain] = useState("IoT / Manufacturing");
  const [parameters, setParameters] = useState<Parameter[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [sampleRow, setSampleRow] = useState<Record<string, any>>({});

  const lastNameInputRef = useRef<HTMLInputElement | null>(null);

  // Fetch Ollama status on mount
  useEffect(() => {
    fetch(`${API_BASE_URL}/api/llm-status`)
      .then((res) => res.json())
      .then((data: LLMStatus) => setLlmStatus(data))
      .catch(() => setLlmStatus({ reachable: false, models_installed: [], model_in_use: null, using_fallback: true }));
  }, []);

  // Update sample row when parameters change
  useEffect(() => {
    generateSampleRow();
  }, [parameters]);

  const wordCount = description.trim() ? description.trim().split(/\s+/).length : 0;

  const handleAnalyze = async () => {
    setErrorMsg(null);
    if (!description.trim()) {
      setErrorMsg("Describe your machine first");
      return;
    }
    if (wordCount < 8) {
      setErrorMsg("Add a little more detail so we can find the inputs");
      return;
    }

    setLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/parse-machine`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ description }),
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Failed to analyze machine description");
      }

      const data = await res.json();
      if (data.name) setMachineName(data.name);
      if (data.suggested_domain) setSuggestedDomain(data.suggested_domain);

      if (data.parameters && data.parameters.length > 0) {
        setParameters(data.parameters);
      } else {
        setErrorMsg("No sensors or fields were detected. Please mention specific sensors or parameters in your description.");
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Error analyzing machine description");
    } finally {
      setLoading(false);
    }
  };

  const generateSampleRow = () => {
    if (parameters.length === 0) {
      setSampleRow({});
      return;
    }
    const sample: Record<string, any> = {};
    parameters.forEach((p) => {
      if (!p.name) return;
      if (p.type === "number" && p.number) {
        const min = p.number.min ?? 0;
        const max = p.number.max ?? 100;
        const val = min + Math.random() * (max - min);
        sample[p.name] = Number(val.toFixed(2));
      } else if (p.type === "category" && p.category && p.category.values.length > 0) {
        const idx = Math.floor(Math.random() * p.category.values.length);
        sample[p.name] = p.category.values[idx];
      } else if (p.type === "boolean") {
        sample[p.name] = Math.random() > 0.5;
      } else if (p.type === "text") {
        sample[p.name] = `${p.name.slice(0, 3).toUpperCase()}-${Math.floor(1000 + Math.random() * 9000)}`;
      } else if (p.type === "datetime") {
        sample[p.name] = new Date().toISOString().replace("T", " ").slice(0, 19);
      }
    });
    setSampleRow(sample);
  };

  const addParameter = () => {
    const newParam: Parameter = {
      name: `parameter_${parameters.length + 1}`,
      type: "number",
      number: { min: 0, max: 100, unit: "units", distribution: "uniform" },
    };
    setParameters([...parameters, newParam]);
    setTimeout(() => lastNameInputRef.current?.focus(), 100);
  };

  const removeParameter = (index: number) => {
    setParameters(parameters.filter((_, i) => i !== index));
  };

  const updateParameter = (index: number, updated: Parameter) => {
    const copy = [...parameters];
    copy[index] = updated;
    setParameters(copy);
  };

  const validateParameters = (): string | null => {
    if (parameters.length === 0) {
      return "At least one parameter is required.";
    }

    const seenNames = new Set<string>();
    for (let i = 0; i < parameters.length; i++) {
      const p = parameters[i];
      if (!p.name || !p.name.trim()) {
        return `Parameter #${i + 1} requires a valid non-empty name.`;
      }
      const lower = p.name.trim().toLowerCase();
      if (seenNames.has(lower)) {
        return `Duplicate parameter name found: '${p.name}'. Parameter names must be unique (case-insensitive).`;
      }
      seenNames.add(lower);

      if (p.type === "number" && p.number) {
        if (p.number.min >= p.number.max) {
          return `Parameter '${p.name}': Minimum value (${p.number.min}) must be strictly less than maximum (${p.number.max}).`;
        }
      } else if (p.type === "category" && p.category) {
        if (!p.category.values || p.category.values.length < 2) {
          return `Parameter '${p.name}': Category parameters must have at least 2 comma-separated values.`;
        }
      } else if (p.type === "boolean" && p.boolean) {
        if (p.boolean.true_share < 0 || p.boolean.true_share > 100) {
          return `Parameter '${p.name}': Boolean True Share must be between 0 and 100%.`;
        }
      }
    }
    return null;
  };

  const handleContinue = async () => {
    setErrorMsg(null);
    const inlineError = validateParameters();
    if (inlineError) {
      setErrorMsg(inlineError);
      return;
    }

    setSaving(true);
    try {
      const profilePayload: MachineProfile = {
        name: machineName.trim() || "Defined Machine",
        description: description,
        suggested_domain: suggestedDomain,
        domain: suggestedDomain,
        parameters: parameters,
      };

      const res = await fetch(`${API_BASE_URL}/api/machines`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(profilePayload),
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Failed to save machine profile");
      }

      const savedMachine: MachineProfile = await res.json();
      router.push(`/configure?machine=${savedMachine.id}`);
    } catch (err: any) {
      setErrorMsg(err.message || "Error saving machine profile");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#090d16] text-gray-100 flex flex-col font-sans">
      <Navbar />

      <main className="max-w-5xl mx-auto w-full px-6 py-10 flex-grow">
        {/* Header & Step Indicator */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8 border-b border-gray-800 pb-6">
          <div>
            <div className="text-xs font-semibold text-cyan-400 uppercase tracking-wider mb-1">
              Step 2 of 4 • Define Machine Schema
            </div>
            <h1 className="text-3xl font-extrabold text-white">Define Your Machine</h1>
          </div>

          {/* Local AI status badge */}
          <div className="flex items-center space-x-2">
            {llmStatus?.reachable && !llmStatus.using_fallback ? (
              <span className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-full bg-emerald-950/80 border border-emerald-700/60 text-emerald-400 text-xs font-medium">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                <span>Local AI ready ({llmStatus.model_in_use})</span>
              </span>
            ) : (
              <span className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-full bg-amber-950/80 border border-amber-700/60 text-amber-400 text-xs font-medium">
                <span className="w-2 h-2 rounded-full bg-amber-400"></span>
                <span>Local AI offline, using basic parser</span>
              </span>
            )}
          </div>
        </div>

        {/* Textarea Description Box */}
        <div className="bg-gray-900/60 border border-gray-800 rounded-2xl p-6 mb-8">
          <label className="block text-sm font-semibold text-white mb-2">
            Describe your machine, equipment, or business system in a paragraph:
          </label>

          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="e.g. A water pump station with a temperature sensor (0-100 °C), pressure gauge (1-10 bar), flow rate meter, operating mode (idle, running, error), and 5-second interval timestamps."
            rows={4}
            className="w-full bg-gray-950 border border-gray-800 rounded-xl p-4 text-sm text-gray-100 placeholder-gray-500 focus:outline-none focus:border-cyan-500 transition-colors"
          />

          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mt-4">
            {/* Example chips */}
            <div className="flex items-center space-x-2 text-xs">
              <span className="text-gray-400 font-medium">Try examples:</span>
              <button
                type="button"
                onClick={() => setDescription(WATER_PUMP_EXAMPLE)}
                className="px-2.5 py-1 rounded-lg bg-gray-800 hover:bg-gray-700 text-cyan-400 font-medium transition-colors"
              >
                Water pump
              </button>
              <button
                type="button"
                onClick={() => setDescription(VENDING_MACHINE_EXAMPLE)}
                className="px-2.5 py-1 rounded-lg bg-gray-800 hover:bg-gray-700 text-cyan-400 font-medium transition-colors"
              >
                Vending machine
              </button>
            </div>

            <div className="flex items-center space-x-4">
              <span className="text-xs font-mono text-gray-400">{wordCount} words</span>

              <button
                type="button"
                disabled={loading}
                onClick={handleAnalyze}
                className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 disabled:bg-gray-800 text-gray-950 disabled:text-gray-500 font-bold text-sm transition-all shadow-md shadow-cyan-500/20"
              >
                {loading ? (
                  <>
                    <RefreshCw className="h-4 w-4 animate-spin text-gray-950" />
                    <span>Local AI is reading your description...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="h-4 w-4" />
                    <span>Analyze description</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Validation / Inline Error Banner */}
        {errorMsg && (
          <div className="mb-6 p-4 rounded-xl bg-red-950/80 border border-red-800 text-red-200 text-sm flex items-start space-x-3">
            <AlertCircle className="h-5 w-5 text-red-400 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold">Validation Notice</p>
              <p className="mt-0.5 text-xs text-red-300">{errorMsg}</p>
            </div>
          </div>
        )}

        {/* Detected Parameters & Suggested Domain */}
        {parameters.length > 0 && (
          <div className="space-y-6 mb-10">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <h2 className="text-xl font-bold text-white">Confirmed Dataset Parameters ({parameters.length})</h2>
                <p className="text-xs text-gray-400 mt-1">Edit any field type, range, or unit below before configuring generation.</p>
              </div>

              <div className="flex items-center space-x-3">
                <span className="text-xs text-gray-400">Suggested Domain:</span>
                <span className="px-3 py-1 rounded-full bg-cyan-950 text-cyan-400 border border-cyan-800 text-xs font-bold">
                  {suggestedDomain}
                </span>
              </div>
            </div>

            {/* Parameter Cards List */}
            <div className="space-y-4">
              {parameters.map((param, index) => (
                <div key={index} className="bg-gray-900/80 border border-gray-800 rounded-xl p-5 relative transition-colors hover:border-gray-700">
                  <div className="grid grid-cols-1 sm:grid-cols-12 gap-4 items-center">
                    {/* Parameter Name */}
                    <div className="sm:col-span-4">
                      <label className="block text-xs text-gray-400 mb-1">Parameter Name</label>
                      <input
                        ref={index === parameters.length - 1 ? lastNameInputRef : null}
                        type="text"
                        value={param.name}
                        onChange={(e) => updateParameter(index, { ...param, name: e.target.value })}
                        className="w-full bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm text-white font-mono focus:outline-none focus:border-cyan-500"
                        placeholder="e.g. temperature"
                      />
                    </div>

                    {/* Parameter Type Select */}
                    <div className="sm:col-span-3">
                      <label className="block text-xs text-gray-400 mb-1">Type</label>
                      <select
                        value={param.type}
                        onChange={(e) => {
                          const newType = e.target.value as any;
                          const updated: Parameter = { ...param, type: newType };
                          if (newType === "number" && !updated.number) updated.number = { min: 0, max: 100, unit: "units", distribution: "uniform" };
                          if (newType === "category" && !updated.category) updated.category = { values: ["active", "inactive"] };
                          if (newType === "boolean" && !updated.boolean) updated.boolean = { true_share: 50 };
                          updateParameter(index, updated);
                        }}
                        className="w-full bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500"
                      >
                        <option value="number">Number</option>
                        <option value="category">Category</option>
                        <option value="boolean">Boolean</option>
                        <option value="text">Text (Fake Token)</option>
                        <option value="datetime">Datetime</option>
                      </select>
                    </div>

                    {/* Type-Specific Fields */}
                    <div className="sm:col-span-4">
                      {param.type === "number" && (
                        <div className="grid grid-cols-3 gap-2">
                          <div>
                            <label className="block text-[10px] text-gray-400">Min</label>
                            <input
                              type="number"
                              value={param.number?.min ?? 0}
                              onChange={(e) =>
                                updateParameter(index, {
                                  ...param,
                                  number: { ...(param.number || { max: 100, unit: "", distribution: "uniform" }), min: parseFloat(e.target.value) || 0 },
                                })
                              }
                              className="w-full bg-gray-950 border border-gray-800 rounded-lg px-2 py-1.5 text-xs text-white"
                            />
                          </div>
                          <div>
                            <label className="block text-[10px] text-gray-400">Max</label>
                            <input
                              type="number"
                              value={param.number?.max ?? 100}
                              onChange={(e) =>
                                updateParameter(index, {
                                  ...param,
                                  number: { ...(param.number || { min: 0, unit: "", distribution: "uniform" }), max: parseFloat(e.target.value) || 0 },
                                })
                              }
                              className="w-full bg-gray-950 border border-gray-800 rounded-lg px-2 py-1.5 text-xs text-white"
                            />
                          </div>
                          <div>
                            <label className="block text-[10px] text-gray-400">Unit</label>
                            <input
                              type="text"
                              value={param.number?.unit ?? ""}
                              onChange={(e) =>
                                updateParameter(index, {
                                  ...param,
                                  number: { ...(param.number || { min: 0, max: 100, distribution: "uniform" }), unit: e.target.value },
                                })
                              }
                              className="w-full bg-gray-950 border border-gray-800 rounded-lg px-2 py-1.5 text-xs text-white"
                              placeholder="e.g. °C"
                            />
                          </div>
                        </div>
                      )}

                      {param.type === "category" && (
                        <div>
                          <label className="block text-[10px] text-gray-400">Values (comma separated)</label>
                          <input
                            type="text"
                            value={(param.category?.values || []).join(", ")}
                            onChange={(e) => {
                              const vals = e.target.value.split(",").map((s) => s.trim());
                              updateParameter(index, {
                                ...param,
                                category: { values: vals },
                              });
                            }}
                            className="w-full bg-gray-950 border border-gray-800 rounded-lg px-3 py-1.5 text-xs text-white"
                            placeholder="idle, running, error"
                          />
                        </div>
                      )}

                      {param.type === "boolean" && (
                        <div>
                          <label className="block text-[10px] text-gray-400">True Share (% Yes)</label>
                          <input
                            type="number"
                            min="0"
                            max="100"
                            value={param.boolean?.true_share ?? 50}
                            onChange={(e) =>
                              updateParameter(index, {
                                ...param,
                                boolean: { true_share: Math.max(0, Math.min(100, parseFloat(e.target.value) || 0)) },
                              })
                            }
                            className="w-full bg-gray-950 border border-gray-800 rounded-lg px-3 py-1.5 text-xs text-white"
                          />
                        </div>
                      )}

                      {(param.type === "text" || param.type === "datetime") && (
                        <div>
                          <label className="block text-[10px] text-gray-400">Generation Note</label>
                          <span className="text-xs text-gray-400 block py-1.5 italic">
                            {param.type === "text" ? "Fake hex/alphanumeric token" : "Sequential 5-sec timestamps"}
                          </span>
                        </div>
                      )}
                    </div>

                    {/* Delete button */}
                    <div className="sm:col-span-1 flex justify-end">
                      <button
                        type="button"
                        onClick={() => removeParameter(index)}
                        className="p-2 text-gray-500 hover:text-red-400 hover:bg-gray-800 rounded-lg transition-colors"
                        title="Remove parameter"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Add Parameter Button */}
            <button
              type="button"
              onClick={addParameter}
              className="inline-flex items-center space-x-2 px-4 py-2.5 rounded-xl border border-gray-800 hover:border-cyan-500/50 bg-gray-900 text-cyan-400 text-xs font-bold transition-all"
            >
              <Plus className="h-4 w-4" />
              <span>+ Add parameter</span>
            </button>

            {/* Live Sample Row Panel */}
            <div className="bg-gray-950 border border-gray-800 rounded-xl p-5 mt-6">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-2">
                  <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse"></span>
                  <span className="text-xs font-bold text-white uppercase tracking-wider">Live Sample Row Preview</span>
                </div>

                <button
                  type="button"
                  onClick={generateSampleRow}
                  className="inline-flex items-center space-x-1.5 text-xs text-cyan-400 hover:text-cyan-300 transition-colors"
                >
                  <RefreshCw className="h-3.5 w-3.5" />
                  <span>New sample</span>
                </button>
              </div>

              <pre className="bg-gray-900 p-4 rounded-lg text-xs font-mono text-cyan-300 overflow-x-auto border border-gray-800/80">
                {JSON.stringify(sampleRow, null, 2)}
              </pre>
            </div>
          </div>
        )}

        {/* Continue to Configuration Button */}
        <div className="flex justify-end pt-6 border-t border-gray-800">
          <button
            type="button"
            disabled={saving || parameters.length === 0}
            onClick={handleContinue}
            className="inline-flex items-center space-x-2 px-8 py-4 rounded-xl bg-cyan-500 hover:bg-cyan-400 disabled:bg-gray-800 text-gray-950 disabled:text-gray-500 font-bold text-base transition-all shadow-lg shadow-cyan-500/25"
          >
            {saving ? (
              <span>Saving profile...</span>
            ) : (
              <>
                <span>Continue to configuration</span>
                <ArrowRight className="h-5 w-5" />
              </>
            )}
          </button>
        </div>
      </main>
    </div>
  );
}
