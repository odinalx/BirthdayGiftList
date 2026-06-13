const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

export class HttpError extends Error {
  public readonly statusCode: number
  public readonly response?: { status: number; data: unknown }

  constructor(message: string, statusCode: number, response?: { status: number; data: unknown }) {
    super(message)
    this.name = 'HttpError'
    this.statusCode = statusCode
    this.response = response
  }
}

function dispatchSessionExpired() {
  window.dispatchEvent(new CustomEvent('auth:session-expired'))
}

export interface User {
  id: string
  email: string
  name: string
  picture?: string
  list_slug: string
  created_at: string
}

export type GiftStatus = 'AVAILABLE' | 'RESERVED' | 'BOUGHT'

export interface Gift {
  id: string
  title: string
  description?: string | null
  image_url?: string | null
  link?: string | null
  price?: number | null
  status: GiftStatus
  claimed_by_name?: string | null
  created_at: string
}

export interface GiftCreate {
  title: string
  description?: string
  image_url?: string
  link?: string
  price?: number
}

export interface GiftUpdate {
  title?: string
  description?: string
  image_url?: string
  link?: string
  price?: number
  status?: GiftStatus
}

class ApiClient {
  private async request<T>(path: string, options?: RequestInit): Promise<T> {
    const res = await fetch(`${API_BASE}${path}`, {
      credentials: 'include',
      headers: { 'Content-Type': 'application/json', ...options?.headers },
      ...options,
    })

    if (res.status === 401) {
      dispatchSessionExpired()
      throw new HttpError('Non authentifié', 401)
    }

    if (!res.ok) {
      const data = await res.json().catch(() => ({}))
      throw new HttpError((data as { detail?: string }).detail || res.statusText, res.status, {
        status: res.status,
        data,
      })
    }

    if (res.status === 204) return undefined as T
    return res.json()
  }

  // Auth
  getGoogleLoginUrl(): string {
    return `${API_BASE}/auth/google/login`
  }

  async checkSession(): Promise<{ authenticated: boolean; user: User | null }> {
    return this.request('/auth/session')
  }

  async logout(): Promise<void> {
    await this.request('/auth/logout', { method: 'POST' })
  }

  // Gifts — admin (requires auth)
  async getMyGifts(): Promise<Gift[]> {
    return this.request('/gifts')
  }

  async createGift(data: GiftCreate): Promise<Gift> {
    return this.request('/gifts', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async updateGift(id: string, data: GiftUpdate): Promise<Gift> {
    return this.request(`/gifts/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    })
  }

  async deleteGift(id: string): Promise<void> {
    await this.request(`/gifts/${id}`, { method: 'DELETE' })
  }

  // Gifts — public (by list slug)
  async getPublicGifts(slug: string): Promise<Gift[]> {
    return this.request(`/gifts/public/${slug}`)
  }

  async reserveGift(id: string, visitorName: string, visitorId: string): Promise<Gift> {
    return this.request(`/gifts/${id}/reserve`, {
      method: 'POST',
      body: JSON.stringify({ visitor_name: visitorName, visitor_id: visitorId }),
    })
  }

  async unreserveGift(id: string, visitorId: string): Promise<Gift> {
    return this.request(`/gifts/${id}/unreserve`, {
      method: 'POST',
      body: JSON.stringify({ visitor_id: visitorId }),
    })
  }

  async buyGift(id: string, visitorId: string): Promise<Gift> {
    return this.request(`/gifts/${id}/buy`, {
      method: 'POST',
      body: JSON.stringify({ visitor_id: visitorId }),
    })
  }

  async fetchUrlMeta(url: string): Promise<{ title?: string; description?: string; image_url?: string; price?: number }> {
    return this.request('/gifts/fetch-meta', {
      method: 'POST',
      body: JSON.stringify({ url }),
    })
  }
}

export const api = new ApiClient()
