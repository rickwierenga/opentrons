import * as React from 'react'
import { useSelector } from 'react-redux'
import compact from 'lodash/compact'
import values from 'lodash/values'
import {
  ModuleViz,
  RobotCoordsText,
  RobotWorkSpace,
  useOnClickOutside,
  FONT_SIZE_BODY_1,
  FONT_WEIGHT_BOLD,
  TEXT_TRANSFORM_UPPERCASE,
  RobotWorkSpaceRenderProps,
} from '@opentrons/components'
import { MODULES_WITH_COLLISION_ISSUES } from '@opentrons/step-generation'
import {
  getLabwareHasQuirk,
  getModuleVizDims,
  inferModuleOrientationFromSlot,
  GEN_ONE_MULTI_PIPETTES,
  DeckSlot as DeckDefSlot,
  ModuleType,
} from '@opentrons/shared-data'
import { getDeckDefinitions } from '@opentrons/components/src/hardware-sim/Deck/getDeckDefinitions'
import { PSEUDO_DECK_SLOTS } from '../../constants'
import { i18n } from '../../localization'
import {
  getLabwareIsCompatible,
  getLabwareIsCustom,
} from '../../utils/labwareModuleCompatibility'
import {
  selectors as labwareDefSelectors,
  LabwareDefByDefURI,
} from '../../labware-defs'

import { selectors as featureFlagSelectors } from '../../feature-flags'
import {
  getSlotsBlockedBySpanning,
  getSlotIsEmpty,
  InitialDeckSetup,
  LabwareOnDeck as LabwareOnDeckType,
  ModuleOnDeck,
} from '../../step-forms'
import { BrowseLabwareModal } from '../labware'
import { ModuleTag } from './ModuleTag'
import { SlotWarning } from './SlotWarning'
import { LabwareOnDeck } from './LabwareOnDeck'
import { SlotControls, LabwareControls, DragPreview } from './LabwareOverlays'

import { TerminalItemId } from '../../steplist'

import styles from './DeckSetup.css'

export const DECK_LAYER_BLOCKLIST = [
  'calibrationMarkings',
  'fixedBase',
  'doorStops',
  'metalFrame',
  'removalHandle',
  'removableDeckOutline',
  'screwHoles',
]

export interface DeckSetupProps {
  selectedTerminalItemId?: TerminalItemId | null
  handleClickOutside?: () => unknown
  drilledDown: boolean
  initialDeckSetup: InitialDeckSetup
}

type ContentsProps = RobotWorkSpaceRenderProps & {
  selectedTerminalItemId?: TerminalItemId | null
  initialDeckSetup: InitialDeckSetup
  showGen1MultichannelCollisionWarnings: boolean
}

export const VIEWBOX_MIN_X = -64
export const VIEWBOX_MIN_Y = -10
export const VIEWBOX_WIDTH = 520
export const VIEWBOX_HEIGHT = 414

const getSlotDefForModuleSlot = (
  moduleOnDeck: ModuleOnDeck,
  deckSlots: { [slotId: string]: DeckDefSlot }
): DeckDefSlot => {
  const parentSlotDef =
    deckSlots[moduleOnDeck.slot] || PSEUDO_DECK_SLOTS[moduleOnDeck.slot]
  const moduleOrientation = inferModuleOrientationFromSlot(moduleOnDeck.slot)
  const moduleData = getModuleVizDims(moduleOrientation, moduleOnDeck.type)

  return {
    ...parentSlotDef,
    id: moduleOnDeck.id,
    position: [
      parentSlotDef.position[0] + moduleData.childXOffset,
      parentSlotDef.position[1] + moduleData.childYOffset,
      0,
    ],
    boundingBox: {
      xDimension: moduleData.childXDimension,
      yDimension: moduleData.childYDimension,
      zDimension: 0,
    },
    displayName: `Slot of ${moduleOnDeck.type} in slot ${moduleOnDeck.slot}`,
  }
}

const getModuleSlotDefs = (
  initialDeckSetup: InitialDeckSetup,
  deckSlots: { [slotId: string]: DeckDefSlot }
): DeckDefSlot[] => {
  return values(initialDeckSetup.modules).map((moduleOnDeck: ModuleOnDeck) =>
    getSlotDefForModuleSlot(moduleOnDeck, deckSlots)
  )
}

export interface SwapBlockedArgs {
  hoveredLabware?: LabwareOnDeckType | null
  draggedLabware?: LabwareOnDeckType | null
  modulesById: InitialDeckSetup['modules']
  customLabwareDefs: LabwareDefByDefURI
}

export const getSwapBlocked = (args: SwapBlockedArgs): boolean => {
  const {
    hoveredLabware,
    draggedLabware,
    modulesById,
    customLabwareDefs,
  } = args
  if (!hoveredLabware || !draggedLabware) {
    return false
  }

  const sourceModuleType: ModuleType | null =
    modulesById[draggedLabware.slot]?.type || null
  const destModuleType: ModuleType | null =
    modulesById[hoveredLabware.slot]?.type || null

  const draggedLabwareIsCustom = getLabwareIsCustom(
    customLabwareDefs,
    draggedLabware
  )
  const hoveredLabwareIsCustom = getLabwareIsCustom(
    customLabwareDefs,
    hoveredLabware
  )

  // dragging custom labware to module gives not compat error
  const labwareSourceToDestBlocked = sourceModuleType
    ? !getLabwareIsCompatible(hoveredLabware.def, sourceModuleType) &&
      !hoveredLabwareIsCustom
    : false
  const labwareDestToSourceBlocked = destModuleType
    ? !getLabwareIsCompatible(draggedLabware.def, destModuleType) &&
      !draggedLabwareIsCustom
    : false

  return labwareSourceToDestBlocked || labwareDestToSourceBlocked
}

// TODO IL 2020-01-12: to support dynamic labware/module movement during a protocol,
// don't use initialDeckSetup here. Use some version of timelineFrameForActiveItem
export const DeckSetupContents = (props: ContentsProps): JSX.Element => {
  const {
    initialDeckSetup,
    deckSlotsById,
    getRobotCoordsFromDOMCoords,
    showGen1MultichannelCollisionWarnings,
  } = props

  // NOTE: handling module<>labware compat when moving labware to empty module
  // is handled by SlotControls.
  // But when swapping labware when at least one is on a module, we need to be aware
  // of not only what labware is being dragged, but also what labware is **being
  // hovered over**. The intrinsic state of `react-dnd` is not designed to handle that.
  // So we need to use our own state here to determine
  // whether swapping will be blocked due to labware<>module compat:
  const [hoveredLabware, setHoveredLabware] = React.useState<
    LabwareOnDeckType | null | undefined
  >(null)
  const [draggedLabware, setDraggedLabware] = React.useState<
    LabwareOnDeckType | null | undefined
  >(null)

  const customLabwareDefs = useSelector(
    labwareDefSelectors.getCustomLabwareDefsByURI
  )
  const swapBlocked = getSwapBlocked({
    hoveredLabware,
    draggedLabware,
    modulesById: initialDeckSetup.modules,
    customLabwareDefs,
  })

  const handleHoverEmptySlot = React.useCallback(
    () => setHoveredLabware(null),
    []
  )

  const slotsBlockedBySpanning = getSlotsBlockedBySpanning(
    props.initialDeckSetup
  )
  const deckSlots: DeckDefSlot[] = values(deckSlotsById)
  const moduleSlots = getModuleSlotDefs(initialDeckSetup, deckSlotsById)
  // NOTE: in these arrays of slots, order affects SVG render layering
  // labware can be in a module or on the deck
  const labwareParentSlots: DeckDefSlot[] = [...deckSlots, ...moduleSlots]
  // modules can be on the deck, including pseudo-slots (eg special 'spanning' slot for thermocycler position)
  const moduleParentSlots = [...deckSlots, ...values(PSEUDO_DECK_SLOTS)]

  const allLabware: LabwareOnDeckType[] = Object.keys(
    initialDeckSetup.labware
  ).reduce<LabwareOnDeckType[]>((acc, labwareId) => {
    const labware = initialDeckSetup.labware[labwareId]
    return getLabwareHasQuirk(labware.def, 'fixedTrash')
      ? acc
      : [...acc, labware]
  }, [])

  const allModules: ModuleOnDeck[] = values(initialDeckSetup.modules)

  // NOTE: naively hard-coded to show warning north of slots 1 or 3 when occupied by any module
  const multichannelWarningSlots: DeckDefSlot[] = showGen1MultichannelCollisionWarnings
    ? compact([
        (allModules.some(
          moduleOnDeck =>
            moduleOnDeck.slot === '1' &&
            // @ts-expect-error(sa, 2021-6-21): ModuleModel is a super type of the elements in MODULES_WITH_COLLISION_ISSUES
            MODULES_WITH_COLLISION_ISSUES.includes(moduleOnDeck.model)
        ) &&
          deckSlotsById?.['4']) ||
          null,
        (allModules.some(
          moduleOnDeck =>
            moduleOnDeck.slot === '3' &&
            // @ts-expect-error(sa, 2021-6-21): ModuleModel is a super type of the elements in MODULES_WITH_COLLISION_ISSUES
            MODULES_WITH_COLLISION_ISSUES.includes(moduleOnDeck.model)
        ) &&
          deckSlotsById?.['6']) ||
          null,
      ])
    : []

  return (
    <>
      {/* all modules */}
      {allModules.map(moduleOnDeck => {
        const slot = moduleParentSlots.find(
          slot => slot.id === moduleOnDeck.slot
        )
        if (!slot) {
          console.warn(
            `no slot ${moduleOnDeck.slot} for module ${moduleOnDeck.id}`
          )
          return null
        }

        const [moduleX, moduleY] = slot.position
        const orientation = inferModuleOrientationFromSlot(slot.id)

        return (
          <React.Fragment key={slot.id}>
            <ModuleViz
              x={moduleX}
              y={moduleY}
              orientation={orientation}
              moduleType={moduleOnDeck.type}
            />
            <ModuleTag
              x={moduleX}
              y={moduleY}
              orientation={orientation}
              id={moduleOnDeck.id}
            />
          </React.Fragment>
        )
      })}

      {/* on-deck warnings */}
      {multichannelWarningSlots.map(slot => (
        <SlotWarning
          key={slot.id}
          warningType="gen1multichannel"
          x={slot.position[0]}
          y={slot.position[1]}
          xDimension={slot.boundingBox.xDimension}
          yDimension={slot.boundingBox.yDimension}
          orientation={inferModuleOrientationFromSlot(slot.id)}
        />
      ))}

      {/* SlotControls for all empty deck + module slots */}
      {labwareParentSlots
        .filter(
          slot =>
            !slotsBlockedBySpanning.includes(slot.id) &&
            getSlotIsEmpty(props.initialDeckSetup, slot.id)
        )
        .map(slot => {
          return (
            // @ts-expect-error (ce, 2021-06-21) once we upgrade to the react-dnd hooks api, and use react-redux hooks, typing this will be easier
            <SlotControls
              key={slot.id}
              slot={slot}
              selectedTerminalItemId={props.selectedTerminalItemId}
              // Module slots' ids reference their parent module
              moduleType={initialDeckSetup.modules[slot.id]?.type || null}
              handleDragHover={handleHoverEmptySlot}
            />
          )
        })}

      {/* all labware on deck and in modules */}
      {allLabware.map(labware => {
        const slot = labwareParentSlots.find(slot => slot.id === labware.slot)
        if (!slot) {
          console.warn(`no slot ${labware.slot} for labware ${labware.id}!`)
          return null
        }
        return (
          <React.Fragment key={labware.id}>
            <LabwareOnDeck
              x={slot.position[0]}
              y={slot.position[1]}
              labwareOnDeck={labware}
            />
            <g>
              <LabwareControls
                slot={slot}
                setHoveredLabware={setHoveredLabware}
                setDraggedLabware={setDraggedLabware}
                swapBlocked={
                  swapBlocked &&
                  (labware.id === hoveredLabware?.id ||
                    labware.id === draggedLabware?.id)
                }
                labwareOnDeck={labware}
                selectedTerminalItemId={props.selectedTerminalItemId}
              />
            </g>
          </React.Fragment>
        )
      })}

      <DragPreview getRobotCoordsFromDOMCoords={getRobotCoordsFromDOMCoords} />
    </>
  )
}

const getHasGen1MultiChannelPipette = (
  pipettes: InitialDeckSetup['pipettes']
): boolean => {
  const pipetteIds = Object.keys(pipettes)
  return pipetteIds.some(pipetteId =>
    GEN_ONE_MULTI_PIPETTES.includes(pipettes[pipetteId]?.name)
  )
}

export const DeckSetup = (props: DeckSetupProps): JSX.Element => {
  const _disableCollisionWarnings = useSelector(
    featureFlagSelectors.getDisableModuleRestrictions
  )
  const _hasGen1MultichannelPipette = React.useMemo(
    () => getHasGen1MultiChannelPipette(props.initialDeckSetup.pipettes),
    [props.initialDeckSetup.pipettes]
  )
  const showGen1MultichannelCollisionWarnings =
    !_disableCollisionWarnings && _hasGen1MultichannelPipette

  const deckDef = React.useMemo(() => getDeckDefinitions().ot2_standard, [])
  const wrapperRef: React.RefObject<HTMLDivElement> = useOnClickOutside({
    onClickOutside: props.handleClickOutside,
  })

  return (
    <React.Fragment>
      <div className={styles.deck_row}>
        {props.drilledDown && <BrowseLabwareModal />}
        <div ref={wrapperRef} className={styles.deck_wrapper}>
          <RobotWorkSpace
            deckLayerBlocklist={DECK_LAYER_BLOCKLIST}
            deckDef={deckDef}
            viewBox={`${VIEWBOX_MIN_X} ${VIEWBOX_MIN_Y} ${VIEWBOX_WIDTH} ${VIEWBOX_HEIGHT}`}
            className={styles.robot_workspace}
          >
            {({ deckSlotsById, getRobotCoordsFromDOMCoords }) => (
              <>
                <DeckSetupContents
                  initialDeckSetup={props.initialDeckSetup}
                  selectedTerminalItemId={props.selectedTerminalItemId}
                  {...{
                    deckSlotsById,
                    getRobotCoordsFromDOMCoords,
                    showGen1MultichannelCollisionWarnings,
                  }}
                />
              </>
            )}
          </RobotWorkSpace>
        </div>
      </div>
    </React.Fragment>
  )
}

export const NullDeckState = (): JSX.Element => {
  const deckDef = React.useMemo(() => getDeckDefinitions().ot2_standard, [])

  return (
    <div className={styles.deck_row}>
      <div className={styles.deck_wrapper}>
        <RobotWorkSpace
          deckLayerBlocklist={DECK_LAYER_BLOCKLIST}
          deckDef={deckDef}
          viewBox={`${VIEWBOX_MIN_X} ${VIEWBOX_MIN_Y} ${VIEWBOX_WIDTH} ${VIEWBOX_HEIGHT}`}
          className={styles.robot_workspace}
        >
          {() => (
            <>
              {/* TODO(IL, 2021-03-15): use styled-components for RobotCoordsText instead of style prop */}
              <RobotCoordsText
                x={5}
                y={375}
                style={{ textTransform: TEXT_TRANSFORM_UPPERCASE }}
                fill="#cccccc"
                fontWeight={FONT_WEIGHT_BOLD}
                fontSize={FONT_SIZE_BODY_1}
              >
                {i18n.t('deck.inactive_deck')}
              </RobotCoordsText>
            </>
          )}
        </RobotWorkSpace>
      </div>
    </div>
  )
}
