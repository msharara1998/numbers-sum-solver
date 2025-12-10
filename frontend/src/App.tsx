import { useState } from 'react';
import ImageUpload from './components/ImageUpload';
import GridDisplay from './components/GridDisplay';
import LoadingAnimation from './components/LoadingAnimation';
import SolvingAnimation from './components/SolvingAnimation';

export type AppState = 'upload' | 'processing' | 'extracted' | 'solving' | 'solved';

export interface GridCell {
  value: number | null;
  isSelected: boolean | null;
  row: number;
  col: number;
}

export interface Constraint {
  type: 'row' | 'column';
  index: number;
  sum: number;
}

export interface PuzzleGrid {
  cells: GridCell[][];
  constraints: Constraint[];
}

function App() {
  const [state, setState] = useState<AppState>('upload');
  const [uploadedImage, setUploadedImage] = useState<string | null>(null);
  const [extractedGrid, setExtractedGrid] = useState<PuzzleGrid | null>(null);
  const [solvingProgress, setSolvingProgress] = useState<GridCell[][]>([]);

  const handleImageUpload = async (imageFile: File) => {
    const imageUrl = URL.createObjectURL(imageFile);
    setUploadedImage(imageUrl);
    setState('processing');

    try {
      const formData = new FormData();
      formData.append('image', imageFile);

      const response = await fetch('/api/process-image', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) throw new Error('Failed to process image');

      const data = await response.json();
      setExtractedGrid(data.grid);
      setState('extracted');
    } catch (error) {
      console.error('Error processing image:', error);
      setState('upload');
      alert('Failed to process image. Please try again.');
    }
  };

  const handleSolveGrid = async () => {
    if (!extractedGrid) return;

    setState('solving');

    try {
      const response = await fetch('/api/solve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(extractedGrid),
      });

      if (!response.ok) throw new Error('Failed to start solving');

      const data = await response.json();
      const solvingId = data.solvingId;

      const eventSource = new EventSource(`/api/solve-stream/${solvingId}`);

      eventSource.onmessage = (event) => {
        const update = JSON.parse(event.data);

        if (update.type === 'progress') {
          setSolvingProgress(update.cells);
        } else if (update.type === 'complete') {
          setSolvingProgress(update.cells);
          setState('solved');
          eventSource.close();
        } else if (update.type === 'error') {
          alert('Failed to solve puzzle: ' + update.message);
          setState('extracted');
          eventSource.close();
        }
      };

      eventSource.onerror = () => {
        eventSource.close();
        alert('Connection lost. Please try again.');
        setState('extracted');
      };
    } catch (error) {
      console.error('Error solving grid:', error);
      setState('extracted');
      alert('Failed to solve puzzle. Please try again.');
    }
  };

  const handleReset = () => {
    setState('upload');
    setUploadedImage(null);
    setExtractedGrid(null);
    setSolvingProgress([]);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      <div className="container mx-auto px-4 py-8">
        <header className="text-center mb-12">
          <h1 className="text-4xl md:text-5xl font-bold text-slate-800 mb-3">
            Numbers Sum Solver
          </h1>
          <p className="text-slate-600 text-lg">
            Upload a puzzle grid and watch it solve itself in real-time
          </p>
        </header>

        <main className="max-w-4xl mx-auto">
          {state === 'upload' && (
            <ImageUpload onImageUpload={handleImageUpload} />
          )}

          {state === 'processing' && (
            <LoadingAnimation
              message="Analyzing your puzzle..."
              submessage="Extracting grid structure and constraints"
            />
          )}

          {state === 'extracted' && extractedGrid && (
            <div className="space-y-6">
              <GridDisplay
                grid={extractedGrid}
                title="Extracted Grid"
              />
              <div className="flex gap-4 justify-center">
                <button
                  onClick={handleSolveGrid}
                  className="px-8 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors shadow-lg hover:shadow-xl"
                >
                  Solve Puzzle
                </button>
                <button
                  onClick={handleReset}
                  className="px-8 py-3 bg-slate-300 text-slate-700 font-semibold rounded-lg hover:bg-slate-400 transition-colors"
                >
                  Start Over
                </button>
              </div>
            </div>
          )}

          {state === 'solving' && (
            <div className="space-y-6">
              <LoadingAnimation
                message="Solving puzzle..."
                submessage="Computing optimal solution"
              />
              {solvingProgress.length > 0 && (
                <SolvingAnimation cells={solvingProgress} />
              )}
            </div>
          )}

          {state === 'solved' && (
            <div className="space-y-6">
              <div className="bg-green-50 border-2 border-green-500 rounded-lg p-4 text-center">
                <p className="text-green-800 font-semibold text-xl">
                  Puzzle Solved Successfully!
                </p>
              </div>
              <SolvingAnimation cells={solvingProgress} />
              <div className="flex justify-center">
                <button
                  onClick={handleReset}
                  className="px-8 py-3 bg-slate-700 text-white font-semibold rounded-lg hover:bg-slate-800 transition-colors shadow-lg"
                >
                  Solve Another Puzzle
                </button>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

export default App;
