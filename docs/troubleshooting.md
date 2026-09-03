# Troubleshooting Guide

This guide details typical errors, recovery routes, and service fixes.

---

## 1. Ollama Connectivity Issues
- **Problem**: RAG pipeline throws: `ConnectionRefusedError: [WinError 10061] No connection could be made...`
- **Fix**: Check that the Ollama app is active. Open `http://127.0.0.1:11434` in your browser. Verify you've pulled the model via `ollama pull llama3.1`.

---

## 2. SQLite Database File Locks
- **Problem**: `sqlite3.OperationalError: database is locked`
- **Fix**: Ensure no concurrent processes are writing to the database file without closing transactions. In development, you can delete `neurasearch.db` and run the server to rebuild table structures cleanly.

---

## 3. Chrome DevTools & Vite Chunk Warning
- **Problem**: Build console displays: `Some chunks are larger than 500 kB after minification.`
- **Fix**: Run `npm run build` inside `frontend/`. Custom manual Rollup config splits the build output into separate core and markdown files. Warnings are safe to ignore as code-splitting is already active.
