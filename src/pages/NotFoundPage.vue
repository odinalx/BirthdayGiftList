<script setup lang="ts">
</script>

<template>
  <div class="not-found">
    <h1>404</h1>
    <p>Page introuvable.</p>
    <a href="/">Retour à l'accueil</a>
  </div>
</template>

<style scoped>
.not-found {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  background: var(--app-bg);
  color: var(--app-text);
}

h1 {
  font-size: 6rem;
  font-weight: 800;
  margin: 0;
}

p {
  color: var(--app-text-muted);
  font-size: 1.1rem;
}

a {
  color: var(--app-text);
  font-weight: 600;
  text-decoration: underline;
}
</style>
