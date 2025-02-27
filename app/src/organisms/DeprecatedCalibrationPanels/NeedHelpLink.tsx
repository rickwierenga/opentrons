import * as React from 'react'
import { Flex, Link, C_BLUE, FONT_SIZE_BODY_1 } from '@opentrons/components'

const NEED_HELP = 'Need Help?'
const SUPPORT_PAGE = 'https://support.opentrons.com/s/ot2-calibration'
type Props = React.ComponentProps<typeof Flex>

/**
 * @deprecated
 */
export function NeedHelpLink(props: Props): JSX.Element {
  return (
    <Flex {...props}>
      <Link
        external
        fontSize={FONT_SIZE_BODY_1}
        color={C_BLUE}
        href={SUPPORT_PAGE}
      >
        {NEED_HELP}
      </Link>
    </Flex>
  )
}
