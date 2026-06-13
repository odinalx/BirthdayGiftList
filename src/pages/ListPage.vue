<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { api, type Gift } from '@/services/api'
import { useVisitor } from '@/composables/useVisitor'
import { Gift as GiftIcon, ExternalLink, Check, RotateCcw, ShoppingBag } from 'lucide-vue-next'

const route = useRoute()
const slug = route.params.slug as string

const { visitorName, visitorId, setVisitorName } = useVisitor()

const gifts = ref<Gift[]>([])
const isLoading = ref(true)
const error = ref<string | null>(null)
const nameInput = ref('')
const showNameDialog = ref(false)
const actionLoadingId = ref<string | null>(null)

onMounted(async () => {
  try {
    gifts.value = await api.getPublicGifts(slug)
  } catch {
    error.value = 'Liste introuvable ou lien invalide.'
  } finally {
    isLoading.value = false
  }

  if (!visitorName.value) {
    showNameDialog.value = true
  }
})

function submitName() {
  const name = nameInput.value.trim()
  if (!name) return
  setVisitorName(name)
  showNameDialog.value = false
}

async function reserve(gift: Gift) {
  if (!visitorName.value) {
    showNameDialog.value = true
    return
  }
  actionLoadingId.value = gift.id
  try {
    const updated = await api.reserveGift(gift.id, visitorName.value, visitorId.value)
    const idx = gifts.value.findIndex(g => g.id === gift.id)
    if (idx !== -1) gifts.value[idx] = updated
  } catch {
    error.value = 'Erreur lors de la réservation.'
    setTimeout(() => (error.value = null), 3000)
  } finally {
    actionLoadingId.value = null
  }
}

async function unreserve(gift: Gift) {
  actionLoadingId.value = gift.id
  try {
    const updated = await api.unreserveGift(gift.id, visitorId.value)
    const idx = gifts.value.findIndex(g => g.id === gift.id)
    if (idx !== -1) gifts.value[idx] = updated
  } catch {
    error.value = 'Erreur lors de l\'annulation.'
    setTimeout(() => (error.value = null), 3000)
  } finally {
    actionLoadingId.value = null
  }
}

async function markAsBought(gift: Gift) {
  actionLoadingId.value = gift.id
  try {
    const updated = await api.buyGift(gift.id, visitorId.value)
    const idx = gifts.value.findIndex(g => g.id === gift.id)
    if (idx !== -1) gifts.value[idx] = updated
  } catch {
    error.value = 'Erreur lors de la mise à jour.'
    setTimeout(() => (error.value = null), 3000)
  } finally {
    actionLoadingId.value = null
  }
}

const isMyClaim = (gift: Gift) =>
  gift.status === 'RESERVED' && gift.claimed_by_name === visitorName.value

function statusLabel(status: Gift['status']) {
  return { AVAILABLE: 'Disponible', RESERVED: 'Réservé', BOUGHT: 'Acheté' }[status]
}
</script>

<template>
  <!-- Name dialog -->
  <div v-if="showNameDialog" class="dialog-overlay">
    <div class="dialog-card">
      <div class="dialog-logo"><GiftIcon :size="20" /></div>
      <h2>Qui êtes-vous ?</h2>
      <p>Entrez votre prénom pour qu'on sache à qui attribuer les cadeaux réservés.</p>
      <input
        v-model="nameInput"
        type="text"
        placeholder="Votre prénom..."
        @keydown.enter="submitName"
        autofocus
      />
      <button :disabled="!nameInput.trim()" @click="submitName">Continuer</button>
    </div>
  </div>

  <div class="page" :class="{ blurred: showNameDialog }">
    <!-- Navbar -->
    <nav class="app-navbar">
      <div class="app-navbar-logo">
        <span class="logo-mark"><GiftIcon :size="14" /></span>
        Liste de cadeaux
      </div>
      <div v-if="visitorName" class="visitor-name">
        Connecté en tant que <strong>{{ visitorName }}</strong>
      </div>
    </nav>

    <main class="main">
      <div v-if="error" class="error-msg">{{ error }}</div>

      <div v-if="isLoading" class="loading">Chargement de la liste...</div>

      <div v-else-if="gifts.length === 0" class="empty">
        <GiftIcon :size="32" class="empty-icon" />
        <p>Aucun cadeau dans cette liste pour l'instant.</p>
      </div>

      <div v-else class="gifts-grid">
        <div v-for="gift in gifts" :key="gift.id" class="gift-card">
          <div class="gift-image-wrap">
            <img v-if="gift.image_url" :src="gift.image_url" :alt="gift.title" class="gift-image" />
            <div v-else class="gift-image-placeholder">
              <GiftIcon :size="32" />
            </div>
            <span class="gift-status-badge" :class="`status-${gift.status.toLowerCase()}`">
              {{ statusLabel(gift.status) }}
            </span>
          </div>

          <div class="gift-body">
            <div class="gift-header">
              <h3>{{ gift.title }}</h3>
              <a v-if="gift.link" :href="gift.link" target="_blank" class="gift-link" title="Voir le produit">
                <ExternalLink :size="14" />
              </a>
            </div>

            <p v-if="gift.description" class="gift-desc">{{ gift.description }}</p>

            <div class="gift-footer">
              <span v-if="gift.price" class="gift-price">{{ gift.price }} €</span>
              <span v-else class="gift-price-empty">Prix non renseigné</span>

              <div class="gift-actions">
                <template v-if="gift.status === 'AVAILABLE'">
                  <button
                    class="btn-reserve"
                    :disabled="actionLoadingId === gift.id"
                    @click="reserve(gift)"
                  >
                    <Check :size="14" />
                    Je l'offre !
                  </button>
                </template>
                <template v-else-if="gift.status === 'RESERVED'">
                  <div v-if="isMyClaim(gift)" class="my-claim">
                    <button
                      class="btn-buy"
                      :disabled="actionLoadingId === gift.id"
                      @click="markAsBought(gift)"
                    >
                      <ShoppingBag :size="13" />
                      Je l'ai acheté !
                    </button>
                    <button
                      class="btn-unreserve"
                      :disabled="actionLoadingId === gift.id"
                      @click="unreserve(gift)"
                    >
                      <RotateCcw :size="13" />
                      Annuler
                    </button>
                  </div>
                  <div v-else class="reserved-by">
                    Réservé par <strong>{{ gift.claimed_by_name }}</strong>
                  </div>
                </template>
                <template v-else-if="gift.status === 'BOUGHT'">
                  <span class="bought-label">Déjà acheté ✓</span>
                </template>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.page {
  min-height: 100vh;
  background: var(--app-bg);
  transition: filter 0.2s;
}

.page.blurred { filter: blur(4px); pointer-events: none; }

.visitor-name {
  font-size: 0.85rem;
  color: var(--app-text-muted);
}

.main {
  max-width: 1000px;
  margin: 0 auto;
  padding: 2rem 1rem;
}

.error-msg {
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  padding: 0.75rem 1rem;
  color: #dc2626;
  font-size: 0.9rem;
  margin-bottom: 1rem;
}

.loading, .empty {
  text-align: center;
  color: var(--app-text-muted);
  padding: 4rem 0;
}

.empty-icon { color: var(--app-text-dim); margin-bottom: 0.75rem; }

.gifts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.25rem;
}

.gift-card {
  background: var(--app-surface);
  border: 1px solid var(--app-border);
  border-radius: 14px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  transition: box-shadow 0.15s;
}

.gift-card:hover {
  box-shadow: 0 4px 16px rgba(0,0,0,0.07);
}

.gift-image-wrap {
  position: relative;
  height: 180px;
  background: var(--app-surface-2);
}

.gift-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.gift-image-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--app-text-dim);
}

.gift-status-badge {
  position: absolute;
  top: 10px;
  right: 10px;
  padding: 3px 10px;
  border-radius: 20px;
  font-size: 0.72rem;
  font-weight: 700;
}

.status-available { background: #dcfce7; color: #16a34a; }
.status-reserved { background: #fef9c3; color: #ca8a04; }
.status-bought { background: #dbeafe; color: #1d4ed8; }

.gift-body {
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  flex: 1;
}

.gift-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 6px;
}

.gift-header h3 {
  font-size: 1rem;
  font-weight: 700;
  color: var(--app-text);
  margin: 0;
}

.gift-link {
  color: var(--app-text-muted);
  text-decoration: none;
  flex-shrink: 0;
  transition: color 0.15s;
}

.gift-link:hover { color: var(--app-text); }

.gift-desc {
  font-size: 0.85rem;
  color: var(--app-text-muted);
  margin: 0;
  line-height: 1.5;
}

.gift-footer {
  margin-top: auto;
  padding-top: 0.75rem;
  border-top: 1px solid var(--app-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  flex-wrap: wrap;
}

.gift-price {
  font-size: 1rem;
  font-weight: 700;
  color: var(--app-text);
}

.gift-price-empty {
  font-size: 0.8rem;
  color: var(--app-text-dim);
}

.gift-actions { display: flex; align-items: center; gap: 6px; }

.btn-reserve {
  display: flex;
  align-items: center;
  gap: 5px;
  background: var(--app-text);
  color: white;
  border: none;
  border-radius: 8px;
  padding: 6px 14px;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
}

.btn-reserve:hover:not(:disabled) { background: #3d3a36; }
.btn-reserve:disabled { opacity: 0.5; cursor: not-allowed; }

.btn-buy {
  display: flex;
  align-items: center;
  gap: 4px;
  background: #16a34a;
  color: white;
  border: none;
  border-radius: 6px;
  padding: 5px 12px;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
}

.btn-buy:hover:not(:disabled) { background: #15803d; }
.btn-buy:disabled { opacity: 0.5; cursor: not-allowed; }

.my-claim {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.82rem;
  color: var(--app-text-muted);
}

.btn-unreserve {
  display: flex;
  align-items: center;
  gap: 4px;
  background: none;
  border: 1px solid var(--app-border);
  border-radius: 6px;
  padding: 4px 10px;
  font-size: 0.8rem;
  color: var(--app-text-muted);
  cursor: pointer;
  transition: all 0.15s;
}

.btn-unreserve:hover:not(:disabled) { background: var(--app-surface-2); color: var(--app-text); }
.btn-unreserve:disabled { opacity: 0.5; cursor: not-allowed; }

.reserved-by {
  font-size: 0.82rem;
  color: var(--app-text-muted);
}

.bought-label {
  font-size: 0.82rem;
  font-weight: 600;
  color: #1d4ed8;
}

/* Name dialog */
.dialog-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 50;
  padding: 1rem;
}

.dialog-card {
  background: var(--app-surface);
  border: 1px solid var(--app-border);
  border-radius: 16px;
  padding: 2rem;
  max-width: 380px;
  width: 100%;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
}

.dialog-logo {
  width: 44px;
  height: 44px;
  border-radius: 11px;
  background: var(--app-text);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 0.25rem;
}

.dialog-card h2 {
  font-size: 1.3rem;
  font-weight: 700;
  color: var(--app-text);
  margin: 0;
}

.dialog-card p {
  font-size: 0.9rem;
  color: var(--app-text-muted);
  margin: 0;
  line-height: 1.5;
}

.dialog-card input {
  width: 100%;
  border: 1px solid var(--app-border);
  border-radius: 8px;
  padding: 10px 14px;
  font-size: 0.95rem;
  color: var(--app-text);
  outline: none;
  text-align: center;
}

.dialog-card input:focus { border-color: var(--app-text); }

.dialog-card button {
  width: 100%;
  background: var(--app-text);
  color: white;
  border: none;
  border-radius: 8px;
  padding: 10px;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
}

.dialog-card button:hover:not(:disabled) { background: #3d3a36; }
.dialog-card button:disabled { opacity: 0.5; cursor: not-allowed; }

@media (max-width: 480px) {
  .main { padding: 1rem 0.75rem; }

  .gifts-grid { grid-template-columns: 1fr; gap: 1rem; }

  .gift-footer { flex-direction: column; align-items: flex-start; gap: 10px; }

  .my-claim { flex-wrap: wrap; gap: 6px; }

  .visitor-name { display: none; }
}
</style>
