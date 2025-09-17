from src.pipeline import run_daily_pipeline
def main():
    path = run_daily_pipeline()
    print(path)
if __name__ == "__main__":
    main()
