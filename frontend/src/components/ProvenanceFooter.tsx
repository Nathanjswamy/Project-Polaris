import { FileJson, Clock, Hash, CheckCircle, Database } from "lucide-react";

export default function ProvenanceFooter({ manifest }) {
  if (!manifest) return null;

  return (
    <footer className="mt-12 border-t border-[var(--border-subtle)] bg-[var(--surface-alt)]">
      <div className="max-w-[1600px] mx-auto w-full px-6 py-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Integrity Statement */}
          <div className="col-span-1 md:col-span-2">
            <div className="flex items-center gap-2 mb-3">
              <Database className="w-5 h-5 text-[var(--text-secondary)]" />
              <h3 className="text-[var(--text-primary)] font-display text-lg">Data Provenance</h3>
            </div>
            <p className="text-sm text-[var(--text-secondary)] leading-relaxed max-w-2xl mb-4">
              Project Polaris operates on a strict zero-synthetic data policy. 
              Every metric, coordinate, and rating displayed in this dashboard traces back to a real 
              Google Maps extraction run. Nothing is hallucinated.
            </p>
            <div className="flex flex-wrap gap-4 text-xs font-mono text-[var(--text-tertiary)]">
              <span className="flex items-center gap-1">
                <Hash className="w-3 h-3" /> Run ID: {manifest.pipeline_run_id || "Unknown"}
              </span>
              <span className="flex items-center gap-1">
                <Clock className="w-3 h-3" /> Extracted: {manifest.completed_at ? new Date(manifest.completed_at).toLocaleString() : "Unknown"}
              </span>
              <span className="flex items-center gap-1">
                <FileJson className="w-3 h-3" /> Source: {manifest.source || "Google Maps via Apify"}
              </span>
            </div>
          </div>

          {/* Pipeline Stats */}
          <div className="col-span-1 border-l border-[var(--border-subtle)] pl-8">
            <h4 className="text-xs font-mono uppercase tracking-wider text-[var(--text-tertiary)] mb-4">
              Pipeline Validation
            </h4>
            <ul className="space-y-3 text-sm">
              <li className="flex justify-between items-center text-[var(--text-secondary)]">
                <span>Raw Records</span>
                <span className="font-mono text-[var(--text-primary)]">{manifest.raw_items_received || 0}</span>
              </li>
              <li className="flex justify-between items-center text-[var(--chili)]">
                <span>Validation Rejections</span>
                <span className="font-mono">{manifest.records_rejected || 0}</span>
              </li>
              <li className="flex justify-between items-center text-[var(--text-secondary)]">
                <span>Duplicates Dropped</span>
                <span className="font-mono">{manifest.duplicates_removed || 0}</span>
              </li>
              <li className="flex justify-between items-center text-[var(--cardamom)] pt-2 border-t border-[var(--border-subtle)]">
                <span className="flex items-center gap-1">
                  <CheckCircle className="w-4 h-4" /> Final Indexed
                </span>
                <span className="font-mono font-medium">{manifest.final_record_count || 0}</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </footer>
  );
}
