import { useEffect, useRef } from "react";
import { useAuth } from "react-oidc-context";

export default function LoginPage() {
  const auth = useAuth();
  const started = useRef(false);

  useEffect(() => {
    if (auth.isLoading || started.current) return;
    started.current = true;
    if (auth.isAuthenticated) {
      window.location.replace("/");
    } else {
      auth.signinRedirect();
    }
  }, [auth.isLoading, auth.isAuthenticated]);

  return <p>Redirecting to sign-in…</p>;
}
