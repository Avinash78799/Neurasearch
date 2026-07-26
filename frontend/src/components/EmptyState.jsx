import React from "react";
import { Info } from "lucide-react";

export default function EmptyState({
  title,
  description,
  icon: Icon = Info,
  primaryActionLabel,
  onPrimaryAction,
  secondaryActionLabel,
  onSecondaryAction
}) {
  return (
    <div className="flex flex-col items-center justify-center text-center p-8 border border-white/5 bg-white/[0.01] rounded-2xl animate-fade-in max-w-md mx-auto my-12">
      <div className="mb-5 relative">
        <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-neon-cyan/15 to-neon-violet/15 flex items-center justify-center border border-white/[0.05] animate-float">
          <Icon className="w-6 h-6 text-neon-cyan/80" />
        </div>
      </div>
      
      <h3 className="text-sm font-bold text-gray-200 mb-1.5 uppercase tracking-wider">
        {title}
      </h3>
      
      <p className="text-xs text-gray-500 leading-relaxed mb-6">
        {description}
      </p>
      
      <div className="flex items-center gap-3 w-full">
        {primaryActionLabel && onPrimaryAction && (
          <button
            onClick={onPrimaryAction}
            className="flex-1 py-2 px-4 bg-neon-cyan/20 border border-neon-cyan/45 hover:bg-neon-cyan/30 text-neon-cyan text-xs font-bold rounded-lg transition-all shadow-md shadow-neon-cyan/5 focus:ring-2 focus:ring-neon-cyan/40 focus:outline-none"
          >
            {primaryActionLabel}
          </button>
        )}
        
        {secondaryActionLabel && onSecondaryAction && (
          <button
            onClick={onSecondaryAction}
            className="flex-1 py-2 px-4 bg-white/5 border border-white/10 hover:bg-white/10 text-gray-400 hover:text-white text-xs font-bold rounded-lg transition-all focus:ring-2 focus:ring-white/20 focus:outline-none"
          >
            {secondaryActionLabel}
          </button>
        )}
      </div>
    </div>
  );
}
