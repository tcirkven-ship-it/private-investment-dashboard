"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { RefreshCw } from "lucide-react";
import { importM1B2Model } from "@/lib/actions";

const STAGE_SEQUENCE: { at: number; label: string }[] = [
  { at: 2000, label: "Loading input data..." },
  { at: 4000, label: "Running M1_B2_QUALITY_VETO_N30 engine..." },
  { at: 7000, label: "Writing model snapshot..." },
];

export default function GenerateModelButton() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [stage, setStage] = useState("");
  const [elapsed, setElapsed] = useState(0);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const timeoutsRef = useRef<ReturnType<typeof setTimeout>[]>([]);

  const clearTimers = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    timeoutsRef.current.forEach(clearTimeout);
    timeoutsRef.current = [];
  }, []);

  useEffect(() => {
    return () => clearTimers();
  }, [clearTimers]);

  async function handleClick() {
    clearTimers();
    setLoading(true);
    setErrorMsg(null);
    setSuccessMsg(null);
    setStage("Starting generation...");
    setElapsed(0);

    intervalRef.current = setInterval(() => {
      setElapsed((prev) => prev + 1);
    }, 1000);

    STAGE_SEQUENCE.forEach(({ at, label }) => {
      const id = setTimeout(() => setStage(label), at);
      timeoutsRef.current.push(id);
    });

    try {
      const res = await importM1B2Model();
      clearTimers();
      setLoading(false);
      setStage("");
      if (res.error) {
        setErrorMsg(res.error);
      } else {
        setSuccessMsg(res.message || "Done");
        router.refresh();
      }
    } catch (e) {
      clearTimers();
      setLoading(false);
      setStage("");
      setErrorMsg(e instanceof Error ? e.message : "Generation failed");
    }
  }

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center gap-3">
        <button
          onClick={handleClick}
          disabled={loading}
          className="btn-primary"
        >
          <RefreshCw className={`w-4 h-4 mr-1.5 ${loading ? "animate-spin" : ""}`} />
          {loading ? "Generating..." : "Generate Quarter-End Top 30"}
        </button>
        {loading && (
          <span className="text-xs text-neutral-500 tabular-nums">{elapsed}s</span>
        )}
      </div>
      {loading && stage && (
        <p className="text-xs text-neutral-400">{stage}</p>
      )}
      {errorMsg && (
        <p className="text-xs text-red-400">{errorMsg}</p>
      )}
      {successMsg && (
        <p className="text-xs text-green-400">{successMsg}</p>
      )}
    </div>
  );
}
