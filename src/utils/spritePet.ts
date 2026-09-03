import { convertFileSrc } from '@tauri-apps/api/core'
import { Assets, Container, Sprite, Ticker } from 'pixi.js'

import { join } from './path'

interface PressedTransform {
  Translate?: [number, number]
  Rotation?: number
  Scale?: [number, number]
}

interface SpriteLayerConfig {
  Id: string
  File: string
  Pivot?: [number, number]
  Parameters?: string[]
  Pressed?: PressedTransform
}

export interface SpritePetManifest {
  Version: 1
  Name: string
  Canvas: {
    Width: number
    Height: number
  }
  Idle?: {
    Amplitude?: number
    Period?: number
  }
  Layers: SpriteLayerConfig[]
}

interface AnimatedLayer {
  sprite: Sprite
  pivot: [number, number]
  parameters: string[]
  pressed: Required<PressedTransform>
  amount: number
}

const DEFAULT_TRANSFORM: Required<PressedTransform> = {
  Translate: [0, 0],
  Rotation: 0,
  Scale: [1, 1],
}

/**
 * Lightweight layered-pet renderer used for artwork that has not been through
 * the proprietary Cubism .moc3 exporter.  It intentionally exposes the same
 * input parameter names as the bundled Live2D keyboard model.
 */
export class SpritePet {
  public readonly root = new Container()
  public readonly width: number
  public readonly height: number

  private readonly content = new Container()
  private readonly parameters = new Map<string, number>()
  private readonly animatedLayers: AnimatedLayer[] = []
  private elapsed = 0

  private constructor(
    private readonly manifest: SpritePetManifest,
  ) {
    this.width = manifest.Canvas.Width
    this.height = manifest.Canvas.Height
    this.root.addChild(this.content)
  }

  public static async create(path: string, manifest: SpritePetManifest) {
    const pet = new SpritePet(manifest)

    for (const layer of manifest.Layers) {
      const texture = await Assets.load(convertFileSrc(join(path, layer.File)))
      const sprite = new Sprite(texture)
      const pivot = layer.Pivot ?? [0, 0]

      sprite.pivot.set(...pivot)
      sprite.position.set(...pivot)
      pet.content.addChild(sprite)

      if (!layer.Parameters?.length || !layer.Pressed) continue

      for (const parameter of layer.Parameters) {
        pet.parameters.set(parameter, 0)
      }

      pet.animatedLayers.push({
        sprite,
        pivot,
        parameters: layer.Parameters,
        pressed: {
          ...DEFAULT_TRANSFORM,
          ...layer.Pressed,
        },
        amount: 0,
      })
    }

    Ticker.shared.add(pet.update)

    return pet
  }

  private update = (ticker: Ticker) => {
    const deltaSeconds = ticker.deltaMS / 1000
    const smoothing = 1 - Math.exp(-18 * deltaSeconds)

    this.elapsed += deltaSeconds

    const amplitude = this.manifest.Idle?.Amplitude ?? 0
    const period = this.manifest.Idle?.Period ?? 3

    this.content.y = amplitude
      ? Math.sin((this.elapsed / period) * Math.PI * 2) * amplitude
      : 0

    for (const layer of this.animatedLayers) {
      const target = Math.max(
        ...layer.parameters.map(parameter => this.parameters.get(parameter) ?? 0),
      )

      layer.amount += (target - layer.amount) * smoothing

      const { sprite, pivot, pressed, amount } = layer
      const [translateX, translateY] = pressed.Translate
      const [scaleX, scaleY] = pressed.Scale

      sprite.position.set(
        pivot[0] + translateX * amount,
        pivot[1] + translateY * amount,
      )
      sprite.rotation = pressed.Rotation * amount
      sprite.scale.set(
        1 + (scaleX - 1) * amount,
        1 + (scaleY - 1) * amount,
      )
    }
  }

  public getParameterValueRangeById(id: string) {
    if (!this.parameters.has(id)) return

    return { min: 0, max: 1 }
  }

  public setParameterValueById(id: string, value: number) {
    if (!this.parameters.has(id)) return

    this.parameters.set(id, Math.max(0, Math.min(1, value)))
  }

  public destroy() {
    Ticker.shared.remove(this.update)
    this.root.destroy({ children: true })
  }
}
