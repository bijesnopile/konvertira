export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 ** 2) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 ** 2).toFixed(1)} MB`
}

export function readableImageType(file: File): string {
  const subtype = file.type.split('/')[1]
  if (subtype) return subtype === 'jpeg' ? 'JPG' : subtype.toUpperCase()
  return file.name.split('.').pop()?.toUpperCase() || 'Unknown'
}
