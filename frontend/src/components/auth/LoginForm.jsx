import { useState } from 'react';
import { useAuth } from '../../hooks/useAuth';
import Input from '../ui/Input';
import Button from '../ui/Button';
import Spinner from '../ui/Spinner';

export default function LoginForm({ onSwitch }) {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(email, password);
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid credentials');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <h2 className="text-2xl font-bold text-surface-900 dark:text-surface-100">Sign in</h2>
      <p className="text-sm text-surface-500 dark:text-surface-400">
        Welcome back! Sign in to your account.
      </p>
      {error && (
        <div className="p-3 text-sm text-negative bg-red-50 dark:bg-red-900/20 rounded-lg">{error}</div>
      )}
      <Input
        label="Email"
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="you@example.com"
        required
      />
      <Input
        label="Password"
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="Your password"
        required
      />
      <Button type="submit" className="w-full" disabled={loading}>
        {loading ? <Spinner size="sm" className="text-white" /> : 'Sign in'}
      </Button>
      <p className="text-center text-sm text-surface-500 dark:text-surface-400">
        Don't have an account?{' '}
        <button type="button" onClick={onSwitch} className="text-primary-600 hover:underline font-medium">
          Sign up
        </button>
      </p>
    </form>
  );
}
