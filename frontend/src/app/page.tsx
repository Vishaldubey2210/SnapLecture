"use client";

import { ChangeEvent, useEffect, useState } from "react";
import { initAnalytics, trackEvent } from "@/lib/analytics";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api";
const INTERVALS = [2, 4, 5, 10];

const formatTime = (seconds: number) => {
  const mins = Math.floor(seconds / 60);
  const secs = Math.ceil(seconds % 60);
  return mins ? `${mins}m ${secs}s` : `${secs}s`;
};

const countFrames = (duration: number, interval: number) =>
  Math.max(1, Math.ceil(duration / interval));

// Realistic fast estimation with parallel segment streaming (~8-16 seconds)
const estimateTime = (duration: number, interval: number, isYouTube: boolean) => {
  const frames = countFrames(duration, interval);
  if (isYouTube) {
    return Math.min(22, Math.max(8, Math.ceil(frames * 0.006 + 6)));
  }
  return Math.max(12, Math.ceil(frames * 0.02 + 6));
};

export default function Home() {
  const [video, setVideo] = useState<File | null>(null);
  const [videoDuration, setVideoDuration] = useState<number | null>(null);
  const [youtubeUrl, setYoutubeUrl] = useState("");
  const [youtubeDuration, setYoutubeDuration] = useState<number | null>(null);
  const [interval, setIntervalValue] = useState(5);
  const [customInterval, setCustomInterval] = useState("");
  const [infoLoading, setInfoLoading] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [estimate, setEstimate] = useState(12);
  const [startedAt, setStartedAt] = useState<number | null>(null);
  const [elapsed, setElapsed] = useState(0);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    initAnalytics();
  }, []);

  useEffect(() => {
    if (!processing || !startedAt) return;
    const tick = () => setElapsed(Math.floor((Date.now() - startedAt) / 1000));
    tick();
    const timer = window.setInterval(tick, 1000);
    return () => window.clearInterval(timer);
  }, [processing, startedAt]);

  const errorMessage = async (response: Response) => {
    try {
      const body = await response.json();
      return (
        body?.error?.message ||
        body?.detail ||
        "Something went wrong while generating the PDF."
      );
    } catch {
      return "Something went wrong while generating the PDF.";
    }
  };

  const start = (seconds: number) => {
    setProcessing(true);
    setEstimate(seconds);
    setStartedAt(Date.now());
    setElapsed(0);
    setError("");
    setSuccess("");
  };

  const finish = () => {
    setProcessing(false);
    setStartedAt(null);
  };

  const download = async (response: Response, name: string) => {
    const url = URL.createObjectURL(await response.blob());
    const link = document.createElement("a");
    link.href = url;
    link.download = name;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  };

  const loadYoutubeInfo = async () => {
    if (!youtubeUrl.trim()) return null;
    setInfoLoading(true);
    try {
      const form = new FormData();
      form.append("youtube_url", youtubeUrl.trim());
      const response = await fetch(`${API_URL}/pdf/youtube-info`, {
        method: "POST",
        body: form,
      });
      if (!response.ok) throw new Error(await errorMessage(response));
      const duration = Number((await response.json()).duration_seconds);
      if (!Number.isFinite(duration) || duration <= 0) {
        throw new Error("Unable to read this video's duration.");
      }
      setYoutubeDuration(duration);
      return duration;
    } catch (err) {
      setYoutubeDuration(null);
      setError(
        err instanceof Error ? err.message : "Unable to read this YouTube video."
      );
      return null;
    } finally {
      setInfoLoading(false);
    }
  };

  const handleVideoChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    setError("");
    setSuccess("");
    setVideoDuration(null);
    if (!file) {
      setVideo(null);
      return;
    }
    const allowed = [
      "video/mp4",
      "video/quicktime",
      "video/webm",
      "video/x-msvideo",
      "video/x-matroska",
    ];
    if (file.type && !allowed.includes(file.type)) {
      setError("Please select a supported video file.");
      setVideo(null);
      return;
    }
    setVideo(file);
    const preview = document.createElement("video");
    preview.preload = "metadata";
    preview.src = URL.createObjectURL(file);
    preview.onloadedmetadata = () => {
      setVideoDuration(preview.duration);
      URL.revokeObjectURL(preview.src);
    };
    preview.onerror = () => URL.revokeObjectURL(preview.src);
  };

  const generateUpload = async () => {
    if (!video) {
      setError("Please select a video first.");
      return;
    }
    start(videoDuration ? estimateTime(videoDuration, interval, false) : 20);
    try {
      const form = new FormData();
      form.append("video", video);
      form.append("interval_seconds", String(interval));
      const response = await fetch(`${API_URL}/pdf/generate`, {
        method: "POST",
        body: form,
      });
      if (!response.ok) throw new Error(await errorMessage(response));
      await download(response, "SnapLecture.pdf");
      trackEvent("pdf_generation_completed", { interval_seconds: interval });
      setSuccess("PDF generated and downloaded successfully.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to generate PDF.");
    } finally {
      finish();
    }
  };

  const generateYoutube = async () => {
    if (!youtubeUrl.trim()) {
      setError("Please enter a YouTube video link first.");
      return;
    }
    const duration = youtubeDuration || (await loadYoutubeInfo());
    if (!duration) return;
    start(estimateTime(duration, interval, true));
    try {
      const form = new FormData();
      form.append("youtube_url", youtubeUrl.trim());
      form.append("interval_seconds", String(interval));
      const response = await fetch(`${API_URL}/pdf/generate-youtube`, {
        method: "POST",
        body: form,
      });
      if (!response.ok) throw new Error(await errorMessage(response));
      await download(response, "SnapLecture-YouTube.pdf");
      trackEvent("youtube_pdf_generation_completed", {
        interval_seconds: interval,
      });
      setSuccess("YouTube PDF generated and downloaded successfully.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to generate PDF.");
    } finally {
      finish();
    }
  };

  const duration = youtubeDuration || videoDuration;
  const frames = duration ? countFrames(duration, interval) : null;
  const predicted = duration
    ? estimateTime(duration, interval, Boolean(youtubeDuration))
    : null;

  const remainingSeconds = Math.max(1, estimate - elapsed);
  const progress = estimate
    ? Math.min(96, Math.max(5, Math.round((elapsed / estimate) * 100)))
    : 10;

  // Processing stage messages based on progress
  let stageMessage = "⚡ Connecting to video stream & spawning parallel segment workers...";
  if (progress > 25 && progress <= 75) {
    stageMessage = `🚀 Parallel workers extracting ${frames || ""} frames across segments...`;
  } else if (progress > 75) {
    stageMessage = "📑 Lossless img2pdf engine assembling your study PDF...";
  }

  return (
    <main className="min-h-screen bg-[#070b14] text-white">
      <nav className="border-b border-white/10">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-500 font-bold shadow-lg shadow-indigo-500/30">
              S
            </div>
            <span className="text-xl font-semibold tracking-tight">SnapLecture</span>
          </div>
          <div className="rounded-full border border-indigo-400/30 bg-indigo-400/10 px-4 py-1.5 text-xs font-medium text-indigo-300">
            ⚡ Ultra-Fast Stream Seeking
          </div>
        </div>
      </nav>

      <section className="mx-auto max-w-5xl px-6 pb-24 pt-16 text-center">
        <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-indigo-400/20 bg-indigo-400/10 px-4 py-1.5 text-sm font-medium text-indigo-300">
          <span>🎬 Video</span>
          <span>→</span>
          <span>⚡ Parallel Seeking</span>
          <span>→</span>
          <span>📄 Study PDF</span>
        </div>

        <h1 className="mx-auto max-w-4xl text-5xl font-extrabold tracking-tight sm:text-7xl">
          Turn your lectures into
          <span className="block bg-gradient-to-r from-indigo-400 via-purple-300 to-cyan-300 bg-clip-text text-transparent">
            study-ready PDFs.
          </span>
        </h1>

        <p className="mx-auto mt-6 max-w-2xl text-lg leading-8 text-slate-400">
          Paste any YouTube link or upload a video. Our dynamic parallel stream engine extracts
          crisp screenshots and builds your PDF in seconds.
        </p>

        <div className="mx-auto mt-12 max-w-2xl rounded-3xl border border-white/10 bg-white/[0.03] p-6 text-left shadow-2xl shadow-black/40 backdrop-blur-xl">
          <label
            htmlFor="youtube-url"
            className="mb-2 block text-sm font-medium text-slate-200"
          >
            YouTube Video Link
          </label>
          <input
            id="youtube-url"
            type="url"
            value={youtubeUrl}
            onChange={(event) => {
              setYoutubeUrl(event.target.value);
              setYoutubeDuration(null);
              setError("");
              setSuccess("");
            }}
            onBlur={() => void loadYoutubeInfo()}
            placeholder="https://www.youtube.com/watch?v=..."
            className="w-full rounded-xl border border-white/10 bg-black/30 px-4 py-3.5 text-sm text-white outline-none placeholder:text-slate-600 transition focus:border-indigo-400 focus:ring-1 focus:ring-indigo-400"
          />

          {infoLoading && (
            <p className="mt-2 flex items-center gap-2 text-xs text-indigo-300">
              <span className="inline-block h-2 w-2 animate-ping rounded-full bg-indigo-400" />
              Reading YouTube metadata & stream info…
            </p>
          )}

          <div className="mt-6">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm font-medium text-slate-200">Screenshot Interval</p>
              <span className="text-xs text-slate-400">Capture 1 screenshot every</span>
            </div>
            <div className="grid grid-cols-4 gap-2">
              {INTERVALS.map((value) => (
                <button
                  key={value}
                  type="button"
                  onClick={() => {
                    setIntervalValue(value);
                    setCustomInterval("");
                  }}
                  className={`rounded-xl border px-3 py-3 text-sm font-medium transition ${
                    interval === value && !customInterval
                      ? "border-indigo-400 bg-indigo-500 text-white shadow-lg shadow-indigo-500/20"
                      : "border-white/10 bg-white/[0.03] text-slate-400 hover:border-white/20 hover:text-white"
                  }`}
                >
                  Every {value}s
                </button>
              ))}
            </div>
            <div className="mt-3 flex items-center gap-3">
              <label htmlFor="custom-interval" className="text-sm text-slate-400">
                Custom Interval:
              </label>
              <input
                id="custom-interval"
                type="number"
                min="1"
                max="300"
                value={customInterval}
                onChange={(event) => {
                  setCustomInterval(event.target.value);
                  const value = Number(event.target.value);
                  if (Number.isInteger(value) && value >= 1 && value <= 300) {
                    setIntervalValue(value);
                  }
                }}
                placeholder="Seconds"
                className="w-28 rounded-lg border border-white/10 bg-black/30 px-3 py-2 text-sm text-white outline-none placeholder:text-slate-600 focus:border-indigo-400"
              />
              <span className="text-xs text-slate-500">(1–300s range)</span>
            </div>
          </div>

          {duration && frames && predicted && (
            <div className="mt-5 flex items-center justify-between rounded-xl border border-indigo-400/20 bg-indigo-400/10 px-4 py-3 text-xs text-indigo-200">
              <span>⏱️ Length: {formatTime(duration)}</span>
              <span>📸 ~{frames} slides</span>
              <span className="font-semibold text-cyan-300">
                ⚡ Ready in ~{predicted}s
              </span>
            </div>
          )}

          <button
            type="button"
            onClick={generateYoutube}
            disabled={processing || infoLoading || !youtubeUrl.trim()}
            className="mt-6 w-full rounded-xl bg-gradient-to-r from-red-500 to-rose-600 px-6 py-4 font-semibold text-white shadow-lg shadow-red-500/20 transition hover:from-red-600 hover:to-rose-700 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {processing ? "⚡ Processing Stream…" : "🚀 Generate PDF from YouTube"}
          </button>

          <div className="my-7 flex items-center gap-4">
            <div className="h-px flex-1 bg-white/10" />
            <span className="text-xs font-medium uppercase tracking-wider text-slate-500">
              Or Upload Local File
            </span>
            <div className="h-px flex-1 bg-white/10" />
          </div>

          <label
            htmlFor="video"
            className="flex cursor-pointer flex-col items-center justify-center rounded-2xl border border-dashed border-white/20 bg-black/20 px-6 py-8 text-center transition hover:border-indigo-400/50 hover:bg-indigo-400/5"
          >
            <div className="mb-2 text-3xl">📹</div>
            <p className="font-medium text-slate-200">
              {video ? video.name : "Select video file"}
            </p>
            <p className="mt-1 text-xs text-slate-500">MP4, MOV, AVI, MKV, or WEBM</p>
            <input
              id="video"
              type="file"
              accept="video/*"
              onChange={handleVideoChange}
              className="hidden"
            />
          </label>

          <button
            type="button"
            onClick={generateUpload}
            disabled={processing || !video}
            className="mt-4 w-full rounded-xl bg-indigo-500 px-6 py-3.5 font-semibold text-white shadow-lg shadow-indigo-500/20 transition hover:bg-indigo-400 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {processing ? "⚡ Processing Video…" : "📄 Generate PDF from File"}
          </button>

          {/* Real-time Dynamic Countdown & Progress Widget */}
          {processing && (
            <div
              className="mt-6 rounded-2xl border border-indigo-400/30 bg-gradient-to-b from-indigo-950/40 to-slate-900/60 p-5 shadow-xl shadow-indigo-500/10 backdrop-blur-md"
              aria-live="polite"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="inline-block h-3 w-3 animate-ping rounded-full bg-cyan-400" />
                  <span className="font-semibold text-cyan-300">
                    Estimated ~{remainingSeconds}s remaining
                  </span>
                </div>
                <span className="text-xs font-medium text-slate-400">
                  Elapsed: {elapsed}s
                </span>
              </div>

              {/* Animated Progress Bar */}
              <div className="mt-3.5 h-2.5 overflow-hidden rounded-full bg-black/40 p-0.5">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-indigo-500 via-cyan-400 to-emerald-400 transition-all duration-700 ease-out"
                  style={{ width: `${progress}%` }}
                />
              </div>

              <div className="mt-3 flex items-center justify-between text-xs text-slate-300">
                <span className="truncate pr-2">{stageMessage}</span>
                <span className="font-semibold text-indigo-300">{progress}%</span>
              </div>
            </div>
          )}

          {error && (
            <div className="mt-6 rounded-xl border border-red-400/20 bg-red-400/10 px-4 py-3 text-sm text-red-300">
              ⚠️ {error}
            </div>
          )}

          {success && (
            <div className="mt-6 rounded-xl border border-emerald-400/20 bg-emerald-400/10 px-4 py-3 text-sm text-emerald-300">
              ✅ {success}
            </div>
          )}

          <p className="mt-5 text-center text-xs text-slate-500">
            🔒 100% Privacy-First: All processing is ephemeral. Video files and PDFs are never permanently stored.
          </p>
        </div>
      </section>

      <footer className="border-t border-white/10 px-6 py-8 text-center text-sm text-slate-500">
        SnapLecture · Built for blazing-fast visual note-taking.
      </footer>
    </main>
  );
}
