"use client";

import { useRouter } from "next/navigation";

export default function BackButton() {
  const router = useRouter();
  return (
    <button
      onClick={() => router.back()}
      className="text-sm opacity-70 hover:opacity-100 transition-opacity cursor-pointer min-h-[44px] flex items-center"
    >
      &larr; Back to search
    </button>
  );
}
