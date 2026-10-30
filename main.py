"""CLI entry point for testing the research workflow."""
import argparse
import json
from core.config import get_settings
from core.llm import GroqProvider
from orchestrator import ResearchOrchestrator

def main():
    parser = argparse.ArgumentParser(description="ResearchPilot AI — Autonomous Research CLI")
    parser.add_argument("question", help="Research question")
    parser.add_argument("--depth", choices=["quick", "standard", "deep"], default="standard", help="Research depth")
    args = parser.parse_args()

    settings = get_settings()
    llm = GroqProvider(
        api_key=settings["groq_api_key"],
        model=settings["groq_model"],
        fallback_model=settings.get("groq_fallback_model")
    )
    agent = ResearchOrchestrator(settings, llm=llm)
    result = agent.run(args.question, depth=args.depth)
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
