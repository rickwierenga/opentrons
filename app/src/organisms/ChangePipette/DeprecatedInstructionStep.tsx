import * as React from 'react'
import screwdriverSrc from '../../assets/images/change-pip/screwdriver.svg'
import styles from './styles.css'
import type {
  PipetteChannels,
  PipetteDisplayCategory,
} from '@opentrons/shared-data'
import type { Mount } from '@opentrons/components'
import type { Direction, Diagram } from './types'
interface DiagramProps {
  direction: Direction
  mount: Mount
  channels: PipetteChannels
  diagram: Diagram
  displayCategory: PipetteDisplayCategory | null
}

interface Props extends DiagramProps {
  step: 'one' | 'two'
  children: React.ReactNode
}
/**
 * @deprecated use InstructionStep instead
 */
export function getDiagramsSrc(props: DiagramProps): string {
  const { channels, displayCategory, direction, mount, diagram } = props
  const channelsKey = channels === 8 ? 'multi' : 'single'

  return displayCategory === 'GEN2'
    ? require(`../../assets/images/change-pip/${direction}-${mount}-${channelsKey}-GEN2-${diagram}@3x.png`)
    : require(`../../assets/images/change-pip/${direction}-${mount}-${channelsKey}-${diagram}@3x.png`)
}
/**
 * @deprecated use InstructionStep instead
 */
export function DeprecatedInstructionStep(props: Props): JSX.Element {
  const { step, children, ...diagramProps } = props

  return (
    <fieldset className={styles.step}>
      <legend className={styles.step_legend}>Step {step}</legend>
      <div>{children}</div>
      {props.diagram === 'screws' && (
        <img src={screwdriverSrc} className={styles.screwdriver} />
      )}
      <img src={getDiagramsSrc(diagramProps)} className={styles.diagram} />
    </fieldset>
  )
}
