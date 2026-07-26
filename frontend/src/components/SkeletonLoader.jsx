import React from "react";

export function SkeletonRow({ className = "" }) {
  return (
    <div className={`h-4 bg-white/[0.04] rounded animate-pulse ${className}`} />
  );
}

export function SkeletonCard({ className = "" }) {
  return (
    <div className={`glass p-6 rounded-2xl space-y-4 border border-white/[0.04] ${className}`}>
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-white/[0.04] animate-pulse" />
        <div className="h-5 bg-white/[0.04] rounded w-1/3 animate-pulse" />
      </div>
      <div className="space-y-2">
        <SkeletonRow className="w-full" />
        <SkeletonRow className="w-5/6" />
        <SkeletonRow className="w-4/5" />
      </div>
    </div>
  );
}

export function SkeletonDashboard() {
  return (
    <div className="space-y-6">
      <div className="glass p-6 rounded-2xl border border-white/[0.04] space-y-4">
        <div className="h-6 bg-white/[0.04] rounded w-1/4 animate-pulse" />
        <div className="space-y-2">
          <SkeletonRow className="w-full" />
          <SkeletonRow className="w-full" />
          <SkeletonRow className="w-3/4" />
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="glass p-6 rounded-2xl border border-white/[0.04] space-y-4">
          <div className="h-5 bg-white/[0.04] rounded w-1/3 animate-pulse" />
          <div className="flex flex-wrap gap-2 pt-2">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="h-7 w-16 bg-white/[0.04] rounded-lg animate-pulse" />
            ))}
          </div>
        </div>
        <div className="glass p-6 rounded-2xl border border-white/[0.04] space-y-4">
          <div className="h-5 bg-white/[0.04] rounded w-1/3 animate-pulse" />
          <div className="space-y-3 pt-2">
            {[1, 2, 3].map((i) => (
              <div key={i} className="flex justify-between items-center">
                <div className="h-4 bg-white/[0.04] rounded w-1/2 animate-pulse" />
                <div className="h-4 bg-white/[0.04] rounded w-1/4 animate-pulse" />
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
