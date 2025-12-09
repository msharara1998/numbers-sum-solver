import { useRef, useState } from 'react';
import { Upload, Camera, Image as ImageIcon } from 'lucide-react';

interface ImageUploadProps {
  onImageUpload: (file: File) => void;
}

function ImageUpload({ onImageUpload }: ImageUploadProps) {
  const [dragActive, setDragActive] = useState(false);
  const [preview, setPreview] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const cameraInputRef = useRef<HTMLInputElement>(null);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleFile = (file: File) => {
    if (!file.type.startsWith('image/')) {
      alert('Please upload an image file');
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      setPreview(e.target?.result as string);
    };
    reader.readAsDataURL(file);
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  const handleSubmit = () => {
    const input = fileInputRef.current || cameraInputRef.current;
    if (input?.files && input.files[0]) {
      onImageUpload(input.files[0]);
    }
  };

  return (
    <div className="bg-white rounded-2xl shadow-xl p-8 md:p-12">
      {!preview ? (
        <div
          className={`border-3 border-dashed rounded-xl p-12 text-center transition-all ${
            dragActive
              ? 'border-blue-500 bg-blue-50'
              : 'border-slate-300 bg-slate-50 hover:border-slate-400 hover:bg-slate-100'
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <div className="flex flex-col items-center space-y-6">
            <div className="bg-blue-100 p-6 rounded-full">
              <ImageIcon className="w-16 h-16 text-blue-600" />
            </div>

            <div>
              <h3 className="text-2xl font-semibold text-slate-800 mb-2">
                Upload Puzzle Image
              </h3>
              <p className="text-slate-600 mb-6">
                Drag and drop your puzzle image here, or choose an option below
              </p>
            </div>

            <div className="flex flex-col sm:flex-row gap-4 w-full max-w-md">
              <button
                onClick={() => fileInputRef.current?.click()}
                className="flex-1 flex items-center justify-center gap-3 px-6 py-4 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors shadow-md hover:shadow-lg"
              >
                <Upload className="w-5 h-5" />
                Choose File
              </button>

              <button
                onClick={() => cameraInputRef.current?.click()}
                className="flex-1 flex items-center justify-center gap-3 px-6 py-4 bg-slate-700 text-white font-semibold rounded-lg hover:bg-slate-800 transition-colors shadow-md hover:shadow-lg"
              >
                <Camera className="w-5 h-5" />
                Take Photo
              </button>
            </div>

            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={handleFileInput}
              className="hidden"
            />

            <input
              ref={cameraInputRef}
              type="file"
              accept="image/*"
              capture="environment"
              onChange={handleFileInput}
              className="hidden"
            />

            <p className="text-sm text-slate-500 mt-4">
              Supported formats: JPG, PNG, JPEG
            </p>
          </div>
        </div>
      ) : (
        <div className="space-y-6">
          <h3 className="text-2xl font-semibold text-slate-800 text-center">
            Preview
          </h3>

          <div className="relative rounded-xl overflow-hidden bg-slate-100 border-2 border-slate-200">
            <img
              src={preview}
              alt="Preview"
              className="w-full h-auto max-h-96 object-contain mx-auto"
            />
          </div>

          <div className="flex gap-4 justify-center">
            <button
              onClick={handleSubmit}
              className="px-8 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors shadow-lg hover:shadow-xl"
            >
              Process Image
            </button>

            <button
              onClick={() => {
                setPreview(null);
                if (fileInputRef.current) fileInputRef.current.value = '';
                if (cameraInputRef.current) cameraInputRef.current.value = '';
              }}
              className="px-8 py-3 bg-slate-300 text-slate-700 font-semibold rounded-lg hover:bg-slate-400 transition-colors"
            >
              Choose Different
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default ImageUpload;
