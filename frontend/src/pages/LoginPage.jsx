import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import LoginForm from '../components/auth/LoginForm';
import RegisterForm from '../components/auth/RegisterForm';
import { TrendingUp } from 'lucide-react';

export default function LoginPage() {
  const [isLogin, setIsLogin] = useState(true);
  const { user } = useAuth();
  const navigate = useNavigate();

  // Always show login page in light mode
  useEffect(() => {
    document.documentElement.classList.remove('dark');
    return () => {
      if (localStorage.getItem('dark-mode') === 'true') {
        document.documentElement.classList.add('dark');
      }
    };
  }, []);

  useEffect(() => {
    if (user) navigate('/dashboard', { replace: true });
  }, [user, navigate]);

  return (
    <div className="min-h-screen flex bg-surface-50 relative">
      {/* Left branding panel */}
      <div className="hidden lg:flex lg:w-1/2 bg-primary-600 items-center justify-center p-12">
        <div className="max-w-md text-white">
          <div className="flex items-center gap-3 mb-8">
            <TrendingUp className="h-10 w-10" />
            <span className="text-3xl font-bold">StockAssist</span>
          </div>
          <h1 className="text-4xl font-bold mb-4">AI-Powered Stock Analysis</h1>
          <p className="text-primary-100 text-lg">
            Get real-time stock data, smart analysis, and AI-driven insights — all in one dashboard.
          </p>
        </div>
      </div>

      {/* Right form panel */}
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="w-full max-w-sm">
          {/* Mobile logo */}
          <div className="flex items-center gap-2 mb-8 lg:hidden">
            <TrendingUp className="h-8 w-8 text-primary-600" />
            <span className="text-2xl font-bold text-surface-900 dark:text-surface-100">StockAssist</span>
          </div>

          {isLogin ? (
            <LoginForm onSwitch={() => setIsLogin(false)} />
          ) : (
            <RegisterForm onSwitch={() => setIsLogin(true)} />
          )}
        </div>
      </div>
    </div>
  );
}
