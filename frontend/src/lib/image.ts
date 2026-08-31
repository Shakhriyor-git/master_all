/** Chek suratini yuborishdan oldin brauzerda siqadi: max 1400 px, JPEG 0.85. */
export async function compressImage(
  file: File,
  maxSide = 1400,
  quality = 0.85,
): Promise<Blob> {
  try {
    const bitmap = await createImageBitmap(file)
    const scale = Math.min(1, maxSide / Math.max(bitmap.width, bitmap.height))
    const w = Math.round(bitmap.width * scale)
    const h = Math.round(bitmap.height * scale)
    const canvas = document.createElement('canvas')
    canvas.width = w
    canvas.height = h
    const ctx = canvas.getContext('2d')
    if (!ctx) return file
    ctx.drawImage(bitmap, 0, 0, w, h)
    bitmap.close?.()
    return await new Promise<Blob>((resolve) => {
      canvas.toBlob(
        (blob) => resolve(blob ?? file),
        'image/jpeg',
        quality,
      )
    })
  } catch {
    // eski webview — asl faylni yuboramiz, server baribir qayta siqadi
    return file
  }
}
