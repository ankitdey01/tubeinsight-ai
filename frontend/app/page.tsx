"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Loader2 } from "lucide-react";

const API_URL = "http://localhost:8000";

export default function Home() {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const router = useRouter();

  const handleAnalyze = async () => {
    if (!url.trim()) {
      setError("Please enter a YouTube URL");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response = await fetch(`${API_URL}/analyze`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ youtube_url: url }),
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || "Analysis failed");
      }

      const data = await response.json();

      // Store data in sessionStorage for the dashboard
      sessionStorage.setItem("analysisData", JSON.stringify(data));
      sessionStorage.setItem("youtubeUrl", url);

      // Redirect to dashboard
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message || "Failed to analyze video. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24 bg-gradient-to-b from-background to-background/95">
      <div className="max-w-2xl w-full space-y-8 text-center">
        <div className="space-y-4">
          <h1 className="text-5xl font-bold tracking-tight bg-gradient-to-r from-primary to-primary/60 bg-clip-text text-transparent">
            TubeInsight AI
          </h1>
          <p className="text-xl text-muted-foreground">
            YouTube Creator Intelligence Platform
          </p>
        </div>

        <div className="space-y-4">
          <div className="flex flex-col gap-2">
            <Input
              type="url"
              placeholder="Enter YouTube video URL..."
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              className="h-12 text-lg"
              onKeyDown={(e) => e.key === "Enter" && handleAnalyze()}
            />
            {error && (
              <p className="text-sm text-destructive text-left">{error}</p>
            )}
          </div>

          <Button
            onClick={handleAnalyze}
            disabled={loading}
            className="w-full h-12 text-lg"
          >
            {loading ? (
              <>
                <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                Analyzing...
              </>
            ) : (
              "Analyze Video"
            )}
          </Button>
        </div>

        <p className="text-sm text-muted-foreground">
          Powered by LangGraph, ChromaDB, and AI
        </p>
      </div>
    </main>
  );
}
