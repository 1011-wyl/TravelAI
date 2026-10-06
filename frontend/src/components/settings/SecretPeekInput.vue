<template>
  <a-input
    :key="revealed ? 'peek' : 'hidden'"
    class="secret-peek-input"
    :value="shown"
    :type="revealed ? 'text' : 'password'"
    :readonly="revealed"
    :placeholder="placeholder"
    allow-clear
    autocomplete="off"
    @update:value="onValue"
  >
    <template #suffix>
      <span
        class="secret-peek-input__toggle ant-input-password-icon"
        role="button"
        tabindex="0"
        :aria-label="revealed ? t('settings.hidePeek') : t('settings.revealPeek')"
        :aria-pressed="revealed"
        @click="revealed = !revealed"
        @keydown.enter.prevent="revealed = !revealed"
        @keydown.space.prevent="revealed = !revealed"
      >
        <EyeOutlined v-if="!revealed" />
        <EyeInvisibleOutlined v-else />
      </span>
    </template>
  </a-input>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { EyeInvisibleOutlined, EyeOutlined } from '@ant-design/icons-vue'
import { maskSecret } from '@/utils/secretMask'

const props = withDefaults(
  defineProps<{
    modelValue: string
    placeholder?: string
  }>(),
  {
    placeholder: '',
  }
)

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const { t } = useI18n()
const revealed = ref(false)

const shown = computed(() => (revealed.value ? maskSecret(props.modelValue) : props.modelValue))

const onValue = (next: string) => {
  if (revealed.value) {
    if (!next) {
      revealed.value = false
      emit('update:modelValue', '')
    }
    return
  }
  emit('update:modelValue', next ?? '')
}
</script>

<style scoped>
.secret-peek-input__toggle {
  display: inline-flex;
  cursor: pointer;
  color: inherit;
}
</style>
