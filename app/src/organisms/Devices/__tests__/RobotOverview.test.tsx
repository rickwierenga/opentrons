import * as React from 'react'
import { MemoryRouter } from 'react-router-dom'
import { fireEvent } from '@testing-library/react'
import { when, resetAllWhenMocks } from 'jest-when'

import { renderWithProviders } from '@opentrons/components'
import {
  mockOT2HealthResponse,
  mockOT2ServerHealthResponse,
  mockOT3HealthResponse,
  mockOT3ServerHealthResponse,
} from '@opentrons/discovery-client/src/__fixtures__'

import { i18n } from '../../../i18n'
import { useCurrentRunId } from '../../ProtocolUpload/hooks'
import { ChooseProtocolSlideout } from '../../ChooseProtocolSlideout'
import { mockConnectableRobot } from '../../../redux/discovery/__fixtures__'
import { useDispatchApiRequest } from '../../../redux/robot-api'
import { getBuildrootUpdateDisplayInfo } from '../../../redux/buildroot'
import { fetchLights } from '../../../redux/robot-controls'
import { getRobotModelByName } from '../../../redux/discovery'
import {
  HEALTH_STATUS_OK,
  ROBOT_MODEL_OT2,
  ROBOT_MODEL_OT3,
} from '../../../redux/discovery/constants'
import { useLights, useRobot, useRunStatuses } from '../hooks'
import { UpdateRobotBanner } from '../../UpdateRobotBanner'
import { RobotStatusBanner } from '../RobotStatusBanner'
import { RobotOverview } from '../RobotOverview'
import { RobotOverviewOverflowMenu } from '../RobotOverviewOverflowMenu'

import type { DispatchApiRequestType } from '../../../redux/robot-api'
import type { State } from '../../../redux/types'

jest.mock('../../../redux/robot-api')
jest.mock('../../../redux/robot-controls')
jest.mock('../../../redux/buildroot/selectors')
jest.mock('../../../redux/discovery/selectors')
jest.mock('../../ProtocolUpload/hooks')
jest.mock('../hooks')
jest.mock('../RobotStatusBanner')
jest.mock('../../UpdateRobotBanner')
jest.mock('../../ChooseProtocolSlideout')
jest.mock('../RobotOverviewOverflowMenu')

const OT2_PNG_FILE_NAME = 'OT2-R_HERO.png'
const OT3_PNG_FILE_NAME = 'OT3.png'

const MOCK_STATE: State = {
  discovery: {
    robot: { connection: { connectedTo: null } },
    robotsByName: {
      otie: {
        name: 'otie',
        health: mockOT2HealthResponse,
        serverHealth: mockOT2ServerHealthResponse,
        addresses: [
          {
            ip: '10.0.0.3',
            port: 31950,
            seen: true,
            healthStatus: HEALTH_STATUS_OK,
            serverHealthStatus: HEALTH_STATUS_OK,
            healthError: null,
            serverHealthError: null,
            advertisedModel: ROBOT_MODEL_OT2,
          },
        ],
      },
      buzz: {
        name: 'buzz',
        health: mockOT3HealthResponse,
        serverHealth: mockOT3ServerHealthResponse,
        addresses: [
          {
            ip: '10.0.0.4',
            port: 31950,
            seen: true,
            healthStatus: HEALTH_STATUS_OK,
            serverHealthStatus: HEALTH_STATUS_OK,
            healthError: null,
            serverHealthError: null,
            advertisedModel: ROBOT_MODEL_OT3,
          },
        ],
      },
    },
  },
} as any

const mockUseLights = useLights as jest.MockedFunction<typeof useLights>
const mockUseRobot = useRobot as jest.MockedFunction<typeof useRobot>
const mockUseCurrentRunId = useCurrentRunId as jest.MockedFunction<
  typeof useCurrentRunId
>
const mockRobotStatusBanner = RobotStatusBanner as jest.MockedFunction<
  typeof RobotStatusBanner
>
const mockChooseProtocolSlideout = ChooseProtocolSlideout as jest.MockedFunction<
  typeof ChooseProtocolSlideout
>
const mockUpdateRobotBanner = UpdateRobotBanner as jest.MockedFunction<
  typeof UpdateRobotBanner
>
const mockRobotOverviewOverflowMenu = RobotOverviewOverflowMenu as jest.MockedFunction<
  typeof RobotOverviewOverflowMenu
>
const mockUseDispatchApiRequest = useDispatchApiRequest as jest.MockedFunction<
  typeof useDispatchApiRequest
>
const mockUseRunStatuses = useRunStatuses as jest.MockedFunction<
  typeof useRunStatuses
>
const mockGetBuildrootUpdateDisplayInfo = getBuildrootUpdateDisplayInfo as jest.MockedFunction<
  typeof getBuildrootUpdateDisplayInfo
>
const mockFetchLights = fetchLights as jest.MockedFunction<typeof fetchLights>
const mockGetRobotModelByName = getRobotModelByName as jest.MockedFunction<
  typeof getRobotModelByName
>

const mockToggleLights = jest.fn()

const render = (props: React.ComponentProps<typeof RobotOverview>) => {
  return renderWithProviders(
    <MemoryRouter>
      <RobotOverview robotName={props.robotName} />
    </MemoryRouter>,
    {
      i18nInstance: i18n,
      initialState: MOCK_STATE,
    }
  )
}

describe('RobotOverview', () => {
  let dispatchApiRequest: DispatchApiRequestType
  let props: React.ComponentProps<typeof RobotOverview>

  beforeEach(() => {
    props = { robotName: 'otie' }
    dispatchApiRequest = jest.fn()
    mockUseRunStatuses.mockReturnValue({
      isRunRunning: false,
      isRunStill: false,
      isRunTerminal: true,
      isRunIdle: false,
    })
    mockGetBuildrootUpdateDisplayInfo.mockReturnValue({
      autoUpdateAction: 'reinstall',
      autoUpdateDisabledReason: null,
      updateFromFileDisabledReason: null,
    })
    mockUseDispatchApiRequest.mockReturnValue([dispatchApiRequest, []])
    mockUseLights.mockReturnValue({
      lightsOn: false,
      toggleLights: mockToggleLights,
    })
    mockUseRobot.mockReturnValue(mockConnectableRobot)
    mockRobotStatusBanner.mockReturnValue(<div>Mock RobotStatusBanner</div>)
    mockChooseProtocolSlideout.mockImplementation(({ showSlideout }) => (
      <div>
        Mock Choose Protocol Slideout {showSlideout ? 'showing' : 'hidden'}
      </div>
    ))
    mockUpdateRobotBanner.mockReturnValue(<div>Mock UpdateRobotBanner</div>)
    mockUseCurrentRunId.mockReturnValue(null)
    mockRobotOverviewOverflowMenu.mockReturnValue(
      <div>mock RobotOverviewOverflowMenu</div>
    )
    when(mockGetRobotModelByName)
      .calledWith(MOCK_STATE, 'otie')
      .mockReturnValue('OT-2')
  })
  afterEach(() => {
    jest.resetAllMocks()
    resetAllWhenMocks()
  })

  it('renders an OT-2 image', () => {
    const [{ getByRole }] = render(props)
    const image = getByRole('img')
    expect(image.getAttribute('src')).toEqual(OT2_PNG_FILE_NAME)
  })

  it('renders an OT-3 image', () => {
    props.robotName = 'buzz'
    when(mockGetRobotModelByName)
      .calledWith(MOCK_STATE, props.robotName)
      .mockReturnValue('OT-3')
    const [{ getByRole }] = render(props)
    const image = getByRole('img')
    expect(image.getAttribute('src')).toEqual(OT3_PNG_FILE_NAME)
  })

  it('renders a RobotStatusBanner component', () => {
    const [{ getByText }] = render(props)
    getByText('Mock RobotStatusBanner')
  })

  it('renders a UpdateRobotBanner component', () => {
    const [{ getByText }] = render(props)
    getByText('Mock UpdateRobotBanner')
  })

  it('fetches lights status', () => {
    render(props)
    expect(dispatchApiRequest).toBeCalledWith(mockFetchLights('otie'))
  })

  it('renders a lights toggle button', () => {
    const [{ getByRole, getByText }] = render(props)

    getByText('Controls')
    getByText('Lights')
    const toggle = getByRole('switch', { name: 'Lights' })
    toggle.click()
    expect(mockToggleLights).toBeCalled()
  })

  it('renders a Run a Protocol button', () => {
    const [{ getByText }] = render(props)

    getByText('Run a protocol')
  })

  it('renders a choose protocol slideout hidden by default, expanded after launch', () => {
    const [{ getByText, getByRole }] = render(props)

    getByText('Mock Choose Protocol Slideout hidden')
    const runButton = getByRole('button', { name: 'Run a protocol' })
    fireEvent.click(runButton)
    getByText('Mock Choose Protocol Slideout showing')
  })

  it('renders an overflow menu for the robot overview', () => {
    const [{ getByText }] = render(props)

    getByText('mock RobotOverviewOverflowMenu')
  })

  it('renders run a protocol button as disabled when run is not terminal and run id is not null', () => {
    mockUseCurrentRunId.mockReturnValue('id')
    mockUseRunStatuses.mockReturnValue({
      isRunRunning: false,
      isRunStill: false,
      isRunTerminal: false,
      isRunIdle: false,
    })
    const [{ getByRole }] = render(props)
    const runButton = getByRole('button', { name: 'Run a protocol' })
    expect(runButton).toBeDisabled()
  })

  it('disables the run a protocol button if robot software update is available', () => {
    mockGetBuildrootUpdateDisplayInfo.mockReturnValue({
      autoUpdateAction: 'upgrade',
      autoUpdateDisabledReason: null,
      updateFromFileDisabledReason: null,
    })

    const [{ getByRole }] = render(props)
    const button = getByRole('button', { name: 'Run a protocol' })
    expect(button).toBeDisabled()
  })

  it('renders run a protocol button as not disabled when run id is null but run status is not terminal', () => {
    mockUseCurrentRunId.mockReturnValue(null)
    mockUseRunStatuses.mockReturnValue({
      isRunRunning: false,
      isRunStill: false,
      isRunTerminal: true,
      isRunIdle: false,
    })
    const [{ getByText, getByRole }] = render(props)
    const runButton = getByRole('button', { name: 'Run a protocol' })
    fireEvent.click(runButton)
    getByText('Mock Choose Protocol Slideout showing')
  })
})
