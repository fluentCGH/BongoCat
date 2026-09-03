import type { MotionInfo } from 'easy-live2d'
import type { Container } from 'pixi.js'

import { convertFileSrc } from '@tauri-apps/api/core'
import { readDir, readTextFile } from '@tauri-apps/plugin-fs'
import { Config, CubismSetting, Live2DSprite, Priority } from 'easy-live2d'
import { groupBy } from 'es-toolkit/compat'
import JSON5 from 'json5'
import { Application, Ticker } from 'pixi.js'

import type { ModelSize } from '@/composables/useModel'

import { i18n } from '@/locales'

import type { SpritePetManifest } from './spritePet'

import { join } from './path'
import { SpritePet } from './spritePet'

Config.MouseFollow = false

class Live2d {
  private app: Application | null = null
  private liveModel: Live2DSprite | null = null
  private spriteModel: SpritePet | null = null
  private displayObject: Live2DSprite | Container | null = null

  constructor() { }

  private initApp() {
    if (this.app) return

    const view = document.getElementById('live2dCanvas') as HTMLCanvasElement

    this.app = new Application()

    return this.app.init({
      view,
      resizeTo: window,
      backgroundAlpha: 0,
      autoDensity: true,
      resolution: devicePixelRatio,
    })
  }

  public async load(path: string) {
    await this.initApp()

    this.destroy()

    const files = await readDir(path)

    const modelFile = files.find(file => file.name.endsWith('.model3.json'))
    const spriteFile = files.find(file => file.name.endsWith('.sprite.json'))

    if (!modelFile && !spriteFile) {
      throw new Error(i18n.global.t('utils.live2d.hints.notFound'))
    }

    if (spriteFile) {
      const manifestPath = join(path, spriteFile.name)
      const manifest = JSON5.parse(
        await readTextFile(manifestPath),
      ) as SpritePetManifest

      this.spriteModel = await SpritePet.create(path, manifest)
      this.displayObject = this.spriteModel.root
      this.app?.stage.addChild(this.displayObject)

      return {
        width: this.spriteModel.width,
        height: this.spriteModel.height,
        motions: {},
        expressions: [],
      }
    }

    const modelPath = join(path, modelFile!.name)

    const modelJSON = JSON5.parse(await readTextFile(modelPath))

    const modelSetting = new CubismSetting({
      modelJSON,
    })

    modelSetting.redirectPath(({ file }) => {
      return convertFileSrc(join(path, file))
    })

    this.liveModel = new Live2DSprite({
      modelSetting,
      ticker: Ticker.shared,
    })

    this.displayObject = this.liveModel
    this.app?.stage.addChild(this.liveModel)

    await this.liveModel.ready

    const { width, height } = this.liveModel

    const motions = groupBy(this.liveModel.getMotions(), 'group')
    const expressions = this.liveModel.getExpressions()

    return {
      width,
      height,
      motions,
      expressions,
    }
  }

  public destroy() {
    if (this.displayObject?.parent) {
      this.displayObject.parent.removeChild(this.displayObject)
    }

    this.liveModel?.destroy()
    this.spriteModel?.destroy()

    this.liveModel = null
    this.spriteModel = null
    this.displayObject = null
  }

  public resizeModel(modelSize: ModelSize) {
    if (!this.displayObject) return

    const { width, height } = modelSize

    const scaleX = innerWidth / width
    const scaleY = innerHeight / height
    const scale = Math.min(scaleX, scaleY)

    this.displayObject.scale.set(scale)
    this.displayObject.x = innerWidth / 2
    this.displayObject.y = innerHeight / 2

    if (this.liveModel) {
      this.liveModel.anchor.set(0.5)
    } else {
      this.displayObject.pivot.set(width / 2, height / 2)
    }
  }

  public startMotion(motion: MotionInfo) {
    return this.liveModel?.startMotion({
      ...motion,
      priority: Priority.Normal,
    })
  }

  public setExpression(index: number) {
    return this.liveModel?.setExpression({ index })
  }

  public getParameterValueRange(id: string) {
    return this.liveModel?.getParameterValueRangeById(id)
      ?? this.spriteModel?.getParameterValueRangeById(id)
  }

  public setParameterValue(id: string, value: number | boolean) {
    return this.liveModel?.setParameterValueById(id, Number(value))
      ?? this.spriteModel?.setParameterValueById(id, Number(value))
  }

  public setMotionSoundEnabled(enabled: boolean) {
    Config.MotionSound = enabled
  }

  public setMaxFPS(fps: number) {
    Ticker.shared.maxFPS = fps
  }
}

const live2d = new Live2d()

export default live2d
