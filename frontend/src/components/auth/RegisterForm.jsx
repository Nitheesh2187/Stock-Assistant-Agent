import { useState } from 'react';
import { useAuth } from '../../hooks/useAuth';
import Input from '../ui/Input';
import Button from '../ui/Button';
import Spinner from '../ui/Spinner';

export default function RegisterForm({ onSwitch }) {
  const { register } = useAuth();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await register(email, name, password);
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <h2 className="text-2xl font-bold text-surface-900 dark:text-surface-100">Create account</h2>
      <p className="text-sm text-surface-500 dark:text-surface-400">
        Get started with your stock assistant.
      </p>
      {error && (
        <div className="p-3 text-sm text-negative bg-red-50 dark:bg-red-900/20 rounded-lg">{error}</div>
      )}
      <Input
        label="Full name"
        type="text"
        value={name}
        onChange={(e) => setName(e.target.value)}
        placeholder="John Doe"
        required
      />
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
        placeholder="Min. 6 characters"
        minLength={6}
        required
      />
      <Button type="submit" className="w-full" disabled={loading}>
        {loading ? <Spinner size="sm" className="text-white" /> : 'Create account'}
      </Button>
      <p className="text-center text-sm text-surface-500 dark:text-surface-400">
        Already have an account?{' '}
        <button type="button" onClick={onSwitch} className="text-primary-600 hover:underline font-medium">
          Sign in
        </button>
      </p>
    </form>
  );
}
