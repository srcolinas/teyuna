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

class ApiClient {
  private client: AxiosInstance
  private playerNickname: string | null = null

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
    })
  }

  setPlayerNickname(nickname: string | null) {
    this.playerNickname = nickname
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
    const headers = { Authorization: `Bearer ${token}` }
    const response = await this.client.get<PrivatePlayerInfo>(`/games/${gameId}/hand`, { headers })
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

  async advanceTurn(gameId: string): Promise<{ phase: string; active_player: string }> {
    const response = await this.client.post(
      `/games/${gameId}/turn-order`,
      {},
      {
        params: { player: this.playerNickname },
      },
    )
    return response.data
  }

  async getConquistadorLocation(gameId: string) {
    const response = await this.client.get(`/games/${gameId}/conquistator`)
    return response.data
  }

  async rollDice(gameId: string): Promise<{ phase: string; result: number }> {
    const response = await this.client.post(
      `/games/${gameId}/turn-order`,
      {},
      {
        params: { player: this.playerNickname },
      },
    )
    return response.data
  }

  async placeInitialBuildings(
    gameId: string,
    terrace: VertexCoordinate,
    path: EdgeCoordinate,
  ): Promise<void> {
    await this.client.post(`/games/${gameId}/initial-placements`, { terrace, path })
  }

  async moveConquistator(gameId: string, location: HexCoordinate): Promise<void> {
    await this.client.post(`/games/${gameId}/conquistator`, { location })
  }

  async buyWisdomCard(gameId: string): Promise<string> {
    const response = await this.client.post(
      `/games/${gameId}/wisdom-cards/buy`,
      {},
      {
        params: { player: this.playerNickname },
      },
    )
    return response.data
  }

  async buildSettlement(
    gameId: string,
    item: SettlementType,
    location: VertexCoordinate,
  ): Promise<string> {
    const response = await this.client.post(`/games/${gameId}/settlements`, { item, location })
    return response.data
  }

  async buildPath(gameId: string, location: EdgeCoordinate): Promise<string> {
    const response = await this.client.post(`/games/${gameId}/paths`, { location })
    return response.data
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
