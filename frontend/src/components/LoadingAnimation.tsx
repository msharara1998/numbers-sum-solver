import { Loader2 } from 'lucide-react';

interface LoadingAnimationProps {
  message: string;
  submessage?: string;
}

function LoadingAnimation({ message, submessage }: LoadingAnimationProps) {
  return (
    <div className="bg-white rounded-2xl shadow-xl p-12">
      <div className="flex flex-col items-center space-y-6">
        <div className="relative">
          <div className="absolute inset-0 bg-blue-500 rounded-full opacity-20 animate-ping"></div>
          <div className="relative bg-blue-100 p-6 rounded-full">
            <Loader2 className="w-16 h-16 text-blue-600 animate-spin" />
          </div>
        </div>

        <div className="text-center space-y-2">
          <h3 className="text-2xl font-semibold text-slate-800">{message}</h3>
          {submessage && (
            <p className="text-slate-600">{submessage}</p>
          )}
        </div>

        <div className="flex space-x-2">
          <div className="w-3 h-3 bg-blue-500 rounded-full animate-bounce"></div>
          <div className="w-3 h-3 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
          <div className="w-3 h-3 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
        </div>
      </div>
    </div>
  );
}

export default LoadingAnimation;
