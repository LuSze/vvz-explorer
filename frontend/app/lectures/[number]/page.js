import Link from "next/link";
import { headers } from "next/headers";
import BackButton from "./BackButton";
import SimilarClient from "./SimilarClient";
import ThemeToggle from "../../ThemeToggle";

function offeredInHref(item, depth) {
  const params = new URLSearchParams();
  params.set("study_track", item.programme);
  if (depth >= 1 && item.section_id) params.set("level1_id", item.section_id);
  if (depth >= 2 && item.sub_section_id) params.set("level2_id", item.sub_section_id);
  return `/?${params.toString()}`;
}

const _cache = new Map();

async function getAPI() {
  const h = await headers();
  const host = h.get("host") || "localhost:3000";
  const proto = h.get("x-forwarded-proto") || "http";
  return `${proto}://${host}/api`;
}

async function fetchJSON(url) {
  if (_cache.has(url)) return _cache.get(url);
  const res = await fetch(url, { next: { revalidate: 0 } });
  if (!res.ok) return null;
  const data = await res.json();
  _cache.set(url, data);
  return data;
}

async function getLecture(number, semester) {
  const api = await getAPI();
  let url = `${api}/lectures/${encodeURIComponent(number)}/`;
  if (semester) url += `?semester=${encodeURIComponent(semester)}`;
  return fetchJSON(url);
}

export async function generateMetadata({ params, searchParams }) {
  const { number } = await params;
  const semester = (await searchParams)?.semester || "";
  const lecture = await getLecture(number, semester);
  if (!lecture) return { title: "Not Found — Course Catalog Explorer" };
  const clean = (s) => (s || "").replace(/\xa0/g, " ");
  return {
    title: `${lecture.title} — VVZ ETH Zürich`,
    description: clean(lecture.abstract).slice(0, 200),
  };
}

function Field({ label, children }) {
  if (!children) return null;
  return (
    <div>
      <h3 className="text-xs font-semibold uppercase tracking-wider text-base-content/50 mb-1">
        {label}
      </h3>
      <div className="text-xs text-base-content/80 leading-relaxed whitespace-pre-line">
        {children}
      </div>
    </div>
  );
}

export default async function LecturePage({ params, searchParams }) {
  const { number } = await params;
  const semester = (await searchParams)?.semester || "";
  const lecture = await getLecture(number, semester);

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
        <div className="max-w-6xl mx-auto px-3 sm:px-4 pt-6 sm:pt-4 pb-8 sm:pb-6">
          <div className="flex items-start justify-between">
            <BackButton />
            <ThemeToggle />
          </div>
          <h1 className="text-sm sm:text-lg font-bold tracking-tight mt-2 leading-snug">
            {lecture.title}
          </h1>
          <div className="flex flex-wrap items-center gap-2 mt-2">
            <span className="badge badge-outline badge-sm font-mono text-xs">
              {lecture.number}
            </span>
            <span className="badge badge-soft badge-sm text-xs">
              {lecture.type || "—"}
            </span>
            {lecture.language && (
              <span className="badge badge-outline badge-sm text-xs text-white">
                {clean(lecture.language)}
              </span>
            )}
            {lecture.periodicity && (
              <span className="text-xs opacity-70">{clean(lecture.periodicity)}</span>
            )}
            {lecture.ects && (
              <span className="text-xs opacity-80">{clean(lecture.ects)}</span>
            )}
            {lecture.hours && (
              <span className="text-xs opacity-80">{clean(lecture.hours)}</span>
            )}
          </div>
          <div className="flex flex-wrap items-start justify-between gap-2 mt-1">
            <div className="min-w-0">
              {lecturerNames && (
                <p className="text-xs opacity-70">{lecturerNames}</p>
              )}
            </div>
            {lecture.url && (
              <a
                href={lecture.url}
                target="_blank"
                rel="noopener noreferrer"
                className="btn btn-xs btn-outline border-white/30 text-white hover:bg-white/20 shrink-0"
              >
                Open in VVZ
              </a>
            )}
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-3 sm:px-4 -mt-4">
        <div className="card card-border border-base-300 bg-base-100 shadow-sm">
          <div className="card-body p-4 sm:p-5 space-y-4">
            <Field label="Abstract">{clean(lecture.abstract)}</Field>
            <Field label="Learning Objectives">{clean(lecture.learning_objective)}</Field>
            <Field label="Content">{clean(lecture.content)}</Field>
            <Field label="Lecture Notes">{clean(lecture.lecture_notes)}</Field>
            <Field label="Literature">{clean(lecture.literature)}</Field>
            <Field label="Performance Assessment">{clean(lecture.performance_assessment)}</Field>

            {lecture.offered_in && lecture.offered_in.length > 0 && (
              <div>
                <h3 className="text-xs font-semibold uppercase tracking-wider text-base-content/50 mb-1">
                  Offered in
                </h3>
                <div className="space-y-1">
                  {lecture.offered_in.map((item, i) => (
                    <div key={i} className="flex items-center gap-1 text-xs flex-wrap -mx-1 px-1 py-1">
                      <Link
                        href={offeredInHref(item, 0)}
                        className="font-medium text-base-content/80 hover:text-primary active:text-primary hover:bg-base-200 active:bg-base-300 -mx-1 px-1.5 py-0.5 rounded transition-colors"
                      >
                        {item.programme}
                      </Link>
                      {item.section && (
                        <>
                          <span className="text-base-content/30 select-none">›</span>
                          <Link
                            href={offeredInHref(item, 1)}
                            className="text-base-content/70 hover:text-secondary active:text-secondary hover:bg-base-200 active:bg-base-300 -mx-1 px-1.5 py-0.5 rounded transition-colors"
                          >
                            {item.section}
                          </Link>
                        </>
                      )}
                      {item.sub_section && (
                        <>
                          <span className="text-base-content/30 select-none">›</span>
                          <Link
                            href={offeredInHref(item, 2)}
                            className="text-base-content/60 hover:text-secondary active:text-secondary hover:bg-base-200 active:bg-base-300 -mx-1 px-1.5 py-0.5 rounded transition-colors"
                          >
                            {item.sub_section}
                          </Link>
                        </>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="pt-2" />
          </div>
        </div>

        <SimilarClient number={number} semester={semester} />
      </main>
    </div>
  );
}
