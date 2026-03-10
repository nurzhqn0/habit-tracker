export type AuthState = {
  isReady: boolean;
  isLoggedIn: boolean;
  email: string | null;
};

export type UseAuthResult = AuthState & {
  login: (email: string) => void;
  logout: () => void;
  refresh: () => void;
};
