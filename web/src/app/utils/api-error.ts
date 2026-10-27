type ErrorResponseField = 'message' | 'detail';

function asRecord(value: unknown): Record<string, unknown> | undefined {
  if (typeof value !== 'object' || value === null) {
    return undefined;
  }
  return value as Record<string, unknown>;
}

export function getApiErrorMessage(error: unknown, responseField: ErrorResponseField, fallback: string): string {
  const errorRecord = asRecord(error);
  const responseRecord = asRecord(errorRecord?.['response']);
  const dataRecord = asRecord(responseRecord?.['data']);
  const responseMessage = dataRecord?.[responseField];
  if (typeof responseMessage === 'string' && responseMessage) {
    return responseMessage;
  }

  const errorMessage = error instanceof Error ? error.message : errorRecord?.['message'];
  if (typeof errorMessage === 'string' && errorMessage) {
    return errorMessage;
  }

  return fallback;
}