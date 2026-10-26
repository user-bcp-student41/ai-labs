import { describe, expect, it } from 'vitest';
import { getApiErrorMessage } from './api-error';

describe('getApiErrorMessage', () => {
  it('prefers the selected backend response field', () => {
    expect(getApiErrorMessage({ response: { data: { detail: 'Unavailable' } } }, 'detail', 'Fallback'))
      .toBe('Unavailable');
  });

  it('uses an Error message when the backend field is absent', () => {
    expect(getApiErrorMessage(new Error('Network failed'), 'message', 'Fallback')).toBe('Network failed');
  });

  it('uses a plain error message when the thrown value is not an Error', () => {
    expect(getApiErrorMessage({ message: 'Rejected' }, 'message', 'Fallback')).toBe('Rejected');
  });

  it('uses the fallback for an unknown error shape', () => {
    expect(getApiErrorMessage(null, 'detail', 'Fallback')).toBe('Fallback');
  });
});