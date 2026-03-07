import { useCallback, useRef, useState } from 'react';

export function useStreaming() {
  const abortRef = useRef<AbortController | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);

  const start = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = new AbortController();
    setIsStreaming(true);
    return abortRef.current.signal;
  }, []);

  const stop = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
    setIsStreaming(false);
  }, []);

  const finish = useCallback(() => {
    abortRef.current = null;
    setIsStreaming(false);
  }, []);

  return { isStreaming, start, stop, finish };
}
