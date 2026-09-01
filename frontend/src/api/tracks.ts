import { api, mediaUrl } from './client'
import { getInitData } from '../lib/telegram'

const BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export interface Track {
  id: number
  original_name: string
  size_bytes: number
  sort_order: number
  /** /media/music/{user_id}/{filename} */
  url: string
}

export interface TracksInfo {
  tracks: Track[]
  total_bytes: number
  limit_bytes: number
  remaining_bytes: number
}

export const listTracks = () => api<TracksInfo>('/api/me/tracks')

export const deleteTrack = (id: number) =>
  api<void>(`/api/me/tracks/${id}`, { method: 'DELETE' })

/** Yuklash — progress uchun XHR (fetch upload-progress bermaydi). */
export function uploadTrack(
  file: File,
  onProgress?: (pct: number) => void,
): Promise<TracksInfo> {
  return new Promise((resolve, reject) => {
    const fd = new FormData()
    fd.append('file', file)
    const xhr = new XMLHttpRequest()
    xhr.open('POST', `${BASE}/api/me/tracks`)
    xhr.setRequestHeader('Authorization', `tma ${getInitData()}`)
    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable && onProgress) {
        onProgress(Math.round((e.loaded / e.total) * 100))
      }
    }
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(JSON.parse(xhr.responseText) as TracksInfo)
      } else {
        let msg = 'Yuklab bo‘lmadi'
        try {
          msg =
            (JSON.parse(xhr.responseText) as { detail?: string }).detail ?? msg
        } catch {
          /* JSON emas */
        }
        reject(new Error(msg))
      }
    }
    xhr.onerror = () => reject(new Error('Internet yo‘q'))
    xhr.send(fd)
  })
}

export function trackAudioUrl(t: Track): string {
  return mediaUrl(t.url) ?? t.url
}
