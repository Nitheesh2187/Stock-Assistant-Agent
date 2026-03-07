import { useNavigate } from 'react-router-dom';
import { TrendingUp, ArrowRight } from 'lucide-react';

export default function LandingPage() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-primary-600 px-6">
      <div className="max-w-lg text-center">
        <div className="flex items-center justify-center gap-3 mb-6">
          <TrendingUp className="h-10 w-10 text-white" />
          <span className="text-4xl font-bold text-white">StockAssist</span>
        </div>

        <p className="text-lg text-primary-100 mb-10 leading-relaxed">
          AI-powered stock market assistant. Get real-time quotes, smart analysis,
          and AI-driven insights — all in one dashboard.
        </p>

        <button
          onClick={() => navigate('/dashboard')}
          className="inline-flex items-center gap-2 px-8 py-3 rounded-lg bg-white text-primary-700 text-lg font-semibold hover:bg-primary-50 transition-colors shadow-lg hover:shadow-xl"
        >
          Try it out
          <ArrowRight className="h-5 w-5" />
        </button>
      </div>
    </div>
  );
}
