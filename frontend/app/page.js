"use client";

import { useState, useEffect, useCallback, useRef, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import ThemeToggle from "./ThemeToggle";
import SearchableDropdown from "./SearchableDropdown";
import LectureCard from "./components/LectureCard";
import GroupedResults from "./components/GroupedResults";

const SEMESTERS = [
  { value: "2026W", label: "HS2026" },
  { value: "2026S", label: "FS2026" },
  { value: "2025W", label: "HS2025" },
  { value: "2025S", label: "FS2025" },
  { value: "2024W", label: "HS2024" },
];

const MODES = [
  { key: "text", label: "Text Search" },
  { key: "semantic", label: "Semantic Search" },
];

const FIELD_OPTIONS = [
  { key: "title", label: "Title" },
  { key: "number", label: "Number" },
  { key: "lecturer", label: "Lecturer" },
  { key: "abstract", label: "Abstract" },
  { key: "content", label: "Content" },
  { key: "learning_objective", label: "Learning Objectives" },
  { key: "lecture_notes", label: "Lecture Notes" },
  { key: "literature", label: "Literature" },
  { key: "performance_assessment", label: "Performance Assessment" },
];

const PAGE_SIZE = 20;

// MOCK schedule data — remove once real schedule scraping is implemented
const MOCK_SCHEDULE = [
  { day: "Mon", time: "10:15–12:00", room: "HG D 3.2" },
  { day: "Tue", time: "13:15–14:00", room: "HG D 3.2" },
];

function SearchPage() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const [query, setQuery] = useState(searchParams.get("q") || "");
  const [mode, setMode] = useState(searchParams.get("mode") || "text");
  const [semester, setSemester] = useState(
    SEMESTERS.find((s) => s.value === searchParams.get("semester")) || SEMESTERS[0]
  );
  const [results, setResults] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState(null);
  const [selectedTrack, setSelectedTrack] = useState(searchParams.get("study_track") || "");
  const [selectedFields, setSelectedFields] = useState(
    searchParams.get("fields") ? searchParams.get("fields").split(",") : []
  );
  const [tracks, setTracks] = useState([]);
  const [trackSearch, setTrackSearch] = useState("");
  const [trackOpen, setTrackOpen] = useState(false);
  const [trackHighlight, setTrackHighlight] = useState(-1);
  const trackHighlightRef = useRef(-1);
  const trackListRef = useRef(null);
  const sentinelRef = useRef(null);

  // Auto-search debounce
  const searchDebounceRef = useRef(null);
  const searchKeyRef = useRef("");

  // Category hierarchy
  const [catLevel1, setCatLevel1] = useState(null);
  const [catLevel2, setCatLevel2] = useState(null);
  const [catLevel3, setCatLevel3] = useState(null);
  const [catLevel1Opts, setCatLevel1Opts] = useState([]);
  const [catLevel2Opts, setCatLevel2Opts] = useState([]);
  const [catLevel3Opts, setCatLevel3Opts] = useState([]);
  const [catLoading1, setCatLoading1] = useState(false);
  const [catLoading2, setCatLoading2] = useState(false);
  const [catLoading3, setCatLoading3] = useState(false);

  // Smart suggest
  const [suggestions, setSuggestions] = useState([]);
  const [suggestOpen, setSuggestOpen] = useState(false);
  const [suggestHighlight, setSuggestHighlight] = useState(-1);
  const [suggestLoading, setSuggestLoading] = useState(false);
  const suggestHighlightRef = useRef(-1);
  const suggestTimerRef = useRef(null);

  const triggerSearch = useCallback(async (q, m, track, fields, p = 1, append = false, l1, l2, l3) => {
    if (!q.trim() && !track) return;
    if (append) {
      setLoadingMore(true);
    } else {
      setLoading(true);
    }
    setError(null);
    try {
      if (m === "semantic") {
        if (!q.trim()) { setLoading(false); return; }
        let url = `/api/search/?q=${encodeURIComponent(q)}&k=20`;
        if (track) url += `&study_track=${encodeURIComponent(track)}`;
        const res = await fetch(url);
        if (!res.ok) throw new Error((await res.json()).error || "Search failed");
        const data = await res.json();
        const patched = (data.results || []).map((r) => ({
          ...r,
          _mockSchedule: MOCK_SCHEDULE,
        }));
        setResults(patched);
        setTotal(patched.length);
        setPage(1);
        if (patched.length === 0) setError("No lectures found.");
      } else {
        let url = `/api/lectures/?search=${encodeURIComponent(q)}&page=${p}&page_size=${PAGE_SIZE}`;
        if (track) url += `&study_track=${encodeURIComponent(track)}`;
        if (fields) url += `&fields=${encodeURIComponent(fields)}`;
        if (l1) url += `&level1_id=${l1}`;
        if (l2) url += `&level2_id=${l2}`;
        if (l3) url += `&level3_id=${l3}`;
        const res = await fetch(url);
        if (!res.ok) throw new Error((await res.json()).error || "Search failed");
        const data = await res.json();
        if (append) {
          const patchedAppend = (data.results || []).map((r) => ({
            ...r,
            _mockSchedule: MOCK_SCHEDULE,
          }));
          setResults((prev) => [...prev, ...patchedAppend]);
        } else {
          const patched = (data.results || []).map((r) => ({
            ...r,
            _mockSchedule: MOCK_SCHEDULE,
          }));
          setResults(patched);
          if (patched.length === 0 && data.total === 0) setError("No lectures found.");
        }
        setTotal(data.total || 0);
        setPage(p);
      }
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  }, []);

  useEffect(() => {
    fetch("/api/study-tracks/")
      .then((r) => r.json())
      .then((d) => setTracks(d.results || []))
      .catch(() => {});
  }, []);

  // Fetch level-1 categories when study track changes
  useEffect(() => {
    if (!selectedTrack) {
      setCatLevel1Opts([]);
      setCatLevel2Opts([]);
      setCatLevel3Opts([]);
      setCatLevel1(null);
      setCatLevel2(null);
      setCatLevel3(null);
      return;
    }
    setCatLoading1(true);
    setCatLevel1(null);
    setCatLevel2(null);
    setCatLevel3(null);
    setCatLevel2Opts([]);
    setCatLevel3Opts([]);
    fetch(`/api/categories/level1/?study_track=${encodeURIComponent(selectedTrack)}`)
      .then((r) => r.json())
      .then((d) => {
        const opts = d.results || [];
        setCatLevel1Opts(opts);
        const l1 = searchParams.get("level1_id");
        if (l1) {
          const match = opts.find((o) => o.id === parseInt(l1));
          if (match) setCatLevel1(match);
        }
      })
      .catch(() => setCatLevel1Opts([]))
      .finally(() => setCatLoading1(false));
  }, [selectedTrack]);

  // Fetch level-2 categories when level-1 changes
  useEffect(() => {
    if (!selectedTrack || !catLevel1) {
      setCatLevel2Opts([]);
      setCatLevel3Opts([]);
      setCatLevel2(null);
      setCatLevel3(null);
      return;
    }
    setCatLoading2(true);
    setCatLevel2(null);
    setCatLevel3(null);
    setCatLevel3Opts([]);
    fetch(`/api/categories/level2/?study_track=${encodeURIComponent(selectedTrack)}&level1_id=${catLevel1.id}`)
      .then((r) => r.json())
      .then((d) => {
        const opts = d.results || [];
        setCatLevel2Opts(opts);
        const l2 = searchParams.get("level2_id");
        if (l2) {
          const match = opts.find((o) => o.id === parseInt(l2));
          if (match) setCatLevel2(match);
        }
      })
      .catch(() => setCatLevel2Opts([]))
      .finally(() => setCatLoading2(false));
  }, [catLevel1, selectedTrack]);

  // Fetch level-3 categories when level-2 changes
  useEffect(() => {
    if (!selectedTrack || !catLevel1 || !catLevel2) {
      setCatLevel3Opts([]);
      setCatLevel3(null);
      return;
    }
    setCatLoading3(true);
    setCatLevel3(null);
    fetch(`/api/categories/level3/?study_track=${encodeURIComponent(selectedTrack)}&level1_id=${catLevel1.id}&level2_id=${catLevel2.id}`)
      .then((r) => r.json())
      .then((d) => {
        const opts = d.results || [];
        setCatLevel3Opts(opts);
        const l3 = searchParams.get("level3_id");
        if (l3) {
          const match = opts.find((o) => o.id === parseInt(l3));
          if (match) setCatLevel3(match);
        }
      })
      .catch(() => setCatLevel3Opts([]))
      .finally(() => setCatLoading3(false));
  }, [catLevel2, catLevel1, selectedTrack]);

  // Smart suggest: debounced fetch when query changes
  useEffect(() => {
    if (suggestTimerRef.current) clearTimeout(suggestTimerRef.current);
    if (!query.trim() || query.length < 2) {
      setSuggestions([]);
      setSuggestOpen(false);
      return;
    }
    suggestTimerRef.current = setTimeout(() => {
      setSuggestLoading(true);
      fetch(`/api/suggest/?q=${encodeURIComponent(query)}&limit=8`)
        .then((r) => r.json())
        .then((d) => {
          const items = d.results || [];
          setSuggestions(items);
          setSuggestOpen(items.length > 0);
          setSuggestHighlight(-1);
        })
        .catch(() => { setSuggestions([]); setSuggestOpen(false); })
        .finally(() => setSuggestLoading(false));
    }, 250);
    return () => { if (suggestTimerRef.current) clearTimeout(suggestTimerRef.current); };
  }, [query]);

  useEffect(() => {
    suggestHighlightRef.current = suggestHighlight;
  }, [suggestHighlight]);

  // Auto-search: debounce when query/filters change (text mode only)
  useEffect(() => {
    if (mode === "semantic") return;
    const hasQuery = query.trim().length > 0;
    const hasAnyFilter = hasQuery || !!selectedTrack || selectedFields.length > 0;
    if (!hasAnyFilter) {
      setResults([]);
      setTotal(0);
      return;
    }

    const urlL1 = searchParams.get("level1_id");
    const urlL2 = searchParams.get("level2_id");
    const urlL3 = searchParams.get("level3_id");
    const effectiveL1 = catLevel1?.id ?? (urlL1 ? parseInt(urlL1) : null);
    const effectiveL2 = catLevel2?.id ?? (urlL2 ? parseInt(urlL2) : null);
    const effectiveL3 = catLevel3?.id ?? (urlL3 ? parseInt(urlL3) : null);
    const key = `${query.trim()}|${mode}|${semester.value}|${selectedTrack}|${selectedFields.join(",")}|${effectiveL1 ?? ""}|${effectiveL2 ?? ""}|${effectiveL3 ?? ""}`;
    if (key === searchKeyRef.current) return;

    if (searchDebounceRef.current) clearTimeout(searchDebounceRef.current);

    searchDebounceRef.current = setTimeout(() => {
      searchKeyRef.current = key;
      const params = new URLSearchParams();
      if (hasQuery) params.set("q", query.trim());
      params.set("mode", mode);
      params.set("semester", semester.value);
      if (selectedTrack) params.set("study_track", selectedTrack);
      if (selectedFields.length) params.set("fields", selectedFields.join(","));
      if (effectiveL1) params.set("level1_id", effectiveL1);
      if (effectiveL2) params.set("level2_id", effectiveL2);
      if (effectiveL3) params.set("level3_id", effectiveL3);
      router.replace(`/?${params.toString()}`, { scroll: false });
      triggerSearch(query, mode, selectedTrack, selectedFields.join(","), 1, false, effectiveL1, effectiveL2, effectiveL3);
    }, hasQuery ? 350 : 0);

    return () => {
      if (searchDebounceRef.current) clearTimeout(searchDebounceRef.current);
    };
  }, [query, mode, semester, selectedTrack, selectedFields, catLevel1, catLevel2, catLevel3]);

  const handleSearch = () => {
    const urlL1 = searchParams.get("level1_id");
    const urlL2 = searchParams.get("level2_id");
    const urlL3 = searchParams.get("level3_id");
    const effectiveL1 = catLevel1?.id ?? (urlL1 ? parseInt(urlL1) : null);
    const effectiveL2 = catLevel2?.id ?? (urlL2 ? parseInt(urlL2) : null);
    const effectiveL3 = catLevel3?.id ?? (urlL3 ? parseInt(urlL3) : null);
    const params = new URLSearchParams();
    if (query) params.set("q", query);
    params.set("mode", mode);
    params.set("semester", semester.value);
    if (selectedTrack) params.set("study_track", selectedTrack);
    if (selectedFields.length) params.set("fields", selectedFields.join(","));
    if (effectiveL1) params.set("level1_id", effectiveL1);
    if (effectiveL2) params.set("level2_id", effectiveL2);
    if (effectiveL3) params.set("level3_id", effectiveL3);
    const qs = params.toString();
    router.replace(qs ? `/?${qs}` : "/", { scroll: false });
    searchKeyRef.current = `${query.trim()}|${mode}|${semester.value}|${selectedTrack}|${selectedFields.join(",")}|${effectiveL1 ?? ""}|${effectiveL2 ?? ""}|${effectiveL3 ?? ""}`;
    if (searchDebounceRef.current) clearTimeout(searchDebounceRef.current);
    triggerSearch(query, mode, selectedTrack, selectedFields.join(","), 1, false, effectiveL1, effectiveL2, effectiveL3);
  };

  const handleLoadMore = () => {
    const nextPage = page + 1;
    const params = new URLSearchParams();
    params.set("q", query);
    params.set("mode", mode);
    params.set("semester", semester.value);
    params.set("page", nextPage.toString());
    if (selectedTrack) params.set("study_track", selectedTrack);
    if (selectedFields.length) params.set("fields", selectedFields.join(","));
    if (catLevel1?.id) params.set("level1_id", catLevel1.id);
    if (catLevel2?.id) params.set("level2_id", catLevel2.id);
    if (catLevel3?.id) params.set("level3_id", catLevel3.id);
    router.replace(`/?${params.toString()}`, { scroll: false });
    triggerSearch(query, mode, selectedTrack, selectedFields.join(","), nextPage, true, catLevel1?.id, catLevel2?.id, catLevel3?.id);
  };

  const handleKeyDown = (e) => {
    const cur = suggestHighlightRef.current;
    if (suggestOpen && suggestions.length > 0) {
      if (e.key === "ArrowDown") {
        e.preventDefault();
        setSuggestHighlight(cur < suggestions.length - 1 ? cur + 1 : 0);
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        setSuggestHighlight(cur > 0 ? cur - 1 : suggestions.length - 1);
      } else if (e.key === "Enter" && cur >= 0) {
        e.preventDefault();
        handleSuggestSelect(suggestions[cur]);
      } else if (e.key === "Escape") {
        setSuggestOpen(false);
        setSuggestHighlight(-1);
      } else if (e.key === "Enter") {
        handleSearch();
      }
    } else {
      if (e.key === "Enter") handleSearch();
    }
  };

  const handleModeSwitch = (m) => {
    setMode(m);
  };

  const handleSuggestSelect = async (suggestion) => {
    setSuggestOpen(false);
    setSuggestHighlight(-1);
    setQuery("");
    const { type, value, id, study_track, level1_id, level1_name, level2_id, level2_name } = suggestion;

    if (type === "study_track") {
      setSelectedTrack(value);
      setCatLevel1(null);
      setCatLevel2(null);
      setCatLevel3(null);
      return;
    }

    if (type === "category_l1") {
      const track = study_track || selectedTrack;
      if (!track) return;
      if (selectedTrack !== track) setSelectedTrack(track);
      setCatLevel2(null);
      setCatLevel3(null);
      const res = await fetch(`/api/categories/level1/?study_track=${encodeURIComponent(track)}`);
      const data = await res.json();
      const opts = data.results || [];
      setCatLevel1Opts(opts);
      const match = opts.find((o) => o.id === id);
      if (match) setCatLevel1(match);
      return;
    }

    if (type === "category_l2") {
      const track = study_track || selectedTrack;
      if (!track || !level1_id) return;
      if (selectedTrack !== track) setSelectedTrack(track);
      setCatLevel3(null);
      const [l1Data, l2Data] = await Promise.all([
        fetch(`/api/categories/level1/?study_track=${encodeURIComponent(track)}`).then((r) => r.json()),
        fetch(`/api/categories/level2/?study_track=${encodeURIComponent(track)}&level1_id=${level1_id}`).then((r) => r.json()),
      ]);
      const l1Opts = l1Data.results || [];
      const l2Opts = l2Data.results || [];
      setCatLevel1Opts(l1Opts);
      setCatLevel2Opts(l2Opts);
      const l1Match = l1Opts.find((o) => o.id === level1_id);
      if (l1Match) setCatLevel1(l1Match);
      const l2Match = l2Opts.find((o) => o.id === id);
      if (l2Match) setCatLevel2(l2Match);
      return;
    }

    if (type === "category_l3") {
      const track = study_track || selectedTrack;
      if (!track || !level1_id || !level2_id) return;
      if (selectedTrack !== track) setSelectedTrack(track);
      const [l1Data, l2Data, l3Data] = await Promise.all([
        fetch(`/api/categories/level1/?study_track=${encodeURIComponent(track)}`).then((r) => r.json()),
        fetch(`/api/categories/level2/?study_track=${encodeURIComponent(track)}&level1_id=${level1_id}`).then((r) => r.json()),
        fetch(`/api/categories/level3/?study_track=${encodeURIComponent(track)}&level1_id=${level1_id}&level2_id=${level2_id}`).then((r) => r.json()),
      ]);
      const l1Opts = l1Data.results || [];
      const l2Opts = l2Data.results || [];
      const l3Opts = l3Data.results || [];
      setCatLevel1Opts(l1Opts);
      setCatLevel2Opts(l2Opts);
      setCatLevel3Opts(l3Opts);
      const l1Match = l1Opts.find((o) => o.id === level1_id);
      if (l1Match) setCatLevel1(l1Match);
      const l2Match = l2Opts.find((o) => o.id === level2_id);
      if (l2Match) setCatLevel2(l2Match);
      const l3Match = l3Opts.find((o) => o.id === id);
      if (l3Match) setCatLevel3(l3Match);
      return;
    }

    if (type === "lecturer" || type === "course_number" || type === "course_title") {
      setQuery(value);
    }
  };

  const handleBreadcrumbClick = (level) => {
    if (level === "track") {
      setSelectedTrack("");
      setCatLevel1(null);
      setCatLevel2(null);
      setCatLevel3(null);
      return;
    }
    if (level === "l1") {
      setCatLevel2(null);
      setCatLevel3(null);
      return;
    }
    if (level === "l2") {
      setCatLevel3(null);
    }
  };

  const toggleField = (key) => {
    setSelectedFields((prev) =>
      prev.includes(key) ? prev.filter((f) => f !== key) : [...prev, key]
    );
  };

  const handleReset = () => {
    setQuery("");
    setMode("text");
    setSelectedTrack("");
    setSelectedFields([]);
    setResults([]);
    setTotal(0);
    setPage(1);
    setError(null);
    setTrackSearch("");
    setTrackOpen(false);
    setCatLevel1(null);
    setCatLevel2(null);
    setCatLevel3(null);
    setCatLevel1Opts([]);
    setCatLevel2Opts([]);
    setCatLevel3Opts([]);
    setSuggestions([]);
    setSuggestOpen(false);
    searchKeyRef.current = "";
    if (searchDebounceRef.current) clearTimeout(searchDebounceRef.current);
    router.replace("/", { scroll: false });
  };

  const filteredTracks = tracks.filter((t) =>
    t.toLowerCase().includes(trackSearch.toLowerCase())
  );

  const handleTrackKeyDown = (e) => {
    const cur = trackHighlightRef.current;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      const next = cur < filteredTracks.length - 1 ? cur + 1 : 0;
      setTrackHighlight(next);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      const next = cur > 0 ? cur - 1 : filteredTracks.length - 1;
      setTrackHighlight(next);
    } else if (e.key === "Enter" && cur >= 0) {
      e.preventDefault();
      const selected = filteredTracks[cur];
      if (selected) {
        setSelectedTrack(selected);
      } else {
        setSelectedTrack("");
      }
      setTrackOpen(false);
      setTrackSearch("");
    } else if (e.key === "Escape") {
      setTrackOpen(false);
      setTrackSearch("");
    }
  };

  useEffect(() => {
    trackHighlightRef.current = trackHighlight;
  }, [trackHighlight]);

  useEffect(() => {
    setTrackHighlight(filteredTracks.length > 0 ? 0 : -1);
  }, [trackSearch, filteredTracks.length]);

  // Dynamic page title — runs after every render to correct
  // any overwrite from router.replace or layout metadata
  useEffect(() => {
    const q = query.trim();
    const parts = [];
    if (q && mode === "semantic") parts.push("Semantic: " + q);
    else if (q) parts.push("Search: " + q);
    if (selectedTrack) parts.push(selectedTrack);
    const title = parts.length > 0
      ? parts.join(" — ") + " — VVZ ETH Zürich"
      : "Course Catalog — VVZ ETH Zürich";
    if (document.title !== title) document.title = title;
  });

  useEffect(() => {
    const el = sentinelRef.current;
    if (!el || results.length >= total || mode !== "text") return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !loadingMore && !loading) {
          handleLoadMore();
        }
      },
      { rootMargin: "200px" }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, [results.length, total, mode, loadingMore, loading]);

  return (
    <div className="min-h-screen bg-base-200">
      <header className="bg-primary text-primary-content shadow-sm">
        <div className="max-w-4xl mx-auto px-4 py-5 sm:py-6">
          <div className="flex items-center gap-2 mb-0.5">
            <svg className="size-5 sm:size-5 opacity-80 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
            <h1 className="text-lg sm:text-2xl font-bold tracking-tight">Course Catalog Explorer</h1>
          </div>
          <div className="flex items-center justify-between">
            <p className="text-xs sm:text-base opacity-80">
              Search ETH Zurich lectures
            </p>
            <ThemeToggle />
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 -mt-4">
        <div className="card card-border border-base-300 bg-base-100 shadow-sm">
          <div className="card-body p-4 sm:p-4 space-y-3 sm:space-y-3">
            <div className="flex items-center justify-between gap-2 max-sm:flex-wrap">
              <div className="flex gap-2 max-sm:gap-1.5">
                {MODES.map((m) => (
                  <button
                    key={m.key}
                    className={`btn btn-sm min-h-[38px] ${mode === m.key ? "btn-primary" : "btn-soft btn-neutral"}`}
                    onClick={() => handleModeSwitch(m.key)}
                  >
                    {m.label}
                  </button>
                ))}
              </div>
              <SearchableDropdown
                label=""
                options={SEMESTERS}
                value={semester}
                onChange={(opt) => setSemester(opt || SEMESTERS[0])}
                placeholder="Semester"
                searchPlaceholder="Search semester…"
                className="w-40 max-sm:w-full"
              />
            </div>

            <div className="relative">
              {/* Desktop: joined horizontal bar */}
              <div className="join w-full max-sm:hidden">
                <input
                  type="text"
                  placeholder={mode === "semantic" ? "Describe what you want to learn…" : "Search lectures by keyword…"}
                  className="input join-item input-bordered w-full min-h-[44px] sm:min-h-[44px] text-sm sm:text-base"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={handleKeyDown}
                />
                <button
                  className="btn join-item btn-primary min-h-[44px] sm:min-h-[44px] px-6 sm:px-8 text-sm sm:text-base"
                  onClick={handleSearch}
                  disabled={loading}
                >
                  {loading ? <span className="loading loading-spinner loading-md" /> : "Search"}
                </button>
                {(query || results.length > 0 || selectedTrack || selectedFields.length > 0) && (
                  <button
                    className="btn join-item btn-soft btn-neutral min-h-[44px] sm:min-h-[48px] px-3 sm:px-4"
                    onClick={handleReset}
                    title="Reset search"
                  >
                    <svg className="size-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                )}
              </div>
              {/* Mobile: stacked input + buttons */}
              <div className="flex flex-col gap-2 sm:hidden">
                <input
                  type="text"
                  placeholder={mode === "semantic" ? "Describe what you want to learn…" : "Search lectures by keyword…"}
                  className="input input-bordered w-full min-h-[44px] text-sm"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={handleKeyDown}
                />
                <div className="flex gap-2">
                  <button
                    className="btn btn-primary flex-1 min-h-[44px] text-sm"
                    onClick={handleSearch}
                    disabled={loading}
                  >
                    {loading ? <span className="loading loading-spinner loading-md" /> : "Search"}
                  </button>
                  {(query || results.length > 0 || selectedTrack || selectedFields.length > 0) && (
                    <button
                      className="btn btn-soft btn-neutral min-h-[44px] px-3"
                      onClick={handleReset}
                      title="Reset search"
                    >
                      <svg className="size-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  )}
                </div>
              </div>

              {suggestOpen && suggestions.length > 0 && (
                <>
                <div className="fixed inset-0 z-20" onClick={() => { setSuggestOpen(false); setSuggestHighlight(-1); }} />
                <div className="absolute z-30 left-0 right-0 mt-1 bg-base-100 border border-base-300 rounded-xl shadow-xl max-h-72 overflow-y-auto">
                  {suggestions.map((s, i) => (
                    <button
                      key={`${s.type}-${s.id || s.value}-${s.study_track || ''}-${s.level1_id || ''}-${s.level2_id || ''}-${s.level3_id || ''}`}
                      className={`w-full text-left px-4 py-3 flex items-center gap-3 transition-colors ${
                        suggestHighlight === i
                          ? "bg-primary/15 text-primary"
                          : "hover:bg-base-200"
                      }`}
                      onMouseDown={(e) => { e.preventDefault(); handleSuggestSelect(s); }}
                    >
                      <span className={`badge badge-xs shrink-0 ${
                        s.type === "study_track" ? "badge-primary" :
                        s.type.startsWith("category") ? "badge-secondary" :
                        s.type.startsWith("course") ? "badge-accent" :
                        "badge-ghost"
                      }`}>
                        {s.type === "study_track" ? "Track" :
                         s.type === "category_l1" ? "L1" :
                         s.type === "category_l2" ? "L2" :
                         s.type === "category_l3" ? "L3" :
                         s.type === "lecturer" ? "Prof" :
                         s.type === "course_number" ? "Nr" :
                         s.type === "course_title" ? "Title" : "?"}
                      </span>
                      <span className="text-sm">
                        {s.breadcrumb ? s.breadcrumb.join(" › ") : s.value}
                      </span>
                    </button>
                  ))}
                </div>
                </>
              )}
            </div>

            <div className="mt-3 space-y-3 pt-3 border-t border-base-300">
              <div className="relative">
                    <label className="text-sm font-medium text-base-content/70 block mb-2">
                      Study Track
                    </label>
                    {tracks.length > 0 ? (
                      <div>
                        <button
                          type="button"
                          className="btn min-h-[48px] btn-border w-full justify-between text-base font-normal"
                          onClick={() => setTrackOpen(!trackOpen)}
                        >
                          <span className={selectedTrack ? "" : "text-base-content/40"}>
                            {selectedTrack || "All tracks"}
                          </span>
                          <svg className={`size-4 opacity-50 transition-transform ${trackOpen ? "rotate-180" : ""}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                          </svg>
                        </button>

                        {trackOpen && (
                          <>
                            <div className="fixed inset-0 z-10" onClick={() => { setTrackOpen(false); setTrackSearch(""); setTrackHighlight(-1); }} />
                             <div
                                className="absolute z-20 mt-2 w-full bg-base-100 border border-base-300 rounded-xl shadow-xl max-h-80 flex flex-col overflow-x-auto"
                              >
                              <div className="p-3 border-b border-base-300">
                                <input
                                  type="text"
                                  placeholder="Search tracks…"
                                  className="input input-bordered w-full min-h-[44px] text-sm"
                                  value={trackSearch}
                                  onClick={(e) => e.stopPropagation()}
                                  onChange={(e) => { setTrackSearch(e.target.value); setTrackHighlight(0); }}
                                  onKeyDown={handleTrackKeyDown}
                                  autoFocus
                                />
                              </div>
                              <div className="overflow-y-auto overflow-x-auto flex-1" ref={trackListRef}>
                                <button
                                  className={`w-full text-left px-4 py-3 text-sm transition-colors ${
                                    trackHighlight === -1
                                      ? "bg-primary/15 text-primary font-medium"
                                      : "hover:bg-base-200"
                                  } ${!selectedTrack ? "bg-primary/10" : ""}`}
                                  onClick={() => { setSelectedTrack(""); setTrackOpen(false); setTrackSearch(""); setTrackHighlight(-1); }}
                                >
                                  All tracks
                                </button>
                                {filteredTracks.map((t, i) => (
                                  <button
                                    key={t}
                                    className={`w-full text-left px-4 py-3 text-sm transition-colors whitespace-nowrap ${
                                      trackHighlight === i
                                        ? "bg-primary/15 text-primary font-medium"
                                        : "hover:bg-base-200"
                                    } ${selectedTrack === t ? "bg-primary/10" : ""}`}
                                    onClick={() => { setSelectedTrack(t); setTrackOpen(false); setTrackSearch(""); setTrackHighlight(-1); }}
                                  >
                                    {t}
                                  </button>
                                ))}
                                {trackSearch && filteredTracks.length === 0 && (
                                  <p className="px-4 py-6 text-sm text-base-content/40 text-center">No matching tracks</p>
                                )}
                              </div>
                            </div>
                          </>
                        )}
                      </div>
                    ) : (
                      <div className="skeleton h-12 w-72 rounded-xl" />
                    )}
                  </div>

                  {selectedTrack && (
                    <div className="space-y-3">
                      <label className="text-sm font-medium text-base-content/70 block">
                        Category Hierarchy
                      </label>
                      <SearchableDropdown
                        label="Level 1"
                        options={catLevel1Opts}
                        value={catLevel1}
                        onChange={(opt) => {
                          setCatLevel1(opt);
                          setCatLevel2(null);
                          setCatLevel3(null);
                        }}
                        placeholder="All categories"
                        searchPlaceholder="Search categories…"
                        loading={catLoading1}
                        disabled={!selectedTrack}
                      />
                      {(catLevel1 && catLevel2Opts.length > 0) || catLoading2 ? (
                        <SearchableDropdown
                          label="Level 2"
                          options={catLevel2Opts}
                          value={catLevel2}
                          onChange={(opt) => {
                            setCatLevel2(opt);
                            setCatLevel3(null);
                          }}
                          placeholder="All subcategories"
                          searchPlaceholder="Search subcategories…"
                          loading={catLoading2}
                        />
                      ) : null}
                      {catLevel2 ? (
                        <SearchableDropdown
                          label="Level 3"
                          options={catLevel3Opts}
                          value={catLevel3}
                          onChange={(opt) => {
                            setCatLevel3(opt);
                          }}
                          placeholder="All subcategories"
                          searchPlaceholder="Search subcategories…"
                          loading={catLoading3}
                        />
                      ) : null}
                    </div>
                  )}

                  {mode === "text" && (
                    <div>
                      <label className="text-sm font-medium text-base-content/70 block mb-2">
                        Search in Fields
                      </label>
                      <div className="flex flex-wrap gap-2">
                        {FIELD_OPTIONS.map((f) => (
                          <button
                            key={f.key}
                            className={`btn btn-xs min-h-[36px] px-3 rounded-full ${
                              selectedFields.includes(f.key)
                                ? "btn-primary"
                                : "btn-soft btn-neutral"
                            }`}
                            onClick={() => toggleField(f.key)}
                          >
                            {f.label}
                          </button>
                        ))}
                      </div>
                      <p className="text-xs text-base-content/40 mt-2">
                        Leave empty to search all fields
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </div>

        {(selectedTrack || catLevel1) && (
          <div className="mt-4 sm:mt-3 flex items-center gap-1.5 text-sm flex-wrap">
            {selectedTrack && (
              <>
                <button
                  className="badge badge-soft badge-primary badge-md hover:badge-outline cursor-pointer transition-colors"
                  onClick={() => handleBreadcrumbClick("track")}
                >
                  {selectedTrack.length > 35 ? selectedTrack.slice(0, 35) + "…" : selectedTrack}
                </button>
                <span className="text-base-content/30">›</span>
              </>
            )}
            {catLevel1 && (
              <>
                <button
                  className="badge badge-soft badge-secondary badge-md hover:badge-outline cursor-pointer transition-colors"
                  onClick={() => handleBreadcrumbClick("l1")}
                >
                  {catLevel1.name.length > 30 ? catLevel1.name.slice(0, 30) + "…" : catLevel1.name}
                </button>
                {catLevel2 && <span className="text-base-content/30">›</span>}
              </>
            )}
            {catLevel2 && (
              <>
                <button
                  className="badge badge-soft badge-secondary badge-md hover:badge-outline cursor-pointer transition-colors"
                  onClick={() => handleBreadcrumbClick("l2")}
                >
                  {catLevel2.name.length > 30 ? catLevel2.name.slice(0, 30) + "…" : catLevel2.name}
                </button>
                {catLevel3 && <span className="text-base-content/30">›</span>}
              </>
            )}
            {catLevel3 && (
              <span className="badge badge-soft badge-accent badge-md">
                {catLevel3.name.length > 30 ? catLevel3.name.slice(0, 30) + "…" : catLevel3.name}
              </span>
            )}
          </div>
        )}

        {loading && (
          <div className="space-y-3 sm:space-y-2 mt-4 sm:mt-3">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="card card-border border-base-300 bg-base-100 shadow-sm">
                <div className="card-body p-5 sm:p-6">
                  <div className="skeleton h-5 w-24 mb-3" />
                  <div className="skeleton h-6 w-3/4 mb-3" />
                  <div className="skeleton h-4 w-1/2" />
                </div>
              </div>
            ))}
          </div>
        )}

        {error && !loading && (
          <div className="alert alert-soft alert-info mt-4 sm:mt-3 p-4 text-sm">
            <svg className="size-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>{error}</span>
          </div>
        )}

        {results.length > 0 && !loading && (
          <div className="mt-3 sm:mt-3 mb-8 sm:mb-6">
            <p className="text-sm text-base-content/50 mb-2 sm:mb-2">
              Showing {results.length} of {total} lecture{total !== 1 ? "s" : ""}
              {selectedTrack && <span className="ml-1">in <span className="font-medium">{selectedTrack}</span></span>}
            </p>
            {results[0].categories ? (
              <GroupedResults lectures={results} />
            ) : (
              <div className="space-y-3 sm:space-y-2">
                {results.map((lecture) => (
                  <LectureCard key={lecture.number} lecture={lecture} />
                ))}
              </div>
            )}
            {results.length < total && mode === "text" && (
              <div
                ref={sentinelRef}
                className="flex justify-center py-6"
              >
                {loadingMore ? (
                  <span className="loading loading-spinner loading-md text-primary" />
                ) : (
                  <span className="text-xs text-base-content/30">Scroll for more</span>
                )}
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

export default function Home() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-base-200 flex items-center justify-center">
        <span className="loading loading-spinner loading-md" />
      </div>
    }>
      <SearchPage />
    </Suspense>
  );
}
