import LoginForm from "@/components/LoginForm";

interface LoginPageProps {
  onLogin: (email: string, password: string) => void;
}

export default function LoginPage({ onLogin }: LoginPageProps) {
  return <LoginForm onLogin={onLogin} />;
}