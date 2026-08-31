import { useRef, useState } from 'react'
import { IconCamera, IconSend, IconSparkles } from '@tabler/icons-react'
import { aiParse, receiptScan, type AiDraft } from '../api/ai'
import { ApiError } from '../api/client'
import { compressImage } from '../lib/image'

interface Props {
  projectId: number
  onDraft: (draft: AiDraft) => void
  /** AI umuman ishlamasa — bo'sh qo'lda forma ochish */
  onManual: () => void
}

export function AiInputBar({ projectId, onDraft, onManual }: Props) {
  const [text, setText] = useState('')
  const [busy, setBusy] = useState<false | 'text' | 'photo'>(false)
  const [error, setError] = useState<string | null>(null)
  const fileRef = useRef<HTMLInputElement>(null)

  async function runText() {
    const t = text.trim()
    if (!t || busy) return
    setBusy('text')
    setError(null)
    try {
      onDraft(await aiParse(projectId, t))
      setText('')
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Xatolik yuz berdi')
    } finally {
      setBusy(false)
    }
  }

  async function runPhoto(file: File) {
    setBusy('photo')
    setError(null)
    try {
      const blob = await compressImage(file)
      onDraft(await receiptScan(projectId, blob))
    } catch (e) {
      setError(
        e instanceof ApiError
          ? e.message
          : 'Chekni o‘qib bo‘lmadi. Yorug‘roq joyda qayta suratga oling.',
      )
    } finally {
      setBusy(false)
    }
  }

  return (
    <div>
      <div className="flex items-center gap-2 rounded-card border border-border bg-surface p-2">
        <IconSparkles size={18} className="shrink-0 text-primary" />
        <input
          className="min-w-0 flex-1 bg-transparent text-body text-text outline-none placeholder:text-text-faint"
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') void runText()
          }}
          placeholder='Yozing… "sement 5 qop 650 ming mijoz naqd"'
          disabled={busy !== false}
        />
        {text.trim() ? (
          <button
            type="button"
            aria-label="Yuborish"
            onClick={() => void runText()}
            disabled={busy !== false}
            className="shrink-0 rounded-btn bg-primary p-1.5 text-on-primary active:scale-95 disabled:opacity-60"
          >
            <IconSend size={16} />
          </button>
        ) : (
          <button
            type="button"
            aria-label="Chek surati"
            onClick={() => fileRef.current?.click()}
            disabled={busy !== false}
            className="shrink-0 rounded-btn bg-surface-2 p-1.5 text-text-muted active:scale-95 disabled:opacity-60"
          >
            <IconCamera size={18} />
          </button>
        )}
      </div>

      <input
        ref={fileRef}
        type="file"
        accept="image/*"
        capture="environment"
        className="hidden"
        onChange={(e) => {
          const f = e.target.files?.[0]
          e.target.value = ''
          if (f) void runPhoto(f)
        }}
      />

      {busy && (
        <p className="mt-1.5 text-label text-text-muted">
          {busy === 'photo' ? 'Chek o‘qilyapti…' : 'Tahlil qilinyapti…'}
        </p>
      )}
      {error && (
        <div className="mt-1.5 text-label text-danger">
          {error}{' '}
          <button
            type="button"
            onClick={onManual}
            className="text-primary underline"
          >
            Qo‘lda kiritish
          </button>
        </div>
      )}
    </div>
  )
}
