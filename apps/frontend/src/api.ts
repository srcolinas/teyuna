import axios, { AxiosInstance } from 'axios'
import {
  ActiveGame,
  EdgeCoordinate,
  HexCoordinate,
  PrivatePlayerInfo,
  SettlementType,
  VertexCoordinate,
} from './types'

const rawApiUrl = import.meta.env.VITE_API_URL
if (typeof rawApiUrl !== 'string' || rawApiUrl.trim() === '') {
  throw new Error('VITE_API_URL must be set (see apps/frontend/.env.example)')
}

export const API_BASE_URL = rawApiUrl.replace(/\/$/, '')

function authHeaders(token: string) {
  return { Authorization: `Bearer ${token}` }
}

function vertexToCoordinate(location: VertexCoordinate) {
  return { q: location.hex_coord.q, r: location.hex_coord.r, d: location.direction }
}

function edgeToCoordinate(location: EdgeCoordinate) {
  return { q: location.hex_coord.q, r: location.hex_coord.r, d: location.direction }
}

class ApiClient {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
    })
  }

  async joinGame(gameId: string, nickname: string): Promise<string> {
    const response = await this.client.post<{ game: ActiveGame; token: string }>(
      `/games/${gameId}/players`,
      { nickname },
    )
    return response.data.token
  }

  async getGame(gameId: string): Promise<ActiveGame> {
    const response = await this.client.get(`/games/${gameId}`)
    return response.data
  }

  async getPrivatePlayerInfo(gameId: string, token: string): Promise<PrivatePlayerInfo> {
    const response = await this.client.get<PrivatePlayerInfo>(`/games/${gameId}/hand`, {
      headers: authHeaders(token),
    })
    return response.data
  }

  async getGameMap(gameId: string) {
    const response = await this.client.get(`/games/${gameId}/map`)
    return response.data
  }

  async getTurnOrder(gameId: string): Promise<string[]> {
    const response = await this.client.get(`/games/${gameId}/turn-order`)
    return response.data
  }

  async submitAction(gameId: string, token: string, action: Record<string, unknown>) {
    const response = await this.client.post(`/games/${gameId}/actions`, action, {
      headers: authHeaders(token),
    })
    return response.data
  }

  async advanceTurn(
    gameId: string,
    token: string,
  ): Promise<{ phase: string; active_player: string }> {
    const result = await this.submitAction(gameId, token, { kind: 'advance' })
    return {
      phase: result.next_phase,
      active_player: result.next_player ?? '',
    }
  }

  async getConquistadorLocation(gameId: string) {
    const response = await this.client.get(`/games/${gameId}/conquistator`)
    return response.data
  }

  async rollDice(gameId: string, token: string): Promise<{ phase: string; result: number }> {
    const result = await this.submitAction(gameId, token, { kind: 'advance' })
    const die1 = typeof result.die_1 === 'number' ? result.die_1 : 0
    const die2 = typeof result.die_2 === 'number' ? result.die_2 : 0
    return {
      phase: result.next_phase,
      result: die1 + die2,
    }
  }

  async placeInitialBuildings(
    gameId: string,
    token: string,
    terrace: VertexCoordinate,
    path: EdgeCoordinate,
  ): Promise<void> {
    await this.submitAction(gameId, token, {
      kind: 'free_placement',
      terrace: vertexToCoordinate(terrace),
      path: edgeToCoordinate(path),
    })
  }

  async moveConquistator(gameId: string, token: string, location: HexCoordinate): Promise<void> {
    await this.submitAction(gameId, token, {
      kind: 'move_conquistator',
      q: location.q,
      r: location.r,
    })
  }

  async buyWisdomCard(gameId: string, token: string): Promise<string> {
    const result = await this.submitAction(gameId, token, { kind: 'buy_wisdom_card' })
    return result.next_phase
  }

  async buildSettlement(
    gameId: string,
    token: string,
    item: SettlementType,
    location: VertexCoordinate,
  ): Promise<string> {
    const result = await this.submitAction(gameId, token, {
      kind: 'build_settlement',
      item,
      coordinate: vertexToCoordinate(location),
    })
    return result.next_phase
  }

  async buildPath(gameId: string, token: string, location: EdgeCoordinate): Promise<string> {
    const result = await this.submitAction(gameId, token, {
      kind: 'build_path',
      coordinate: edgeToCoordinate(location),
    })
    return result.next_phase
  }
}

export const apiClient = new ApiClient()

export function apiErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail
    if (typeof detail === 'string') return detail
    return error.message
  }
  return error instanceof Error ? error.message : 'Unknown error'
}
