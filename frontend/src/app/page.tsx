"use client";

import { ChangeEvent, useState } from "react";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  "http://127.0.0.1:8000/api";

const INTERVALS = [5, 10, 30];

export default function Home() {
  const [video, setVideo] = useState<File | null>(null);
  const [interval, setIntervalValue] = useState(5);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const handleVideoChange = (
    event: ChangeEvent<HTMLInputElement>,
  ) => {
    const file = event.target.files?.[0];

    setError("");
    setSuccess("");

    if (!file) {
      setVideo(null);
      return;
    }

    const allowedTypes = [
      "video/mp4",
      "video/quicktime",
      "video/webm",
      "video/x-msvideo",
      "video/x-matroska",
    ];

    if (
      file.type &&
      !allowedTypes.includes(file.type)
    ) {
      setError(
        "Please select a supported video file.",
      );
      setVideo(null);
      return;
    }

    setVideo(file);
  };

  const generatePDF = async () => {
    if (!video) {
      setError("Please select a video first.");
      return;
    }

    setProcessing(true);
    setError("");
    setSuccess("");

    try {
      const formData = new FormData();

      formData.append("video", video);
      formData.append(
        "interval_seconds",
        String(interval),
      );

      const response = await fetch(
        `${API_URL}/pdf/generate`,
        {
          method: "POST",
          body: formData,
        },
      );

      if (!response.ok) {
        let message =
          "Something went wrong while generating the PDF.";

        try {
          const data = await response.json();

          if (data?.detail) {
            message = data.detail;
          }
        } catch {
          // Ignore JSON parsing errors.
        }

        throw new Error(message);
      }

      const blob = await response.blob();

      const downloadUrl =
        window.URL.createObjectURL(blob);

      const anchor =
        document.createElement("a");

      anchor.href = downloadUrl;
      anchor.download = "SnapLecture.pdf";

      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();

      window.URL.revokeObjectURL(
        downloadUrl,
      );

      setSuccess(
        "PDF generated successfully.",
      );
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to generate PDF.",
      );
    } finally {
      setProcessing(false);
    }
  };

  return (
    <main className="min-h-screen bg-[#070b14] text-white">
      <nav className="border-b border-white/10">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-500 font-bold">
              S
            </div>

            <span className="text-xl font-semibold">
              SnapLecture
            </span>
          </div>

          <div className="rounded-full border border-orange-400/30 bg-orange-400/10 px-4 py-2 text-xs font-medium text-orange-300">
            🚧 Ongoing Project
          </div>
        </div>
      </nav>

      <section className="mx-auto max-w-5xl px-6 pb-24 pt-20 text-center">
        <div className="mb-6 inline-flex rounded-full border border-indigo-400/20 bg-indigo-400/10 px-4 py-2 text-sm text-indigo-300">
          Video → Frames → PDF
        </div>

        <h1 className="mx-auto max-w-4xl text-5xl font-bold tracking-tight sm:text-7xl">
          Turn your lectures into
          <span className="block text-indigo-400">
            study-ready PDFs.
          </span>
        </h1>

        <p className="mx-auto mt-6 max-w-2xl text-lg leading-8 text-slate-400">
          Upload an authorized video, choose a capture
          interval, and generate a PDF containing
          captured learning frames.
        </p>

        <div className="mx-auto mt-12 max-w-2xl rounded-3xl border border-white/10 bg-white/[0.03] p-6 text-left shadow-2xl shadow-black/20 backdrop-blur">
          <label
            htmlFor="video"
            className="mb-3 block text-sm font-medium text-slate-200"
          >
            Video file
          </label>

          <label
            htmlFor="video"
            className="flex cursor-pointer flex-col items-center justify-center rounded-2xl border border-dashed border-white/20 bg-black/20 px-6 py-12 text-center transition hover:border-indigo-400/50 hover:bg-indigo-400/5"
          >
            <div className="mb-4 text-4xl">
              📹
            </div>

            <p className="font-medium">
              {video
                ? video.name
                : "Choose a video"}
            </p>

            <p className="mt-2 text-sm text-slate-500">
              MP4, MOV, AVI, MKV or WEBM
            </p>

            <input
              id="video"
              type="file"
              accept="video/*"
              onChange={handleVideoChange}
              className="hidden"
            />
          </label>

          <div className="mt-7">
            <p className="mb-3 text-sm font-medium text-slate-200">
              Capture interval
            </p>

            <div className="grid grid-cols-3 gap-3">
              {INTERVALS.map((value) => (
                <button
                  key={value}
                  type="button"
                  onClick={() =>
                    setIntervalValue(value)
                  }
                  className={`rounded-xl border px-4 py-3 text-sm font-medium transition ${
                    interval === value
                      ? "border-indigo-400 bg-indigo-500 text-white"
                      : "border-white/10 bg-white/[0.03] text-slate-400 hover:border-white/20 hover:text-white"
                  }`}
                >
                  Every {value}s
                </button>
              ))}
            </div>
          </div>

          {error && (
            <div className="mt-6 rounded-xl border border-red-400/20 bg-red-400/10 px-4 py-3 text-sm text-red-300">
              {error}
            </div>
          )}

          {success && (
            <div className="mt-6 rounded-xl border border-emerald-400/20 bg-emerald-400/10 px-4 py-3 text-sm text-emerald-300">
              {success}
            </div>
          )}

          <button
            type="button"
            onClick={generatePDF}
            disabled={processing || !video}
            className="mt-7 w-full rounded-xl bg-indigo-500 px-6 py-4 font-semibold text-white transition hover:bg-indigo-400 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {processing
              ? "Generating PDF..."
              : "Generate PDF"}
          </button>

          <p className="mt-4 text-center text-xs text-slate-500">
            Processing is temporary. Generated documents
            are not intended to be permanently stored.
          </p>
        </div>
      </section>

      <footer className="border-t border-white/10 px-6 py-8 text-center text-sm text-slate-500">
        SnapLecture · Built for smarter visual learning.
      </footer>
    </main>
  );
}