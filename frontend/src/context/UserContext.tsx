"use client";

import { createContext, useContext, type ReactNode } from "react";
import type { User } from "@/lib/api";

const UserContext = createContext<User | null>(null);

export function UserProvider({
  user,
  children,
}: {
  user: User;
  children: ReactNode;
}) {
  return (
    <UserContext.Provider value={user}>{children}</UserContext.Provider>
  );
}

export function useUser() {
  return useContext(UserContext);
}
