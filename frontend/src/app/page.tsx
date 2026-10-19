
"use client";

import { FormEvent, useEffect, useRef, useState } from "react";

type Message = {
  role: "user" | "assistant";
  content: string;
};

const EXAMPLES = [
  "How much did I spend in January 2024?",
  "Show spending by category in January 2024.",
  "Calculate the return of Apex Gold Savings Fund between 2023-04-01 and 2025-03-01.",
  "Summarize my holdings and portfolio value.",
];

export default function Home() {
  const [question, setQuestion] = useState("");
  const [snapshot, setSnapshot] = useState("sample_a");
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content:
        "Hello! I'm Jemi, your Finance Research Assistant. Ask me about spending, transactions, fund returns, or investment holdings.",
    },
  ]);
  const [loading, setLoading] = useState(false);

  const messagesContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = messagesContainerRef.current;

    if (container) {
      container.scrollTo({
        top: container.scrollHeight,
        behavior: "smooth",
      });
    }
  }, [messages, loading]);

  async function sendQuestion(
    event?: FormEvent<HTMLFormElement>,
    suggestedQuestion?: string,
  ) {
    event?.preventDefault();

    const currentQuestion = (suggestedQuestion ?? question).trim();
    if (!currentQuestion || loading) return;

    setQuestion("");
    setMessages((previous) => [
      ...previous,
      { role: "user", content: currentQuestion },
    ]);
    setLoading(true);

    try {
      const baseUrl =
        process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

      const response = await fetch(`${baseUrl}/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: currentQuestion,
          snapshot_id: snapshot,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : "The request could not be completed.",
        );
      }

      setMessages((previous) => [
        ...previous,
        {
          role: "assistant",
          content: data.answer ?? "The agent returned no answer.",
        },
      ]);
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : "Unable to connect to the finance service.";

      setMessages((previous) => [
        ...previous,
        {
          role: "assistant",
          content: `Sorry, I couldn't complete that request. ${message} Check that the backend is running and try again.`,
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <div className="mx-auto flex min-h-screen max-w-6xl flex-col px-4 py-6 sm:px-8">
        <header className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-5">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-emerald-400 text-xl font-bold text-slate-950">
              ₹
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight">
                Finance Research Agent
              </h1>
              <p className="text-sm text-slate-400">
                Jemi · Your financial research assistant
              </p>
            </div>
          </div>

          <label className="flex items-center gap-2 text-sm text-slate-300">
            Dataset
            <select
              value={snapshot}
              onChange={(event) => setSnapshot(event.target.value)}
              disabled={loading}
              className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 outline-none focus:border-emerald-400"
            >
              <option value="sample_a">Sample A</option>
              <option value="sample_b">Sample B</option>
              <option value="sample_c">Sample C</option>
              <option value="sample_d">Sample D</option>
            </select>
          </label>
        </header>

        <section className="grid flex-1 items-start gap-6 py-8 md:grid-cols-[260px_1fr]">
          <aside className="space-y-5">
            <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
              <h2 className="font-semibold">What I can help with</h2>
              <ul className="mt-4 space-y-3 text-sm text-slate-400">
                <li>↗ Spending summaries</li>
                <li>↗ Category and merchant analysis</li>
                <li>↗ Fund NAV returns</li>
                <li>↗ Holding valuations</li>
              </ul>
            </div>

            <div>
              <h2 className="mb-3 text-sm font-semibold text-slate-300">
                Try an example
              </h2>
              <div className="space-y-2">
                {EXAMPLES.map((example) => (
                  <button
                    key={example}
                    type="button"
                    disabled={loading}
                    onClick={() => void sendQuestion(undefined, example)}
                    className="w-full rounded-xl border border-slate-800 bg-slate-900/50 p-3 text-left text-sm text-slate-300 transition hover:border-emerald-500/60 hover:bg-slate-900 disabled:opacity-50"
                  >
                    {example}
                  </button>
                ))}
              </div>
            </div>
          </aside>

          <section className="flex h-[min(600px,70vh)] min-h-[350px] flex-col overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/50">
            <div className="shrink-0 border-b border-slate-800 px-5 py-4">
              <h2 className="font-semibold">Ask Jemi</h2>
              <p className="mt-1 text-xs text-slate-400">
                Answers are based on the selected dataset.
              </p>
            </div>

            <div
              ref={messagesContainerRef}
              className="chat-scrollbar flex-1 min-h-0 space-y-5 overflow-y-auto p-5"
              aria-live="polite"
            >
              {messages.map((message, index) => (
                <div
                  key={`${index}-${message.role}`}
                  className={`flex ${
                    message.role === "user" ? "justify-end" : "justify-start"
                  }`}
                >
                  <div
                    className={`max-w-[90%] rounded-2xl px-4 py-3 text-sm leading-7 ${
                      message.role === "user"
                        ? "bg-emerald-400 text-slate-950"
                        : "border border-slate-800 bg-slate-950 text-slate-200"
                    }`}
                  >
                    <p className="mb-1 text-xs font-semibold opacity-70">
                      {message.role === "user" ? "You" : "Jemi"}
                    </p>
                    <p className="whitespace-pre-wrap break-words">
                      {message.content}
                    </p>
                  </div>
                </div>
              ))}

              {loading && (
                <div role="status" className="text-sm text-emerald-300">
                  Jemi is checking your financial data...
                </div>
              )}
            </div>

            <form
              onSubmit={(event) => void sendQuestion(event)}
              className="shrink-0 border-t border-slate-800 p-4"
            >
              <div className="flex items-end gap-3">
                <textarea
                  value={question}
                  onChange={(event) => setQuestion(event.target.value)}
                  onKeyDown={(event) => {
                    if (
                      event.key === "Enter" &&
                      !event.shiftKey &&
                      !event.nativeEvent.isComposing
                    ) {
                      event.preventDefault();
                      event.currentTarget.form?.requestSubmit();
                    }
                  }}
                  placeholder="Ask about spending, funds, or holdings..."
                  aria-label="Your financial question"
                  maxLength={2000}
                  rows={2}
                  disabled={loading}
                  className="min-h-14 flex-1 resize-y rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm outline-none placeholder:text-slate-500 focus:border-emerald-400 disabled:opacity-60"
                />
                <button
                  type="submit"
                  disabled={loading || !question.trim()}
                  className="rounded-xl bg-emerald-400 px-5 py-3 text-sm font-bold text-slate-950 transition hover:bg-emerald-300 disabled:cursor-not-allowed disabled:opacity-40"
                >
                  {loading ? "Thinking..." : "Ask"}
                </button>
              </div>
              <p className="mt-2 text-xs text-slate-500">
                Enter to send · Shift+Enter for a new line
              </p>
            </form>
          </section>
        </section>

        <footer className="border-t border-slate-800 py-4 text-center text-xs text-slate-500">
          Finance Research Agent · Historical calculations are not
          investment advice.
        </footer>
      </div>
    </main>
  );
}
