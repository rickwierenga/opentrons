import * as React from 'react'
import { MemoryRouter, Route } from 'react-router-dom'

import { renderWithProviders } from '@opentrons/components'

import { i18n } from '../../../../i18n'
import { CalibrationDashboard } from '..'

jest.mock('../../../../organisms/Devices/hooks')
jest.mock('../../../../organisms/Devices/PipettesAndModules')
jest.mock('../../../../organisms/Devices/RecentProtocolRuns')
jest.mock('../../../../organisms/Devices/RobotOverview')
jest.mock('../../../../redux/discovery')

const render = (path = '/') => {
  return renderWithProviders(
    <MemoryRouter initialEntries={[path]} initialIndex={0}>
      <Route path="/devices/:robotName/robot-settings/calibration/dashboard">
        <CalibrationDashboard />
      </Route>
    </MemoryRouter>,
    {
      i18nInstance: i18n,
    }
  )
}

describe('CalibrationDashboard', () => {
  it('renders a robot calibration dashboard title', () => {
    const [{ getByText }] = render(
      '/devices/otie/robot-settings/calibration/dashboard'
    )

    getByText(`otie Calibration Dashboard`)
  })
})
