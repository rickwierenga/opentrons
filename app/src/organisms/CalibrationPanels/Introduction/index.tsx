import * as React from 'react'
import { useTranslation } from 'react-i18next'
import { getLabwareDisplayName } from '@opentrons/shared-data'
import {
  Flex,
  DIRECTION_COLUMN,
  JUSTIFY_SPACE_BETWEEN,
  SPACING,
  ALIGN_CENTER,
} from '@opentrons/components'

import * as Sessions from '../../../redux/sessions'
import { PrimaryButton, SecondaryButton } from '../../../atoms/buttons'
import { StyledText } from '../../../atoms/text'
import { NeedHelpLink } from '../NeedHelpLink'
import { ChooseTipRack } from '../ChooseTipRack'

import { TRASH_BIN_LOAD_NAME } from '../constants'
import { WizardRequiredLabwareList } from '../../../molecules/WizardRequiredLabwareList'
import { Body } from './Body'

import type { LabwareDefinition2 } from '@opentrons/shared-data'
import type { CalibrationPanelProps } from '../types'

const TRASH_BIN = 'Removable black plastic trash bin'

export function Introduction(props: CalibrationPanelProps): JSX.Element {
  const {
    tipRack,
    calBlock,
    sendCommands,
    sessionType,
    instruments,
    supportedCommands,
  } = props
  const { t } = useTranslation('robot_calibration')

  const [showChooseTipRack, setShowChooseTipRack] = React.useState(false)
  const [
    chosenTipRack,
    setChosenTipRack,
  ] = React.useState<LabwareDefinition2 | null>(null)

  const handleChosenTipRack = (value: LabwareDefinition2 | null): void => {
    value != null && setChosenTipRack(value)
  }
  const uniqueTipRacks = new Set(
    instruments?.map(instr => instr.tipRackLoadName)
  )

  let equipmentList: Array<{ loadName: string; displayName: string }> =
    uniqueTipRacks.size > 1
      ? instruments?.map(instr => ({
          loadName: instr.tipRackLoadName,
          displayName: instr.tipRackDisplay,
        })) ?? []
      : [
          {
            loadName: tipRack.loadName,
            displayName: getLabwareDisplayName(tipRack.definition),
          },
        ]

  if (chosenTipRack != null) {
    equipmentList = [
      {
        loadName: chosenTipRack.parameters.loadName,
        displayName: chosenTipRack.metadata.displayName,
      },
    ]
  }
  if (calBlock != null) {
    equipmentList = [
      ...equipmentList,
      {
        loadName: calBlock.loadName,
        displayName: getLabwareDisplayName(calBlock.definition),
      },
    ]
  } else if (
    sessionType === Sessions.SESSION_TYPE_CALIBRATION_HEALTH_CHECK ||
    sessionType === Sessions.SESSION_TYPE_TIP_LENGTH_CALIBRATION
  ) {
    equipmentList = [
      ...equipmentList,
      {
        loadName: TRASH_BIN_LOAD_NAME,
        displayName: TRASH_BIN,
      },
    ]
  }

  const proceed = (): void => {
    if (
      supportedCommands?.includes(Sessions.sharedCalCommands.LOAD_LABWARE) ??
      false
    ) {
      sendCommands({
        command: Sessions.sharedCalCommands.LOAD_LABWARE,
        data: { tiprackDefinition: chosenTipRack ?? tipRack.definition },
      })
    } else {
      sendCommands({ command: Sessions.sharedCalCommands.LOAD_LABWARE })
    }
  }

  return showChooseTipRack ? (
    <ChooseTipRack
      tipRack={props.tipRack}
      mount={props.mount}
      chosenTipRack={chosenTipRack}
      handleChosenTipRack={handleChosenTipRack}
      closeModal={() => setShowChooseTipRack(false)}
      robotName={props.robotName}
      defaultTipracks={props.defaultTipracks}
    />
  ) : (
    <Flex
      flexDirection={DIRECTION_COLUMN}
      justifyContent={JUSTIFY_SPACE_BETWEEN}
      padding={SPACING.spacing6}
      minHeight="25rem"
    >
      <Flex gridGap={SPACING.spacingXXL}>
        <Flex
          flex="1"
          flexDirection={DIRECTION_COLUMN}
          gridGap={SPACING.spacing3}
        >
          <StyledText as="h1" marginBottom={SPACING.spacing4}>
            {t('before_you_begin')}
          </StyledText>

          {/* TODO(bc, 2022-08-29): update InvalidationWarning logic once calibration dashboard is in place {false ? <InvalidationWarning /> : null} */}
          <Body sessionType={sessionType} />
        </Flex>
        <Flex flex="1">
          <WizardRequiredLabwareList
            equipmentList={equipmentList}
            footer={
              sessionType === Sessions.SESSION_TYPE_CALIBRATION_HEALTH_CHECK
                ? t('this_is_the_tip_used_in_pipette_offset_cal')
                : t('important_to_use_listed_equipment')
            }
          />
        </Flex>
      </Flex>
      <Flex
        width="100%"
        marginTop={SPACING.spacing6}
        justifyContent={JUSTIFY_SPACE_BETWEEN}
        alignItems={ALIGN_CENTER}
      >
        <NeedHelpLink />
        <Flex alignItems={ALIGN_CENTER} gridGap={SPACING.spacing3}>
          {sessionType === Sessions.SESSION_TYPE_DECK_CALIBRATION ? (
            <SecondaryButton onClick={() => setShowChooseTipRack(true)}>
              {t('change_tip_rack')}
            </SecondaryButton>
          ) : null}
          <PrimaryButton onClick={proceed}>{t('get_started')}</PrimaryButton>
        </Flex>
      </Flex>
    </Flex>
  )
}
