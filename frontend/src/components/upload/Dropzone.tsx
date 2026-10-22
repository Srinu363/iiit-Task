/** Drag-and-drop file upload with preview and client-side validation — IQ Detect SaaS Dashboard. */
import { useCallback, useState, useRef } from "react";
import { Button } from "../ui";

const ALLOWED = [".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff"];
const MAX_MB = 20;

interface DropzoneProps {
  onFileSelect: (file: File) => void;
  disabled?: boolean;
}

export default function Dropzone({ onFileSelect, disabled }: DropzoneProps) {
  const [dragOver, setDragOver] = useState(false);
  const [preview, setPreview] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const validate = (file: File): string | null => {
    const ext = "." + file.name.split(".").pop()?.toLowerCase();
    if (!ALLOWED.includes(ext)) return `Unsupported format: ${ext}. Please upload a standard image.`;
    if (file.size > MAX_MB * 1024 * 1024) return `File too large (${(file.size / 1024 / 1024).toFixed(1)}MB). Maximum allowed is ${MAX_MB}MB.`;
    return null;
  };

  const handleFile = useCallback((file: File) => {
    const err = validate(file);
    if (err) { setError(err); return; }
    setError(null);
    setSelectedFile(file);

    const reader = new FileReader();
    reader.onload = (e) => setPreview(e.target?.result as string);
    reader.readAsDataURL(file);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  }, [handleFile]);

  const handleSubmit = () => {
    if (selectedFile) onFileSelect(selectedFile);
  };

  const reset = () => {
    setPreview(null);
    setSelectedFile(null);
    setError(null);
    if (inputRef.current) inputRef.current.value = "";
  };

  return (
    <div className="animate-fade-in">
      {!preview ? (
        <div
          onDrop={handleDrop}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onClick={() => inputRef.current?.click()}
          className={`group relative cursor-pointer rounded-2xl border-2 border-dashed p-10 sm:p-14 text-center transition-all duration-200 ${
            dragOver
              ? "border-[#5145FF] bg-[#EEF0FF]/70 scale-[1.008] shadow-lg shadow-[#5145FF]/5 ring-4 ring-[#5145FF]/10"
              : "border-[#E8EDF5] bg-white hover:border-[#5145FF]/40 hover:bg-[#F7F9FC] shadow-card hover:shadow-card-hover"
          }`}
          role="button"
          tabIndex={0}
          aria-label="Upload image"
          onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") inputRef.current?.click(); }}
        >
          <input
            ref={inputRef}
            type="file"
            accept={ALLOWED.join(",")}
            className="hidden"
            onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
            disabled={disabled}
          />
          <div className="mb-5 flex justify-center">
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-[#EEF0FF] text-[#5145FF] border border-[#D7DCFF] shadow-xs transition-transform duration-200 group-hover:scale-105 group-hover:bg-[#E5E8FF]">
              <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.75}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
              </svg>
            </div>
          </div>
          <p className="text-lg font-bold text-[#111827]">
            Drop your image here, or <span className="text-[#5145FF] underline decoration-[#5145FF]/30 underline-offset-4 font-extrabold">browse file</span>
          </p>
          <p className="mt-2 text-sm text-slate-500">
            Automated quality assessment for blur, noise, exposure, and defect levels
          </p>
          <div className="mt-6 flex flex-wrap justify-center gap-1.5 text-xs text-slate-400">
            {["JPG", "PNG", "WebP", "TIFF", "BMP"].map((fmt) => (
              <span key={fmt} className="rounded-md bg-[#F7F9FC] px-2 py-0.5 font-semibold text-slate-600 border border-[#E8EDF5]">
                {fmt}
              </span>
            ))}
            <span className="rounded-md bg-white px-2 py-0.5 text-slate-400 border border-slate-100 font-mono">
              Max {MAX_MB}MB
            </span>
          </div>
        </div>
      ) : (
        <div className="dashboard-card p-6 sm:p-7">
          <div className="flex flex-col items-center gap-6 sm:flex-row">
            <div className="relative shrink-0 overflow-hidden rounded-xl border border-[#E8EDF5] bg-[#F7F9FC] p-1.5 shadow-xs">
              <img
                src={preview}
                alt="Upload preview"
                className="h-44 w-auto max-w-xs object-contain rounded-lg"
              />
            </div>
            <div className="flex flex-1 flex-col justify-between gap-3 text-center sm:text-left">
              <div>
                <span className="inline-block rounded-md bg-[#EEF0FF] text-[#5145FF] font-bold px-2 py-0.5 text-xs border border-[#D7DCFF] mb-1.5">
                  Ready to Evaluate
                </span>
                <p className="font-bold text-[#111827] text-base break-all">{selectedFile?.name}</p>
                <p className="text-slate-500 text-xs font-mono mt-0.5">
                  {((selectedFile?.size || 0) / 1024).toFixed(1)} KB • {selectedFile?.type || "image"}
                </p>
              </div>
              <div className="flex flex-wrap items-center justify-center sm:justify-start gap-2.5 pt-2">
                <Button onClick={handleSubmit} disabled={disabled} variant="primary">
                  {disabled ? (
                    <>
                      <span className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      Analyzing…
                    </>
                  ) : (
                    <>
                      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
                      </svg>
                      Analyze Image Quality
                    </>
                  )}
                </Button>
                <Button variant="secondary" onClick={reset} disabled={disabled}>
                  Choose Different Image
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
      {error && (
        <div className="mt-3 rounded-xl border border-[#FECACA] bg-[#FEF2F2] px-4 py-2.5 text-sm text-[#991B1B] flex items-center gap-2">
          <svg className="h-4 w-4 shrink-0 text-[#EF4444]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          {error}
        </div>
      )}
    </div>
  );
}
