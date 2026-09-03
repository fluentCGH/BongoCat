import type { ExpressionInfo, MotionInfo } from 'easy-live2d'

import { resolveResource } from '@tauri-apps/api/path'
import { filter } from 'es-toolkit/compat'
import { defineStore } from 'pinia'
import { reactive, ref } from 'vue'

import { join } from '@/utils/path'

export type ModelMode = 'standard' | 'keyboard' | 'gamepad'

export interface Model {
  id: string
  path: string
  mode: ModelMode
  isPreset: boolean
}

export const useModelStore = defineStore('model', () => {
  const modelReady = ref(true)
  const models = ref<Model[]>([])
  const currentModel = ref<Model>()
  const supportKeys = reactive<Record<string, string>>({})
  const pressedKeys = reactive<Record<string, string>>({})
  const currentMotions = ref<Array<[string, MotionInfo[]]>>([])
  const currentExpressions = ref<ExpressionInfo[]>([])
  const shortcuts = reactive<Record<string, string>>({})

  const init = async () => {
    const modelsPath = await resolveResource('assets/models')

    const nextModels = filter(models.value, { isPreset: false })
    const presets: Array<{ directory: string, mode: ModelMode }> = [
      { directory: 'standard', mode: 'standard' },
      { directory: 'keyboard', mode: 'keyboard' },
      { directory: 'gamepad', mode: 'gamepad' },
      { directory: 'vessel', mode: 'keyboard' },
    ]

    for (const { directory, mode } of presets) {
      nextModels.unshift({
        id: `preset:${directory}`,
        mode,
        isPreset: true,
        path: join(modelsPath, directory),
      })
    }

    const matched = nextModels.find(({ id }) => id === currentModel.value?.id)

    currentModel.value = matched ?? nextModels[0]

    models.value = nextModels
  }

  return {
    modelReady,
    models,
    currentModel,
    supportKeys,
    pressedKeys,
    currentMotions,
    currentExpressions,
    shortcuts,
    init,
  }
}, {
  tauri: {
    filterKeys: ['supportKeys', 'pressedKeys'],
  },
})
