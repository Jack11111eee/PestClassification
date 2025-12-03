<template>
  <div id="app">
    <main>
      <RouterView />
    </main>
  </div>
</template>

<script setup>
import { RouterLink, RouterView } from 'vue-router'
</script>

<style scoped>
a {
  text-decoration: none;
  color: #42b983;
  font-weight: bold;
}

a.router-link-active {
  text-decoration: underline;
}
</style>