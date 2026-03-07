'use client';

import * as React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useTheme } from '@/hooks/useTheme';

export function Providers({ children }: { children: React.ReactNode }) {
  useTheme();

  const [client] = React.useState(() => new QueryClient());

  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}
