const COLOR_SATURATION = 82
const COLOR_LIGHTNESS = 58

const hashTicker = (ticker: string): number => {
  let hash = 0
  for (let index = 0; index < ticker.length; index += 1) {
    hash = (hash * 31 + ticker.charCodeAt(index)) % 360
  }
  return hash
}

export const getTickerColor = (ticker: string): string => {
  return `hsl(${hashTicker(ticker)}, ${COLOR_SATURATION}%, ${COLOR_LIGHTNESS}%)`
}