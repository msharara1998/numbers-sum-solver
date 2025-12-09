import { PuzzleGrid } from '../App';

interface GridDisplayProps {
  grid: PuzzleGrid;
  title?: string;
}

function GridDisplay({ grid, title }: GridDisplayProps) {
  const rowConstraints = grid.constraints.filter((c) => c.type === 'row');
  const colConstraints = grid.constraints.filter((c) => c.type === 'column');

  const gridSize = grid.cells.length;
  const cellSize = gridSize <= 5 ? 'w-16 h-16' : gridSize <= 7 ? 'w-14 h-14' : 'w-12 h-12';
  const fontSize = gridSize <= 5 ? 'text-2xl' : gridSize <= 7 ? 'text-xl' : 'text-lg';

  return (
    <div className="bg-white rounded-2xl shadow-xl p-8">
      {title && (
        <h3 className="text-2xl font-semibold text-slate-800 text-center mb-6">
          {title}
        </h3>
      )}

      <div className="flex justify-center">
        <div className="inline-block">
          <div className="flex">
            <div className={`${cellSize}`}></div>

            {colConstraints.map((constraint, idx) => (
              <div
                key={`col-${idx}`}
                className={`${cellSize} flex items-center justify-center font-semibold text-blue-600`}
              >
                {constraint.sum}
              </div>
            ))}
          </div>

          {grid.cells.map((row, rowIdx) => (
            <div key={`row-${rowIdx}`} className="flex">
              <div
                className={`${cellSize} flex items-center justify-center font-semibold text-blue-600`}
              >
                {rowConstraints.find((c) => c.index === rowIdx)?.sum || ''}
              </div>

              {row.map((cell, colIdx) => (
                <div
                  key={`cell-${rowIdx}-${colIdx}`}
                  className={`${cellSize} ${fontSize} border-2 flex items-center justify-center font-semibold transition-all ${cell.isSelected === true
                    ? 'bg-white text-slate-800 border-blue-500 rounded-full'
                    : cell.isSelected === false
                      ? 'bg-white text-slate-400 border-slate-300'
                      : cell.value !== null
                        ? 'bg-green-50 text-green-700 border-green-400'
                        : 'bg-white text-slate-400 border-slate-300'
                    }`}
                >
                  {cell.isSelected === false ? '' : (cell.value !== null ? cell.value : '')}
                </div>
              ))}
            </div>
          ))}
        </div>
      </div>

      <div className="mt-6 flex justify-center gap-8 text-sm">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-slate-200 border-2 border-slate-400 rounded"></div>
          <span className="text-slate-600">Fixed values</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-green-50 border-2 border-green-400 rounded"></div>
          <span className="text-slate-600">Solved values</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-white border-2 border-slate-300 rounded"></div>
          <span className="text-slate-600">Empty cells</span>
        </div>
      </div>
    </div>
  );
}

export default GridDisplay;
