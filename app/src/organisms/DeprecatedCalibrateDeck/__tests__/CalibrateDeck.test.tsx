import * as React from 'react'
import { Provider } from 'react-redux'
import { mount } from 'enzyme'
import { act } from 'react-dom/test-utils'
import { when, resetAllWhenMocks } from 'jest-when'

import { getDeckDefinitions } from '@opentrons/components/src/hardware-sim/Deck/getDeckDefinitions'

import * as Sessions from '../../../redux/sessions'
import { mockDeckCalibrationSessionAttributes } from '../../../redux/sessions/__fixtures__'

import { DeprecatedCalibrateDeck } from '../index'
import {
  Introduction,
  DeckSetup,
  TipPickUp,
  TipConfirmation,
  SaveZPoint,
  SaveXYPoint,
  CompleteConfirmation,
} from '../../DeprecatedCalibrationPanels'

import type { ReactWrapper, HTMLAttributes } from 'enzyme'
import type { DeckCalibrationStep } from '../../../redux/sessions/types'
import type { DispatchRequestsType } from '../../../redux/robot-api'
import type { Dispatch } from '../../../redux/types'
import type { CalibrationPanelProps } from '../../DeprecatedCalibrationPanels/types'

jest.mock('@opentrons/components/src/hardware-sim/Deck/getDeckDefinitions')
jest.mock('../../../redux/sessions/selectors')
jest.mock('../../../redux/robot-api/selectors')
jest.mock('../../../redux/config')

interface DeprecatedCalibrateDeckSpec {
  component: (props: CalibrationPanelProps) => JSX.Element
  currentStep: DeckCalibrationStep
}

const mockGetDeckDefinitions = getDeckDefinitions as jest.MockedFunction<
  typeof getDeckDefinitions
>

describe('DeprecatedCalibrateDeck', () => {
  let mockStore: any
  let render: (
    props?: Partial<React.ComponentProps<typeof DeprecatedCalibrateDeck>>
  ) => ReactWrapper<React.ComponentProps<typeof DeprecatedCalibrateDeck>>
  let dispatch: Dispatch
  let dispatchRequests: DispatchRequestsType
  let mockDeckCalSession: Sessions.DeckCalibrationSession = {
    id: 'fake_session_id',
    ...mockDeckCalibrationSessionAttributes,
  }

  const getExitButton = (
    wrapper: ReactWrapper<React.ComponentProps<typeof DeprecatedCalibrateDeck>>
  ): ReactWrapper<HTMLAttributes> => wrapper.find('button[title="exit"]')

  const POSSIBLE_CHILDREN = [
    Introduction,
    DeckSetup,
    TipPickUp,
    TipConfirmation,
    SaveZPoint,
    SaveXYPoint,
    CompleteConfirmation,
  ]

  const SPECS: DeprecatedCalibrateDeckSpec[] = [
    { component: Introduction, currentStep: 'sessionStarted' },
    { component: DeckSetup, currentStep: 'labwareLoaded' },
    { component: TipPickUp, currentStep: 'preparingPipette' },
    { component: TipConfirmation, currentStep: 'inspectingTip' },
    { component: SaveZPoint, currentStep: 'joggingToDeck' },
    { component: SaveXYPoint, currentStep: 'savingPointOne' },
    { component: SaveXYPoint, currentStep: 'savingPointTwo' },
    { component: SaveXYPoint, currentStep: 'savingPointThree' },
    { component: CompleteConfirmation, currentStep: 'calibrationComplete' },
  ]

  beforeEach(() => {
    dispatch = jest.fn()
    dispatchRequests = jest.fn()
    mockStore = {
      subscribe: () => {},
      getState: () => ({
        robotApi: {},
      }),
      dispatch,
    }
    when(mockGetDeckDefinitions).calledWith().mockReturnValue({})

    mockDeckCalSession = {
      id: 'fake_session_id',
      ...mockDeckCalibrationSessionAttributes,
    }

    render = (props = {}) => {
      const {
        showSpinner = false,
        isJogging = false,
        session = mockDeckCalSession,
      } = props
      return mount(
        <DeprecatedCalibrateDeck
          robotName="robot-name"
          session={session}
          dispatchRequests={dispatchRequests}
          showSpinner={showSpinner}
          isJogging={isJogging}
        />,
        {
          wrappingComponent: Provider,
          wrappingComponentProps: { store: mockStore },
        }
      )
    }
  })

  afterEach(() => {
    resetAllWhenMocks()
  })

  SPECS.forEach(spec => {
    it(`renders correct contents when currentStep is ${spec.currentStep}`, () => {
      mockDeckCalSession = {
        ...mockDeckCalSession,
        details: {
          ...mockDeckCalSession.details,
          currentStep: spec.currentStep,
        },
      }
      const wrapper = render()

      POSSIBLE_CHILDREN.forEach(child => {
        if (child === spec.component) {
          expect(wrapper.exists(child)).toBe(true)
        } else {
          expect(wrapper.exists(child)).toBe(false)
        }
      })
    })
  })

  it('renders confirm exit modal on exit click', () => {
    const wrapper = render()

    expect(wrapper.find('ConfirmExitModal').exists()).toBe(false)
    act((): void =>
      getExitButton(wrapper).invoke('onClick')?.({} as React.MouseEvent)
    )
    wrapper.update()
    expect(wrapper.find('ConfirmExitModal').exists()).toBe(true)
  })

  it('does not render spinner when showSpinner is false', () => {
    const wrapper = render({ showSpinner: false })
    expect(wrapper.find('SpinnerModalPage').exists()).toBe(false)
  })

  it('renders spinner when showSpinner is true', () => {
    const wrapper = render({ showSpinner: true })
    expect(wrapper.find('SpinnerModalPage').exists()).toBe(true)
  })
  it('does dispatch jog requests when not isJogging', () => {
    const session = {
      id: 'fake_session_id',
      ...mockDeckCalibrationSessionAttributes,
      details: {
        ...mockDeckCalibrationSessionAttributes.details,
        currentStep: Sessions.DECK_STEP_PREPARING_PIPETTE,
      },
    }
    const wrapper = render({ isJogging: false, session })
    wrapper.find('button[title="forward"]').invoke('onClick')?.(
      {} as React.MouseEvent
    )
    expect(dispatchRequests).toHaveBeenCalledWith(
      Sessions.createSessionCommand('robot-name', session.id, {
        command: Sessions.sharedCalCommands.JOG,
        data: { vector: [0, -0.1, 0] },
      })
    )
  })

  it('does not dispatch jog requests when isJogging', () => {
    const session = {
      id: 'fake_session_id',
      ...mockDeckCalibrationSessionAttributes,
      details: {
        ...mockDeckCalibrationSessionAttributes.details,
        currentStep: Sessions.DECK_STEP_PREPARING_PIPETTE,
      },
    }
    const wrapper = render({ isJogging: true, session })
    wrapper.find('button[title="forward"]').invoke('onClick')?.(
      {} as React.MouseEvent
    )
    expect(dispatchRequests).not.toHaveBeenCalledWith(
      Sessions.createSessionCommand('robot-name', session.id, {
        command: Sessions.sharedCalCommands.JOG,
        data: { vector: [0, -0.1, 0] },
      })
    )
  })
})
