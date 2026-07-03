'use client'

import { useState } from 'react'
import { Sparkles, X } from 'lucide-react'

export function FloatingAIButton() {
  const [open, setOpen] = useState(false)

  return (
    <>
      {/* Panel */}
      {open && (
        <div className="fixed bottom-20 right-6 z-40 w-80 bg-white dark:bg-slate-900 rounded-xl shadow-2xl border border-slate-200 dark:border-slate-700 p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <div
                className="w-6 h-6 rounded-full flex items-center justify-center"
                style={{ background: 'linear-gradient(135deg, #3b82f6 0%, #7c3aed 100%)' }}
              >
                <Sparkles className="w-3 h-3 text-white" />
              </div>
              <span className="text-sm font-medium text-slate-900 dark:text-slate-100">
                Assistente AI
              </span>
            </div>
            <button
              onClick={() => setOpen(false)}
              className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            L&apos;assistente AI per OpenPassCom sarà disponibile a breve.
          </p>
        </div>
      )}

      {/* Trigger button */}
      <button
        onClick={() => setOpen((v) => !v)}
        className="fixed bottom-6 right-6 z-40 w-12 h-12 rounded-full shadow-lg flex items-center justify-center text-white transition-transform hover:scale-105 active:scale-95"
        style={{ background: 'linear-gradient(135deg, #3b82f6 0%, #7c3aed 100%)' }}
        aria-label="Assistente AI"
      >
        <Sparkles className="w-5 h-5" />
      </button>
    </>
  )
}
