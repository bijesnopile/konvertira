import { useState } from 'react'

export const ACKNOWLEDGEMENT_ERROR = 'Please acknowledge the upload and Terms before processing.'

export function sameProcessingScope(
  previousFiles: readonly File[], previousOperation: string,
  files: readonly File[], operation: string,
): boolean {
  return previousOperation === operation && previousFiles.length === files.length
    && previousFiles.every((file, index) => file === files[index])
}

// Component-local only: no cookies, storage, identity collection or API records.
// Compare File identities, not names: a replacement can have the same filename.
export function useProcessingAcknowledgement(files: readonly File[], operation: string) {
  const [state, setState] = useState({ files: [...files], operation, accepted: false, error: false })
  const matches = sameProcessingScope(state.files, state.operation, files, operation)
  // Reset during render so a changed scope can never briefly enable submission,
  // and returning to an earlier operation cannot revive its old acceptance.
  if (!matches) setState({ files: [...files], operation, accepted: false, error: false })
  const accepted = matches && state.accepted
  const setAccepted = (value: boolean) => setState({ files: [...files], operation, accepted: value, error: false })
  const reset = () => setAccepted(false)
  const guard = () => {
    if (accepted && files.length) return true
    setState({ files: [...files], operation, accepted: false, error: true })
    return false
  }
  return { accepted, setAccepted, reset, guard, error: matches && state.error }
}
