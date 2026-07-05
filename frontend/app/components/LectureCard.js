"use client";

import { useState } from "react";
import Link from "next/link";
import Field from "./Field";

const clean = (s) => (s || "").replace(/\xa0/g, " ");

export default function LectureCard({ lecture }) {
  const [expanded, setExpanded] = useState(false);
  const lecturerNames = (lecture.lecturers || []).map((l) => l.name).join(", ");

  return (
    <div className="card card-border border-base-300 bg-base-100 shadow-sm hover:shadow-md transition-shadow">
      <div
        className="card-body p-4 sm:p-4 cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex flex-wrap items-start justify-between gap-2 sm:gap-2">
          <div className="sm:flex-1 min-w-0 w-full sm:w-auto">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="badge badge-outline badge-md shrink-0 font-mono text-xs">
                {lecture.number}
              </span>
              <span className="badge badge-soft badge-primary badge-md shrink-0">
                {lecture.type || "—"}
              </span>
              {lecture.language && (
                <span className="badge badge-outline badge-xs shrink-0 text-base-content">
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
                <span className="text-xs text-base-content/50 shrink-0 ml-auto">
                  {clean(lecture.ects)}
                </span>
              )}
            </div>
            <h3 className="text-lg font-semibold mt-2 leading-snug">
              {lecture.title}
            </h3>
          </div>
        </div>

        <div className="flex items-center justify-between gap-2 mt-2">
          {lecturerNames ? (
            <div className="flex items-center gap-2 min-w-0">
              <svg className="size-4 opacity-50 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
              <span className="text-sm text-base-content/60 truncate">{lecturerNames}</span>
            </div>
          ) : (
            <div />
          )}
          <Link
            href={`/lectures/${encodeURIComponent(lecture.number)}/`}
            className="btn btn-primary btn-xs sm:btn-sm shrink-0"
            onClick={(e) => e.stopPropagation()}
          >
            Details
          </Link>
        </div>

        {!expanded && lecture.abstract && (
          <p className="text-sm text-base-content/70 mt-3 line-clamp-3 leading-relaxed">
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

            {/* TODO: replace mock schedule with real data once scraped */}
            {lecture._mockSchedule && (
              <div>
                <h4 className="text-xs font-semibold uppercase tracking-wider text-base-content/50 mb-1">
                  Schedule
                </h4>
                <div className="text-xs text-base-content/50 space-y-1">
                  {lecture._mockSchedule.map((s, i) => (
                    <div key={i} className="flex gap-2">
                      <span className="font-medium w-8 shrink-0">{s.day}</span>
                      <span>{s.time}</span>
                      <span className="text-base-content/30">{s.room}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
