export interface HexLocation {
  q: number
  r: number
}

export interface Coordinate {
  q: number
  r: number
  d: number
}

export type HexType = 'mountains' | 'quarries' | 'highlands' | 'valleys' | 'jungle' | 'desert'

export interface Hex {
  coordinate: HexLocation
  type: HexType
  number: number | null
}

export type SettlementType = 'terrace' | 'great terrace'

export interface PlayedSettlement {
  owner: string
  location: Coordinate
  type: SettlementType
}

export interface PlayedStonePath {
  owner: string
  location: Coordinate
}

export type ResourceCard = 'gold' | 'stone' | 'cotton' | 'maize' | 'wood'
export type WisdomCard =
  'warrior' | 'blessing of aluna' | 'wisdom of mamo' | 'pathfinder' | 'legacy of the elders'

export interface Harbour {
  resource: ResourceCard | null
  vertices: [Coordinate, Coordinate]
}

export interface Player {
  nickname: string
  victory_points: number
  played_wisdom_cards: string[]
  num_hidden_wisdom_cards: number
  num_resources: number
  available_terraces: number
  available_great_terraces: number
  available_paths: number
}

export interface PrivatePlayerInfo {
  resources: Record<ResourceCard, number>
  wisdom_cards: WisdomCard[]
}

export interface ActiveGame {
  id: string
  turns_played: number
  map: Hex[]
  conquistator_location: HexLocation
  harbours: Harbour[]
  players: Player[]
  settlements: PlayedSettlement[]
  paths: PlayedStonePath[]
  turn_order: string[]
  phase: string
  phase_deadline: string | null
}

export const HEX_TYPE_TO_RESOURCE: Record<HexType, ResourceCard> = {
  mountains: 'gold',
  quarries: 'stone',
  highlands: 'cotton',
  valleys: 'maize',
  jungle: 'wood',
  desert: 'gold',
}

export const HEX_TYPE_COLORS: Record<HexType, string> = {
  mountains: '#D36E3D',
  quarries: '#808080',
  highlands: '#87C14E',
  valleys: '#E5AF4D',
  jungle: '#3E6037',
  desert: '#D8AE6F',
}
