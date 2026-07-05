"use client";

import { useState } from "react";
import LectureCard from "../../components/LectureCard";

export default function SimilarClient({ number }) {
  const [similar, setSimilar] = useState(null);
  const [loading, setLoading] = useState(false);

  const loadSimilar = () => {
    setLoading(true);
    fetch(`/api/similar/${encodeURIComponent(number)}/?k=10`)
      .then((r) => r.json())
      .then((data) => setSimilar((data.results || []).slice(0, 5)))
      .catch(() => setSimilar([]))
      .finally(() => setLoading(false));
  };

  if (loading) {
    return (
      <div id="similar" className="mt-6 mb-12">
        <h2 className="text-sm font-semibold text-base-content/50 uppercase tracking-wider mb-4">
          Similar Lectures
        </h2>
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="card card-border border-base-300 bg-base-100 shadow-sm">
              <div className="card-body p-4 sm:p-5">
                <div className="skeleton h-5 w-3/4" />
                <div className="skeleton h-4 w-full mt-3" />
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (!similar || similar.length === 0) {
    return (
      <div id="similar" className="mt-6 mb-12">
        <button
          className="btn btn-soft btn-neutral min-h-[44px] text-sm"
          onClick={loadSimilar}
        >
          Show Similar Lectures
        </button>
      </div>
    );
  }

  return (
    <div id="similar" className="mt-6 mb-12">
      <h2 className="text-sm font-semibold text-base-content/50 uppercase tracking-wider mb-4">
        Similar Lectures
      </h2>
      <div className="space-y-3">
        {similar.map((sim) => (
          <LectureCard key={sim.number} lecture={sim} />
        ))}
      </div>
    </div>
  );
}
