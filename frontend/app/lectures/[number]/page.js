import Link from "next/link";
import BackButton from "./BackButton";
import SimilarClient from "./SimilarClient";
import ThemeToggle from "../../ThemeToggle";

function offeredInHref(item) {
  const params = new URLSearchParams();
  params.set("study_track", item.programme);
  if (item.section_id) params.set("level1_id", item.section_id);
  if (item.sub_section_id) params.set("level2_id", item.sub_section_id);
  return `/?${params.toString()}`;
}

const API = process.env.API_URL || "http://backend:8000/api";

const _cache = new Map();

async function fetchJSON(url) {
  if (_cache.has(url)) return _cache.get(url);
  const res = await fetch(url, { next: { revalidate: 0 } });
  if (!res.ok) return null;
  const data = await res.json();
  _cache.set(url, data);
  return data;
}

function getLecture(number) {
  return fetchJSON(`${API}/lectures/${encodeURIComponent(number)}/`);
}

export async function generateMetadata({ params }) {
  const { number } = await params;
  const lecture = await getLecture(number);
  if (!lecture) return { title: "Not Found — Course Catalog Explorer" };
  const clean = (s) => (s || "").replace(/\xa0/g, " ");
  return {
    title: `${lecture.title} — Course Catalog Explorer`,
    description: clean(lecture.abstract).slice(0, 200),
  };
}

function Field({ label, children }) {
  if (!children) return null;
  return (
    <div>
      <h3 className="text-sm font-semibold uppercase tracking-wider text-base-content/50 mb-2">
        {label}
      </h3>
      <div className="text-base text-base-content/80 leading-relaxed whitespace-pre-line">
        {children}
      </div>
    </div>
  );
}

export default async function LecturePage({ params }) {
  const { number } = await params;
  const lecture = await getLecture(number);

  if (!lecture) {
    return (
      <div className="min-h-screen bg-base-200 flex items-center justify-center">
        <div className="alert alert-soft alert-error max-w-md">
          <span>Lecture &quot;{number}&quot; not found.</span>
        </div>
      </div>
    );
  }

  const clean = (s) => (s || "").replace(/\xa0/g, " ");
  const lecturerNames = (lecture.lecturers || []).map((l) => l.name).join(", ");

  return (
    <div className="min-h-screen bg-base-200">
      <header className="bg-primary text-primary-content shadow-sm">
        <div className="max-w-4xl mx-auto px-4 py-6 sm:py-4">
          <div className="flex items-start justify-between">
            <BackButton />
            <ThemeToggle />
          </div>
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight mt-3 leading-snug">
            {lecture.title}
          </h1>
          <div className="flex flex-wrap items-center gap-3 mt-3">
            <span className="badge badge-outline badge-md font-mono text-sm">
              {lecture.number}
            </span>
            <span className="badge badge-soft badge-md text-sm">
              {lecture.type || "—"}
            </span>
            {lecture.language && (
              <span className="badge badge-soft badge-neutral badge-sm text-sm">
                {clean(lecture.language)}
              </span>
            )}
            {lecture.periodicity && (
              <span className="text-sm opacity-70">{clean(lecture.periodicity)}</span>
            )}
            {lecture.ects && (
              <span className="text-sm opacity-80">{clean(lecture.ects)}</span>
            )}
            {lecture.hours && (
              <span className="text-sm opacity-80">{clean(lecture.hours)}</span>
            )}
          </div>
          <div className="flex flex-wrap items-start justify-between gap-3 mt-2">
            <div className="min-w-0">
              {lecturerNames && (
                <p className="text-sm opacity-70">{lecturerNames}</p>
              )}
            </div>
            {lecture.url && (
              <a
                href={lecture.url}
                target="_blank"
                rel="noopener noreferrer"
                className="btn btn-sm btn-outline border-white/30 text-white hover:bg-white/20 shrink-0"
              >
                Open in VVZ
              </a>
            )}
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 -mt-4">
        <div className="card card-border border-base-300 bg-base-100 shadow-sm">
          <div className="card-body p-5 sm:p-8 space-y-6">
            <Field label="Abstract">{clean(lecture.abstract)}</Field>
            <Field label="Learning Objectives">{clean(lecture.learning_objective)}</Field>
            <Field label="Content">{clean(lecture.content)}</Field>
            <Field label="Lecture Notes">{clean(lecture.lecture_notes)}</Field>
            <Field label="Literature">{clean(lecture.literature)}</Field>
            <Field label="Performance Assessment">{clean(lecture.performance_assessment)}</Field>

            {lecture.offered_in && lecture.offered_in.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold uppercase tracking-wider text-base-content/50 mb-2">
                  Offered in
                </h3>
                <div className="space-y-1.5">
                  {lecture.offered_in.map((item, i) => (
                    <Link
                      key={i}
                      href={offeredInHref(item)}
                      className="flex items-center gap-1 text-sm flex-wrap hover:bg-base-200 -mx-1 px-1 py-0.5 rounded-lg transition-colors"
                    >
                      <span className="font-medium text-base-content/80 hover:text-primary transition-colors">{item.programme}</span>
                      {item.section && <><span className="text-base-content/30">›</span><span className="text-base-content/70 hover:text-secondary transition-colors">{item.section}</span></>}
                      {item.sub_section && <><span className="text-base-content/30">›</span><span className="text-base-content/60 hover:text-secondary transition-colors">{item.sub_section}</span></>}
                    </Link>
                  ))}
                </div>
              </div>
            )}

            <div className="pt-4" />
          </div>
        </div>

        <SimilarClient number={number} />
      </main>
    </div>
  );
}
