import * as React from 'react'
import { fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import {
  renderWithProviders,
  SPACING,
  COLORS,
  TYPOGRAPHY,
  BORDERS,
} from '@opentrons/components'
import { NavTab } from '..'

const render = (props: React.ComponentProps<typeof NavTab>) => {
  return renderWithProviders(
    <MemoryRouter>
      <NavTab {...props} />
    </MemoryRouter>
  )[0]
}

describe('NavTab', () => {
  let props: React.ComponentProps<typeof NavTab>

  beforeEach(() => {
    props = {
      to: '/protocols',
      tabName: 'protocols',
      disabled: false,
    }
  })

  afterEach(() => {
    jest.resetAllMocks()
  })

  it('renders navtab with text and link', () => {
    const { getByText } = render(props)
    const tab = getByText('protocols')
    expect(tab).toHaveAttribute('href', '/protocols')
    expect(tab).toHaveStyle(
      `padding: 0 ${SPACING.spacing2} ${SPACING.spacing3}`
    )
    expect(tab).toHaveStyle(`font-size: ${TYPOGRAPHY.fontSizeLabel}`)
    expect(tab).toHaveStyle(`font-weight: ${TYPOGRAPHY.fontWeightSemiBold}`)
    expect(tab).toHaveStyle(`color: ${COLORS.darkGreyEnabled}`)
    fireEvent.click(tab)
    expect(tab).toHaveStyle(`color: ${COLORS.darkBlackEnabled}`)
    expect(tab).toHaveStyle(`border-bottom-color: ${COLORS.blueEnabled}`)
    expect(tab).toHaveStyle(`border-bottom-width: ${SPACING.spacing1}`)
    expect(tab).toHaveStyle(`border-bottom-style: ${BORDERS.styleSolid}`)
  })

  it('should navtab is disabled if disabled is true', () => {
    props.disabled = true
    const { getByText } = render(props)
    const tab = getByText('protocols')
    expect(tab.tagName.toLowerCase()).toBe('span')
    expect(tab).toHaveStyle(
      `padding: 0 ${SPACING.spacing2} ${SPACING.spacing3}`
    )
    expect(tab).toHaveStyle(`font-size: ${TYPOGRAPHY.fontSizeLabel}`)
    expect(tab).toHaveStyle(`font-weight: ${TYPOGRAPHY.fontWeightSemiBold}`)
    expect(tab).toHaveStyle(`color: ${COLORS.errorDisabled}`)
  })

  it('renders navtab when pass to / as to', () => {
    props.to = '/'
    props.tabName = 'root'
    const { getByText } = render(props)
    const tab = getByText('root')
    expect(tab).toHaveAttribute('href', '/')
  })
})
