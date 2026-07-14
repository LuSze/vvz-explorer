"use client";

import { useState } from "react";
import Link from "next/link";
import Field from "./Field";

const clean = (s) => (s || "").replace(/\xa0/g, " ");

export default function LectureCard({ lecture, minimal, semester }) {
  const [expanded, setExpanded] = useState(false);
  const lecturerNames = (lecture.lecturers || []).map((l) => l.name).join(", ");

  return (
    <div className="card card-border border-base-300 bg-base-100 shadow-sm hover:shadow-md transition-shadow">
      <div
        className="card-body p-4 sm:p-4 cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-start justify-between gap-1">
          <div className="flex items-center gap-1 flex-wrap min-w-0">
            <span className="badge badge-outline badge-sm shrink-0 font-mono text-xs">
              {lecture.number}
            </span>
            <span className="badge badge-soft badge-primary badge-sm shrink-0 text-xs">
              {lecture.type || "—"}
            </span>
            {lecture.language && (
              <span className="badge badge-outline badge-xs shrink-0 text-base-content text-xs">
                {clean(lecture.language)}
              </span>
            )}
            {lecture.periodicity && (
              <span className="text-xs text-base-content/40 shrink-0 hidden sm:inline">
                {clean(lecture.periodicity)}
              </span>
            )}
            {lecture.hours && (
              <span className="text-xs text-base-content/50 shrink-0">
                {clean(lecture.hours)}
              </span>
            )}
            {lecture.ects && (
              <span className="text-xs text-base-content/50 shrink-0">
                {clean(lecture.ects)}
              </span>
            )}
            {lecturerNames && (
              <span className="text-xs text-base-content/60 truncate min-w-0">
                {lecturerNames}
              </span>
            )}
          </div>
          <Link
            href={`/lectures/${encodeURIComponent(lecture.number)}/${semester ? `?semester=${encodeURIComponent(semester)}` : ""}`}
            className="btn btn-primary btn-xs shrink-0"
            onClick={(e) => e.stopPropagation()}
          >
            Details
          </Link>
        </div>

        <h3 className="text-sm font-semibold leading-snug mt-1">
          {lecture.title}
        </h3>

        {!expanded && !minimal && lecture.abstract && (
          <p className="text-xs text-base-content/70 mt-2 line-clamp-3 leading-relaxed">
            {clean(lecture.abstract)}
          </p>
        )}

        {expanded && (
          <div className="mt-4 space-y-4 pt-4 border-t border-base-300">
            <Field label="Abstract">{clean(lecture.abstract)}</Field>
            <Field label="Learning Objectives">{clean(lecture.learning_objective)}</Field>
            <Field label="Content">{clean(lecture.content)}</Field>
            <Field label="Lecture Notes">{clean(lecture.lecture_notes)}</Field>
            <Field label="Literature">{clean(lecture.literature)}</Field>
            <Field label="Performance Assessment">{clean(lecture.performance_assessment)}</Field>

          </div>
        )}
      </div>
    </div>
  );
}
