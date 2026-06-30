"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Upload } from "lucide-react";
import { loadNotebookModel } from "@/lib/loader";

export default function LoadNotebookModelButton() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const router = useRouter();

  async function handleFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    setLoading(true);
    setResult(null);

    const formData = new FormData();
    formData.append("csv", file);

    const res = await loadNotebookModel(formData);
    setLoading(false);

    if (res.error) {
      setResult(res.error);
    } else {
      setResult(res.message || `Loaded ${res.holdings} holdings.`);
    }
    router.refresh();
    e.target.value = "";
  }

  return (
    <div>
      <label
        className={`btn-primary text-sm cursor-pointer inline-flex items-center ${loading ? "opacity-50 pointer-events-none" : ""}`}
      >
        <Upload className={`w-4 h-4 mr-1.5 ${loading ? "animate-pulse" : ""}`} />
        {loading ? "Loading..." : "Load Notebook-Generated Top 30"}
        <input
          type="file"
          accept=".csv"
          onChange={handleFile}
          className="hidden"
          disabled={loading}
        />
      </label>
      {result && (
        <p className="text-xs text-neutral-400 mt-1">{result}</p>
      )}
    </div>
  );
}
