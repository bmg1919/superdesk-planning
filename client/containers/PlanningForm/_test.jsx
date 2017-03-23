import { createTestStore } from '../../utils'
import { mount } from 'enzyme'
import { PlanningForm } from '../index'
import React from 'react'
import { Provider } from 'react-redux'
import sinon from 'sinon'

describe('<PlanningForm />', () => {
    it('removes a coverage', () => {
        const initialState = {
            planning: {
                plannings: {
                    2: {
                        _id: '2',
                        slugline: 'slug',
                        coverages: [{ _id: 'coverage1' }],
                    },
                },
                agendas: [{
                    _id: '1',
                    name: 'agenda',
                }],
                currentAgendaId: '1',
                currentPlanningId: '2',
            },
        }
        const spyRemove = sinon.spy((resource, item) => {
            expect(item._id).toBe('coverage1')
            expect(spyRemove.callCount).toBe(1)
        })
        const store = createTestStore({
            initialState,
            extraArguments: { apiRemove: spyRemove },
        })
        const wrapper = mount(
            <Provider store={store}>
                <PlanningForm />
            </Provider>
        )
        expect(wrapper.mount().find('CoveragesFieldArray').find('.Coverage__item').length).toBe(1)
        wrapper.find('CoveragesFieldArray').find('.Coverage__remove').simulate('click')
        expect(wrapper.mount().find('CoveragesFieldArray').find('.Coverage__item').length).toBe(0)
        wrapper.find('form').simulate('submit')
        expect(wrapper.mount().find('CoveragesFieldArray').find('.Coverage__item').length).toBe(0)
    })
})
