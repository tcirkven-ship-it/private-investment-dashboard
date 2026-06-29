"use client";

import { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { Upload } from "lucide-react";
import { loadNotebookModel } from "@/lib/loader";

export default function LoadNotebookModelButton() {
  const router = useRouter();
  const fileRef = useRef<HTMLInputElement>(null);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  async function handleFile(e: React.ChangeEvent<HTMLInputElement>) {
    const csv = e.target.files?.[0];
    if (!csv) return;
    setLoading(true); setMsg(null);

    const fd = new FormData();
    fd.set("csv", csv);
    // Try reading companion manifest if exists alongside
    const manifestName = csv.name.replace(/\.csv$/i, "_manifest.json");
    const manifestInput = document.querySelector<HTMLInputElement>(`input[type="hidden"][data-manifest]`);
    if (manifestInput?.value) fd.set("manifest", manifestInput.value);

    const res = await loadNotebookModel(fd);
    setMsg(res.error || res.message || "Done");
    if (!res.error) router.push("/model");
    setLoading(false);
    if (fileRef.current) fileRef.current.value = "";
  }

  return (
    <div className="flex items-center gap-3">
      <input ref={fileRef} type="file" accept=".csv" onChange={handleFile} className="hidden" />
      <button onClick={() => fileRef.current?.click()} disabled={loading} className="btn-ghost text-sm flex items-center gap-2">
        <Upload className="w-4 h-4" />
        {loading ? "Loading..." : "Load Notebook-Generated Top 30"}
      </button>
      {msg && (
        <span className={`text-xs ${msg.startsWith("Expected") || msg.startsWith("Missing") || msg.startsWith("Duplicate") || msg.startsWith("CSV") || msg.startsWith("Manifest") ? "text-red-400" : "text-green-400"}`}>
          {msg}
        </span>
      )}
    </div>
  );
}
