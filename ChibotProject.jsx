import { ArrowLeft } from "lucide-react";
import { Link } from "react-router-dom";
import { ThemeToggle } from "../components/ThemeToggle";

const ScreenshotPlaceholder = ({ label }) => {
  return (
    <div className="w-full rounded-xl border-2 border-dashed border-primary/40 bg-card p-10 text-center">
      <p className="text-lg font-semibold">Screenshot Placeholder</p>
      <p className="text-muted-foreground mt-2">{label}</p>
      <p className="text-sm text-muted-foreground mt-1">
        Add your image later in this section.
      </p>
    </div>
  );
};

export const ChibotProject = () => {
  return (
    <div className="min-h-screen bg-background text-foreground px-4 py-12">
      <ThemeToggle />
      <div className="container max-w-4xl mx-auto space-y-12 text-left">
        <Link
          to="/"
          className="inline-flex items-center gap-2 text-primary hover:opacity-80 transition-opacity"
        >
          <ArrowLeft size={18} />
          Back to Portfolio
        </Link>

        <section className="space-y-4">
          <p className="text-sm uppercase tracking-wide text-primary font-semibold">
            Personal Project
          </p>
          <h1 className="text-4xl md:text-5xl font-bold leading-tight">
            Chibot
          </h1>
          <p className="text-xl text-muted-foreground">
            A Private, Local AI Chat Assistant You Can Reach from Anywhere
          </p>
          <p className="text-primary">
            React, Vite, Python, FastAPI, LangChain, Ollama, Tailscale, GitHub Pages
          </p>

          <div className="flex flex-wrap gap-4 pt-2">
            <a
              href="https://aditfadhillah.github.io/Local-AI-Model-Chibot-/"
              target="_blank"
              rel="noopener noreferrer"
              className="cosmic-button"
            >
              Live Demo
            </a>
            <a
              href="https://github.com/AditFadhillah/Local-AI-Model-Chibot-/"
              target="_blank"
              rel="noopener noreferrer"
              className="cosmic-button"
            >
              Source Code
            </a>
          </div>
        </section>

        <section className="space-y-4">
          <ScreenshotPlaceholder label="Hero: Chibot chat interface" />
        </section>

        <section className="space-y-4">
          <h2 className="text-2xl font-bold">Overview</h2>
          <p className="text-muted-foreground leading-relaxed">
            Chibot is a chat web app that talks to a language model running entirely on
            my own laptop through Ollama. No cloud AI API or API key is needed. The
            frontend is hosted on GitHub Pages, and a secured backend on my PC serves
            the model, so the chat works from my phone as well as my laptop.
          </p>
        </section>

        <section className="space-y-4">
          <h2 className="text-2xl font-bold">Motivation</h2>
          <p className="text-muted-foreground leading-relaxed">
            I wanted a personal AI assistant that keeps my conversations on my own
            hardware and that I can still show to others online. Chibot is a hands-on
            way to learn how a model is served, streamed to a browser, and exposed safely
            from a home machine.
          </p>
        </section>

        <section className="space-y-6">
          <h2 className="text-2xl font-bold">Features</h2>

          <div className="space-y-3">
            <h3 className="text-xl font-semibold">Streamed Local Responses</h3>
            <p className="text-muted-foreground">
              Answers appear token by token as the model writes them. The backend
              streams responses from Ollama through LangChain to the browser, so long
              replies show progress straight away.
            </p>
            <ScreenshotPlaceholder label="Streaming response in progress" />
          </div>

          <div className="space-y-3">
            <h3 className="text-xl font-semibold">Model Selection and Chat History</h3>
            <p className="text-muted-foreground">
              A model selector lists the models the server allows. Conversations are kept
              in browser local storage, so they survive a page refresh. Markdown and code
              blocks are rendered with syntax highlighting.
            </p>
            <ScreenshotPlaceholder label="Model selector and formatted code reply" />
          </div>

          <div className="space-y-3">
            <h3 className="text-xl font-semibold">Secure Public Access</h3>
            <p className="text-muted-foreground">
              The backend is reachable through Tailscale Funnel and protected with an API
              key, CORS limits, per-IP rate limiting, input size limits, and a cap on
              output tokens. Health and status endpoints show whether Ollama is running.
            </p>
            <ScreenshotPlaceholder label="Health and status check" />
          </div>
        </section>

        <section className="space-y-4">
          <h2 className="text-2xl font-bold">Technical Architecture</h2>
          <p className="text-muted-foreground">
            A React and Vite frontend is deployed to GitHub Pages with GitHub Actions. It
            calls a FastAPI backend on my PC through a Tailscale Funnel URL. The backend
            uses LangChain to send prompts to Ollama, which runs the qwen3:8b model
            locally. Each request is logged with a request ID, and the chat outcome is
            recorded in a log file.
          </p>
          <ScreenshotPlaceholder label="Architecture diagram: GitHub Pages, Tailscale Funnel, FastAPI, Ollama" />
        </section>

        <section className="space-y-4">
          <h2 className="text-2xl font-bold">Engineering Challenges</h2>
          <ul className="list-disc pl-5 space-y-2 text-muted-foreground">
            <li>Streaming tokens from a local model through a backend to a remote browser.</li>
            <li>Exposing a home PC to the internet without leaving the model open to misuse.</li>
            <li>Keeping replies responsive on limited laptop hardware, where the first token can take a while.</li>
            <li>Handling a user who stops a request midway, so the backend stops cleanly.</li>
          </ul>
        </section>

        <section className="space-y-4">
          <h2 className="text-2xl font-bold">Status and Next Steps</h2>
          <p className="text-muted-foreground">
            Chibot works end to end: local chat, the public GitHub Pages site, and phone
            access through the Funnel. Next I want to improve response speed on this
            hardware and add more screenshots and a short demo video.
          </p>
        </section>
      </div>
    </div>
  );
};
