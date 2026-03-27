"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Loader2, Send, ArrowLeft, Youtube, MessageSquare, TrendingUp, Users, FileText } from "lucide-react";

const API_URL = "http://localhost:8000";

interface AnalysisData {
  sentiment: {
    label: string;
    score: number;
    vibe_score: number;
    likeness_score: number;
    toxicity_level: string;
  };
  top_comments: string[];
  channel_insights: {
    subscriber_count: number;
    avg_views: number;
    engagement_rate: number;
    channel_name: string;
    channel_id: string;
  };
  agent_summaries: {
    data_agent: string;
    sentiment_agent: string;
    topic_agent: string;
    report_agent: string;
  };
  video_metadata: {
    title: string;
    views: number;
    likes: number;
    duration: string;
    thumbnail: string;
    published_at: string;
    video_id: string;
    url: string;
  };
}

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export default function Dashboard() {
  const router = useRouter();
  const [data, setData] = useState<AnalysisData | null>(null);
  const [youtubeUrl, setYoutubeUrl] = useState("");
  const [chatInput, setChatInput] = useState("");
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatLoading, setChatLoading] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const stored = sessionStorage.getItem("analysisData");
    const url = sessionStorage.getItem("youtubeUrl");
    if (stored) {
      setData(JSON.parse(stored));
    } else {
      router.push("/");
    }
    if (url) {
      setYoutubeUrl(url);
    }
  }, [router]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatMessages]);

  const handleSendMessage = async () => {
    if (!chatInput.trim() || !data) return;

    const userMsg: ChatMessage = { role: "user", content: chatInput };
    setChatMessages((prev) => [...prev, userMsg]);
    setChatInput("");
    setChatLoading(true);

    try {
      const response = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: chatInput }),
      });

      if (!response.ok) throw new Error("Chat failed");

      const result = await response.json();
      const assistantMsg: ChatMessage = { role: "assistant", content: result.response };
      setChatMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      const errorMsg: ChatMessage = {
        role: "assistant",
        content: "Sorry, I couldn't process that request. Please try again.",
      };
      setChatMessages((prev) => [...prev, errorMsg]);
    } finally {
      setChatLoading(false);
    }
  };

  if (!data) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  const sentimentColor =
    data.sentiment.label === "positive"
      ? "text-green-500"
      : data.sentiment.label === "negative"
      ? "text-red-500"
      : "text-yellow-500";

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" onClick={() => router.push("/")}>
              <ArrowLeft className="h-5 w-5" />
            </Button>
            <div>
              <h1 className="text-xl font-bold">Analysis Dashboard</h1>
              <p className="text-sm text-muted-foreground truncate max-w-md">
                {data.video_metadata.title}
              </p>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto p-6 pb-32">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Sentiment Card */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-lg flex items-center gap-2">
                <TrendingUp className="h-5 w-5" />
                Sentiment
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="text-center">
                  <p className={`text-4xl font-bold capitalize ${sentimentColor}`}>
                    {data.sentiment.label}
                  </p>
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Score</span>
                    <span>{(data.sentiment.score * 100).toFixed(0)}%</span>
                  </div>
                  <Progress value={Math.abs(data.sentiment.score) * 100} />
                </div>
                <div className="grid grid-cols-2 gap-4 pt-2">
                  <div className="text-center">
                    <p className="text-2xl font-bold">{data.sentiment.vibe_score}/10</p>
                    <p className="text-xs text-muted-foreground">Vibe Score</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold">{data.sentiment.likeness_score}/10</p>
                    <p className="text-xs text-muted-foreground">Likeness</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Video Metadata Card */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-lg flex items-center gap-2">
                <Youtube className="h-5 w-5" />
                Video Stats
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {data.video_metadata.thumbnail && (
                  <img
                    src={data.video_metadata.thumbnail}
                    alt={data.video_metadata.title}
                    className="w-full h-32 object-cover rounded-md"
                  />
                )}
                <div className="grid grid-cols-2 gap-4">
                  <div className="text-center">
                    <p className="text-2xl font-bold">{data.video_metadata.views.toLocaleString()}</p>
                    <p className="text-xs text-muted-foreground">Views</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold">{data.video_metadata.likes.toLocaleString()}</p>
                    <p className="text-xs text-muted-foreground">Likes</p>
                  </div>
                </div>
                <a
                  href={data.video_metadata.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-primary hover:underline block text-center"
                >
                  Open on YouTube →
                </a>
              </div>
            </CardContent>
          </Card>

          {/* Channel Insights Card */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-lg flex items-center gap-2">
                <Users className="h-5 w-5" />
                Channel
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <p className="font-semibold text-center">{data.channel_insights.channel_name}</p>
                <div className="grid grid-cols-1 gap-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-muted-foreground">Avg Views</span>
                    <span className="font-medium">{data.channel_insights.avg_views.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-muted-foreground">Toxicity Level</span>
                    <span className="font-medium capitalize">{data.sentiment.toxicity_level}</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Top Comments Card */}
          <Card className="lg:col-span-2">
            <CardHeader className="pb-2">
              <CardTitle className="text-lg flex items-center gap-2">
                <MessageSquare className="h-5 w-5" />
                Top Comments
              </CardTitle>
              <CardDescription>Most liked comments from viewers</CardDescription>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-48">
                <div className="space-y-3">
                  {data.top_comments.map((comment, i) => (
                    <div key={i} className="p-3 bg-secondary/50 rounded-md">
                      <p className="text-sm">{comment}</p>
                    </div>
                  ))}
                  {data.top_comments.length === 0 && (
                    <p className="text-sm text-muted-foreground text-center py-4">
                      No comments available
                    </p>
                  )}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>

          {/* Agent Summaries */}
          <Card className="lg:col-span-3">
            <CardHeader className="pb-2">
              <CardTitle className="text-lg flex items-center gap-2">
                <FileText className="h-5 w-5" />
                Agent Insights
              </CardTitle>
              <CardDescription>AI-generated analysis from each agent</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="p-4 bg-secondary/50 rounded-lg">
                  <h4 className="font-semibold mb-2 text-sm">Data Agent</h4>
                  <p className="text-sm text-muted-foreground">{data.agent_summaries.data_agent}</p>
                </div>
                <div className="p-4 bg-secondary/50 rounded-lg">
                  <h4 className="font-semibold mb-2 text-sm">Sentiment Agent</h4>
                  <p className="text-sm text-muted-foreground">{data.agent_summaries.sentiment_agent}</p>
                </div>
                <div className="p-4 bg-secondary/50 rounded-lg">
                  <h4 className="font-semibold mb-2 text-sm">Topic Agent</h4>
                  <p className="text-sm text-muted-foreground">{data.agent_summaries.topic_agent}</p>
                </div>
                <div className="p-4 bg-secondary/50 rounded-lg">
                  <h4 className="font-semibold mb-2 text-sm">Report Agent</h4>
                  <p className="text-sm text-muted-foreground line-clamp-4">{data.agent_summaries.report_agent}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </main>

      {/* Chat Interface */}
      <div className="fixed bottom-0 left-0 right-0 bg-background border-t border-border p-4">
        <div className="max-w-7xl mx-auto">
          {/* Chat Messages */}
          {chatMessages.length > 0 && (
            <ScrollArea className="h-48 mb-4 bg-secondary/30 rounded-lg p-4">
              <div className="space-y-4">
                {chatMessages.map((msg, i) => (
                  <div
                    key={i}
                    className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                  >
                    <div
                      className={`max-w-[70%] p-3 rounded-lg ${
                        msg.role === "user"
                          ? "bg-primary text-primary-foreground"
                          : "bg-secondary text-secondary-foreground"
                      }`}
                    >
                      <p className="text-sm">{msg.content}</p>
                    </div>
                  </div>
                ))}
                <div ref={chatEndRef} />
              </div>
            </ScrollArea>
          )}

          {/* Chat Input */}
          <div className="flex gap-2">
            <Input
              placeholder="Ask about your audience..."
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSendMessage()}
              className="flex-1"
            />
            <Button onClick={handleSendMessage} disabled={chatLoading}>
              {chatLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
            </Button>
          </div>
          <p className="text-xs text-muted-foreground mt-2 text-center">
            RAG-powered chat using your video comments
          </p>
        </div>
      </div>
    </div>
  );
}
