import { useAuth } from "react-oidc-context";

export default function AuthBar() {
  const auth = useAuth();

  const signOut = async () => {
    await auth.removeUser();
    const clientId = import.meta.env.VITE_COGNITO_CLIENT_ID;
    const domain = import.meta.env.VITE_COGNITO_DOMAIN;
    window.location.href =
      `${domain}/logout?client_id=${clientId}` +
      `&logout_uri=${encodeURIComponent(window.location.origin + "/")}`;
  };

  if (auth.isLoading) return <header>Loading…</header>;

  return (
    <header style={{ display: "flex", gap: 12, justifyContent: "flex-end", padding: 12 }}>
      {auth.isAuthenticated ? (
        <>
          <span>{auth.user?.profile.email}</span>
          <button onClick={signOut}>Sign out</button>
        </>
      ) : (
        <button onClick={() => auth.signinRedirect()}>Sign in</button>
      )}
    </header>
  );
}
