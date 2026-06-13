<script setup lang="ts">
import { RouterView } from 'vue-router'
import { onMounted } from 'vue'
import { useAuth } from '@/composables/useAuth'

const { init: initAuth } = useAuth()

onMounted(async () => {
  await initAuth()
})
</script>

<template>
  <RouterView />
</template>

<style>
:root {
  --app-bg: #faf8f5;
  --app-surface: #ffffff;
  --app-surface-2: #f5f2ed;
  --app-surface-3: #ebe7e0;
  --app-border: #e2ddd5;
  --app-border-hover: #d4cec5;
  --app-text: #1a1815;
  --app-text-muted: #78716c;
  --app-text-dim: #a8a29e;
  --theme-accent: #78716c;
  --theme-accent-hover: #57534e;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  background: var(--app-bg);
  color: var(--app-text);
}
</style>
