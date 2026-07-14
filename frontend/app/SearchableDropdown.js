"use client";

import { useState, useEffect, useRef } from "react";

function optionLabel(opt) {
  if (!opt) return "";
  return typeof opt === "string" ? opt : (opt.name || opt.label || "");
}

function optionValue(opt) {
  if (!opt) return null;
  return typeof opt === "string" ? opt : (opt.id ?? opt.value ?? opt.name);
}

export default function SearchableDropdown({
  label,
  options,
  value,
  onChange,
  placeholder = "Select...",
  searchPlaceholder = "Search...",
  disabled = false,
  loading = false,
  className = "",
}) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [highlight, setHighlight] = useState(-1);
  const highlightRef = useRef(-1);
  const listRef = useRef(null);

  const filtered = options.filter((opt) => {
    const val = optionLabel(opt).toLowerCase();
    return val.includes(search.toLowerCase());
  });

  useEffect(() => { highlightRef.current = highlight; }, [highlight]);

  useEffect(() => {
    setHighlight(filtered.length > 0 ? 0 : -1);
  }, [search, filtered.length]);

  const handleKeyDown = (e) => {
    const cur = highlightRef.current;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setHighlight(cur < filtered.length - 1 ? cur + 1 : 0);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setHighlight(cur > 0 ? cur - 1 : filtered.length - 1);
    } else if (e.key === "Enter" && cur >= 0) {
      e.preventDefault();
      onChange(filtered[cur] || null);
      setOpen(false);
      setSearch("");
    } else if (e.key === "Escape") {
      setOpen(false);
      setSearch("");
    }
  };

  const displayValue = value ? optionLabel(value) : placeholder;

  return (
    <div className={`relative ${className}`}>
      {label && (
        <label className="text-xs font-medium text-base-content/60 block mb-1">
          {label}
        </label>
      )}
      {loading ? (
        <div className="skeleton h-9 w-full rounded-lg" />
      ) : (
        <button
          type="button"
          className={`btn min-h-[36px] btn-border w-full justify-between text-sm font-normal ${
            disabled ? "opacity-40 cursor-not-allowed" : ""
          }`}
          onClick={() => !disabled && setOpen(!open)}
          disabled={disabled}
        >
          <span className={value ? "truncate" : "text-base-content/40 truncate"}>
            {displayValue}
          </span>
          <svg
            className={`size-3.5 opacity-50 shrink-0 transition-transform ${open ? "rotate-180" : ""}`}
            fill="none" viewBox="0 0 24 24" stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
      )}

      {open && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => { setOpen(false); setSearch(""); setHighlight(-1); }} />
          <div className="absolute z-20 mt-1 w-full bg-base-100 border border-base-300 rounded-xl shadow-xl max-h-80 flex flex-col">
            <div className="p-2 border-b border-base-300">
              <input
                type="text"
                placeholder={searchPlaceholder}
                className="input input-bordered w-full min-h-[36px] text-xs"
                value={search}
                onClick={(e) => e.stopPropagation()}
                onChange={(e) => { setSearch(e.target.value); setHighlight(0); }}
                onKeyDown={handleKeyDown}
                autoFocus
              />
            </div>
            <div className="overflow-y-auto overflow-x-auto flex-1" ref={listRef}>
              <button
                className={`w-full text-left px-3 py-2 text-xs transition-colors ${
                  highlight === -1
                    ? "bg-primary/15 text-primary font-medium"
                    : "hover:bg-base-200"
                } ${!value ? "bg-primary/10" : ""}`}
                onClick={() => { onChange(null); setOpen(false); setSearch(""); setHighlight(-1); }}
              >
                {placeholder}
              </button>
              {filtered.map((opt, i) => (
                <button
                  key={optionValue(opt)}
                  className={`w-full text-left px-3 py-2 text-xs transition-colors whitespace-nowrap ${
                    highlight === i
                      ? "bg-primary/15 text-primary font-medium"
                      : "hover:bg-base-200"
                  } ${
                    value && optionValue(value) === optionValue(opt) ? "bg-primary/10" : ""
                  }`}
                  onClick={() => { onChange(opt); setOpen(false); setSearch(""); setHighlight(-1); }}
                >
                  {optionLabel(opt)}
                </button>
              ))}
              {search && filtered.length === 0 && (
                <p className="px-3 py-4 text-xs text-base-content/40 text-center">No matching options</p>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
