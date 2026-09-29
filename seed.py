"""Run once from the terminal to load demo data:  python seed.py"""
import config
import pipeline

if __name__ == "__main__":
    missing = config.missing_config()
    if missing:
        raise SystemExit(f"Fill these in your .env first: {', '.join(missing)}")
    pipeline.load_demo(progress=lambda i, n, t: print(f"[{i}/{n}] ingesting: {t}"))
    print("Done. Now run:  streamlit run app.py")
