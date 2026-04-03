import { describe, it, expect, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useAppStore } from '../../stores/appStore'

describe('appStore', () => {
  beforeEach(() => {
    useAppStore.getState().reset?.()
  })

  it('should initialize with default state', () => {
    const { result } = renderHook(() => useAppStore())
    
    expect(result.current.currentAnswers).toEqual([])
    expect(result.current.chatHistory).toEqual([])
    expect(result.current.sidebarCollapsed).toBe(false)
  })

  it('should add answer', () => {
    const { result } = renderHook(() => useAppStore())
    
    act(() => {
      result.current.addAnswer({
        question_id: 'q1',
        question_text: 'Test Question',
        question_type: 'text',
        answer_value: 'answer1',
      })
    })

    expect(result.current.currentAnswers).toHaveLength(1)
    expect(result.current.currentAnswers[0]).toEqual({
      question_id: 'q1',
      question_text: 'Test Question',
      question_type: 'text',
      answer_value: 'answer1',
    })
  })

  it('should update existing answer', () => {
    const { result } = renderHook(() => useAppStore())
    
    act(() => {
      result.current.addAnswer({
        question_id: 'q1',
        question_text: 'Test Question',
        question_type: 'text',
        answer_value: 'answer1',
      })
      result.current.updateAnswer({
        question_id: 'q1',
        question_text: 'Test Question',
        question_type: 'text',
        answer_value: 'updated_answer',
      })
    })

    expect(result.current.currentAnswers).toHaveLength(1)
    expect(result.current.currentAnswers[0].answer_value).toBe('updated_answer')
  })

  it('should toggle sidebar', () => {
    const { result } = renderHook(() => useAppStore())
    
    act(() => {
      result.current.setSidebarCollapsed(true)
    })

    expect(result.current.sidebarCollapsed).toBe(true)
  })

  it('should show notification', () => {
    const { result } = renderHook(() => useAppStore())
    
    act(() => {
      result.current.showNotification('Test message', 'success')
    })

    expect(result.current.notification.open).toBe(true)
    expect(result.current.notification.message).toBe('Test message')
    expect(result.current.notification.severity).toBe('success')
  })
})
