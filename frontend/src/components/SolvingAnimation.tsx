import { GridCell } from '../App';

interface SolvingAnimationProps {
  cells: GridCell[][];
}

function SolvingAnimation({ cells }: SolvingAnimationProps) {
  if (!cells || cells.length === 0) return null;

  const gridSize = cells.length;
  const cellSize = gridSize <= 5 ? 'w-16 h-16' : gridSize <= 7 ? 'w-14 h-14' : 'w-12 h-12';
  const fontSize = gridSize <= 5 ? 'text-2xl' : gridSize <= 7 ? 'text-xl' : 'text-lg';

  return (
    <div className="bg-white rounded-2xl shadow-xl p-8">
      <h3 className="text-2xl font-semibold text-slate-800 text-center mb-6">
        Solution Progress
      </h3>

      <div className="flex justify-center">
        <div className="inline-block">
          {cells.map((row, rowIdx) => (
            <div key={`solving-row-${rowIdx}`} className="flex">
              {row.map((cell, colIdx) => (
                <div
                  key={`solving-cell-${rowIdx}-${colIdx}`}
                  className={`${cellSize} ${fontSize} border-2 flex items-center justify-center font-semibold transition-all duration-300 ${
                    cell.isFixed
                      ? 'bg-slate-200 text-slate-800 border-slate-400'
                      : cell.value !== null
                      ? 'bg-gradient-to-br from-green-50 to-emerald-50 text-green-700 border-green-400 scale-105'
                      : 'bg-white text-slate-400 border-slate-300'
                  }`}
                  style={{
                    animation: !cell.isFixed && cell.value !== null ? 'pulse 0.5s ease-in-out' : 'none',
                  }}
                >
                  {cell.value !== null ? cell.value : ''}
                </div>
              ))}
            </div>
          ))}
        </div>
      </div>

      <div className="mt-6 text-center">
        <div className="inline-flex items-center gap-2 px-4 py-2 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
          <span className="text-blue-700 font-medium text-sm">
            Solving in progress...
          </span>
        </div>
      </div>
    </div>
  );
}

export default SolvingAnimation;
