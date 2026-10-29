import ReactDOM from "react-dom/client";
import { AuthProvider } from "react-oidc-context";
import App from "./App";
import "./index.css";

const oidcConfig = {
  authority: import.meta.env.VITE_COGNITO_AUTHORITY,
  client_id: import.meta.env.VITE_COGNITO_CLIENT_ID,
  redirect_uri: window.location.origin + "/",
  scope: "openid email profile",
  onSigninCallback: () => window.history.replaceState({}, document.title, "/"),
};

ReactDOM.createRoot(document.getElementById("root")).render(
  <AuthProvider {...oidcConfig}>
    <App />
  </AuthProvider>
);
