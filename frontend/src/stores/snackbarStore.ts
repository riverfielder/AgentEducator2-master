import { defineStore } from 'pinia';
import { ref, computed } from 'vue';

export const useSnackbar = defineStore('snackbar', () => {
  const visible = ref(false);
  const text = ref('');
  const color = ref('primary');
  const timeout = ref(3000);

  function show(options: { text: string; color?: string; timeout?: number }) {
    text.value = options.text;
    color.value = options.color || 'primary';
    timeout.value = options.timeout || 3000;
    visible.value = true;
  }

  function hide() {
    visible.value = false;
  }

  return {
    visible,
    text,
    color,
    timeout,
    show,
    hide
  };
});