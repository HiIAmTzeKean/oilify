export function convertToSeconds(value: string, unit: string): number {
  const num = parseInt(value)
  if (isNaN(num)) return 0
  switch (unit) {
    case 'hours': return num * 3600
    case 'days': return num * 86400
    default: return num
  }
}