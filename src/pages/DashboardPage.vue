<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useAuth } from '@/composables/useAuth'
import { api, type Gift, type GiftCreate } from '@/services/api'
import { Copy, Plus, Trash2, ExternalLink, Gift as GiftIcon, LogOut, Check } from 'lucide-vue-next'

const { user, logout } = useAuth()
const gifts = ref<Gift[]>([])
const isLoading = ref(true)
const showAddForm = ref(false)
const copiedLink = ref(false)
const error = ref<string | null>(null)

const shareLink = computed(() => {
  if (!user.value?.list_slug) return ''
  return `${window.location.origin}/list/${user.value.list_slug}`
})

const form = ref<GiftCreate>({
  title: '',
  description: '',
  image_url: '',
  link: '',
  price: undefined,
})
const isSubmitting = ref(false)

onMounted(async () => {
  try {
    gifts.value = await api.getMyGifts()
  } catch {
    error.value = 'Erreur lors du chargement des cadeaux.'
  } finally {
    isLoading.value = false
  }
})

async function addGift() {
  if (!form.value.title.trim()) return
  isSubmitting.value = true
  try {
    const gift = await api.createGift({
      title: form.value.title.trim(),
      description: form.value.description || undefined,
      image_url: form.value.image_url || undefined,
      link: form.value.link || undefined,
      price: form.value.price || undefined,
    })
    gifts.value.unshift(gift)
    form.value = { title: '', description: '', image_url: '', link: '', price: undefined }
    showAddForm.value = false
  } catch {
    error.value = 'Erreur lors de l\'ajout du cadeau.'
  } finally {
    isSubmitting.value = false
  }
}

async function markBought(gift: Gift) {
  try {
    const updated = await api.updateGift(gift.id, {
      status: gift.status === 'BOUGHT' ? 'AVAILABLE' : 'BOUGHT',
    })
    const idx = gifts.value.findIndex(g => g.id === gift.id)
    if (idx !== -1) gifts.value[idx] = updated
  } catch {
    error.value = 'Erreur lors de la mise à jour du statut.'
  }
}

async function deleteGift(id: string) {
  if (!confirm('Supprimer ce cadeau ?')) return
  try {
    await api.deleteGift(id)
    gifts.value = gifts.value.filter(g => g.id !== id)
  } catch {
    error.value = 'Erreur lors de la suppression.'
  }
}

function copyLink() {
  navigator.clipboard.writeText(shareLink.value)
  copiedLink.value = true
  setTimeout(() => (copiedLink.value = false), 2000)
}

function statusLabel(status: Gift['status']) {
  return { AVAILABLE: 'Disponible', RESERVED: 'Réservé', BOUGHT: 'Offert' }[status]
}

function statusClass(status: Gift['status']) {
  return {
    AVAILABLE: 'status-available',
    RESERVED: 'status-reserved',
    BOUGHT: 'status-bought',
  }[status]
}

async function handleLogout() {
  await logout()
  window.location.href = '/'
}
</script>

<template>
  <div class="page">
    <!-- Navbar -->
    <nav class="app-navbar">
      <a href="/dashboard" class="app-navbar-logo">
        <span class="logo-mark"><GiftIcon :size="14" /></span>
        Ma Liste d'Anniversaire
      </a>
      <div class="nav-right">
        <img
          v-if="user?.picture"
          :src="user.picture"
          :alt="user.name"
          class="avatar"
        />
        <button class="logout-btn" @click="handleLogout">
          <LogOut :size="16" />
          Déconnexion
        </button>
      </div>
    </nav>

    <main class="main">
      <!-- Share link -->
      <section class="share-section">
        <div class="share-label">Lien à partager avec vos proches</div>
        <div class="share-row">
          <div class="share-link">{{ shareLink }}</div>
          <button class="copy-btn" @click="copyLink">
            <Check v-if="copiedLink" :size="15" />
            <Copy v-else :size="15" />
            {{ copiedLink ? 'Copié !' : 'Copier' }}
          </button>
        </div>
      </section>

      <div v-if="error" class="error-msg">{{ error }}</div>

      <!-- Header row -->
      <div class="section-header">
        <h2>Mes cadeaux ({{ gifts.length }})</h2>
        <button class="add-btn" @click="showAddForm = !showAddForm">
          <Plus :size="16" />
          Ajouter un cadeau
        </button>
      </div>

      <!-- Add form -->
      <div v-if="showAddForm" class="add-form">
        <h3>Nouveau cadeau</h3>
        <div class="form-grid">
          <div class="field">
            <label>Nom du cadeau *</label>
            <input v-model="form.title" type="text" placeholder="ex : AirPods Pro" />
          </div>
          <div class="field">
            <label>Prix (€)</label>
            <input v-model.number="form.price" type="number" placeholder="ex : 249" />
          </div>
          <div class="field full">
            <label>Lien vers le produit</label>
            <input v-model="form.link" type="url" placeholder="https://..." />
          </div>
          <div class="field full">
            <label>URL de l'image</label>
            <input v-model="form.image_url" type="url" placeholder="https://..." />
          </div>
          <div class="field full">
            <label>Description (optionnel)</label>
            <textarea v-model="form.description" rows="2" placeholder="Précisions sur la couleur, taille..." />
          </div>
        </div>
        <div class="form-actions">
          <button class="btn-secondary" @click="showAddForm = false">Annuler</button>
          <button class="btn-primary" :disabled="isSubmitting || !form.title.trim()" @click="addGift">
            {{ isSubmitting ? 'Ajout...' : 'Ajouter' }}
          </button>
        </div>
      </div>

      <!-- Gift table -->
      <div v-if="isLoading" class="loading">Chargement...</div>
      <div v-else-if="gifts.length === 0 && !showAddForm" class="empty">
        <GiftIcon :size="32" class="empty-icon" />
        <p>Aucun cadeau pour l'instant. Ajoutez votre premier cadeau !</p>
      </div>
      <div v-else class="gift-table-wrap">
        <table class="gift-table">
          <thead>
            <tr>
              <th>Cadeau</th>
              <th>Prix</th>
              <th>Statut</th>
              <th>Réservé par</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="gift in gifts" :key="gift.id">
              <td>
                <div class="gift-name-cell">
                  <img v-if="gift.image_url" :src="gift.image_url" :alt="gift.title" class="gift-thumb" />
                  <div>
                    <div class="gift-title">{{ gift.title }}</div>
                    <div v-if="gift.description" class="gift-desc">{{ gift.description }}</div>
                  </div>
                </div>
              </td>
              <td>{{ gift.price ? `${gift.price} €` : '—' }}</td>
              <td>
                <span :class="['status-badge', statusClass(gift.status)]">
                  {{ statusLabel(gift.status) }}
                </span>
              </td>
              <td>{{ gift.claimed_by_name || '—' }}</td>
              <td>
                <div class="row-actions">
                  <a v-if="gift.link" :href="gift.link" target="_blank" class="icon-btn" title="Voir le produit">
                    <ExternalLink :size="15" />
                  </a>
                  <button
                    class="icon-btn"
                    :title="gift.status === 'BOUGHT' ? 'Marquer comme disponible' : 'Marquer comme offert'"
                    @click="markBought(gift)"
                  >
                    <Check :size="15" />
                  </button>
                  <button class="icon-btn danger" title="Supprimer" @click="deleteGift(gift.id)">
                    <Trash2 :size="15" />
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </main>
  </div>
</template>

<style scoped>
.page {
  min-height: 100vh;
  background: var(--app-bg);
}

.nav-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  object-fit: cover;
}

.logout-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  background: none;
  border: 1px solid var(--app-border);
  border-radius: 8px;
  padding: 6px 12px;
  font-size: 0.85rem;
  color: var(--app-text-muted);
  cursor: pointer;
  transition: all 0.15s;
}

.logout-btn:hover {
  background: var(--app-surface-2);
}

.main {
  max-width: 900px;
  margin: 0 auto;
  padding: 2rem 1rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.share-section {
  background: var(--app-surface);
  border: 1px solid var(--app-border);
  border-radius: 12px;
  padding: 1.25rem 1.5rem;
}

.share-label {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--app-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.5rem;
}

.share-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.share-link {
  flex: 1;
  font-family: monospace;
  font-size: 0.9rem;
  color: var(--app-text);
  background: var(--app-surface-2);
  border: 1px solid var(--app-border);
  border-radius: 6px;
  padding: 8px 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.copy-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  background: var(--app-text);
  color: white;
  border: none;
  border-radius: 8px;
  padding: 8px 16px;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.15s;
}

.copy-btn:hover { background: #3d3a36; }

.error-msg {
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  padding: 0.75rem 1rem;
  color: #dc2626;
  font-size: 0.9rem;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.section-header h2 {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--app-text);
  margin: 0;
}

.add-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  background: var(--app-text);
  color: white;
  border: none;
  border-radius: 8px;
  padding: 8px 16px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
}

.add-btn:hover { background: #3d3a36; }

.add-form {
  background: var(--app-surface);
  border: 1px solid var(--app-border);
  border-radius: 12px;
  padding: 1.5rem;
}

.add-form h3 {
  margin: 0 0 1rem;
  font-size: 1rem;
  font-weight: 700;
  color: var(--app-text);
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.field.full { grid-column: 1 / -1; }

.field label {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--app-text-muted);
}

.field input,
.field textarea {
  border: 1px solid var(--app-border);
  border-radius: 8px;
  padding: 8px 12px;
  font-size: 0.9rem;
  color: var(--app-text);
  background: var(--app-surface);
  outline: none;
  resize: vertical;
  font-family: inherit;
}

.field input:focus,
.field textarea:focus {
  border-color: var(--app-text);
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 1rem;
}

.btn-primary {
  background: var(--app-text);
  color: white;
  border: none;
  border-radius: 8px;
  padding: 8px 20px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
}

.btn-primary:hover:not(:disabled) { background: #3d3a36; }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }

.btn-secondary {
  background: transparent;
  color: var(--app-text-muted);
  border: 1px solid var(--app-border);
  border-radius: 8px;
  padding: 8px 20px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
}

.btn-secondary:hover { background: var(--app-surface-2); }

.loading, .empty {
  text-align: center;
  color: var(--app-text-muted);
  padding: 3rem 0;
}

.empty-icon { color: var(--app-text-dim); margin-bottom: 0.75rem; }

.gift-table-wrap {
  background: var(--app-surface);
  border: 1px solid var(--app-border);
  border-radius: 12px;
  overflow: hidden;
}

.gift-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9rem;
}

.gift-table th {
  padding: 12px 16px;
  text-align: left;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--app-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 1px solid var(--app-border);
  background: var(--app-surface-2);
}

.gift-table td {
  padding: 12px 16px;
  border-bottom: 1px solid var(--app-border);
  color: var(--app-text);
  vertical-align: middle;
}

.gift-table tr:last-child td { border-bottom: none; }

.gift-name-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}

.gift-thumb {
  width: 40px;
  height: 40px;
  border-radius: 6px;
  object-fit: cover;
  border: 1px solid var(--app-border);
}

.gift-title { font-weight: 600; }
.gift-desc { font-size: 0.8rem; color: var(--app-text-muted); }

.status-badge {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 600;
}

.status-available { background: #f0fdf4; color: #16a34a; }
.status-reserved { background: #fefce8; color: #ca8a04; }
.status-bought { background: #f0f9ff; color: #0284c7; }

.row-actions {
  display: flex;
  align-items: center;
  gap: 6px;
}

.icon-btn {
  background: none;
  border: 1px solid var(--app-border);
  border-radius: 6px;
  padding: 5px;
  cursor: pointer;
  color: var(--app-text-muted);
  display: flex;
  align-items: center;
  transition: all 0.15s;
  text-decoration: none;
}

.icon-btn:hover { background: var(--app-surface-2); color: var(--app-text); }
.icon-btn.danger:hover { background: #fef2f2; color: #dc2626; border-color: #fecaca; }
</style>
