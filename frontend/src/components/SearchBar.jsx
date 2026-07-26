import React, { useState } from "react";
import { Search, ArrowRight, Loader2, Info } from "lucide-react";

export default function SearchBar({ onSubmit, isLoading, proMode }) {
  const [value, setValue] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!value.trim() || isLoading) return;
    onSubmit(value.trim());
    setValue("");
  };

  return (
    <div className="space-y-2">
      <form onSubmit={handleSubmit} className="relative group">
        {/* Outer glow ring on focus */}
        <div className="absolute -inset-0.5 rounded-2xl bg-gradient-to-r from-neon-cyan/20 via-neon-violet/20 to-neon-cyan/20 opacity-0 group-focus-within:opacity-100 transition-opacity duration-500 blur-md" />

        <div className="relative glass rounded-2xl flex items-center transition-all duration-300 group-focus-within:neon-glow-cyan bg-dark-800/80">
          {/* Search icon */}
          <div className="pl-5 pr-3 flex items-center">
            <Search className="w-5 h-5 text-gray-500 group-focus-within:text-neon-cyan transition-colors duration-300" />
          </div>

          {/* Input */}
          <input
            type="text"
            value={value}
            onChange={(e) => setValue(e.target.value)}
            placeholder="Ask anything about your documents..."
            disabled={isLoading}
            className="flex-1 bg-transparent py-4.5 text-[15px] text-gray-100 placeholder-gray-500 focus:outline-none disabled:opacity-60 font-medium"
          />

          {/* Submit button */}
          <div className="pr-3">
            <button
              type="submit"
              disabled={isLoading || !value.trim()}
              className="relative flex items-center justify-center w-11 h-11 rounded-xl bg-gradient-to-br from-neon-cyan to-neon-violet text-white transition-all duration-300 hover:shadow-lg hover:shadow-neon-cyan/20 disabled:opacity-30 disabled:cursor-not-allowed active:scale-95"
            >
              {isLoading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <ArrowRight className="w-5 h-5" />
              )}
            </button>
          </div>
        </div>
      </form>

      {/* Info helper line */}
      <div className="flex items-center justify-between px-3 text-[10px] text-gray-600">
        <div className="flex items-center gap-1">
          <Info className="w-3.5 h-3.5" />
          <span>Local processing: answers are 100% private and generated offline.</span>
        </div>
        <div>
          <span>Estimated query duration: </span>
          <span className="text-gray-500 font-semibold">{proMode ? "~45-60s" : "~75-90s"}</span>
        </div>
      </div>
    </div>
  );
}
