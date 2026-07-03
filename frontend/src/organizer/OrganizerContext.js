import { createContext, useContext } from 'react';

export const OrganizerContext = createContext(null);

export function useOrganizer() {
  const ctx = useContext(OrganizerContext);
  if (!ctx) {
    throw new Error('useOrganizer must be used within OrganizerApp');
  }
  return ctx;
}
