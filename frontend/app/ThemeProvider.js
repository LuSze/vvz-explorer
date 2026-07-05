"use client";

import { useState, useEffect } from "react";

function getPref() {
  if (typeof window === "undefined") return "auto";
  return localStorage.getItem("vvz-theme") || "auto";
}

function resolve(pref) {
  if (pref === "light") return "eth";
  if (pref === "dark") return "eth-dark";
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "eth-dark" : "eth";
}

function apply(pref) {
  document.documentElement.setAttribute("data-theme", resolve(pref));
}

export function useTheme() {
  const [pref, setPref] = useState("auto");
  const [effective, setEffective] = useState("eth");

  useEffect(() => {
    const p = getPref();
    setPref(p);
    setEffective(resolve(p));
  }, []);

  const setTheme = (p) => {
    localStorage.setItem("vvz-theme", p);
    setPref(p);
    setEffective(resolve(p));
    apply(p);
  };

  return { pref, effective, setTheme };
}

export default function ThemeProvider({ children }) {
  useEffect(() => {
    const p = getPref();
    apply(p);
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const handler = () => {
      if (getPref() === "auto") apply("auto");
    };
    mq.addEventListener("change", handler);
    return () => mq.removeEventListener("change", handler);
  }, []);

  return children;
}
