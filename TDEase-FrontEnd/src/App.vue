<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'

onMounted(() => {})
</script>

<style>
:root {
  font-family: Inter, Avenir, Helvetica, Arial, sans-serif;
  font-size: 16px;
  line-height: 24px;
  font-weight: 400;

  /* Use Catppuccin semantic colors */
  color: var(--ctp-text);
  background-color: var(--ctp-base);

  font-synthesis: none;
  text-rendering: optimizeLegibility;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  -webkit-text-size-adjust: 100%;
}

#app {
  width: 100%;
  height: 100vh;
  margin: 0;
  padding: 0;
  background-color: var(--ctp-base);
  color: var(--ctp-text);
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  padding: 0;
  min-height: 100vh;
  background-color: var(--ctp-base);
  color: var(--ctp-text);
}

/* Selection color */
::selection {
  background-color: var(--ctp-surface2);
  color: var(--ctp-text);
}

/* Scrollbar styling */
::-webkit-scrollbar {
  width: 12px;
  height: 12px;
}

::-webkit-scrollbar-track {
  background: var(--ctp-mantle);
}

::-webkit-scrollbar-thumb {
  background: var(--ctp-surface1);
  border-radius: 6px;
  border: 3px solid var(--ctp-mantle);
}

::-webkit-scrollbar-thumb:hover {
  background: var(--ctp-surface2);
}

/* Focus styles */
:focus-visible {
  outline: 2px solid var(--ctp-blue);
  outline-offset: 2px;
}

/* Global icon styles */
.el-icon {
  color: var(--icon-primary);
}

.el-button .el-icon {
  color: inherit;
}
</style>
