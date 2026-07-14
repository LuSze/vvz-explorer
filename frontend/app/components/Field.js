"use client";

export default function Field({ label, children }) {
  if (!children) return null;
  return (
    <div>
      <h4 className="text-xs font-semibold uppercase tracking-wider text-base-content/50 mb-1">
        {label}
      </h4>
      <div className="text-xs text-base-content/70 leading-relaxed whitespace-pre-line">
        {children}
      </div>
    </div>
  );
}
