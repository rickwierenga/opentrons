import * as React from 'react'
import { css } from 'styled-components'
import {
  SPACING,
  COLORS,
  BORDERS,
  TYPOGRAPHY,
  styleProps,
} from '@opentrons/components'

interface SubmitPrimaryButtonProps {
  form: string
  value: string
  onClick?: (event: React.MouseEvent<HTMLInputElement>) => unknown
  disabled?: boolean
}
export const SubmitPrimaryButton = (
  props: SubmitPrimaryButtonProps
): JSX.Element => {
  const SUBMIT_INPUT_STYLE = css`
    background-color: ${COLORS.blueEnabled};
    border-radius: ${BORDERS.radiusSoftCorners};
    padding: ${SPACING.spacing3} ${SPACING.spacing4};
    color: ${COLORS.white};
    ${TYPOGRAPHY.pSemiBold}
    width: 100%;
    border: none;

    ${styleProps}

    &:focus-visible {
      box-shadow: 0 0 0 3px ${COLORS.warningEnabled};
    }

    &:hover {
      background-color: ${COLORS.blueHover};
      box-shadow: 0 0 0;
    }

    &:active {
      background-color: ${COLORS.bluePressed};
    }

    &:disabled {
      background-color: ${COLORS.darkGreyDisabled};
      color: ${COLORS.successDisabled};
    }
  `
  return <input {...props} css={SUBMIT_INPUT_STYLE} type="submit" />
}
