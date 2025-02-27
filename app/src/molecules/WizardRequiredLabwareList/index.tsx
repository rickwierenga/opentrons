import * as React from 'react'
import { useTranslation } from 'react-i18next'
import { css } from 'styled-components'
import {
  Flex,
  ALIGN_CENTER,
  DIRECTION_COLUMN,
  JUSTIFY_CENTER,
  JUSTIFY_SPACE_BETWEEN,
  SPACING,
  COLORS,
  JUSTIFY_SPACE_AROUND,
  TYPOGRAPHY,
} from '@opentrons/components'

import { StyledText } from '../../atoms/text'
import { Divider } from '../../atoms/structure'
import { labwareImages } from '../../organisms/CalibrationPanels/labwareImages'

interface WizardRequiredLabwareListProps {
  equipmentList: Array<React.ComponentProps<typeof RequiredLabwareCard>>
  footer: string
}
export function WizardRequiredLabwareList(
  props: WizardRequiredLabwareListProps
): JSX.Element {
  const { t } = useTranslation('robot_calibration')
  const { equipmentList, footer } = props

  return (
    <Flex flexDirection={DIRECTION_COLUMN}>
      <StyledText as="h3" fontWeight={TYPOGRAPHY.fontWeightSemiBold}>
        {t('you_will_need')}
      </StyledText>
      <Divider />
      {equipmentList.map(requiredLabwareProps => (
        <RequiredLabwareCard
          key={requiredLabwareProps.loadName}
          {...requiredLabwareProps}
        />
      ))}
      <StyledText
        marginTop={SPACING.spacing3}
        as="label"
        color={COLORS.darkGreyEnabled}
      >
        {footer}
      </StyledText>
    </Flex>
  )
}

interface RequiredLabwareCardProps {
  loadName: string
  displayName: string
  subtitle?: string
}

function RequiredLabwareCard(props: RequiredLabwareCardProps): JSX.Element {
  const { loadName, displayName, subtitle } = props
  const imageSrc =
    loadName in labwareImages
      ? labwareImages[loadName as keyof typeof labwareImages]
      : labwareImages.generic_custom_tiprack

  return (
    <>
      <Flex
        width="100%"
        justifyContent={JUSTIFY_SPACE_BETWEEN}
        alignItems={ALIGN_CENTER}
      >
        <Flex
          height="6rem"
          flex="0 1 30%"
          justifyContent={JUSTIFY_CENTER}
          alignItems={ALIGN_CENTER}
          marginRight={SPACING.spacing4}
        >
          <img
            css={css`
              max-width: 100%;
              max-height: 100%;
              flex: 0 1 5rem;
              display: block;
            `}
            src={imageSrc}
          />
        </Flex>
        <Flex
          flex="0 1 70%"
          flexDirection={DIRECTION_COLUMN}
          justifyContent={JUSTIFY_SPACE_AROUND}
        >
          <StyledText as="p">{displayName}</StyledText>
          {subtitle != null ? (
            <StyledText as="p" color={COLORS.darkGreyEnabled}>
              {subtitle}
            </StyledText>
          ) : null}
        </Flex>
      </Flex>
      <Divider />
    </>
  )
}
