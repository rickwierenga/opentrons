import React from 'react'
import { Provider } from 'react-redux'
import { mount } from 'enzyme'
import {
  MAGNETIC_MODULE_V2,
  THERMOCYCLER_MODULE_TYPE,
  TEMPERATURE_MODULE_TYPE,
  MAGNETIC_MODULE_TYPE,
  HEATERSHAKER_MODULE_TYPE,
  THERMOCYCLER_MODULE_V2,
} from '@opentrons/shared-data'
import { CheckboxField } from '@opentrons/components'
import { getEnabledThermocyclerGen2 } from '../../../../feature-flags/selectors'
import { DEFAULT_MODEL_FOR_MODULE_TYPE } from '../../../../constants'
import { ModuleDiagram } from '../../../modules'
import { ModuleFields, ModuleFieldsProps } from '../ModuleFields'

jest.mock('../../../../feature-flags/selectors')

const getEnabledThermocyclerGen2Mock: jest.MockedFunction<any> = getEnabledThermocyclerGen2

describe('ModuleFields', () => {
  let magnetModuleOnDeck,
    temperatureModuleNotOnDeck,
    thermocyclerModuleNotOnDeck,
    heaterShakerModuleNotOnDeck
  let props: ModuleFieldsProps
  let store: any
  beforeEach(() => {
    getEnabledThermocyclerGen2Mock.mockReturnValue(false)
    store = {
      dispatch: jest.fn(),
      subscribe: jest.fn(),
      getState: () => ({}),
    }

    magnetModuleOnDeck = {
      onDeck: true,
      slot: '1',
      model: MAGNETIC_MODULE_V2,
    }
    temperatureModuleNotOnDeck = {
      onDeck: false,
      slot: '2',
      model: null,
    }
    thermocyclerModuleNotOnDeck = {
      onDeck: false,
      slot: '9',
      model: null,
    }
    heaterShakerModuleNotOnDeck = {
      onDeck: false,
      slot: '6',
      model: null,
    }

    props = {
      values: {
        [MAGNETIC_MODULE_TYPE]: magnetModuleOnDeck,
        [TEMPERATURE_MODULE_TYPE]: temperatureModuleNotOnDeck,
        [THERMOCYCLER_MODULE_TYPE]: thermocyclerModuleNotOnDeck,
        [HEATERSHAKER_MODULE_TYPE]: heaterShakerModuleNotOnDeck,
      },
      onFieldChange: jest.fn(),
      onSetFieldValue: jest.fn(),
      onSetFieldTouched: jest.fn(),
      onBlur: jest.fn(),
      touched: null,
      errors: null,
    }
  })

  function render(props: ModuleFieldsProps) {
    return mount(
      <Provider store={store}>
        <ModuleFields {...props} />
      </Provider>
    )
  }

  it('renders a module selection element for every module', () => {
    const wrapper = render(props)

    expect(wrapper.find(CheckboxField)).toHaveLength(4)
  })

  it('adds module to protocol when checkbox is selected and resets the model field', () => {
    const checkboxTargetName = `modulesByType.${TEMPERATURE_MODULE_TYPE}.onDeck`
    const targetToClear = `modulesByType.${TEMPERATURE_MODULE_TYPE}.model`
    const expectedEvent = {
      target: {
        name: checkboxTargetName,
        value: true,
      },
    }

    const wrapper = render(props)
    const temperatureSelectChange = wrapper
      .find({ name: checkboxTargetName })
      .first()
      .prop('onChange')
    temperatureSelectChange(expectedEvent)

    expect(props.onFieldChange).toHaveBeenCalledWith(expectedEvent)
    expect(props.onSetFieldValue).toHaveBeenCalledWith(targetToClear, null)
    expect(props.onSetFieldTouched).toHaveBeenCalledWith(targetToClear, false)
  })

  it('displays model select when module is selected and selects the model for the module', () => {
    const magnetModelName = `modulesByType.${MAGNETIC_MODULE_TYPE}.model`
    const expectedEvent = {
      target: {
        name: magnetModelName,
        value: MAGNETIC_MODULE_V2,
      },
    }

    const wrapper = render(props)
    const magnetModelSelect = wrapper
      .find({
        name: magnetModelName,
      })
      .first()
    magnetModelSelect.prop('onChange')(expectedEvent)

    expect(magnetModelSelect).toHaveLength(1)
    expect(props.onFieldChange).toHaveBeenCalledWith(expectedEvent)
  })

  it('displays an error for model select when select has been touched but no selection was made', () => {
    const propsWithErrors = {
      ...props,
      touched: {
        [MAGNETIC_MODULE_TYPE]: {
          model: true,
        },
      },
      errors: {
        [MAGNETIC_MODULE_TYPE]: {
          model: 'required',
        },
      },
    }
    const magnetModelSelectName = `modulesByType.${MAGNETIC_MODULE_TYPE}.model`

    const wrapper = render(propsWithErrors)
    const magnetModelSelect = wrapper
      .find({ name: magnetModelSelectName })
      .first()

    expect(magnetModelSelect.prop('error')).toEqual('required')
  })

  it('displays a default module img when no model has been selected', () => {
    const wrapper = render(props)
    const temperatureModuleDiagramProps = wrapper
      .find(ModuleDiagram)
      .filter({ type: TEMPERATURE_MODULE_TYPE })
      .props()

    expect(temperatureModuleDiagramProps).toEqual({
      type: TEMPERATURE_MODULE_TYPE,
      model: DEFAULT_MODEL_FOR_MODULE_TYPE[TEMPERATURE_MODULE_TYPE],
    })
  })

  it('displays specific module img when model has been selected', () => {
    props.values[MAGNETIC_MODULE_TYPE].model = MAGNETIC_MODULE_V2

    const wrapper = render(props)
    const magnetModuleDiagramProps = wrapper
      .find(ModuleDiagram)
      .filter({ type: MAGNETIC_MODULE_TYPE })
      .props()

    expect(magnetModuleDiagramProps).toEqual({
      type: MAGNETIC_MODULE_TYPE,
      model: MAGNETIC_MODULE_V2,
    })
  })

  it('displays Thermocycler gen2 module img when model has been selected and FF is turned on', () => {
    getEnabledThermocyclerGen2Mock.mockReturnValue(true)
    props.values[THERMOCYCLER_MODULE_TYPE].model = THERMOCYCLER_MODULE_V2

    const wrapper = render(props)
    const thermocyclerModuleDiagramProps = wrapper
      .find(ModuleDiagram)
      .filter({ type: THERMOCYCLER_MODULE_TYPE })
      .props()

    expect(thermocyclerModuleDiagramProps).toEqual({
      type: THERMOCYCLER_MODULE_TYPE,
      model: THERMOCYCLER_MODULE_V2,
    })
  })
})
