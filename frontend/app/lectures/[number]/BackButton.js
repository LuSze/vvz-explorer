"use client";

import { useRouter } from "next/navigation";

export default function BackButton() {
  const router = useRouter();
  return (
    <button
      onClick={() => router.back()}
      className="text-xs opacity-70 hover:opacity-100 transition-opacity cursor-pointer min-h-[36px] flex items-center"
    >
      &larr; Back to search
    </button>
  );
}
