"use client";

import LectureCard from "./LectureCard";

const CAT_ORDER = [
  "1. Semester", "2. Semester", "3. Semester", "4. Semester",
  "5. Semester", "6. Semester", "7. Semester", "8. Semester",
  "Basic Courses", "Core Courses", "Electives", "Majors", "Minors",
  "Seminars", "Laboratory", "Complementary Courses",
];

function catSortKey(name) {
  const i = CAT_ORDER.indexOf(name);
  return i >= 0 ? String(i).padStart(3, "0") : ("ZZZ" + (name || ""));
}

function buildCategoryTree(lectures) {
  const tree = {};
  for (const lecture of lectures) {
    const cats = lecture.categories;
    if (!cats || cats.length === 0) {
      if (!tree.__uncategorized__) tree.__uncategorized__ = [];
      if (!tree.__uncategorized__.find((l) => l.number === lecture.number))
        tree.__uncategorized__.push(lecture);
      continue;
    }
    for (const cat of cats) {
      const c1 = cat.cat1 || "Other";
      if (!tree[c1]) tree[c1] = {};
      const c2 = cat.cat2 || "";
      if (!tree[c1][c2]) tree[c1][c2] = {};
      const c3 = cat.cat3 || "";
      if (!tree[c1][c2][c3]) tree[c1][c2][c3] = [];
      if (!tree[c1][c2][c3].find((l) => l.number === lecture.number))
        tree[c1][c2][c3].push(lecture);
    }
  }
  return tree;
}

export default function GroupedResults({ lectures, activeCat1Name, activeCat2Name, minimal, semester }) {
  const tree = buildCategoryTree(lectures);
  let keys = Object.keys(tree).filter((k) => k !== "__uncategorized__");
  keys.sort((a, b) => catSortKey(a).localeCompare(catSortKey(b)));
  if (activeCat1Name) {
    keys = keys.filter((k) => k === activeCat1Name);
  }

  return (
    <>
      {keys.map((cat1) => {
        const cat2Map = tree[cat1];
        let cat2Keys = Object.keys(cat2Map).sort((a, b) => {
          if (!a) return 1;
          if (!b) return -1;
          return a.localeCompare(b);
        });
        if (activeCat2Name) {
          cat2Keys = cat2Keys.filter((c2) => c2 === activeCat2Name);
        }
        return (
          <div key={cat1} className="mb-4">
            <h2 className="text-xs font-bold text-base-content/70 uppercase tracking-wider mb-2">
              {cat1}
            </h2>
            {cat2Keys.map((cat2) => {
              const cat3Map = cat2Map[cat2];
              const cat3Keys = Object.keys(cat3Map).sort((a, b) => {
                if (!a) return 1;
                if (!b) return -1;
                return a.localeCompare(b);
              });
              return (
                <div key={cat2} className="mb-3 ml-0 sm:ml-4">
                  {cat2 && (
                    <h3 className="text-xs font-semibold text-base-content/60 mb-1">
                      {cat2}
                    </h3>
                  )}
                  {cat3Keys.map((cat3) => {
                    const lectures = cat3Map[cat3];
                    return (
                      <div key={cat3} className="mb-2 ml-0 sm:ml-4">
                        {cat3 && (
                          <h4 className="text-[10px] font-medium text-base-content/50 uppercase tracking-wider mb-1">
                            {cat3}
                          </h4>
                        )}
                        <div className="space-y-1.5">
                          {lectures.map((l) => (
                            <LectureCard key={l.number} lecture={l} minimal={minimal} semester={semester} />
                          ))}
                        </div>
                      </div>
                    );
                  })}
                </div>
              );
            })}
          </div>
        );
      })}
      {tree.__uncategorized__ && tree.__uncategorized__.length > 0 && (
        <div className="mb-4">
          <h2 className="text-xs font-bold text-base-content/70 uppercase tracking-wider mb-2">
            Other
          </h2>
          <div className="space-y-1.5">
            {tree.__uncategorized__.map((l) => (
              <LectureCard key={l.number} lecture={l} minimal={minimal} semester={semester} />
            ))}
          </div>
        </div>
      )}
    </>
  );
}
